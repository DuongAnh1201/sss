"""In-process consent span recorder + OpenTelemetry export for Phoenix.

Each ``gate()`` call opens a recorder that emits the span contract from
03-observability-and-ledger.md and keeps an ordered sequence for the bypass
evaluator (independent of OTLP export latency).
"""
from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from observability.spans import (
    GATE_PAUSED,
    INTENT_GENERATED,
    LEDGER_APPENDED,
    TOOL_EXECUTED,
    VOICE_APPROVAL,
)
from schemas.consent import ActionDecision, ActionRequest

_tracer = trace.get_tracer("moneypenny.consent")

_active_recorder: contextvars.ContextVar["ConsentSpanRecorder | None"] = contextvars.ContextVar(
    "moneypenny_consent_recorder", default=None
)


@dataclass
class ConsentSpanRecorder:
    action_id: str
    action_type: str
    agent: str
    sequence: list[str] = field(default_factory=list)
    ledger_token: str = ""
    _spans: list[Any] = field(default_factory=list, repr=False)

    def _emit(self, name: str, attributes: dict[str, str] | None = None) -> None:
        self.sequence.append(name)
        span = _tracer.start_span(name, attributes=attributes or {})
        self._spans.append(span)

    def _end_last(self, *, ok: bool = True, message: str = "") -> None:
        if not self._spans:
            return
        span = self._spans.pop()
        if not ok:
            span.set_status(Status(StatusCode.ERROR, message))
        span.end()

    def intent_generated(self, req: ActionRequest) -> None:
        self._emit(
            INTENT_GENERATED,
            {
                "action_id": req.action_id,
                "action_type": req.action_type,
                "agent": req.agent,
                "summary": req.summary[:200],
            },
        )
        self._end_last()

    def gate_paused(self) -> None:
        self._emit(
            GATE_PAUSED,
            {
                "action_id": self.action_id,
                "action_type": self.action_type,
            },
        )
        # Leave open until voice approval completes.

    def voice_approval(self, decision: ActionDecision) -> None:
        self._end_last()
        self._emit(
            VOICE_APPROVAL,
            {
                "action_id": self.action_id,
                "decision": decision.decision,
            },
        )
        self._end_last()

    def ledger_appended(self, token: str) -> None:
        self.ledger_token = token
        self._emit(
            LEDGER_APPENDED,
            {
                "action_id": self.action_id,
                "action_type": self.action_type,
                "token": token[:16] + "…" if token else "",
            },
        )
        # Left open until tool executes or path aborts.

    def ledger_only(self) -> None:
        """For non-execute outcomes (cancel/revise) — close without Tool_Executed."""
        self._end_last()

    def tool_executed(self, action_type: str) -> None:
        self._end_last()
        self._emit(
            TOOL_EXECUTED,
            {
                "action_id": self.action_id,
                "action_type": action_type,
            },
        )
        self._end_last()

    def abort_open_spans(self, message: str = "") -> None:
        while self._spans:
            self._end_last(ok=False, message=message)


def active_recorder() -> ConsentSpanRecorder | None:
    return _active_recorder.get()


class consent_recorder_scope:
    """Activate a recorder for the duration of a ``gate()`` call."""

    def __init__(self, recorder: ConsentSpanRecorder) -> None:
        self._recorder = recorder
        self._token: contextvars.Token | None = None

    def __enter__(self) -> ConsentSpanRecorder:
        self._token = _active_recorder.set(self._recorder)
        return self._recorder

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self._recorder.abort_open_spans(str(exc))
        if self._token is not None:
            _active_recorder.reset(self._token)
