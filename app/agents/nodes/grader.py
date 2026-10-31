import logfire
from app.agents.state import AgentState
from app.gateway import get_langchain_llm

llm = get_langchain_llm(feature="grader")

def grade_documents_node(state: AgentState):
    """
    Evaluates whether the retrieved documents are relevant to the user query or not.
    """
    query = state["current_query"]
    documents = state["documents"]

    docs_text = "\n\n".join(documents) if documents else "No documents found."

    prompt = f"""
    You are a strict technical grader assessing the relevance of retrieved documents to a user query.
    
    USER QUERY: "{query}"
    
    RETRIEVED DOCUMENTS:
    {docs_text}
    
    Task:
    Evaluate if the retrieved documents contain sufficient information to directly answer the user query.
    Output ONLY 'yes' if they are relevant, or 'no' if they are irrelevant or insufficient. Do not add any extra text or punctuation.
    """

    with logfire.span("Document Grading"):
        response = llm.invoke(prompt).content.strip().lower()
        score = "yes" if "yes" in response else "no"
        logfire.info(f"Grading result for query '{query}': {score}")

    return {
        "document_score": score,
        "plan": state["plan"] + [f"Document Graded: {score.upper()}"]
    }