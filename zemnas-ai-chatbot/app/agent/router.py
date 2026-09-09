
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


def route_after_lead_status(state):
    """
    Appointment flow routing.

    If the user wants an appointment and both date and time
    are already available, save the appointment request.

    Otherwise continue to the normal response node so the
    assistant can ask for the missing appointment detail.
    """

    intent = state.get(
        "intent",
        "general_chat"
    )

    appointment_requested = state.get(
        "appointment_requested",
        False
    )

    appointment_date = state.get(
        "appointment_date"
    )

    appointment_time = state.get(
        "appointment_time"
    )

    if (
        intent == "appointment_booking"
        or appointment_requested
    ):
        if appointment_date and appointment_time:
            return "save_appointment_request"

    return "generate_response"
