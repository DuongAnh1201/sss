"""One WebSocket connection — owns OrchestratorDeps and routes client messages."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from ai.agents.orchestrator import get_orchestrator
from ai.session.deps_factory import build_orchestrator_deps
from backend.approval import WebSocketApprover
from backend.protocol import serialize_ledger_entry
from observability.kill_switch import SessionFrozenError, assert_session_active

logger = logging.getLogger(__name__)


class AgentSession:
    """Phase 2 session handler: browser ↔ orchestrator over a single WebSocket."""

    def __init__(self, websocket: WebSocket) -> None:
        self._ws = websocket
        self._approver = WebSocketApprover(self.send_json)
        self._run_lock = asyncio.Lock()
        self._guest = False
        self._user_id = "default"
        self._deps = None
        self._started = False

    async def send_json(self, payload: dict[str, Any]) -> None:
        await self._ws.send_text(json.dumps(payload))

    async def run(self) -> None:
        await self.send_json({"type": "session_ready"})
        await self.send_json({"type": "state", "speaking": False})

        try:
            while True:
                raw = await self._ws.receive_text()
                message = json.loads(raw)
                if not isinstance(message, dict):
                    continue
                await self.handle_message(message)
        except WebSocketDisconnect:
            logger.info("client disconnected user_id=%s", self._user_id)
        finally:
            self._approver.cancel_all()

    async def handle_message(self, message: dict[str, Any]) -> None:
        msg_type = message.get("type")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})
            return

        if msg_type == "session_start":
            self._guest = bool(message.get("guest"))
            self._user_id = str(message.get("user_id") or ("guest" if self._guest else "default"))
            self._deps = await build_orchestrator_deps(
                user_id=self._user_id,
                guest=self._guest,
                request_approval=self._approver,
            )
            self._started = True
            await self.send_json(
                {
                    "type": "transcript",
                    "role": "assistant",
                    "text": (
                        "Good evening. I'm Désir — at your service. "
                        "What shall we handle first?"
                        if not self._guest
                        else "Welcome, Guest. I'm Désir in demo mode — try asking me to draft an email."
                    ),
                }
            )
            return

        if not self._started:
            self._deps = await build_orchestrator_deps(request_approval=self._approver)
            self._started = True

        if msg_type == "text":
            text = str(message.get("text", "")).strip()
            if text:
                await self.run_prompt(text)
            return

        if msg_type == "audio":
            if message.get("final"):
                await self.send_json(
                    {
                        "type": "error",
                        "message": "Voice input arrives in Phase 3. Send a text message for now.",
                    }
                )
            return

        if msg_type == "approval_decision":
            action_id = str(message.get("action_id") or message.get("request_id") or "")
            decision = str(message.get("decision") or "cancel")
            note = str(message.get("revision_note") or message.get("note") or "")
            if action_id:
                self._approver.resolve(action_id, decision, revision_note=note)
            return

        if msg_type == "tool_result":
            return

        logger.debug("ignored message type=%s", msg_type)

    async def run_prompt(self, prompt: str) -> None:
        async with self._run_lock:
            try:
                assert_session_active()
            except SessionFrozenError as exc:
                await self.send_json({"type": "error", "message": str(exc)})
                return

            assert self._deps is not None
            await self.send_json({"type": "transcript", "role": "user", "text": prompt})
            await self.send_json({"type": "state", "speaking": True})

            try:
                result = await get_orchestrator().run(prompt, deps=self._deps)
                response = result.output.response
                await self.send_json({"type": "transcript", "role": "assistant", "text": response})
                await self.send_json({"type": "completed", "message": "Ready for your next instruction."})
            except SessionFrozenError as exc:
                await self.send_json({"type": "error", "message": str(exc)})
            except Exception as exc:  # noqa: BLE001
                logger.exception("orchestrator run failed")
                await self.send_json({"type": "error", "message": str(exc)})
            finally:
                await self.send_json({"type": "state", "speaking": False})
                await self.push_ledger_tail()

    async def push_ledger_tail(self, limit: int = 10) -> None:
        if self._deps is None:
            return
        entries = await self._deps.ledger.history(limit=limit)
        if not entries:
            return
        await self.send_json(
            {
                "type": "ledger_update",
                "entries": [serialize_ledger_entry(e) for e in entries],
            }
        )
