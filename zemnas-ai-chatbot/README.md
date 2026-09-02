 # Zemnas AI Chatbot

FastAPI backend for a Zemnas website assistant using LangGraph, Gemini, LangChain RAG, Chroma, and SQLAlchemy.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and set `GOOGLE_API_KEY`.
3. Build the website index once:

```powershell
python scripts/ingest_website.py
```

4. Start the API:

```powershell
uvicorn app.main:app --reload
```

The API is available at `/api/v1/chat` and `/api/v1/health`.

## Configuration

`DATABASE_URL` defaults to local SQLite. Use PostgreSQL in deployment. `CORS_ORIGINS` is a comma-separated allowlist. Calendar booking is intentionally an integration boundary: appointment requests are stored with status `requested` until a provider adapter is configured.

## Tests

```powershell
pytest
```
