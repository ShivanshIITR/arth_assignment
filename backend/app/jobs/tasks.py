from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.email.factory import get_email_provider
from app.db.session import get_session_factory
from app.jobs import email_templates
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger("app.jobs")


async def health_job(ctx: dict) -> str:
    """Minimal job used to verify the worker can dequeue and run work."""
    return "ok"


async def send_email_job(
    ctx: dict,
    notification_type: str,
    recipient_user_id: str,
    context_id: str,
) -> None:
    """Render and send one notification. Payload is IDs only; data is re-fetched."""
    provider = ctx.get("email_provider") or get_email_provider(get_settings())
    session_factory = ctx.get("session_factory") or get_session_factory()
    async with session_factory() as session:
        rendered = await _render(
            session,
            notification_type=notification_type,
            recipient_user_id=UUID(recipient_user_id),
            context_id=UUID(context_id),
        )
    if rendered is None:
        return
    to, subject, body = rendered
    await provider.send(to, subject, body)


async def _render(
    session: AsyncSession,
    *,
    notification_type: str,
    recipient_user_id: UUID,
    context_id: UUID,
) -> tuple[str, str, str] | None:
    recipient = await UserRepository(session).get_by_id(recipient_user_id)
    if recipient is None:
        logger.warning(
            "email_recipient_missing",
            notification_type=notification_type,
            recipient_user_id=str(recipient_user_id),
        )
        return None

    if notification_type == "member_added":
        project = await ProjectRepository(session).get_by_id(context_id)
        if project is None:
            logger.warning("email_project_missing", project_id=str(context_id))
            return None
        subject, body = email_templates.member_added(
            recipient_name=recipient.full_name,
            project_name=project.name,
        )
        return recipient.email, subject, body

    if notification_type in {"task_assigned", "task_completed"}:
        task = await TaskRepository(session).get_by_id(context_id)
        if task is None:
            logger.warning("email_task_missing", task_id=str(context_id))
            return None
        template = (
            email_templates.task_assigned
            if notification_type == "task_assigned"
            else email_templates.task_completed
        )
        subject, body = template(
            recipient_name=recipient.full_name,
            task_title=task.title,
            project_name=task.project.name,
        )
        return recipient.email, subject, body

    logger.warning("email_unknown_notification_type", notification_type=notification_type)
    return None
