"""Consent lifecycle span names — the contract Phoenix evals enforce.

Healthy Tier-2 trace (real-world action):
  Intent_Generated → Gate_Paused → Voice_Approval → Ledger_Appended → Tool_Executed
"""

from __future__ import annotations

INTENT_GENERATED = "Intent_Generated"
GATE_PAUSED = "Gate_Paused"
VOICE_APPROVAL = "Voice_Approval"
LEDGER_APPENDED = "Ledger_Appended"
TOOL_EXECUTED = "Tool_Executed"

CONSENT_SPAN_NAMES = frozenset(
    {
        INTENT_GENERATED,
        GATE_PAUSED,
        VOICE_APPROVAL,
        LEDGER_APPENDED,
        TOOL_EXECUTED,
    }
)
