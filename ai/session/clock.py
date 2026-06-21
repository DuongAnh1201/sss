"""Wall-clock context for agents — models don't know today's date."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def current_datetime_context(*, tz_name: str | None = None) -> str:
    """Return a human-readable 'now' string for agent prompts.

    Uses ``settings.calendar_timezone`` (default ``America/Los_Angeles``).
    Example: ``2026-06-21 09:30 (Saturday) America/Los_Angeles``
    """
    from config import settings

    name = tz_name or settings.calendar_timezone or "UTC"
    try:
        tz = ZoneInfo(name)
    except Exception:  # noqa: BLE001 — bad env → UTC
        tz = ZoneInfo("UTC")
        name = "UTC"
    now = datetime.now(tz)
    return f"{now:%Y-%m-%d %H:%M (%A)} {name}"


def with_datetime_context(prompt: str) -> str:
    """Prefix a sub-agent prompt with the current date/time."""
    return f"[Current date and time: {current_datetime_context()}]\n\n{prompt}"
