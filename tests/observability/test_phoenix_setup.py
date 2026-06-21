"""Tests for Phoenix OTLP setup and agent instrumentation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

import observability.phoenix as phoenix


class _FakeSettings:
    def __init__(
        self,
        *,
        phoenix_enabled: bool = True,
        phoenix_collector_endpoint: str = "http://127.0.0.1:6006",
        phoenix_api_key: str = "",
        phoenix_project_name: str = "moneypenny-test",
    ) -> None:
        self.phoenix_enabled = phoenix_enabled
        self.phoenix_collector_endpoint = phoenix_collector_endpoint
        self.phoenix_api_key = phoenix_api_key
        self.phoenix_project_name = phoenix_project_name


def test_setup_observability_disabled(monkeypatch):
    monkeypatch.setattr("config.settings", _FakeSettings(phoenix_enabled=False))

    assert phoenix.setup_observability() is False
    assert phoenix.setup_observability() is True


def test_setup_observability_configures_local_exporter(monkeypatch):
    monkeypatch.setattr("config.settings", _FakeSettings())
    captured: dict = {}

    class FakeExporter:
        def __init__(self, endpoint: str, headers: dict | None = None) -> None:
            captured["endpoint"] = endpoint
            captured["headers"] = headers or {}

        def shutdown(self) -> None:
            return None

    with patch(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
        FakeExporter,
    ):
        assert phoenix.setup_observability() is True

    assert captured["endpoint"] == "http://127.0.0.1:6006/v1/traces"
    assert captured["headers"] == {}
    assert isinstance(trace.get_tracer_provider(), TracerProvider)


def test_setup_observability_cloud_sends_bearer_token(monkeypatch):
    monkeypatch.setattr(
        "config.settings",
        _FakeSettings(
            phoenix_collector_endpoint="https://app.phoenix.arize.com/s/demo-space",
            phoenix_api_key="phx_test_key",
        ),
    )
    captured: dict = {}

    class FakeExporter:
        def __init__(self, endpoint: str, headers: dict | None = None) -> None:
            captured["endpoint"] = endpoint
            captured["headers"] = headers or {}

        def shutdown(self) -> None:
            return None

    with patch(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
        FakeExporter,
    ):
        assert phoenix.setup_observability() is True

    assert captured["endpoint"] == "https://app.phoenix.arize.com/s/demo-space/v1/traces"
    assert captured["headers"] == {"Authorization": "Bearer phx_test_key"}


def test_setup_observability_survives_exporter_failure(monkeypatch):
    monkeypatch.setattr("config.settings", _FakeSettings())

    class BrokenExporter:
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError("collector unreachable")

        def shutdown(self) -> None:
            return None

    with patch(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
        BrokenExporter,
    ):
        assert phoenix.setup_observability() is True

    assert isinstance(trace.get_tracer_provider(), TracerProvider)


def test_get_agent_instrumentation_disabled(monkeypatch):
    monkeypatch.setattr("config.settings", _FakeSettings(phoenix_enabled=False))
    assert phoenix.get_agent_instrumentation() is None


def test_get_agent_instrumentation_enabled(monkeypatch):
    monkeypatch.setattr("config.settings", _FakeSettings(phoenix_enabled=True))
    instrumentation = phoenix.get_agent_instrumentation()
    assert instrumentation is not None
    assert instrumentation.version == 2


@pytest.mark.phoenix_integration
def test_live_phoenix_cloud_accepts_otlp_span(monkeypatch):
    """Opt-in: export one span to a real Phoenix Cloud collector."""
    import os

    endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "")
    api_key = os.getenv("PHOENIX_API_KEY", "")
    if not endpoint or not api_key or "phoenix.arize.com" not in endpoint:
        pytest.skip("Set PHOENIX_COLLECTOR_ENDPOINT + PHOENIX_API_KEY for cloud integration")

    monkeypatch.setattr(
        "config.settings",
        _FakeSettings(
            phoenix_collector_endpoint=endpoint,
            phoenix_api_key=api_key,
            phoenix_project_name=os.getenv("PHOENIX_PROJECT_NAME", "moneypenny-test"),
        ),
    )

    assert phoenix.setup_observability() is True
    tracer = trace.get_tracer("moneypenny.test")
    with tracer.start_as_current_span("phoenix_integration_probe") as span:
        span.set_attribute("test.integration", True)

    provider = trace.get_tracer_provider()
    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()
