import logfire
from app.agents.state import AgentState
from app.config import settings
from langchain_groq import ChatGroq
from app.gateway import portkey_client, extract_cache_status





def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.

    """
    query = state["current_query"]

    history_str = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    user_msg = state["messages"][-1]["content"] if state["messages"] else ""

    if query == "CONVERSATIONAL":
        logfire.info("Generating conversational response using memory.")
        prompt = f"""
        You are a friendly and helpful Enterprise AI Assistant.
        Answer the user's latest message using the CONVERSATION HISTORY below.

        CONVERSATION HISTORY:
        {history_str}

        LATEST MESSAGE:
        "{user_msg}"
        """
    else:

        
        
        if state.get("document_score") == "no" and state.get("retry_count", 0) >= 2:
            logfire.warning("Max retries reached with irrelevant documents. Returning fallback message.")
            fallback_msg = "I'm sorry, but I couldn't find any relevant documentation regarding this."
            return {
                "final_answer": fallback_msg,
                "status": "No relevant documents found after retries.",
                "plan": state["plan"] + ["Fallback: Max retries exceeded"],
                "messages": [{"role": "assistant", "content": fallback_msg}]
            }


        # ... 

        logfire.info("Generating technical RAG response.")
        max_context_chars = 25000
        full_context = ""

        for doc in state["documents"]:
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break

        prompt = f"""
        You are a Senior Technical Architect specializing in Kubernetes.
        Answer the question using the TECHNICAL CONTEXT provided below.
        
        CRITICAL OUTPUT INSTRUCTIONS:
        1. PRIORITY ON CODE/MANIFESTS: Always output complete, fully valid YAML manifests, configurations, or CLI commands FIRST. Never truncate or compromise a code block.
        2. STRICT BREVITY FOR TEXT: Limit all prose and explanation to maximum 2-3 sentences. Omit all greeting intros, preambles, and lengthy bullet points.
        3. NO VERBOSE QUOTING: Do not repeat the context verbosely.

        TECHNICAL CONTEXT:
        {full_context}

        CONVERSATION HISTORY:
        {history_str}

        USER QUESTION:
        "{user_msg}"
        """

    with logfire.span("LLM Synthesis"):
        try:
            response = portkey_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=600
            )
            content = response.choices[0].message.content
            cache_status = extract_cache_status(response)
            is_cache_hit = cache_status == "HIT"

            if is_cache_hit:
                logfire.info("Gateway Cache Hit — response served from Portkey cache.")
                plan_update = state["plan"] + ["Cache: Hit"]
                status = "Cache hit — instant response."
            else:
                logfire.info("Response synthesised via LLM.")
                plan_update = state["plan"]
                status = "Response generated."

            return {
                "final_answer": content,
                "status": status,
                "plan": plan_update,
                "messages": [{"role": "assistant", "content": content}]
            }

        except Exception as e:
            logfire.error(f"LLM Generation failed: {e}")
            raise e
