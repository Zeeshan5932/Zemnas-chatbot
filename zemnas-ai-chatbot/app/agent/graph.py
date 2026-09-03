from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from app.agent.state import AgentState

from app.agent.nodes import (
    analyze_message,
    retrieve_knowledge,
    check_lead_status,
    generate_response,
)

from app.agent.router import (
    route_after_intent,
    route_after_retrieval,
)


def create_graph():

    workflow = StateGraph(
        AgentState
    )

    # Nodes
    workflow.add_node(
        "analyze_message",
        analyze_message
    )

    workflow.add_node(
        "retrieve_knowledge",
        retrieve_knowledge
    )

    workflow.add_node(
        "check_lead_status",
        check_lead_status
    )

    workflow.add_node(
        "generate_response",
        generate_response
    )

    # Start
    workflow.add_edge(
        START,
        "analyze_message"
    )

    # Intent routing
    workflow.add_conditional_edges(
        "analyze_message",
        route_after_intent,
        {
            "retrieve_knowledge":
                "retrieve_knowledge",

            "generate_response":
                "check_lead_status",
        }
    )

    # RAG → lead status
    workflow.add_edge(
        "retrieve_knowledge",
        "check_lead_status"
    )

    # Lead status → response
    workflow.add_edge(
        "check_lead_status",
        "generate_response"
    )

    # End
    workflow.add_edge(
        "generate_response",
        END
    )

    return workflow.compile()


chatbot_graph = create_graph()