import json

from app.services.llm_service import (
    get_llm
)

from app.agent.prompts import (
    SYSTEM_PROMPT,
    INTENT_PROMPT,
    EXTRACTION_PROMPT
)

from app.rag.retriever import (
    get_context
)


def classify_intent(state):

    llm = get_llm()

    message = state[
        "user_message"
    ]


    prompt = INTENT_PROMPT.format(
        message=message
    )


    response = llm.invoke(
        prompt
    )


    intent = (
        response.content
        .strip()
        .lower()
    )


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


def retrieve_knowledge(state):

    query = state[
        "user_message"
    ]


    context = get_context(
        query=query
    )


    return {

        "retrieved_context": context
    }


def extract_lead_information(state):

    llm = get_llm()

    message = state[
        "user_message"
    ]


    prompt = EXTRACTION_PROMPT.format(
        message=message
    )


    response = llm.invoke(
        prompt
    )


    content = response.content.strip()


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
                "```",
                ""
            )
            .strip()
        )


    try:

        data = json.loads(
            content
        )

    except Exception:

        data = {}


    update = {}


    for key, value in data.items():

        if value not in [
            None,
            "",
            "null"
        ]:

            update[key] = value


    return update


def generate_response(state):

    llm = get_llm()


    context = state.get(
        "retrieved_context",
        ""
    )


    user_message = state[
        "user_message"
    ]


    prompt = SYSTEM_PROMPT.format(
        context=context
    )


    prompt += f"""

User Message:

{user_message}
"""


    lead_status = state.get(
        "lead_status"
    )


    if lead_status == "collecting":

        missing_fields = get_missing_fields(
            state
        )


        if missing_fields:

            prompt += f"""

The user is interested in a service.

Known information:

Service: {state.get("service")}
Name: {state.get("name")}
Email: {state.get("email")}
Phone: {state.get("phone")}
Company: {state.get("company_name")}
Project Description:
{state.get("project_description")}

Ask for ONLY the most relevant next missing
information.

Missing fields:

{missing_fields}
"""


    response = llm.invoke(
        prompt
    )


    return {

        "response": response.content
    }


def get_missing_fields(state):

    important_fields = [

        "name",

        "service",

        "project_description",

        "email",

        "phone"
    ]


    missing = []


    for field in important_fields:

        value = state.get(
            field
        )


        if not value:

            missing.append(
                field
            )


    return missing


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


    if intent in [

        "service_inquiry",

        "lead_inquiry"

    ]:

        return {

            "lead_status": "collecting"
        }


    if service or project_description:

        return {

            "lead_status": "collecting"
        }


    return {

        "lead_status": "not_started"
    }