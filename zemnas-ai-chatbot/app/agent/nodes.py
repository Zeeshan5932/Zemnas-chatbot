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


# ============================================================
# CONSTANTS
# ============================================================

LEAD_FIELDS = [

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


VALID_INTENTS = [

    "general_chat",
    "company_information",
    "service_inquiry",
    "pricing_inquiry",
    "lead_inquiry",
    "appointment_booking",
    "human_support",
    "other"
]


REQUIRED_LEAD_FIELDS = [

    "name",
    "service",
    "project_description",
    "email",
    "phone"
]


# ============================================================
# 1. CLASSIFY INTENT
# ============================================================

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

        response = llm.invoke(
            prompt
        )

        intent = str(
            response.content
        ).strip().lower()

        intent = (
            intent
            .replace("`", "")
            .strip()
        )

    except Exception:

        logger.exception(
            "Intent classification failed"
        )

        intent = "general_chat"


    if intent not in VALID_INTENTS:

        intent = "general_chat"


    return {
        "intent": intent
    }


# ============================================================
# 2. RETRIEVE WEBSITE KNOWLEDGE
# ============================================================

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

            content = (
                document.page_content
                .strip()
            )


            if not content:

                continue


            context_parts.append(

                f"Source: {source}\n"
                f"{content}"
            )


        return {

            "retrieved_context":
                "\n\n".join(
                    context_parts
                )
        }


    except Exception:

        logger.exception(
            "RAG retrieval failed"
        )

        return {
            "retrieved_context": ""
        }


# ============================================================
# 3. EXTRACT NEW LEAD INFORMATION
# ============================================================

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


        if content.startswith(
            "```"
        ):

            content = (
                content
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```JSON",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()
            )


        data = json.loads(
            content
        )


        if not isinstance(
            data,
            dict
        ):

            data = {}


    except Exception:

        logger.exception(
            "Lead extraction failed"
        )

        data = {}


    extracted = {}


    for key in LEAD_FIELDS:

        if key not in data:

            continue


        value = data.get(
            key
        )


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


        extracted[key] = value


    # --------------------------------------------------------
    # IMPORTANT:
    # Merge newly extracted information with existing state.
    # --------------------------------------------------------

    update = {}

    for field in LEAD_FIELDS:

        old_value = state.get(
            field
        )

        new_value = extracted.get(
            field
        )


        if new_value not in [
            None,
            ""
        ]:

            update[field] = new_value

        elif old_value not in [
            None,
            ""
        ]:

            update[field] = old_value


    return update


# ============================================================
# 4. CHECK LEAD STATUS
# ============================================================

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

    appointment_requested = state.get(
        "appointment_requested",
        False
    )


    lead_intents = [

        "service_inquiry",
        "lead_inquiry",
        "pricing_inquiry",
        "appointment_booking"
    ]


    if intent in lead_intents:

        return {
            "lead_status": "collecting"
        }


    if service:

        return {
            "lead_status": "collecting"
        }


    if project_description:

        return {
            "lead_status": "collecting"
        }


    if appointment_requested:

        return {
            "lead_status": "collecting"
        }


    return {
        "lead_status": "not_started"
    }


# ============================================================
# 5. FIND MISSING LEAD INFORMATION
# ============================================================

def get_missing_fields(state):

    missing = []


    for field in REQUIRED_LEAD_FIELDS:

        value = state.get(
            field
        )


        if value is None:

            missing.append(
                field
            )

        elif isinstance(
            value,
            str
        ) and not value.strip():

            missing.append(
                field
            )


    return missing


# ============================================================
# 6. CHECK WHETHER LEAD IS COMPLETE
# ============================================================

def is_lead_complete(state):

    return len(
        get_missing_fields(
            state
        )
    ) == 0


# ============================================================
# 7. FORMAT CHAT HISTORY
# ============================================================

def format_chat_history(state):

    history = state.get(
        "chat_history",
        []
    )


    if not history:

        return (
            "No previous conversation."
        )


    formatted = []


    for item in history:

        role = item.get(
            "role",
            "user"
        )

        content = item.get(
            "content",
            ""
        )


        if not content:

            continue


        formatted.append(

            f"{role.upper()}: {content}"
        )


    return "\n".join(
        formatted
    )


# ============================================================
# 8. GENERATE RESPONSE
# ============================================================

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


    history = format_chat_history(
        state
    )


    # --------------------------------------------------------
    # Base prompt
    # --------------------------------------------------------

    prompt = SYSTEM_PROMPT.format(
        context=context
    )


    # --------------------------------------------------------
    # Conversation information
    # --------------------------------------------------------

    prompt += f"""

CONVERSATION HISTORY:

{history}

CURRENT USER MESSAGE:

{user_message}

CURRENT INTENT:

{intent}

CURRENT LEAD INFORMATION:

Name: {state.get("name", "Not provided")}
Email: {state.get("email", "Not provided")}
Phone: {state.get("phone", "Not provided")}
Company: {state.get("company_name", "Not provided")}
Service: {state.get("service", "Not provided")}
Project: {state.get("project_description", "Not provided")}
Budget: {state.get("budget", "Not provided")}
Timeline: {state.get("timeline", "Not provided")}

IMPORTANT:
Use the conversation history and current lead information
together.

Do not ask the visitor for information that is already known.
"""


    # ========================================================
    # LEAD COLLECTION
    # ========================================================

    if lead_status == "collecting":

        missing_fields = get_missing_fields(
            state
        )


        # ----------------------------------------------------
        # Lead incomplete
        # ----------------------------------------------------

        if missing_fields:

            next_field = (
                missing_fields[0]
            )


            next_actions = {

                "name":
                    "Naturally ask for the visitor's name.",

                "service":
                    "Naturally ask what service they need.",

                "project_description":
                    "Naturally ask what they want to build or achieve.",

                "email":
                    "Naturally ask which email Zemnas can use to contact them.",

                "phone":
                    "Naturally ask for their phone or WhatsApp number."
            }


            next_action = next_actions.get(

                next_field,

                "Ask for the most useful missing information."
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


        # ----------------------------------------------------
        # Lead complete
        # ----------------------------------------------------

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


    # ========================================================
    # APPOINTMENT
    # ========================================================

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


    # ========================================================
    # CALL LLM
    # ========================================================

    try:

        response = llm.invoke(
            prompt
        )


        final_response = str(
            response.content
        ).strip()


        if not final_response:

            final_response = (
                "Sorry, I couldn't generate a response right now."
            )


    except Exception:

        logger.exception(
            "Response generation failed"
        )


        final_response = (
            "Sorry, I'm having a little trouble right now. "
            "Please try again."
        )


    return {
        "response": final_response
    }