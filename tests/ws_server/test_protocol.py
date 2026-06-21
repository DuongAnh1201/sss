"""Unit tests for WebSocket ↔ browser protocol mapping."""
from __future__ import annotations

from datetime import datetime, timezone

from schemas.consent import ActionDecision, ActionRequest, LedgerEntry
from backend.protocol import action_to_approval_request, serialize_ledger_entry


def test_action_to_approval_request_email():
    req = ActionRequest(
        action_id="abc123",
        action_type="email.send",
        agent="email",
        summary="Send email to Priya about the deck",
        payload={"to": "priya@example.com", "subject": "Deck ready", "body": "Hi Priya"},
    )
    mapped = action_to_approval_request(req)

    assert mapped["id"] == "abc123"
    assert mapped["toolName"] == "send_email"
    assert mapped["preview"]["to"] == "priya@example.com"


def test_serialize_ledger_entry():
    req = ActionRequest(
        action_id="xyz",
        action_type="email.send",
        agent="email",
        summary="Test send",
        payload={},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    entry = LedgerEntry(
        request=req,
        decision=ActionDecision(action_id="xyz", decision="approve"),
        outcome="executed",
        result_message="Sent (demo)",
        resolved_at=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
    )

    serialized = serialize_ledger_entry(entry)

    assert serialized["action_id"] == "xyz"
    assert serialized["decision"] == "approve"
