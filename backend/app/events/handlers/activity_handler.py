from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.events import (
    AttachmentDeleted,
    AttachmentUploaded,
    MemberAdded,
    MemberRemoved,
    ProjectCreated,
    ProjectUpdated,
    TaskAssigned,
    TaskCreated,
    TaskDeleted,
    TaskStatusChanged,
    TaskUpdated,
)
from app.models.activity_log import ActivityLog
from app.models.enums import ActivityEventType
from app.repositories.activity_repository import ActivityRepository


def _meta(**values: object) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in values.items():
        if value is None:
            continue
        payload[key] = str(value) if isinstance(value, UUID) else value
    return payload


class ActivityHandler:
    async def _write(
        self,
        session: AsyncSession,
        *,
        project_id: UUID,
        event_type: ActivityEventType,
        actor_id: UUID | None = None,
        task_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        await ActivityRepository(session).create(
            ActivityLog(
                project_id=project_id,
                actor_id=actor_id,
                event_type=event_type,
                task_id=task_id,
                event_metadata=metadata,
            )
        )

    async def on_project_created(
        self, event: ProjectCreated, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.PROJECT_CREATED,
        )

    async def on_project_updated(
        self, event: ProjectUpdated, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.PROJECT_UPDATED,
        )

    async def on_member_added(self, event: MemberAdded, session: AsyncSession) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.MEMBER_ADDED,
            metadata=_meta(user_id=event.user_id),
        )

    async def on_member_removed(
        self, event: MemberRemoved, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.MEMBER_REMOVED,
            metadata=_meta(
                removed_user_id=event.removed_user_id,
                reassigned_task_count=event.reassigned_task_count,
            ),
        )
        if event.reassigned_task_count > 0:
            await self._write(
                session,
                project_id=event.project_id,
                actor_id=None,
                event_type=ActivityEventType.TASK_REASSIGNED,
                metadata=_meta(
                    from_user_id=event.removed_user_id,
                    to_user_id=event.project_owner_id,
                    task_count=event.reassigned_task_count,
                ),
            )

    async def on_task_created(self, event: TaskCreated, session: AsyncSession) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.TASK_CREATED,
            task_id=event.task_id,
        )

    async def on_task_assigned(
        self, event: TaskAssigned, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.TASK_ASSIGNED,
            task_id=event.task_id,
            metadata=_meta(assignee_id=event.assignee_id),
        )

    async def on_task_status_changed(
        self, event: TaskStatusChanged, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.TASK_STATUS_CHANGED,
            task_id=event.task_id,
            metadata=_meta(old_status=event.old_status, new_status=event.new_status),
        )

    async def on_task_updated(self, event: TaskUpdated, session: AsyncSession) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.TASK_UPDATED,
            task_id=event.task_id,
        )

    async def on_task_deleted(self, event: TaskDeleted, session: AsyncSession) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.TASK_DELETED,
            task_id=event.task_id,
            metadata=_meta(task_id=event.task_id),
        )

    async def on_attachment_uploaded(
        self, event: AttachmentUploaded, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.ATTACHMENT_UPLOADED,
            task_id=event.task_id,
            metadata=_meta(attachment_id=event.attachment_id),
        )

    async def on_attachment_deleted(
        self, event: AttachmentDeleted, session: AsyncSession
    ) -> None:
        await self._write(
            session,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=ActivityEventType.ATTACHMENT_DELETED,
            task_id=event.task_id,
            metadata=_meta(attachment_id=event.attachment_id),
        )
