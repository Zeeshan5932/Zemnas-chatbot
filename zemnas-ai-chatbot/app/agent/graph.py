from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.agent.state import (
    AgentState
)

from app.agent.nodes import (

    classify_intent,

    retrieve_knowledge,

    extract_lead_information,

    check_lead_status,

    generate_response
)
from app.agent.router import route_after_intent, route_after_retrieval


def create_graph():

    workflow = StateGraph(
        AgentState
    )


    workflow.add_node(

        "classify_intent",

        classify_intent
    )


    workflow.add_node(

        "retrieve_knowledge",

        retrieve_knowledge
    )


    workflow.add_node(

        "extract_lead_information",

        extract_lead_information
    )


    workflow.add_node(

        "check_lead_status",

        check_lead_status
    )


    workflow.add_node(

        "generate_response",

        generate_response
    )


    workflow.add_edge(

        START,

        "classify_intent"
    )


    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "retrieve_knowledge": "retrieve_knowledge",
            "extract_lead_information": "extract_lead_information",
            "generate_response": "generate_response",
        },
    )


    workflow.add_conditional_edges(
        "retrieve_knowledge",
        route_after_retrieval,
        {
            "extract_lead_information": "extract_lead_information",
            "generate_response": "generate_response",
        },
    )


    workflow.add_edge(

        "extract_lead_information",

        "check_lead_status"
    )


    workflow.add_edge(

        "check_lead_status",

        "generate_response"
    )


    workflow.add_edge(

        "generate_response",

        END
    )


    return workflow.compile()


chatbot_graph = create_graph()