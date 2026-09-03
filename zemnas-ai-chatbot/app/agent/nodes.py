import json
from typing import Any

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


# ============================================================
# CONSTANTS
# ============================================================

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


# Intents that actually benefit from Zemnas knowledge retrieval.
#
# This prevents Chroma/RAG from running for messages like:
# "hi"
# "thanks"
# "okay"
# "great"
# etc.
RAG_INTENTS = {
    "company_information",
    "service_inquiry",
    "pricing_inquiry",
    "lead_inquiry",
}


EMPTY_VALUES = {
    "",
    "null",
    "none",
    "unknown",
    "n/a",
    "not provided",
}


# ============================================================
# HELPERS
# ============================================================

def _clean_value(value: Any):
    """
    Clean values returned by the analysis LLM.
    """

    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if value.lower() in EMPTY_VALUES:
            return None

        return value

    return value


def _clean_json_response(content: str) -> str:
    """
    Clean a model response before json.loads().
    Handles accidental markdown JSON fences.
    """

    content = content.strip()

    if not content:
        return ""

    if content.startswith("```"):
        lines = content.splitlines()

        # Remove first fence
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        # Remove final fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    return content


def _safe_bool(value: Any) -> bool:
    """
    Convert model output into a reliable boolean.
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
        }

    if isinstance(value, (int, float)):
        return bool(value)

    return False


def _has_value(value: Any) -> bool:
    """
    Check whether a state field actually contains useful data.
    """

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


# ============================================================
# 1. ANALYZE USER MESSAGE
# ============================================================
#
# ONE LLM CALL
#
# Detects:
# - intent
# - newly provided lead information
# - appointment request
#
# It does NOT overwrite existing lead information.
# ============================================================

def analyze_message(state):
    llm = get_llm()

    message = state.get(
        "user_message",
        "",
    ).strip()

    if not message:
        return {
            "intent": "general_chat",
        }

    prompt = ANALYSIS_PROMPT.format(
        message=message,
    )

    try:
        response = llm.invoke(prompt)

        content = str(
            response.content
        ).strip()

        content = _clean_json_response(content)

        data = json.loads(content)

        if not isinstance(data, dict):
            logger.warning(
                "Analysis response was not a JSON object"
            )

            return {
                "intent": "general_chat",
            }

    except json.JSONDecodeError:
        logger.exception(
            "Analysis returned invalid JSON"
        )

        return {
            "intent": "general_chat",
        }

    except Exception:
        logger.exception(
            "Message analysis failed"
        )

        return {
            "intent": "general_chat",
        }

    # --------------------------------------------------------
    # Intent
    # --------------------------------------------------------

    intent = str(
        data.get(
            "intent",
            "general_chat",
        )
    ).strip().lower()

    if intent not in VALID_INTENTS:
        intent = "general_chat"

    update = {
        "intent": intent,
    }

    # --------------------------------------------------------
    # Extract only allowed fields
    # --------------------------------------------------------

    for field in LEAD_FIELDS:

        if field not in data:
            continue

        value = _clean_value(
            data.get(field)
        )

        if value is None:
            continue

        if field == "appointment_requested":
            update[field] = _safe_bool(value)
        else:
            update[field] = value

    return update


# ============================================================
# 2. RETRIEVE ZEMNAS KNOWLEDGE
# ============================================================
#
# IMPORTANT:
# RAG does NOT run for every message.
#
# Example:
# "hi bro"
# "thanks"
# "okay"
#
# -> no vector search
#
# But:
# "What services does Zemnas offer?"
# "What does Zemnas do?"
# "How much does it cost?"
#
# -> RAG search
# ============================================================

def retrieve_knowledge(state):
    intent = state.get(
        "intent",
        "general_chat",
    )

    query = state.get(
        "user_message",
        "",
    ).strip()

    # --------------------------------------------------------
    # Skip unnecessary RAG calls
    # --------------------------------------------------------

    if intent not in RAG_INTENTS:
        return {
            "retrieved_context": "",
        }

    if not query:
        return {
            "retrieved_context": "",
        }

    try:
        retriever = get_retriever(
            k=4,
        )

        documents = retriever.invoke(
            query,
        )

        if not documents:
            return {
                "retrieved_context": "",
            }

        context_parts = []

        for document in documents:

            content = (
                getattr(
                    document,
                    "page_content",
                    "",
                )
                or ""
            ).strip()

            if not content:
                continue

            metadata = getattr(
                document,
                "metadata",
                {},
            ) or {}

            source = metadata.get(
                "source",
                "Zemnas Knowledge Base",
            )

            context_parts.append(
                f"Source: {source}\n{content}"
            )

        if not context_parts:
            return {
                "retrieved_context": "",
            }

        return {
            "retrieved_context": "\n\n".join(
                context_parts
            ),
        }

    except Exception:
        logger.exception(
            "RAG retrieval failed"
        )

        # Do not break chatbot if vector search fails.
        return {
            "retrieved_context": "",
        }


# ============================================================
# 3. CHECK LEAD STATUS
# ============================================================

def check_lead_status(state):
    intent = state.get(
        "intent",
        "general_chat",
    )

    service = state.get(
        "service",
    )

    project_description = state.get(
        "project_description",
    )

    appointment_requested = state.get(
        "appointment_requested",
        False,
    )

    # --------------------------------------------------------
    # Actual lead/project interest
    # --------------------------------------------------------

    if intent == "lead_inquiry":
        return {
            "lead_status": "collecting",
        }

    if _has_value(service):
        return {
            "lead_status": "collecting",
        }

    if _has_value(project_description):
        return {
            "lead_status": "collecting",
        }

    if appointment_requested:
        return {
            "lead_status": "collecting",
        }

    # --------------------------------------------------------
    # Normal informational conversation
    # --------------------------------------------------------

    return {
        "lead_status": "not_started",
    }


# ============================================================
# 4. FIND MISSING REQUIRED LEAD FIELDS
# ============================================================

def get_missing_fields(state):
    missing = []

    for field in REQUIRED_LEAD_FIELDS:

        value = state.get(
            field,
        )

        if not _has_value(value):
            missing.append(field)

    return missing


# ============================================================
# 5. CHECK IF LEAD IS COMPLETE
# ============================================================

def is_lead_complete(state):
    return not get_missing_fields(state)


# ============================================================
# 6. FORMAT CHAT HISTORY
# ============================================================

def format_chat_history(state):
    history = state.get(
        "chat_history",
        [],
    )

    if not history:
        return "No previous conversation."

    formatted = []

    for message in history:

        if not isinstance(
            message,
            dict,
        ):
            continue

        role = str(
            message.get(
                "role",
                "user",
            )
        ).upper()

        content = str(
            message.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        formatted.append(
            f"{role}: {content}"
        )

    if not formatted:
        return "No previous conversation."

    # Keep prompt size under control.
    #
    # If frontend/state stores a very long history,
    # sending everything to Groq every time becomes expensive.
    #
    # Keep the latest messages.
    MAX_HISTORY_MESSAGES = 12

    formatted = formatted[
        -MAX_HISTORY_MESSAGES:
    ]

    return "\n".join(
        formatted
    )


# ============================================================
# 7. BUILD LEAD CONTEXT
# ============================================================

def build_lead_context(state):
    return {
        "name": state.get(
            "name",
            "Not provided",
        ),
        "email": state.get(
            "email",
            "Not provided",
        ),
        "phone": state.get(
            "phone",
            "Not provided",
        ),
        "company_name": state.get(
            "company_name",
            "Not provided",
        ),
        "service": state.get(
            "service",
            "Not provided",
        ),
        "project_description": state.get(
            "project_description",
            "Not provided",
        ),
        "budget": state.get(
            "budget",
            "Not provided",
        ),
        "timeline": state.get(
            "timeline",
            "Not provided",
        ),
    }


# ============================================================
# 8. GENERATE RESPONSE
# ============================================================

def generate_response(state):
    llm = get_llm()

    context = state.get(
        "retrieved_context",
        "",
    )

    user_message = state.get(
        "user_message",
        "",
    )

    intent = state.get(
        "intent",
        "general_chat",
    )

    lead_status = state.get(
        "lead_status",
        "not_started",
    )

    chat_history = format_chat_history(
        state
    )

    lead_context = build_lead_context(
        state
    )

    # --------------------------------------------------------
    # Base system prompt
    # --------------------------------------------------------

    prompt = SYSTEM_PROMPT.format(
        context=(
            context
            if context
            else "No relevant knowledge found."
        ),
    )

    # --------------------------------------------------------
    # Conversation context
    # --------------------------------------------------------

    prompt += f"""

