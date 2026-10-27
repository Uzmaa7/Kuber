import logfire
from app.agents.state import AgentState
from app.services.retrieval.qdrant_service import search_enterprise_knowledge
from app.services.retrieval.ranking_service import rerank_documents


def retrieve_node(state: AgentState):
    """
    Performs hybrid search and semantic reranking for technical queries.
    """
    query = state["current_query"]
    
    with logfire.span("Knowledge Retrieval"):
        logfire.info(f"Searching Qdrant for: {query}")

        # Qdrant se list[dict] milti hai
        raw_results = search_enterprise_knowledge(query, limit=15)
        logfire.info(f"Retrieved {len(raw_results)} candidates from Vector DB")
        
        with logfire.span("Semantic Reranking"):
            # Seedha raw_results (list[dict]) pass karo kyunki reranker ko source/content dono chahiye
            reranked_docs = rerank_documents(query, raw_results, top_n=5)
            
            logfire.info("Reranking complete. Kept top 5 most relevant chunks.")

            
            
        # Ab source aur content dono ko nicely format kar lo LLM ke liye
        formatted_docs = [
            f"SOURCE: {doc['source']}\nCONTENT: {doc['content']}" 
            for doc in reranked_docs
        ]
    
    return {
        "documents": formatted_docs,
        "raw_documents": reranked_docs,
        "status": f"Found technical context.",
        "plan": state["plan"] + ["Context Retrieved"]
    }