"""Knowledge base sub-agent — create, read, update, and annotate knowledge files."""
import asyncio

from pydantic_ai import Agent, RunContext

from ai.agents.consent import gate
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
        async def create_new_file(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> str:
            """Create a new file in the knowledge base."""
            from tools.knowledge_base import create_new_file as _create

            async def _execute() -> str:
                result = await asyncio.to_thread(_create, request.file_name, request.file_content)
                return result.message

            return await gate(
                ctx,
                action_type="knowledge.create",
                agent="knowledge_base_agent",
                summary=f"Create knowledge file '{request.file_name}'",
                payload={"file_name": request.file_name, "file_content": request.file_content},
                execute=_execute,
            )

        @_knowledge_base_agent.tool
        async def update_file(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> str:
            """Update a file in the knowledge base."""
            from tools.knowledge_base import update_file as _update

            async def _execute() -> str:
                result = await asyncio.to_thread(_update, request.file_name, request.file_content)
                return result.message

            return await gate(
                ctx,
                action_type="knowledge.update",
                agent="knowledge_base_agent",
                summary=f"Update knowledge file '{request.file_name}'",
                payload={"file_name": request.file_name, "file_content": request.file_content},
                execute=_execute,
            )

        @_knowledge_base_agent.tool
        async def add_context(
            ctx: RunContext[OrchestratorDeps], request: KnowledgeBaseRequest
        ) -> str:
            """Append a piece of context to a file in the knowledge base."""
            from tools.knowledge_base import add_context as _add_context

            async def _execute() -> str:
                result = await asyncio.to_thread(_add_context, request.file_name, request.context)
                return result.message

            return await gate(
                ctx,
                action_type="knowledge.add_context",
                agent="knowledge_base_agent",
                summary=f"Add context to knowledge file '{request.file_name}'",
                payload={"file_name": request.file_name, "context": request.context},
                execute=_execute,
            )

    return _knowledge_base_agent
