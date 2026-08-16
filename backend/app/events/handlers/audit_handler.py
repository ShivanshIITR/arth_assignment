from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.events import (
    AttachmentDeleted,
    AttachmentUploaded,
    MemberAdded,
    MemberRemoved,
    ProjectCreated,
    ProjectDeleted,
    ProjectUpdated,
    TaskCompleted,
    TaskDeleted,
    TokenReuseDetected,
    UserLoggedIn,
    UserLoggedOut,
)
from app.models.audit_log import AuditLog
from app.models.enums import AuditEventType
from app.repositories.audit_repository import AuditRepository


def _meta(**values: object) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in values.items():
        if value is None:
            continue
        payload[key] = str(value) if isinstance(value, UUID) else value
    return payload


class AuditHandler:
    async def _write(
        self,
        session: AsyncSession,
        *,
        event_type: AuditEventType,
        actor_id: UUID | None = None,
        project_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
        ip_address: str | None = None,
    ) -> None:
        await AuditRepository(session).create(
            AuditLog(
                actor_id=actor_id,
                event_type=event_type,
                project_id=project_id,
                resource_type=resource_type,
                resource_id=resource_id,
                event_metadata=metadata,
                ip_address=ip_address,
            )
        )

    async def on_user_logged_in(
        self, event: UserLoggedIn, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.LOGIN,
            actor_id=event.user_id,
            ip_address=event.ip_address,
        )

    async def on_user_logged_out(
        self, event: UserLoggedOut, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.LOGOUT,
            actor_id=event.user_id,
        )

    async def on_token_reuse_detected(
        self, event: TokenReuseDetected, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.TOKEN_REUSE_DETECTED,
            actor_id=event.user_id,
            ip_address=event.ip_address,
            metadata=_meta(family_id=event.family_id),
        )

    async def on_project_created(
        self, event: ProjectCreated, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.PROJECT_CREATED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="project",
            resource_id=event.project_id,
        )

    async def on_project_updated(
        self, event: ProjectUpdated, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.PROJECT_UPDATED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="project",
            resource_id=event.project_id,
        )

    async def on_project_deleted(
        self, event: ProjectDeleted, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.PROJECT_DELETED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="project",
            resource_id=event.project_id,
        )

    async def on_member_added(self, event: MemberAdded, session: AsyncSession) -> None:
        await self._write(
            session,
            event_type=AuditEventType.MEMBER_ADDED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="user",
            resource_id=event.user_id,
            metadata=_meta(user_id=event.user_id),
        )

    async def on_member_removed(
        self, event: MemberRemoved, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.MEMBER_REMOVED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="user",
            resource_id=event.removed_user_id,
            metadata=_meta(
                removed_user_id=event.removed_user_id,
                reassigned_task_count=event.reassigned_task_count,
            ),
        )

    async def on_task_deleted(self, event: TaskDeleted, session: AsyncSession) -> None:
        await self._write(
            session,
            event_type=AuditEventType.TASK_DELETED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="task",
            resource_id=event.task_id,
        )

    async def on_task_completed(
        self, event: TaskCompleted, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.TASK_COMPLETED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="task",
            resource_id=event.task_id,
        )

    async def on_attachment_uploaded(
        self, event: AttachmentUploaded, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.ATTACHMENT_UPLOADED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="attachment",
            resource_id=event.attachment_id,
            metadata=_meta(task_id=event.task_id),
        )

    async def on_attachment_deleted(
        self, event: AttachmentDeleted, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            event_type=AuditEventType.ATTACHMENT_DELETED,
            actor_id=event.actor_id,
            project_id=event.project_id,
            resource_type="attachment",
            resource_id=event.attachment_id,
            metadata=_meta(task_id=event.task_id),
        )
