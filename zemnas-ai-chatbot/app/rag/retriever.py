from app.rag.vectorstore import get_vectorstore


def retrieve_documents(
    query: str,
    k: int = 5
):

    vectorstore = get_vectorstore()

    documents = vectorstore.similarity_search(
        query,
        k=k
    )

    return documents


def get_context(query: str):

    documents = retrieve_documents(query)

    if not documents:

        return ""

    context_parts = []

    for document in documents:

        context_parts.append(
            document.page_content
        )

    return "\n\n".join(context_parts)