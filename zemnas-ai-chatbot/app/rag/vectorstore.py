try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)

from app.config import settings


def get_embeddings():

    return GoogleGenerativeAIEmbeddings(

        model="models/text-embedding-004",

        google_api_key=settings.GOOGLE_API_KEY
    )


def create_vectorstore(documents):

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(

        documents=documents,

        embedding=embeddings,

        persist_directory=
        settings.CHROMA_PERSIST_DIRECTORY
    )

    return vectorstore


def get_vectorstore():

    embeddings = get_embeddings()

    return Chroma(

        persist_directory=
        settings.CHROMA_PERSIST_DIRECTORY,

        embedding_function=embeddings
    )