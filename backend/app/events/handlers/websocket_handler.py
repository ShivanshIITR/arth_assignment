from collections.abc import Callable
from uuid import UUID

from app.events.events import (
    AttachmentDeleted,
    AttachmentUploaded,
    MemberRemoved,
    TaskAssigned,
    TaskCreated,
    TaskDeleted,
    TaskStatusChanged,
    TaskUpdated,
)
from app.websocket.connection_manager import ConnectionManager

ManagerProvider = Callable[[], ConnectionManager]


class WebSocketHandler:
    def __init__(self, manager_provider: ManagerProvider) -> None:
        self._manager_provider = manager_provider

    async def _task_changed(
        self, project_id: UUID, task_id: UUID, action: str
    ) -> None:
        await self._manager_provider().broadcast(
            project_id,
            {
                "type": "task_changed",
                "task_id": str(task_id),
                "action": action,
            },
        )

    async def on_task_created(self, event: TaskCreated) -> None:
        await self._task_changed(event.project_id, event.task_id, "created")

    async def on_task_updated(self, event: TaskUpdated) -> None:
        await self._task_changed(event.project_id, event.task_id, "updated")

    async def on_task_status_changed(self, event: TaskStatusChanged) -> None:
        await self._task_changed(
            event.project_id, event.task_id, "status_changed"
        )

    async def on_task_deleted(self, event: TaskDeleted) -> None:
        await self._task_changed(event.project_id, event.task_id, "deleted")

    async def on_task_assigned(self, event: TaskAssigned) -> None:
        await self._task_changed(event.project_id, event.task_id, "assigned")

    async def on_member_removed(self, event: MemberRemoved) -> None:
        await self._manager_provider().disconnect_user(
            event.project_id, event.removed_user_id
        )

    async def _attachment_changed(
        self, project_id: UUID, task_id: UUID, action: str
    ) -> None:
        await self._manager_provider().broadcast(
            project_id,
            {
                "type": "attachment_changed",
                "task_id": str(task_id),
                "action": action,
            },
        )

    async def on_attachment_uploaded(self, event: AttachmentUploaded) -> None:
        await self._attachment_changed(
            event.project_id, event.task_id, "uploaded"
        )

    async def on_attachment_deleted(self, event: AttachmentDeleted) -> None:
        await self._attachment_changed(
            event.project_id, event.task_id, "deleted"
        )
