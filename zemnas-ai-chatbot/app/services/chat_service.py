from typing import Optional

from app.agent.graph import chatbot_graph
from app.core.logging import get_logger
from app.database.models import Lead, Message
from app.database.session import SessionLocal
from app.services.appointment_service import request_appointment
from app.services.lead_service import update_lead


logger = get_logger(__name__)


def save_message(db, session_id: str, role: str, content: str) -> None:
    db.add(Message(session_id=session_id, role=role, content=content))
    db.commit()


def get_conversation_history(db, session_id: str, limit: int = 10) -> list:
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()
    return [{"role": item.role, "content": item.content} for item in messages]


def _lead_state(lead: Optional[Lead]) -> dict:
    if lead is None:
        return {}
    fields = (
        "name", "email", "phone", "company_name", "service",
        "project_description", "budget", "timeline",
        "appointment_requested", "appointment_date", "appointment_time",
    )
    return {field: getattr(lead, field) for field in fields if getattr(lead, field) is not None}


def process_chat(session_id: str, message: str):
    db = SessionLocal()
    try:
        history = get_conversation_history(db, session_id)
        save_message(db, session_id, "user", message)
        lead = db.query(Lead).filter(Lead.session_id == session_id).first()
        result = chatbot_graph.invoke({
            "session_id": session_id,
            "user_message": message,
            "chat_history": history,
            **_lead_state(lead),
        })
        response = result.get("response", "Sorry, I couldn't process that.")
        save_message(db, session_id, "assistant", response)

        lead_data = {
            field: result.get(field)
            for field in (
                "name", "email", "phone", "company_name", "service",
                "project_description", "budget", "timeline",
                "appointment_requested", "appointment_date", "appointment_time",
            )
            if result.get(field) is not None and result.get(field) != ""
        }
        if result.get("lead_status"):
            lead_data["status"] = result["lead_status"]
        if lead_data:
            lead = update_lead(db, session_id, lead_data)
        if result.get("appointment_requested") and lead:
            request_appointment(
                db, lead.id, result.get("appointment_date"), result.get("appointment_time")
            )

        return {
            "response": response,
            "session_id": session_id,
            "intent": result.get("intent"),
            "lead_data": lead_data,
            "lead_status": result.get("lead_status"),
        }
    except Exception:
        db.rollback()
        logger.exception("Chat processing failed for session %s", session_id)
        raise
    finally:
        db.close()
