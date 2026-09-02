import unittest

from langchain_core.documents import Document

from app.rag.splitter import split_documents


class RagUnitTests(unittest.TestCase):
	def test_documents_are_split_with_metadata(self):
		chunks = split_documents([Document(page_content="Zemnas services " * 200, metadata={"source": "test"})])
		self.assertGreater(len(chunks), 1)
		self.assertEqual(chunks[0].metadata["source"], "test")


if __name__ == "__main__":
	unittest.main()
