from dataclasses import dataclass, field
from typing import Any
from ai.prompts import load_prompt

_TOM_HISTORY = load_prompt("tombio")

@dataclass
class OrchestratorDeps:
    history_context: dict = field(default_factory=dict)
    preferred_pronouns: str = field(default="Sir")
    name: str = field(default="Tom")
    email_address: str = field(default="tomnguyen6766@gmail.com")
    tom_history_context: str = field(default=_TOM_HISTORY)
    search_api_key: str = field(default="")
    calendar_event_ids: dict = field(default_factory=dict)
    request_email_approval: Any = field(default=None)
    """Async callback set by session_handler. When present, agent1 tools request
    user approval before sending instead of sending directly."""
