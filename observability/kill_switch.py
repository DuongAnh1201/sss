"""Kill switch — P0 response when the consent bypass evaluator fires.

Favors a false shutdown over a true bypass: a halted assistant is recoverable;
an un-consented side effect is not (03-observability-and-ledger.md).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_frozen = False
_reason: str | None = None
_callbacks: list = []


class SessionFrozenError(RuntimeError):
    """Raised when the session was shut down after a consent bypass was detected."""


@dataclass
class KillSwitchEvent:
    reason: str
    action_id: str = ""
    trace_id: str = ""


def is_session_frozen() -> bool:
    return _frozen


def freeze_reason() -> str | None:
    return _reason


def register_kill_switch_callback(fn) -> None:
    """Optional hook for revoking API keys / alerting the user (wired later)."""
    _callbacks.append(fn)


def trigger_kill_switch(event: KillSwitchEvent) -> None:
    global _frozen, _reason
    _frozen = True
    _reason = event.reason
    logger.critical(
        "CONSENT BYPASS DETECTED — session frozen. action_id=%s trace_id=%s reason=%s",
        event.action_id,
        event.trace_id,
        event.reason,
    )
    for cb in _callbacks:
        try:
            cb(event)
        except Exception:  # noqa: BLE001
            logger.exception("kill switch callback failed")


def assert_session_active() -> None:
    """Fail closed if the kill switch has fired."""
    if _frozen:
        raise SessionFrozenError(
            _reason
            or "Session frozen — an action tried to run without your approval. "
            "Re-authorize MoneyPenny before continuing."
        )


def reset_kill_switch() -> None:
    """Test-only / operator recovery."""
    global _frozen, _reason
    _frozen = False
    _reason = None
