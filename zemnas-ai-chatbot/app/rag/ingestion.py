from app.rag.loader import load_from_text_file
from app.rag.splitter import split_documents
from app.rag.vectorstore import create_vectorstore


def ingest_website():

    print("Starting Zemnas knowledge ingestion...")

    # Step 1: Load zemnas.txt
    documents = load_from_text_file()

    if not documents:
        raise Exception(
            "No Zemnas knowledge documents found."
        )

    print(
        f"Loaded {len(documents)} document(s)"
    )

    # Step 2: Split into chunks
    chunks = split_documents(documents)

    print(
        f"Created {len(chunks)} chunks"
    )

    # Step 3: Create Chroma vector database
    create_vectorstore(chunks)

    print(
        "Zemnas vector database created successfully!"
    )