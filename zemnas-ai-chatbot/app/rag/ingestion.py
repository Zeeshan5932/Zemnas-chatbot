from app.rag.loader import (
    load_from_sitemap
)

from app.rag.splitter import (
    split_documents
)

from app.rag.vectorstore import (
    create_vectorstore
)


def ingest_website():

    print(
        "Starting website ingestion..."
    )


    # Step 1
    documents = load_from_sitemap()


    if not documents:

        raise Exception(
            "No website documents found."
        )


    print(
        f"Loaded {len(documents)} pages"
    )


    # Step 2
    chunks = split_documents(
        documents
    )


    print(
        f"Created {len(chunks)} chunks"
    )


    # Step 3
    create_vectorstore(
        chunks
    )


    print(
        "Vector database created successfully!"
    )