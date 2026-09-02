from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Zemnas AI Chatbot"

    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"

    PORT: int = 8000

    GOOGLE_API_KEY: str

    MODEL_NAME: str = "gemini-2.5-flash"

    DATABASE_URL: str

    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    WEBSITE_URL: str = "https://www.zemnas.com"

    TEMPERATURE: float = 0.3

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()