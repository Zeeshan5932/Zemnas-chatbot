from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):

    # ==========================================
    # SESSION
    # ==========================================

    session_id: str

    # ==========================================
    # CURRENT MESSAGE
    # ==========================================

    user_message: str

    # ==========================================
    # CONVERSATION
    # ==========================================

    chat_history: List[Dict[str, str]]

    # ==========================================
    # INTENT
    # ==========================================

    intent: Optional[str]

    # ==========================================
    # LEAD INFORMATION
    # ==========================================

    service: Optional[str]

    name: Optional[str]

    email: Optional[str]

    phone: Optional[str]

    company_name: Optional[str]

    project_description: Optional[str]

    budget: Optional[str]

    timeline: Optional[str]

    # ==========================================
    # APPOINTMENT
    # ==========================================

    appointment_requested: bool

    appointment_date: Optional[str]

    appointment_time: Optional[str]

    # ==========================================
    # RAG
    # ==========================================

    retrieved_context: str

    # ==========================================
    # LEAD STATUS
    # ==========================================

    lead_status: Optional[str]

    # ==========================================
    # FINAL RESPONSE
    # ==========================================

    response: str

    # ==========================================
    # TEMPORARY EXTRACTION
    # ==========================================

    extracted_lead: Dict[str, Any]