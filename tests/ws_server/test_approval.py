"""Unit tests for WebSocket-backed consent approval."""
from __future__ import annotations

import asyncio

from schemas.consent import ActionRequest
from backend.approval import WebSocketApprover


def test_websocket_approver_approve_flow():
    sent: list[dict] = []

    async def send_json(payload: dict) -> None:
        sent.append(payload)

    async def run() -> None:
        approver = WebSocketApprover(send_json)
        req = ActionRequest(
            action_id="act-1",
            action_type="email.send",
            agent="email",
            summary="Send test email",
            payload={"to": "a@b.com", "subject": "Hi", "body": "Hello"},
        )

        async def decide_later() -> None:
            await asyncio.sleep(0.01)
            assert approver.resolve("act-1", "approve")

        asyncio.create_task(decide_later())
        decision = await approver(req)

        assert decision.decision == "approve"
        assert any(m["type"] == "approval_request" for m in sent)
        assert any(m["type"] == "approval_resolved" for m in sent)

    asyncio.run(run())


def test_websocket_approver_cancel():
    sent: list[dict] = []

    async def send_json(payload: dict) -> None:
        sent.append(payload)

    async def run() -> None:
        approver = WebSocketApprover(send_json)
        req = ActionRequest(
            action_id="act-2",
            action_type="calendar.create",
            agent="calendar",
            summary="Schedule meeting",
            payload={"title": "Sync"},
        )

        async def cancel_later() -> None:
            await asyncio.sleep(0.01)
            approver.resolve("act-2", "cancel")

        asyncio.create_task(cancel_later())
        decision = await approver(req)

        assert decision.decision == "cancel"

    asyncio.run(run())
