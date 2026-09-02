from app.agent.graph import (
    chatbot_graph
)

from app.database.session import (
    SessionLocal
)

from app.database.models import (
    Message
)

from app.services.lead_service import (
    update_lead
)


def save_message(

    db,

    session_id,

    role,

    content

):

    message = Message(

        session_id=session_id,

        role=role,

        content=content
    )


    db.add(
        message
    )


    db.commit()


def get_conversation_history(

    db,

    session_id,

    limit=10

):

    messages = (

        db.query(Message)

        .filter(
            Message.session_id
            == session_id
        )

        .order_by(
            Message.created_at.desc()
        )

        .limit(
            limit
        )

        .all()
    )


    messages.reverse()


    return [

        {

            "role": message.role,

            "content": message.content
        }

        for message in messages
    ]


def process_chat(

    session_id: str,

    message: str

):

    db = SessionLocal()


    try:

        history = (
            get_conversation_history(

                db=db,

                session_id=session_id
            )
        )


        save_message(

            db=db,

            session_id=session_id,

            role="user",

            content=message
        )


        initial_state = {

            "session_id": session_id,

            "user_message": message,

            "chat_history": history
        }


        result = chatbot_graph.invoke(
            initial_state
        )


        response = result.get(

            "response",

            "Sorry, I couldn't process that."
        )


        save_message(

            db=db,

            session_id=session_id,

            role="assistant",

            content=response
        )


        lead_fields = {

            "name":

                result.get("name"),

            "email":

                result.get("email"),

            "phone":

                result.get("phone"),

            "company_name":

                result.get("company_name"),

            "service":

                result.get("service"),

            "project_description":

                result.get(
                    "project_description"
                ),

            "budget":

                result.get("budget"),

            "timeline":

                result.get("timeline"),

            "status":

                result.get(
                    "lead_status"
                )
        }


        clean_lead_data = {

            key: value

            for key, value

            in lead_fields.items()

            if value
        }


        if clean_lead_data:

            update_lead(

                db=db,

                session_id=session_id,

                data=clean_lead_data
            )


        return {

            "response": response,

            "session_id": session_id,

            "intent":

                result.get(
                    "intent"
                ),

            "lead_data":

                clean_lead_data,

            "lead_status":

                result.get(
                    "lead_status"
                )
        }


    finally:

        db.close()