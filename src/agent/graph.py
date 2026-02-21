from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.state import AgentState
from agent.nodes import (
    context_manager_node,
    intent_classifier_node,
    clarification_node,
    plan_creator_node,
    plan_editor_node,
    summarizer_node,
    responder_node,
    route_intent
)


def create_graph():
    #initialize graph with our state
    graph = StateGraph(AgentState)

    #add all nodes 
    graph.add_node("context_manager", context_manager_node)
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("plan_creator", plan_creator_node)
    graph.add_node("plan_editor", plan_editor_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("responder", responder_node)

    #entry point
    #every conversation starts at context_manager
    graph.set_entry_point("context_manager")

    #fixed edges
    # context_manager always goes to intent_classifier
    graph.add_edge("context_manager", "intent_classifier")

    #conditional edges
    #intent_classifier uses route_intent to decide next node
    graph.add_conditional_edges(
        "intent_classifier",
        route_intent,
        {
            "plan_creator": "plan_creator",
            "plan_editor": "plan_editor",
            "clarification": "clarification",
            "summarizer": "summarizer",
            "responder": "responder"
        }
    )

    #All action nodes go to END
    graph.add_edge("clarification", END)
    graph.add_edge("plan_creator", END)
    graph.add_edge("plan_editor", END)
    graph.add_edge("summarizer", END)
    graph.add_edge("responder", END)

    #Memory
    # MemorySaver persists state across turns using thread_id
    memory = MemorySaver()

    #compile and return
    return graph.compile(checkpointer=memory)


#single instance used across the app
planning_graph = create_graph()