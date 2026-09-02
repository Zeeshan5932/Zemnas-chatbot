from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.chat import router as chat_router
from app.api.health import router as health_router

from app.database.session import init_db


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():

    init_db()


app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"]
)


app.include_router(
    chat_router,
    prefix="/api/v1",
    tags=["Chat"]
)


@app.get("/")
def root():

    return {
        "message": "Zemnas AI Chatbot API is running"
    }