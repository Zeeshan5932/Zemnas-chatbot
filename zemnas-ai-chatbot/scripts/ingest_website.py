from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from app.config import settings

from app.rag.crawler import (
    WebsiteCrawler
)

from app.rag.vectorstore import (
    get_vectorstore
)


def ingest_website():

    print("=" * 60)

    print(
        "Starting Zemnas Website Ingestion"
    )

    print("=" * 60)


    crawler = WebsiteCrawler(

        base_url=settings.WEBSITE_URL,

        max_pages=30
    )


    documents = crawler.crawl()


    print(
        f"\nTotal pages collected: "
        f"{len(documents)}"
    )


    splitter = RecursiveCharacterTextSplitter(

        chunk_size=1000,

        chunk_overlap=200
    )


    chunks = splitter.split_documents(
        documents
    )


    print(
        f"Total chunks created: "
        f"{len(chunks)}"
    )


    vectorstore = get_vectorstore()


    vectorstore.add_documents(
        chunks
    )


    print(
        "\nWebsite ingestion completed successfully!"
    )


if __name__ == "__main__":

    ingest_website()