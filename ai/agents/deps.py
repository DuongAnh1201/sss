from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from ai.prompts import load_prompt
from tools.ledger import ConsentLedger, get_ledger
from schemas.consent import ActionDecision, ActionRequest

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

    # ── Consent gate ───────────────────────────────────────────────────────────
    request_approval: Callable[[ActionRequest], Awaitable[ActionDecision]] | None = field(
        default=None
    )
    """Async callback set by the session/UI layer.

    Receives an ActionRequest, presents it to the user (console, WebSocket, voice),
    and returns the user's ActionDecision. When None and auto_approve is False,
    the gate denies every action by default.
    """

    ledger: ConsentLedger = field(default_factory=get_ledger)
    """Append-only consent ledger. Defaults to FileLedger unless REDIS_URL is set."""

    auto_approve: bool = field(default=False)
    """When True, all gated actions are auto-approved without prompting.
    Only for smoke tests and the demo 'Try as Guest' persona. Still writes to the ledger.
    """
