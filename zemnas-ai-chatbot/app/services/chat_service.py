from typing import Optional

from app.agent.graph import chatbot_graph

from app.core.logging import get_logger

from app.database.models import (
    Lead,
    Message,
)

from app.database.session import SessionLocal

from app.services.appointment_service import (
    request_appointment,
)

from app.services.lead_service import (
    update_lead,
)


logger = get_logger(__name__)


LEAD_FIELDS = (
    "name",
    "email",
    "phone",
    "company_name",
    "service",
    "project_description",
    "budget",
    "timeline",
    "appointment_requested",
    "appointment_date",
    "appointment_time",
)


def save_message(
    db,
    session_id: str,
    role: str,
    content: str,
):
    db.add(
        Message(
            session_id=session_id,
            role=role,
            content=content,
        )
    )

    db.commit()


def get_conversation_history(
    db,
    session_id: str,
    limit: int = 10,
):
    messages = (
        db.query(Message)
        .filter(
            Message.session_id == session_id
        )
        .order_by(
            Message.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    messages.reverse()

    return [
        {
            "role": item.role,
            "content": item.content,
        }
        for item in messages
    ]


def _lead_state(
    lead: Optional[Lead],
) -> dict:

    if lead is None:
        return {}

    state = {}

    for field in LEAD_FIELDS:

        value = getattr(
            lead,
            field,
            None,
        )

        if value is not None:
            state[field] = value

    return state


def _extract_lead_data(
    result: dict,
) -> dict:

    lead_data = {}

    for field in LEAD_FIELDS:

        value = result.get(
            field
        )

        if value is None:
            continue

        if isinstance(value, str):

            value = value.strip()

            if not value:
                continue

        lead_data[field] = value

    return lead_data


def process_chat(
    session_id: str,
    message: str,
):

    db = SessionLocal()

    try:

        # ---------------------------------------------
        # Previous conversation
        # ---------------------------------------------

        history = get_conversation_history(
            db,
            session_id,
            limit=10,
        )

        # ---------------------------------------------
        # Existing lead
        # ---------------------------------------------

        lead = (
            db.query(Lead)
            .filter(
                Lead.session_id == session_id
            )
            .first()
        )

        existing_lead_state = _lead_state(
            lead
        )

        # ---------------------------------------------
        # Save user message
        # ---------------------------------------------

        save_message(
            db,
            session_id,
            "user",
            message,
        )

        # ---------------------------------------------
        # Agent state
        # ---------------------------------------------

        agent_state = {
            "session_id": session_id,
            "user_message": message,
            "chat_history": history,
            **existing_lead_state,
        }

        # ---------------------------------------------
        # Run graph
        # ---------------------------------------------

        result = chatbot_graph.invoke(
            agent_state
        )

        response = (
            result.get("response")
            or
            "Sorry, I couldn't process that right now."
        )

        # ---------------------------------------------
        # Save assistant response
        # ---------------------------------------------

        save_message(
            db,
            session_id,
            "assistant",
            response,
        )

        # ---------------------------------------------
        # Lead data
        # ---------------------------------------------

        lead_data = _extract_lead_data(
            result
        )

        lead_status = result.get(
            "lead_status"
        )

        if lead_status:
            lead_data["status"] = lead_status

        # ---------------------------------------------
        # Save/update lead
        # ---------------------------------------------

        if lead_data:

            lead = update_lead(
                db,
                session_id,
                lead_data,
            )

        # ---------------------------------------------
        # Appointment
        # ---------------------------------------------

        appointment_requested = result.get(
            "appointment_requested",
            False,
        )

        appointment_date = result.get(
            "appointment_date"
        )

        appointment_time = result.get(
            "appointment_time"
        )

        # Only send to booking system when
        # BOTH date and time are available.
        if (
            appointment_requested
            and lead
            and appointment_date
            and appointment_time
        ):

            request_appointment(
                db,
                lead.id,
                appointment_date,
                appointment_time,
            )

        return {
            "response": response,
            "session_id": session_id,
            "intent": result.get(
                "intent"
            ),
            "lead_data": lead_data,
            "lead_status": result.get(
                "lead_status"
            ),
        }

    except Exception:

        db.rollback()

        logger.exception(
            "Chat processing failed for session %s",
            session_id,
        )

        raise

    finally:

        db.close()