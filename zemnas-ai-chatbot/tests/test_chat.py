import unittest

from pydantic import ValidationError

from app.schemas.chat import ChatRequest


class ChatSchemaTests(unittest.TestCase):
	def test_chat_request_validates_size(self):
		request = ChatRequest(session_id="session-1", message="Hi")
		self.assertEqual(request.session_id, "session-1")
		with self.assertRaises(ValidationError):
			ChatRequest(session_id="", message="Hi")


if __name__ == "__main__":
	unittest.main()
