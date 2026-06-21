"""Fetch.ai / Agentverse transport for MoneyPenny.

Publishes the orchestrator as a uAgent on the Fetch.ai network so it can:
  - receive natural-language requests from any other Agentverse agent
  - reply directly to the sender
  - proactively message other agents by their Fetch.ai address

Quick start
-----------
1. Add to .env:
       FETCH_AGENT_SEED="some long random passphrase"   # pick once, never change
       AGENTVERSE_API_KEY="your-key-from-agentverse.ai" # optional, enables cloud mailbox

2. Run:
       uv run python -m ai.transport.fetch_wrapper

3. The agent's Fetch.ai address is printed on startup.
   Paste it into agentverse.ai → "My Agents" to make MoneyPenny discoverable.

Inter-agent messaging
---------------------
Other agents send a  DesirRequest  message to MoneyPenny's address.
MoneyPenny routes it through the pydantic-ai orchestrator and replies with a
DesirResponse.

To send a message TO another agent from inside the orchestrator, push a
SendTask onto the outbound queue and the interval handler will deliver it:

    from ai.transport.fetch_wrapper import enqueue_send
    await enqueue_send(address="agent1q...", text="...", user_id="moneypenny")
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from uagents import Agent, Context, Model, Protocol

from config import settings

logger = logging.getLogger(__name__)

# ── Message schemas ────────────────────────────────────────────────────────────

class SSSRequest(Model):
    """Sent by any other Agentverse agent to invoke MoneyPenny."""
    text: str
    user_id: str = "agent_guest"


class SSSResponse(Model):
    """MoneyPenny's reply to the requesting agent."""
    text: str
    intent: str
    success: bool = True


# ── Outbound queue ─────────────────────────────────────────────────────────────
# Push a SendTask here from anywhere in the app to deliver a message to another
# agent on the next interval tick.

@dataclass
class SendTask:
    address: str
    text: str
    user_id: str = "moneypenny"


_outbound: asyncio.Queue[SendTask] = asyncio.Queue()


async def enqueue_send(address: str, text: str, user_id: str = "moneypenny") -> None:
    """Queue a DesirRequest to be sent to another Agentverse agent."""
    await _outbound.put(SendTask(address=address, text=text, user_id=user_id))


# ── Protocol ──────────────────────────────────────────────────────────────────

desir_protocol = Protocol(name="DesirProtocol", version="1.0.0")


# ── Orchestrator runner ───────────────────────────────────────────────────────

async def _run_orchestrator(text: str, user_id: str) -> tuple[str, str]:
    """Route a text request through the pydantic-ai orchestrator.

    Returns (response_text, intent).  Always auto-approves — the consent gate
    is designed for human sessions; agent-to-agent calls are pre-authorised.
    """
    from ai.agents.orchestrator import get_orchestrator
    from ai.agents.deps import OrchestratorDeps
    from tools.ledger import get_ledger

    knowledge = None
    execution_log = None
    if settings.redis_url:
        try:
            from memory.execution_log import get_execution_log
            execution_log = get_execution_log()
        except Exception:
            pass
        if settings.openai_api_key:
            try:
                from memory.graph import get_graph_knowledge
                knowledge = get_graph_knowledge()
            except Exception:
                pass

    deps = OrchestratorDeps(
        user_id=user_id,
        knowledge=knowledge,
        execution_log=execution_log,
        ledger=get_ledger(),
        auto_approve=True,
    )

    result = await get_orchestrator().run(text, deps=deps)
    return result.output.response, result.output.intent


# ── Handlers ──────────────────────────────────────────────────────────────────

@desir_protocol.on_message(model=SSSRequest, replies={SSSResponse})
async def handle_request(ctx: Context, sender: str, msg: SSSRequest) -> None:
    """Process an incoming request from another Agentverse agent."""
    logger.info("[fetch] ← %s: %s", sender[:20], msg.text[:100])
    try:
        response_text, intent = await _run_orchestrator(msg.text, msg.user_id)
        await ctx.send(sender, SSSResponse(
            text=response_text,
            intent=intent,
            success=True,
        ))
        logger.info("[fetch] → %s (%s): %s", sender[:20], intent, response_text[:80])
    except Exception as exc:
        logger.exception("[fetch] orchestrator error for %s", sender)
        await ctx.send(sender, SSSResponse(
            text=f"MoneyPenny encountered an error: {exc}",
            intent="unknown",
            success=False,
        ))


# ── Agent factory ─────────────────────────────────────────────────────────────

def _build_agent() -> Agent:
    if not settings.fetch_agent_seed:
        raise RuntimeError(
            "FETCH_AGENT_SEED is not set. "
            "Add a stable seed phrase to .env so MoneyPenny has a fixed Fetch.ai address."
        )

    public_url = (
        settings.fetch_agent_endpoint.rstrip("/")
        or f"http://localhost:{settings.fetch_agent_port}"
    )
    agent = Agent(
        name="moneypenny",
        seed=settings.fetch_agent_seed,
        port=settings.fetch_agent_port,
        endpoint=[f"{public_url}/submit"],
        mailbox=bool(settings.agentverse_api_key),
    )

    # ── Startup ────────────────────────────────────────────────────────────────
    @agent.on_event("startup")
    async def on_startup(ctx: Context) -> None:
        print()
        print("─" * 60)
        print("  MoneyPenny (Fetch.ai uAgent)")
        print(f"  Address : {ctx.address}")
        print(f"  Port    : {settings.fetch_agent_port}")
        mailbox_status = "enabled" if settings.agentverse_api_key else "disabled (set AGENTVERSE_API_KEY)"
        print(f"  Mailbox : {mailbox_status}")
        print()
        print("  → Paste the address above into agentverse.ai → My Agents")
        print("    to make MoneyPenny publicly discoverable.")
        print("─" * 60)
        print()

    # ── Outbound interval: drain the send queue ───────────────────────────────
    @agent.on_interval(period=2.0)
    async def flush_outbound(ctx: Context) -> None:
        while not _outbound.empty():
            task = _outbound.get_nowait()
            try:
                await ctx.send(task.address, SSSRequest(
                    text=task.text,
                    user_id=task.user_id,
                ))
                logger.info("[fetch] outbound → %s: %s", task.address[:20], task.text[:80])
            except Exception as exc:
                logger.error("[fetch] failed to send to %s: %s", task.address[:20], exc)

    agent.include(desir_protocol, publish_manifest=True)
    return agent


_fetch_agent: Agent | None = None


def get_fetch_agent() -> Agent:
    """Return the singleton MoneyPenny uAgent (builds it on first call)."""
    global _fetch_agent
    if _fetch_agent is None:
        _fetch_agent = _build_agent()
    return _fetch_agent


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    get_fetch_agent().run()
