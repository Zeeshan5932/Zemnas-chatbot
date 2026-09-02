from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger

from app.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from app.services.chat_service import process_chat


router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    try:

        result = process_chat(
            session_id=request.session_id,
            message=request.message
        )

        return result

    except Exception:

        logger.exception("Chat request failed for session %s", request.session_id)

        raise HTTPException(
            status_code=500,
            detail="We could not process your message right now. Please try again."
        )