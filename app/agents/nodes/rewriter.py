import logfire
from app.agents.state import AgentState
from app.gateway import get_langchain_llm

llm = get_langchain_llm(feature="rewriter")

def rewrite_query_node(state: AgentState):
    """
    Rewrites the search query to improve retrieval performance after a failed grade.
    """
    old_query = state["current_query"]
    retry_count = state.get("retry_count", 0) + 1

    prompt = f"""
    You are an expert Query Refiner for an Enterprise Kubernetes and IT RAG system.
    The previous search query failed to retrieve relevant documents.
    
    ORIGINAL QUERY: "{old_query}"
    
    Task:
    Rewrite the query to be more specific, keyword-rich, and optimized for vector/hybrid search. Include precise technical terminology, resource kinds (e.g., Pod, Job, CronJob), or CLI flags if applicable.
    Output ONLY the refined query string.
    """

    with logfire.span("Query Rewriting", retry_count=retry_count):
        new_query = llm.invoke(prompt).content.strip()
        logfire.info(f"Rewritten query (Attempt {retry_count}): '{new_query}'")

    return {
        "current_query": new_query,
        "retry_count": retry_count,
        "plan": state["plan"] + [f"Query Rewritten (Retry {retry_count}): {new_query}"]
    }