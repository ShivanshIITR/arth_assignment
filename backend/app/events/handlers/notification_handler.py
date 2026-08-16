from collections.abc import Callable
from uuid import UUID

from arq.connections import ArqRedis

from app.events.events import MemberAdded, TaskAssigned, TaskCompleted
from app.jobs.enqueue import enqueue

ArqPoolProvider = Callable[[], ArqRedis | None]


class NotificationHandler:
    def __init__(self, pool_provider: ArqPoolProvider) -> None:
        self._pool_provider = pool_provider

    async def _enqueue(
        self,
        notification_type: str,
        recipient_user_id: UUID,
        context_id: UUID,
        actor_id: UUID,
    ) -> None:
        if recipient_user_id == actor_id:
            return
        await enqueue(
            self._pool_provider(),
            "send_email",
            notification_type,
            str(recipient_user_id),
            str(context_id),
        )

    async def on_member_added(self, event: MemberAdded) -> None:
        await self._enqueue(
            "member_added", event.user_id, event.project_id, event.actor_id
        )

    async def on_task_assigned(self, event: TaskAssigned) -> None:
        await self._enqueue(
            "task_assigned", event.assignee_id, event.task_id, event.actor_id
        )

    async def on_task_completed(self, event: TaskCompleted) -> None:
        await self._enqueue(
            "task_completed", event.owner_id, event.task_id, event.actor_id
        )
