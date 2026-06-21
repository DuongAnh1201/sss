"""Email sub-agent."""
import asyncio

from pydantic_ai import Agent, RunContext

from ai.agents.consent import gate
from ai.agents.deps import OrchestratorDeps
from ai.prompts import load_prompt
from schemas.agent1 import EmailAgentResult, EmailDraft  # noqa: F401 — EmailDraft re-exported for callers

_email_agent: Agent | None = None
_SYSTEM_PROMPT = load_prompt("email_agent")


def get_email_agent() -> Agent:
    global _email_agent
    if _email_agent is None:
        from config import settings
        from observability.phoenix import get_agent_instrumentation

        _email_agent = Agent(
            model=settings.ai_model,
            name="email_agent",
            system_prompt=_SYSTEM_PROMPT,
            output_type=EmailAgentResult,
            deps_type=OrchestratorDeps,
            instrument=get_agent_instrumentation(),
        )

        @_email_agent.tool
        async def send_user_email(
            ctx: RunContext[OrchestratorDeps],
            to: str,
            subject: str,
            body: str,
        ) -> str:
            """Send a plain email to any recipient on behalf of the user."""
            from config import settings
            from tools.sending_email import send_user_email as _send

            async def _execute() -> str:
                result = await asyncio.to_thread(
                    _send,
                    recipient=to,
                    subject=subject,
                    body=body,
                    api_key=settings.resend_api_key,
                    from_address=settings.resend_from,
                )
                if result == "ok":
                    return f"Email successfully sent to {to}."
                return f"Failed to send email to {to}. Reason: {result}"

            return await gate(
                ctx,
                action_type="email.send",
                agent="email_agent",
                summary=f"Send email to {to} — subject '{subject}'",
                payload={"to": to, "subject": subject, "body": body},
                execute=_execute,
            )

        @_email_agent.tool
        async def send_notification_email(
            ctx: RunContext[OrchestratorDeps],
            recipient: str,
            subject: str,
            details: str,
            link: str = "",
        ) -> str:
            """Send a styled HTML notification email (system alerts, reminders, status updates)."""
            from config import settings
            from tools.sending_email import send_notification_email as _send
            from schemas.agent1 import NotificationEmailRequest

            async def _execute() -> str:
                n = NotificationEmailRequest(
                    recipient=recipient,
                    subject=subject,
                    details=details,
                    link=link,
                    api_key=settings.resend_api_key,
                    from_address=settings.resend_from,
                )
                result = await asyncio.to_thread(_send, n)
                if result == "ok":
                    return f"Notification email successfully sent to {recipient}."
                return f"Failed to send notification to {recipient}. Reason: {result}"

            return await gate(
                ctx,
                action_type="email.notification",
                agent="email_agent",
                summary=f"Send notification to {recipient} — subject '{subject}'",
                payload={"recipient": recipient, "subject": subject, "details": details, "link": link},
                execute=_execute,
            )

        @_email_agent.tool
        async def register_domain(ctx: RunContext[OrchestratorDeps], domain_name: str) -> str:
            """Register a sending domain with Resend and return the DNS records to configure."""
            from tools.sending_email import add_domain

            async def _execute() -> str:
                try:
                    domain = await asyncio.to_thread(add_domain, domain_name)
                    records = domain.records if hasattr(domain, "records") else domain.get("records", [])
                    lines = [f"Domain '{domain_name}' added (ID: {domain.id if hasattr(domain, 'id') else domain.get('id')})."]
                    lines.append("Add these DNS records at your registrar:")
                    for r in records:
                        rec = r if isinstance(r, dict) else vars(r)
                        lines.append(f"  {rec.get('type')} {rec.get('name')} → {rec.get('value')}")
                    return "\n".join(lines)
                except Exception as e:  # noqa: BLE001
                    return f"Failed to register domain: {e}"

            return await gate(
                ctx,
                action_type="email.register_domain",
                agent="email_agent",
                summary=f"Register sending domain '{domain_name}' with Resend",
                payload={"domain_name": domain_name},
                execute=_execute,
            )

    return _email_agent
