from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    session_id: str
    user_message: str

    chat_history: List[Dict[str, str]]

    # AI understanding
    intent: Optional[str]

    # Lead information
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    company_name: Optional[str]
    service: Optional[str]
    project_description: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]

    # Appointment
    appointment_requested: bool
    appointment_date: Optional[str]
    appointment_time: Optional[str]

    # RAG
    retrieved_context: str

    # Lead status
    lead_status: Optional[str]

    # Final answer
    response: str

    # Internal analysis
    extracted_lead: Dict[str, Any]