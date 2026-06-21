"""WebSocket session tests for the Phase 2 backend."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.ws_server.conftest import create_app


def _collect_until(ws, msg_type: str, limit: int = 10) -> dict:
    for _ in range(limit):
        message = json.loads(ws.receive_text())
        if message.get("type") == msg_type:
            return message
    raise AssertionError(f"Did not receive {msg_type!r} within {limit} messages")


@pytest.fixture
def ws_client():
    return TestClient(create_app())


def test_websocket_session_ready_and_ping(ws_client):
    with ws_client.websocket_connect("/ws") as ws:
        ready = json.loads(ws.receive_text())
        state = json.loads(ws.receive_text())
        assert ready["type"] == "session_ready"
        assert state == {"type": "state", "speaking": False}

        ws.send_text(json.dumps({"type": "ping"}))
        assert json.loads(ws.receive_text()) == {"type": "pong"}


def test_websocket_session_start_greeting(ws_client):
    with ws_client.websocket_connect("/ws") as ws:
        ws.receive_text()
        ws.receive_text()

        ws.send_text(json.dumps({"type": "session_start", "guest": False}))
        greeting = _collect_until(ws, "transcript")

        assert greeting["role"] == "assistant"
        assert "Désir" in greeting["text"]


def test_websocket_guest_session_start(ws_client):
    with ws_client.websocket_connect("/ws") as ws:
        ws.receive_text()
        ws.receive_text()

        ws.send_text(json.dumps({"type": "session_start", "guest": True}))
        greeting = _collect_until(ws, "transcript")

        assert "Guest" in greeting["text"]
        assert "demo mode" in greeting["text"]


def test_websocket_text_runs_orchestrator(ws_client, monkeypatch, tmp_path):
    mock_result = MagicMock()
    mock_result.output.response = "Email draft prepared."

    mock_orchestrator = MagicMock()
    mock_orchestrator.run = AsyncMock(return_value=mock_result)

    async def fake_build_deps(**kwargs):
        from ai.agents.deps import OrchestratorDeps
        from tools.ledger import FileLedger

        return OrchestratorDeps(
            user_id="default",
            ledger=FileLedger(path=tmp_path / "ledger.jsonl"),
            auto_approve=True,
            request_approval=kwargs.get("request_approval"),
        )

    with (
        patch("backend.session.get_orchestrator", return_value=mock_orchestrator),
        patch("backend.session.build_orchestrator_deps", side_effect=fake_build_deps),
    ):
        with ws_client.websocket_connect("/ws") as ws:
            ws.receive_text()
            ws.receive_text()
            ws.send_text(json.dumps({"type": "session_start", "guest": False}))
            _collect_until(ws, "transcript")

            ws.send_text(json.dumps({"type": "text", "text": "Email Priya the deck is ready"}))
            user_line = _collect_until(ws, "transcript")
            assistant_line = _collect_until(ws, "transcript")
            completed = _collect_until(ws, "completed")

            assert user_line == {
                "type": "transcript",
                "role": "user",
                "text": "Email Priya the deck is ready",
            }
            assert assistant_line["role"] == "assistant"
            assert assistant_line["text"] == "Email draft prepared."
            assert completed["type"] == "completed"

    mock_orchestrator.run.assert_awaited_once()


def test_websocket_audio_final_returns_phase3_message(ws_client):
    with ws_client.websocket_connect("/ws") as ws:
        ws.receive_text()
        ws.receive_text()
        ws.send_text(json.dumps({"type": "session_start", "guest": False}))
        _collect_until(ws, "transcript")

        ws.send_text(json.dumps({"type": "audio", "final": True}))
        error = _collect_until(ws, "error")

        assert "Phase 3" in error["message"]
