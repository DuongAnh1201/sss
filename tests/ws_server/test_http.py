"""HTTP endpoint tests for the Phase 2 backend."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from schemas.consent import ActionDecision, ActionRequest
from tools.ledger import FileLedger
from tests.ws_server.conftest import create_app


@pytest.fixture
def client(monkeypatch, tmp_path):
    ledger = FileLedger(path=tmp_path / "ledger.jsonl")

    async def _seed() -> None:
        req = ActionRequest(
            action_id="seed-1",
            action_type="email.send",
            agent="email",
            summary="Seeded ledger row",
            payload={},
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        await ledger.record_request(req)
        await ledger.record_decision(
            ActionDecision(action_id=req.action_id, decision="approve")
        )
        await ledger.record_outcome(req.action_id, "executed", "demo")

    import asyncio

    asyncio.run(_seed())
    monkeypatch.setattr("tools.ledger.get_ledger", lambda: ledger)
    import tests.ws_server.conftest as ws_conftest

    monkeypatch.setattr(ws_conftest._server, "get_ledger", lambda: ledger)
    return TestClient(create_app())


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "moneypenny"}


def test_ledger_endpoint_returns_entries(client):
    response = client.get("/api/ledger?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert len(body["entries"]) == 1
    assert body["entries"][0]["action_id"] == "seed-1"
    assert body["entries"][0]["outcome"] == "executed"
