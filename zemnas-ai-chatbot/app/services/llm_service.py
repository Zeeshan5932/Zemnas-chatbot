from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


_llm = None


def get_llm():

    global _llm

    if _llm is None:

        _llm = ChatGoogleGenerativeAI(

            model=settings.MODEL_NAME,

            google_api_key=settings.GOOGLE_API_KEY,

            temperature=settings.TEMPERATURE
        )

    return _llm