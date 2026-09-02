from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Zemnas AI Chatbot"

    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"

    PORT: int = 8000

    GOOGLE_API_KEY: Optional[str] = None

    MODEL_NAME: str = "gemini-2.5-flash"

    DATABASE_URL: str = "sqlite:///./zemnas.db"

    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    WEBSITE_URL: str = "https://www.zemnas.com"

    TEMPERATURE: float = 0.3

    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()