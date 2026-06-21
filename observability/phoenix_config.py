"""Phoenix collector URL + auth helpers (local and Phoenix Cloud)."""
from __future__ import annotations

from urllib.parse import urlparse


def normalize_phoenix_collector_endpoint(endpoint: str) -> str:
    """Ensure the OTLP HTTP trace URL ends with ``/v1/traces``.

    Accepts:
    - ``http://127.0.0.1:6006`` (local ``phoenix serve``)
    - ``http://127.0.0.1:6006/v1/traces`` (already normalized)
    - ``https://app.phoenix.arize.com/s/my-space`` (Phoenix Cloud hostname)
    """
    trimmed = endpoint.strip().rstrip("/")
    if trimmed.endswith("/v1/traces"):
        return trimmed
    return f"{trimmed}/v1/traces"


def phoenix_otlp_headers(api_key: str) -> dict[str, str]:
    """Build OTLP HTTP headers. Cloud requires ``Authorization: Bearer …``."""
    key = api_key.strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def is_phoenix_cloud_endpoint(endpoint: str) -> bool:
    """True when the collector points at Arize-hosted Phoenix Cloud."""
    host = urlparse(endpoint.strip()).hostname or ""
    return "phoenix.arize.com" in host


def describe_phoenix_target(endpoint: str, api_key: str) -> str:
    """Human-readable label for startup logs."""
    if is_phoenix_cloud_endpoint(endpoint):
        return "Phoenix Cloud" if api_key.strip() else "Phoenix Cloud (missing PHOENIX_API_KEY)"
    return "local Phoenix"
