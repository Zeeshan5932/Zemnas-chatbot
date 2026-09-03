from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """
    Create the Gemini client once and reuse it.

    This avoids recreating the LLM client for every request.
    """

    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    return ChatGroq(
        model=settings.GROQ_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=settings.TEMPERATURE,
    )