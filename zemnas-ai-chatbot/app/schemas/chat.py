from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):

    session_id: str = Field(
        ...,
        description="Unique conversation session ID"
    )

    message: str = Field(
        ...,
        min_length=1
    )


class ChatResponse(BaseModel):

    response: str

    session_id: str

    intent: Optional[str] = None

    lead_data: Optional[Dict[str, Any]] = None

    lead_status: Optional[str] = None