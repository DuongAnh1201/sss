"""Tests for in-process consent span recording (Phoenix eval contract)."""
from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from observability.consent_trace import ConsentSpanRecorder, active_recorder, consent_recorder_scope
from observability.spans import (
    GATE_PAUSED,
    INTENT_GENERATED,
    LEDGER_APPENDED,
    TOOL_EXECUTED,
    VOICE_APPROVAL,
)
from schemas.consent import ActionDecision, ActionRequest


def _install_tracer() -> None:
    trace.set_tracer_provider(TracerProvider())


def test_consent_span_recorder_happy_path():
    _install_tracer()
    req = ActionRequest(
        action_id="act-1",
        action_type="email.send",
        agent="email",
        summary="Send test email",
        payload={"to": "a@example.com"},
    )
    recorder = ConsentSpanRecorder(
        action_id=req.action_id,
        action_type=req.action_type,
        agent=req.agent,
    )

    recorder.intent_generated(req)
    recorder.gate_paused()
    recorder.voice_approval(ActionDecision(action_id=req.action_id, decision="approve"))
    recorder.ledger_appended("token-abc")
    recorder.tool_executed(req.action_type)

    assert recorder.sequence == [
        INTENT_GENERATED,
        GATE_PAUSED,
        VOICE_APPROVAL,
        LEDGER_APPENDED,
        TOOL_EXECUTED,
    ]
    assert recorder.ledger_token == "token-abc"


def test_consent_span_recorder_cancel_path():
    _install_tracer()
    req = ActionRequest(
        action_id="act-2",
        action_type="email.send",
        agent="email",
        summary="Draft only",
        payload={},
    )
    recorder = ConsentSpanRecorder(
        action_id=req.action_id,
        action_type=req.action_type,
        agent=req.agent,
    )

    recorder.intent_generated(req)
    recorder.gate_paused()
    recorder.voice_approval(ActionDecision(action_id=req.action_id, decision="cancel"))
    recorder.ledger_only()

    assert TOOL_EXECUTED not in recorder.sequence
    assert recorder.sequence == [INTENT_GENERATED, GATE_PAUSED, VOICE_APPROVAL]


def test_consent_recorder_scope_sets_active_recorder():
    _install_tracer()
    recorder = ConsentSpanRecorder(
        action_id="act-3",
        action_type="calendar.create",
        agent="calendar",
    )

    assert active_recorder() is None
    with consent_recorder_scope(recorder) as active:
        assert active_recorder() is active
    assert active_recorder() is None
