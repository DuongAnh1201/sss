"""The consent gate — the single funnel for every consequential action.

Usage inside any gated tool:

    return await gate(
        ctx,
        action_type="email.send",
        agent="email_agent",
        summary="Send email to priya@example.com — subject 'Deck is ready'",
        payload={"to": ..., "subject": ..., "body": ...},
        execute=_execute,   # async () -> str
    )

The gate records the request, asks the user (via deps.request_approval), records
the decision, runs the side effect on approve, and records the outcome.
Default policy when no approver is set: DENY (nothing fires silently).
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from schemas.consent import ActionDecision, ActionRequest, ActionType

if TYPE_CHECKING:
    from pydantic_ai import RunContext
    from ai.agents.deps import OrchestratorDeps


async def gate(
    ctx: RunContext[OrchestratorDeps],
    action_type: ActionType,
    agent: str,
    summary: str,
    payload: dict,
    execute: Callable[[], Awaitable[str]],
) -> str:
    """Ask for consent, then execute (or not). Always writes to the ledger."""
    deps = ctx.deps
    ledger = deps.ledger

    req = ActionRequest(
        action_type=action_type,
        agent=agent,
        summary=summary,
        payload=payload,
    )
    await ledger.record_request(req)

    decision = await _decide(deps, req)
    await ledger.record_decision(decision)

    if decision.decision == "cancel":
        await ledger.record_outcome(req.action_id, "cancelled", "User cancelled.")
        return "Cancelled — nothing was done."

    if decision.decision == "revise":
        note = decision.revision_note or "No note provided."
        await ledger.record_outcome(
            req.action_id, "cancelled", f"User requested revision: {note}"
        )
        return f"Revision requested: {note} — please adjust and re-propose."

    # decision == "approve"
    try:
        result = await execute()
        await ledger.record_outcome(req.action_id, "executed", result)
        return result
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        await ledger.record_outcome(req.action_id, "failed", msg)
        return f"Action failed: {msg}. Do not retry."


async def _decide(
    deps: OrchestratorDeps, req: ActionRequest
) -> ActionDecision:
    """Return a decision, either from the registered approver or the auto policy."""
    if deps.request_approval is not None:
        return await deps.request_approval(req)

    if deps.auto_approve:
        return ActionDecision(action_id=req.action_id, decision="approve")

    # Safe default: deny when no approver is wired up.
    return ActionDecision(action_id=req.action_id, decision="cancel")