CONVERSATION HISTORY:

{chat_history}

CURRENT USER MESSAGE:

{user_message}

DETECTED INTENT:

{intent}

CURRENT LEAD STATUS:

{lead_status}

CURRENT LEAD INFORMATION:

Name: {lead_context["name"]}
Email: {lead_context["email"]}
Phone: {lead_context["phone"]}
Company: {lead_context["company_name"]}
Service: {lead_context["service"]}
Project: {lead_context["project_description"]}
Budget: {lead_context["budget"]}
Timeline: {lead_context["timeline"]}
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

            prompt += "\n\n"

            prompt += LEAD_COLLECTION_PROMPT.format(
                name=lead_context["name"],
                email=lead_context["email"],
                phone=lead_context["phone"],
                company_name=lead_context["company_name"],
                service=lead_context["service"],
                project_description=lead_context[
                    "project_description"
                ],
                budget=lead_context["budget"],
                timeline=lead_context["timeline"],
                missing_fields=", ".join(
                    missing_fields
                ),
            )

        # ----------------------------------------------------
        # Lead complete
        # ----------------------------------------------------

        else:

            prompt += "\n\n"

            prompt += LEAD_COMPLETE_PROMPT.format(
                name=lead_context["name"],
                email=lead_context["email"],
                phone=lead_context["phone"],
                company_name=lead_context[
                    "company_name"
                ],
                service=lead_context["service"],
                project_description=lead_context[
                    "project_description"
                ],
                budget=lead_context["budget"],
                timeline=lead_context["timeline"],
            )

    # ========================================================
    # APPOINTMENT FLOW
    # ========================================================

    if (
        intent == "appointment_booking"
        or state.get(
            "appointment_requested",
            False,
        )
    ):

        prompt += "\n\n"

        prompt += APPOINTMENT_PROMPT.format(
            name=lead_context["name"],
            email=lead_context["email"],
            phone=lead_context["phone"],
            company_name=lead_context[
                "company_name"
            ],
            service=lead_context["service"],
            project_description=lead_context[
                "project_description"
            ],
            appointment_date=state.get(
                "appointment_date",
                "Not provided",
            ),
            appointment_time=state.get(
                "appointment_time",
                "Not provided",
            ),
        )

    # ========================================================
    # GENERATE FINAL RESPONSE
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
                "Sorry, I couldn't generate a response right now. "
                "Please try again."
            )

    except Exception:
        logger.exception(
            "Response generation failed"
        )

        final_response = (
            "Sorry, I'm having trouble responding right now. "
            "Please try again."
        )

    return {
        "response": final_response,
    }