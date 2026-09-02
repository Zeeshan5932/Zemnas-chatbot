RETRIEVAL_INTENTS = {"company_information", "service_inquiry", "pricing_inquiry"}
LEAD_INTENTS = {"service_inquiry", "pricing_inquiry", "lead_inquiry", "appointment_booking"}


def route_after_intent(state):
	intent = state.get("intent", "general_chat")
	if intent in RETRIEVAL_INTENTS:
		return "retrieve_knowledge"
	if intent in LEAD_INTENTS:
		return "extract_lead_information"
	return "generate_response"


def route_after_retrieval(state):
	if state.get("intent") in {"service_inquiry", "pricing_inquiry"}:
		return "extract_lead_information"
	return "generate_response"
