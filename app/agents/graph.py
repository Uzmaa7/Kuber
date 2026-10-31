from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retriever import retrieve_node
from app.agents.nodes.responder import generate_node
from app.agents.nodes.grader import grade_documents_node
from app.agents.nodes.rewriter import rewrite_query_node


# 1. Initialize the State Graph
graph = StateGraph(AgentState)


# 2. Define the Nodes
graph.add_node("planner", planner_node)
graph.add_node("retriever", retrieve_node)
graph.add_node("grader", grade_documents_node)
graph.add_node("rewriter", rewrite_query_node)
graph.add_node("responder", generate_node)

# 3. Define the Edges & Routing Logic
def route_planner(state: AgentState):
    """
    Routes the workflow based on the planner's decision.
    """
    if state["current_query"] == "CONVERSATIONAL":
        return "responder"
    return "retriever"




def decide_to_generate(state: AgentState):
    """
    Determines whether to generate an answer, or re-write the query.
    """
    score = state.get("document_score", "no")
    retry_count = state.get("retry_count", 0)

   
    if score == "yes" or retry_count >= 2:
        return "generate"
    else:
        # Increment retry count and route to rewriter
        # state["retry_count"] = retry_count + 1
        return "rewrite"

# ----------------- BASELINE TEMPORARY CHANGE -----------------
# Planner node ko bypass karke direct retriever par bhej rahe hain
# graph.add_edge("planner", "retriever")
# -------------------------------------------------------------


graph.set_entry_point("planner")


graph.add_conditional_edges(
    "planner",
    route_planner,
    {
        "retriever": "retriever",
        "responder": "responder"
    }
)

graph.add_edge("retriever", "grader")

graph.add_conditional_edges(
    "grader",
    decide_to_generate, 
    {
        "generate": "responder",
        "rewrite": "rewriter",
    }
)
graph.add_edge("rewriter", "retriever")
graph.add_edge("responder", END)


# --- MEMORY UPGRADE ---
# MemorySaver allows the agent to remember conversations based on 'thread_id'
checkpointer = MemorySaver()


# 4. Compile the Graph with Memory
workflow = graph.compile(checkpointer=checkpointer)








