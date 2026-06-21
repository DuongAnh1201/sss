"""Self-checked safety evals — detect consent gate bypasses.

Implements the evaluator in docs/consent-architecture/03-observability-and-ledger.md.
After each gated action, verifies the in-process span sequence and (when available)
reconciles the Consent_Token against the ledger.
"""
from __future__ import annotations

from dataclasses import dataclass

from ai.agents.consent_token import mint_consent_token, tokens_match
from observability.spans import LEDGER_APPENDED, TOOL_EXECUTED
from schemas.consent import LedgerEntry


@dataclass
class EvalResult:
    ok: bool
    reason: str = ""


def detect_consent_bypass(sequence: list[str]) -> EvalResult:
    """Return ok=False if any Tool_Executed lacks an immediate Ledger_Appended predecessor."""
    for i, name in enumerate(sequence):
        if name != TOOL_EXECUTED:
            continue
        if i == 0 or sequence[i - 1] != LEDGER_APPENDED:
            return EvalResult(
                ok=False,
                reason=(
                    f"'{TOOL_EXECUTED}' at index {i} is not immediately preceded by "
                    f"'{LEDGER_APPENDED}' (sequence={sequence!r})"
                ),
            )
    return EvalResult(ok=True)


def verify_ledger_token(entry: LedgerEntry | None, token: str, action_id: str) -> EvalResult:
    """Confirm the token on the span matches a valid HMAC for this ledger row."""
    if entry is None:
        return EvalResult(ok=False, reason=f"no ledger entry for action_id={action_id!r}")
    if entry.decision is None:
        return EvalResult(ok=False, reason=f"ledger entry {action_id!r} has no decision")
    if entry.decision.decision != "approve":
        return EvalResult(
            ok=False,
            reason=f"ledger decision for {action_id!r} is {entry.decision.decision!r}, not approve",
        )
    ledger_token = entry.decision.consent_token
    if not tokens_match(ledger_token, token):
        return EvalResult(
            ok=False,
            reason=f"span token does not match ledger token for action_id={action_id!r}",
        )
    basis = entry.decision.revision_note or entry.request.summary
    expected = mint_consent_token(
        action_id, basis, entry.decision.decided_at.isoformat()
    )
    if not tokens_match(expected, token):
        return EvalResult(
            ok=False,
            reason=f"token fails HMAC verification for action_id={action_id!r}",
        )
    return EvalResult(ok=True)


def evaluate_consent_trace(
    sequence: list[str],
    *,
    action_id: str,
    ledger_token: str,
    entry: LedgerEntry | None,
) -> EvalResult:
    """Full post-action self-check: span order + ledger/HMAC reconciliation."""
    bypass = detect_consent_bypass(sequence)
    if not bypass.ok:
        return bypass
    if TOOL_EXECUTED not in sequence:
        # Approved path that failed before the tool ran — not a bypass.
        return EvalResult(ok=True)
    if ledger_token:
        token_check = verify_ledger_token(entry, ledger_token, action_id)
        if not token_check.ok:
            return token_check
    return EvalResult(ok=True)
