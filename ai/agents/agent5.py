# this agent for updating and modifying the knowledge base
import asyncio

from pydantic_ai import Agent, RunContext

from ai.agents.deps import OrchestratorDeps
from ai.prompts import load_prompt
from schemas.agent5 import KnowledgeBaseResult, KnowledgeBaseRequest

_knowledge_base_agent: Agent | None = None


def get_knowledge_base_agent() -> Agent:
    global _knowledge_base_agent
    if _knowledge_base_agent is None:
        from config import settings

        _knowledge_base_agent = Agent(
            model=settings.ai_model,
            name="knowledge_base_agent",
            system_prompt=load_prompt("knowledge_base_agent"),
            output_type=KnowledgeBaseResult,
            deps_type=OrchestratorDeps,
        )

        @_knowledge_base_agent.tool
        async def create_new_file(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> KnowledgeBaseResult:
            """Create a new file in the knowledge base."""
            from tools.knowledge_base import create_new_file as _create_new_file
            try:
                return await asyncio.to_thread(
                    _create_new_file, request.file_name, request.file_content
                )
            except Exception as e:  # noqa: BLE001
                return KnowledgeBaseResult(success=False, context="", message=str(e))

        @_knowledge_base_agent.tool
        async def read_file(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> KnowledgeBaseResult:
            """Read a file from the knowledge base."""
            from tools.knowledge_base import read_file as _read_file
            try:
                return await asyncio.to_thread(_read_file, request.file_name)
            except Exception as e:  # noqa: BLE001
                return KnowledgeBaseResult(success=False, context="", message=str(e))

        @_knowledge_base_agent.tool
        async def update_file(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> KnowledgeBaseResult:
            """Update a file in the knowledge base."""
            from tools.knowledge_base import update_file as _update_file
            try:
                return await asyncio.to_thread(
                    _update_file, request.file_name, request.file_content
                )
            except Exception as e:  # noqa: BLE001
                return KnowledgeBaseResult(success=False, context="", message=str(e))

        @_knowledge_base_agent.tool
        async def add_context(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> KnowledgeBaseResult:
            """Append a piece of context to a file in the knowledge base."""
            from tools.knowledge_base import add_context as _add_context
            try:
                return await asyncio.to_thread(
                    _add_context, request.file_name, request.context
                )
            except Exception as e:  # noqa: BLE001
                return KnowledgeBaseResult(success=False, context="", message=str(e))

    return _knowledge_base_agent
