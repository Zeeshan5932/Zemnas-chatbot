import unittest

from app.agent.nodes import get_missing_fields, is_lead_complete
from app.agent.router import route_after_intent, route_after_retrieval


class AgentUnitTests(unittest.TestCase):
	def test_intent_routes_are_meaningful(self):
		self.assertEqual(route_after_intent({"intent": "general_chat"}), "generate_response")
		self.assertEqual(route_after_intent({"intent": "company_information"}), "retrieve_knowledge")
		self.assertEqual(route_after_intent({"intent": "service_inquiry"}), "retrieve_knowledge")
		self.assertEqual(route_after_intent({"intent": "lead_inquiry"}), "extract_lead_information")
		self.assertEqual(route_after_retrieval({"intent": "service_inquiry"}), "extract_lead_information")
		self.assertEqual(route_after_retrieval({"intent": "company_information"}), "generate_response")

	def test_missing_fields_and_completion(self):
		state = {"name": "Ali", "service": "AI chatbot", "project_description": "Ecommerce bot"}
		self.assertEqual(get_missing_fields(state), ["email", "phone"])
		self.assertFalse(is_lead_complete(state))
		state.update({"email": "ali@example.com", "phone": "+1 555 0100"})
		self.assertTrue(is_lead_complete(state))


if __name__ == "__main__":
	unittest.main()
