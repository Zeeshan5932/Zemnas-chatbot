import json

from app.services.llm_service import get_llm

from app.agent.prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_PROMPT,
    LEAD_COLLECTION_PROMPT,
    LEAD_COMPLETE_PROMPT,
    APPOINTMENT_PROMPT,
)

from app.rag.retriever import get_retriever
from app.core.logging import get_logger


logger = get_logger(__name__)


VALID_INTENTS = {
    "general_chat",
    "company_information",
    "service_inquiry",
    "pricing_inquiry",
    "lead_inquiry",
    "appointment_booking",
    "human_support",
    "other",
}


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


REQUIRED_LEAD_FIELDS = (
    "name",
    "service",
    "project_description",
    "email",
    "phone",
)


# ============================================================
# 1. INTENT + LEAD EXTRACTION
# ONE LLM CALL
# ============================================================

def analyze_message(state):
    llm = get_llm()

    message = state.get(
        "user_message",
        ""
    )

    prompt = ANALYSIS_PROMPT.format(
        message=message
    )

    try:
        response = llm.invoke(prompt)

        content = str(
            response.content
        ).strip()

        # Remove markdown JSON fences if Gemini returns them
        if content.startswith("```"):
            content = (
                content
                .replace("```json", "")
                .replace("```JSON", "")
                .replace("```", "")
                .strip()
            )

        data = json.loads(content)

        if not isinstance(data, dict):
            return {
                "intent": "general_chat"
            }

    except Exception:
        logger.exception(
            "Message analysis failed"
        )

        return {
            "intent": "general_chat"
        }

    intent = str(
        data.get(
            "intent",
            "general_chat"
        )
    ).strip().lower()

    if intent not in VALID_INTENTS:
        intent = "general_chat"

    update = {
        "intent": intent
    }

    # Only accept allowed lead fields
    for field in LEAD_FIELDS:

        if field not in data:
            continue

        value = data.get(field)

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

            if value.lower() in {
                "",
                "null",
                "none",
                "unknown",
                "n/a",
            }:
                continue

        update[field] = value

    # Keep appointment_requested boolean
    if "appointment_requested" in data:
        update["appointment_requested"] = bool(
            data["appointment_requested"]
        )

    return update


# ============================================================
# 2. RETRIEVE ZEMNAS KNOWLEDGE
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

            content = (
                document.page_content
                or ""
            ).strip()

            if not content:
                continue

            source = (
                document.metadata.get(
                    "source",
                    "Zemnas Knowledge Base"
                )
            )

            context_parts.append(
                f"Source: {source}\n{content}"
            )

        return {
            "retrieved_context": "\n\n".join(
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
# 3. LEAD STATUS
# ============================================================

def check_lead_status(state):

    intent = state.get(
        "intent",
        "general_chat"
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

    # Actual project/service interest
    if intent == "lead_inquiry":
        return {
            "lead_status": "collecting"
        }

    if service or project_description:
        return {
            "lead_status": "collecting"
        }

    if appointment_requested:
        return {
            "lead_status": "collecting"
        }

    # A pure pricing/service/company question
    # should NOT automatically become a lead form.
    return {
        "lead_status": "not_started"
    }


# ============================================================
# 4. FIND MISSING REQUIRED LEAD FIELDS
# ============================================================

def get_missing_fields(state):

    missing = []

    for field in REQUIRED_LEAD_FIELDS:

        value = state.get(field)

        if value is None:
            missing.append(field)
            continue

        if isinstance(value, str):
            if not value.strip():
                missing.append(field)

    return missing


def is_lead_complete(state):
    return not get_missing_fields(state)


# ============================================================
# 5. CHAT HISTORY
# ============================================================

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

        if not content:
            continue

        formatted.append(
            f"{role.upper()}: {content}"
        )

    return "\n".join(
        formatted
    )


# ============================================================
# 6. GENERATE FINAL RESPONSE
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

    prompt = SYSTEM_PROMPT.format(
        context=context or "No relevant knowledge found."
    )

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

LEAD STATUS:

{lead_status}
"""

    # --------------------------------------------------------
    # Appointment flow
    # --------------------------------------------------------

    if intent == "appointment_booking" or state.get(
        "appointment_requested",
        False
    ):

        prompt += "\n\n"

        prompt += APPOINTMENT_PROMPT.format(
            appointment_date=state.get(
                "appointment_date",
                "Not provided"
            ),
            appointment_time=state.get(
                "appointment_time",
                "Not provided"
            ),
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
        )

    # --------------------------------------------------------
    # Lead collection
    # --------------------------------------------------------

    elif lead_status == "collecting":

        missing_fields = get_missing_fields(
            state
        )

        if missing_fields:

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
            )

        else:

            prompt += "\n\n"

            prompt += LEAD_COMPLETE_PROMPT

    try:

        response = llm.invoke(
            prompt
        )

        content = str(
            response.content
        ).strip()

        return {
            "response": content
        }

    except Exception:
        logger.exception(
            "Response generation failed"
        )

        return {
            "response": (
                "Sorry, something went wrong. "
                "Please try again."
            )
        }