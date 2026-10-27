# ============================================================
# CRITICAL: logfire MUST be configured before ALL other imports
# so that spans from all modules are captured from the start.
# ============================================================
import logfire
import os
from dotenv import load_dotenv

load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
import logging
logging.getLogger("nemoguardrails").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Now safe to import app modules - logfire is already active
from fastapi import FastAPI, Response
from app.agents.graph import workflow
from app.guardrails import initialize_rails, guard
from app.services.cache.redis_cache import create_redis_cache_index
from app.services.retrieval.embedding import embed_query
from app.services.cache.redis_cache import check_semantic_cache, store_in_semantic_cache

from pydantic import BaseModel
from typing import Optional


# Initialize FastAPI
app = FastAPI(title="Enterprise Agentic RAG API")


@app.on_event("startup")
def startup_event():
    initialize_rails()
    create_redis_cache_index()
    logfire.info("Redis Semantic Cache index initialized.")

class QueryRequest(BaseModel):
    q: str
    thread_id: Optional[str] = "default_user"
    
    
@app.get("/")
def home():
    return {"message": "Enterprise LangGraph RAG API is live."}


@app.get("/graph")
def get_graph_image():
    """
    Returns the Mermaid image of the agent's workflow.
    """
    try:
        png_bytes = workflow.get_graph().draw_mermaid_png()
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        return {"error": f"Could not generate graph image: {e}"}
    
    
@app.post("/query")
def query(request: QueryRequest):
    """
    Executes the LangGraph RAG flow with memory using a POST request.
    """
    q = request.q
    thread_id = request.thread_id

    initial_state = {
        "messages": [{"role": "user", "content": q}],
        "current_query": q,
        "documents": [],
        "plan": ["Start"],
        "status": "Initializing Graph..."
    }
    
    # Configuration for Memory (Thread ID)
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        


        # 1. Query ka embedding nikalo
        query_vector = embed_query(q)

        # 2. Redis semantic cache check karo
        cached_answer = check_semantic_cache(query_vector, threshold=0.71)

        if cached_answer:
            print(f"🚀 [REDIS CACHE HIT] Query served instantly for: '{q}'")
            return {
                "question": q,
                "answer": cached_answer,
                "thought_process": ["Cache: Hit (Redis Semantic Cache)", "Retrieval: Skipped"],
                "status": "Cache hit — instant response (<50ms).",
                "sources": []
            }


        print(f"❌ [REDIS CACHE MISS] Running normal RAG pipeline for: '{q}'")



        # Gate 1: NeMo Guardrails — blocks off-topic, jailbreaks, and handles dialog
        rail_fired, rail_response = guard(q)
        if rail_fired:
            logfire.info(f"Request blocked by guardrails | thread={thread_id}")
            return {
                "question": q,
                "answer": rail_response,
                "thought_process": ["Intent: Guardrails Fired", "Retrieval: Skipped"],
                "status": "Blocked by guardrails.",
                "sources": []
            }

        final_output = workflow.invoke(initial_state, config=config)
        final_answer = final_output.get("final_answer")

        if final_answer:
            store_in_semantic_cache(query=q, response=final_answer, query_vector=query_vector)
            logfire.info(f"New response stored in Redis Semantic Cache for query: '{q}'")
        
        
        return {
            "question": q,
            "answer": final_output.get("final_answer"),
            "thought_process": final_output.get("plan"),
            "status": final_output.get("status"),
            "sources": final_output.get("raw_documents", [])
        }
    except Exception as e:
        logfire.error(f" Backend Execution Failed: {e}")
        return {
            "question": q,
            "answer": "I apologize, but I encountered an internal error while processing your request. Please try again later.",
            "thought_process": ["Error encountered during execution."],
            "status": "error",
            "sources": []
        }
