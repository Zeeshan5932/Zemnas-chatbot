RAG_INTENTS = {
    "company_information",
    "service_inquiry",
    "pricing_inquiry",
}


LEAD_INTENTS = {
    "lead_inquiry",
    "appointment_booking",
}


def route_after_intent(state):
    intent = state.get(
        "intent",
        "general_chat"
    )

    # Zemnas factual knowledge required
    if intent in RAG_INTENTS:
        return "retrieve_knowledge"

    # Lead / project conversation
    if intent in LEAD_INTENTS:
        return "generate_response"

    # Casual / support / other
    return "generate_response"


def route_after_retrieval(state):
    return "generate_response"