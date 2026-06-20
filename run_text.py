"""Text-mode harness for the Desir orchestrator (Phase 0).

Two uses:

    uv run python run_text.py --check
        Build every agent and import every tool without any network calls.
        Verifies the skeleton is wired correctly. Exits non-zero on failure.

    uv run python run_text.py "Email Priya that the deck is ready"
        Run the orchestrator against a typed request (needs LLM credentials in
        .env). Real-world actions are simulated unless DESIR_DEMO=0.

Voice (Phase 3) replaces stdin/stdout with speech; the orchestrator core is the
same path exercised here.
"""
from __future__ import annotations

import asyncio
import sys


def build_check() -> None:
    """Import tools and construct every agent to validate wiring."""
    from ai.prompts import load_prompt
    from ai.agents.orchestrator import get_orchestrator
    from ai.agents.agent1 import get_email_agent
    from ai.agents.agent2 import get_calendar_agent
    from ai.agents.agent3 import get_search_agent
    from ai.agents.agent4 import get_communication_agent
    from ai.agents.agent5 import get_knowledge_base_agent
    import tools.sending_email  # noqa: F401
    import tools.calendar  # noqa: F401
    import tools.communication  # noqa: F401
    import tools.knowledge_base  # noqa: F401

    for name in (
        "orchestrator",
        "email_agent",
        "calendar_agent",
        "search_agent",
        "communication_agent",
        "knowledge_base_agent",
        "tombio",
    ):
        load_prompt(name)

    agents = {
        "orchestrator": get_orchestrator(),
        "email": get_email_agent(),
        "calendar": get_calendar_agent(),
        "search": get_search_agent(),
        "communication": get_communication_agent(),
        "knowledge_base": get_knowledge_base_agent(),
    }
    print("OK — prompts loaded, tools imported, agents built:")
    for label, agent in agents.items():
        print(f"  - {label}: {agent.name}")


async def run_once(prompt: str) -> None:
    from ai.agents.orchestrator import get_orchestrator
    from ai.agents.deps import OrchestratorDeps

    deps = OrchestratorDeps()
    result = await get_orchestrator().run(prompt, deps=deps)
    print(result.output)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "--check":
        build_check()
        return
    asyncio.run(run_once(" ".join(args)))


if __name__ == "__main__":
    main()
