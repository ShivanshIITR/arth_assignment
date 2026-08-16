from collections.abc import Callable
from uuid import UUID

from redis.asyncio import Redis

from app.core.cache import dashboard_key, delete_key, project_detail_key
from app.events.events import (
    MemberAdded,
    MemberRemoved,
    ProjectCreated,
    ProjectDeleted,
    ProjectUpdated,
    TaskCreated,
    TaskDeleted,
    TaskStatusChanged,
    TaskUpdated,
)

RedisProvider = Callable[[], Redis | None]


class CacheInvalidationHandler:
    def __init__(self, redis_provider: RedisProvider) -> None:
        self._redis_provider = redis_provider

    @property
    def redis(self) -> Redis | None:
        return self._redis_provider()

    async def _dashboards(self, user_ids: tuple[UUID, ...]) -> None:
        for user_id in user_ids:
            await delete_key(dashboard_key(user_id), self.redis)

    async def _project(self, project_id: UUID) -> None:
        await delete_key(project_detail_key(project_id), self.redis)

    async def on_project_created(self, event: ProjectCreated) -> None:
        await self._project(event.project_id)
        await self._dashboards(event.affected_user_ids or (event.owner_id,))

    async def on_project_updated(self, event: ProjectUpdated) -> None:
        await self._project(event.project_id)
        await self._dashboards(event.affected_user_ids)

    async def on_project_deleted(self, event: ProjectDeleted) -> None:
        await self._project(event.project_id)
        await self._dashboards(event.affected_user_ids)

    async def on_member_changed(self, event: MemberAdded | MemberRemoved) -> None:
        await self._project(event.project_id)
        await self._dashboards(event.affected_user_ids)

    async def on_task_changed(
        self,
        event: TaskCreated | TaskUpdated | TaskStatusChanged | TaskDeleted,
    ) -> None:
        await self._dashboards(event.affected_user_ids)
