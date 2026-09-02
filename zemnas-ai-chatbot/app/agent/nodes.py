import json

from app.services.llm_service import get_llm

from app.agent.prompts import (
    SYSTEM_PROMPT,
    INTENT_PROMPT,
    EXTRACTION_PROMPT,
    LEAD_COLLECTION_PROMPT,
    LEAD_COMPLETE_PROMPT,
    APPOINTMENT_PROMPT
)

from app.rag.retriever import get_retriever
from app.core.logging import get_logger


logger = get_logger(__name__)


# ==========================================
# 1. CLASSIFY USER INTENT
# ==========================================

def classify_intent(state):

    llm = get_llm()

    message = state.get(
        "user_message",
        ""
    )

    prompt = INTENT_PROMPT.format(
        message=message
    )

    try:

        response = llm.invoke(prompt)

        intent = str(
            response.content
        ).strip().lower()

        intent = (
            intent
            .replace("`", "")
            .strip()
        )

    except Exception as error:

        logger.exception("Intent classification failed")

        intent = "general_chat"


    valid_intents = [
        "general_chat",
        "company_information",
        "service_inquiry",
        "pricing_inquiry",
        "lead_inquiry",
        "appointment_booking",
        "human_support",
        "other"
    ]


    if intent not in valid_intents:

        intent = "general_chat"


    return {
        "intent": intent
    }


# ==========================================
# 2. RETRIEVE ZEMNAS KNOWLEDGE
# ==========================================

def retrieve_knowledge(state):

    query = state.get(
        "user_message",
        ""
    )

    try:

        retriever = get_retriever()

        documents = retriever.invoke(
            query
        )

        if not documents:

            return {
                "retrieved_context": ""
            }


        context_parts = []


        for document in documents:

            source = document.metadata.get(
                "source",
                "Zemnas Website"
            )

            content = document.page_content.strip()

            context_parts.append(
                f"Source: {source}\n{content}"
            )


        context = "\n\n".join(
            context_parts
        )


        return {
            "retrieved_context": context
        }


    except Exception as error:

        logger.exception("RAG retrieval failed")

        return {
            "retrieved_context": ""
        }


# ==========================================
# 3. EXTRACT LEAD INFORMATION
# ==========================================

def extract_lead_information(state):

    llm = get_llm()

    message = state.get(
        "user_message",
        ""
    )

    prompt = EXTRACTION_PROMPT.format(
        message=message
    )


    try:

        response = llm.invoke(
            prompt
        )

        content = str(
            response.content
        ).strip()


        # Remove markdown JSON block
        if content.startswith("```"):

            content = (
                content
                .replace("```json", "")
                .replace("```JSON", "")
                .replace("```", "")
                .strip()
            )


        data = json.loads(
            content
        )


        if not isinstance(
            data,
            dict
        ):

            return {}


    except Exception as error:

        logger.exception("Lead extraction failed")

        return {}


    allowed_fields = [

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
        "appointment_time"
    ]


    update = {}


    for key, value in data.items():

        if key not in allowed_fields:

            continue


        if value is None:

            continue


        if isinstance(
            value,
            str
        ):

            value = value.strip()

            if value.lower() in [
                "",
                "null",
                "none",
                "unknown",
                "n/a"
            ]:

                continue


        update[key] = value


    return update


# ==========================================
# 4. CHECK LEAD STATUS
# ==========================================

def check_lead_status(state):

    intent = state.get(
        "intent"
    )

    service = state.get(
        "service"
    )

    project_description = state.get(
        "project_description"
    )


    service_intents = [

        "service_inquiry",
        "lead_inquiry",
        "pricing_inquiry"
    ]


    if intent in service_intents:

        return {
            "lead_status": "collecting"
        }


    if service or project_description:

        return {
            "lead_status": "collecting"
        }


    if state.get(
        "appointment_requested"
    ):

        return {
            "lead_status": "collecting"
        }


    return {
        "lead_status": "not_started"
    }


# ==========================================
# 5. FIND MISSING LEAD FIELDS
# ==========================================

def get_missing_fields(state):

    required_fields = [

        "name",
        "service",
        "project_description",
        "email",
        "phone"
    ]


    missing = []


    for field in required_fields:

        value = state.get(
            field
        )


        if not value:

            missing.append(
                field
            )


    return missing


# ==========================================
# 6. CHECK COMPLETE LEAD
# ==========================================

def is_lead_complete(state):

    return len(
        get_missing_fields(state)
    ) == 0


