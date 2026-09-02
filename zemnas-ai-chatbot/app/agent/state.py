from typing import TypedDict
from typing import Optional
from typing import List
from typing import Dict
from typing import Any


class AgentState(TypedDict, total=False):

    session_id: str

    user_message: str

    chat_history: List[Dict[str, str]]

    intent: Optional[str]

    service: Optional[str]

    name: Optional[str]

    email: Optional[str]

    phone: Optional[str]

    company_name: Optional[str]

    project_description: Optional[str]

    budget: Optional[str]

    timeline: Optional[str]

    appointment_requested: bool

    appointment_date: Optional[str]

    appointment_time: Optional[str]

    response: str

    retrieved_context: str

    lead_status: Optional[str]

    lead_data: Dict[str, Any]