# ==========================================
# 7. FORMAT CHAT HISTORY
# ==========================================

def format_chat_history(state):

    history = state.get(
        "chat_history",
        []
    )


    if not history:

        return "No previous conversation."


    formatted = []


    for message in history:

        role = message.get(
            "role",
            "user"
        )

        content = message.get(
            "content",
            ""
        )


        formatted.append(
            f"{role.upper()}: {content}"
        )


    return "\n".join(
        formatted
    )


# ==========================================
# 8. GENERATE RESPONSE
# ==========================================

def generate_response(state):

    llm = get_llm()


    context = state.get(
        "retrieved_context",
        ""
    )


    user_message = state.get(
        "user_message",
        ""
    )


    intent = state.get(
        "intent",
        "general_chat"
    )


    lead_status = state.get(
        "lead_status",
        "not_started"
    )


    chat_history = format_chat_history(
        state
    )


    # ======================================
    # BASE SYSTEM PROMPT
    # ======================================

    prompt = SYSTEM_PROMPT.format(
        context=context
    )


    prompt += f"""

CONVERSATION HISTORY:

{chat_history}


CURRENT USER MESSAGE:

{user_message}


DETECTED INTENT:

{intent}
"""


    # ======================================
    # LEAD COLLECTION
    # ======================================

    if lead_status == "collecting":

        missing_fields = get_missing_fields(
            state
        )


        # ------------------------------
        # Lead incomplete
        # ------------------------------

        if missing_fields:

            next_field = (
                missing_fields[0]
            )


            next_actions = {

                "name":
                    "Ask the visitor for their name.",

                "service":
                    "Ask which Zemnas service they need.",

                "project_description":
                    "Ask the visitor to briefly describe what they want to build or achieve.",

                "email":
                    "Ask for their email address so the Zemnas team can contact them.",

                "phone":
                    "Ask for their phone or WhatsApp number."
            }


            next_action = next_actions.get(

                next_field,

                "Ask for the next missing information."
            )


            prompt += "\n\n"

            prompt += LEAD_COLLECTION_PROMPT.format(

                name=state.get(
                    "name",
                    "Not provided"
                ),

                email=state.get(
                    "email",
                    "Not provided"
                ),

                phone=state.get(
                    "phone",
                    "Not provided"
                ),

                company_name=state.get(
                    "company_name",
                    "Not provided"
                ),

                service=state.get(
                    "service",
                    "Not provided"
                ),

                project_description=state.get(
                    "project_description",
                    "Not provided"
                ),

                budget=state.get(
                    "budget",
                    "Not provided"
                ),

                timeline=state.get(
                    "timeline",
                    "Not provided"
                ),

                missing_fields=", ".join(
                    missing_fields
                ),

                next_action=next_action
            )


        # ------------------------------
        # Lead complete
        # ------------------------------

        else:

            prompt += "\n\n"

            prompt += LEAD_COMPLETE_PROMPT.format(

                name=state.get(
                    "name"
                ),

                email=state.get(
                    "email"
                ),

                phone=state.get(
                    "phone"
                ),

                company_name=state.get(
                    "company_name"
                ),

                service=state.get(
                    "service"
                ),

                project_description=state.get(
                    "project_description"
                ),

                budget=state.get(
                    "budget"
                ),

                timeline=state.get(
                    "timeline"
                )
            )


    # ======================================
    # APPOINTMENT FLOW
    # ======================================

    if intent == "appointment_booking":

        prompt += "\n\n"

        prompt += APPOINTMENT_PROMPT.format(

            name=state.get(
                "name",
                "Not provided"
            ),

            email=state.get(
                "email",
                "Not provided"
            ),

            phone=state.get(
                "phone",
                "Not provided"
            ),

            company_name=state.get(
                "company_name",
                "Not provided"
            ),

            service=state.get(
                "service",
                "Not provided"
            ),

            project_description=state.get(
                "project_description",
                "Not provided"
            ),

            appointment_date=state.get(
                "appointment_date",
                "Not provided"
            ),

            appointment_time=state.get(
                "appointment_time",
                "Not provided"
            )
        )


    # ======================================
    # GENERATE LLM RESPONSE
    # ======================================

    try:

        response = llm.invoke(
            prompt
        )

        final_response = str(
            response.content
        ).strip()


    except Exception as error:

        logger.exception("Response generation failed")

        final_response = (
            "Sorry, I'm having trouble responding right now. "
            "Please try again."
        )


    return {
        "response": final_response
    }