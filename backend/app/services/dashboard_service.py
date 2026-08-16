from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import DASHBOARD_TTL_SECONDS, dashboard_key, get_or_set
from app.models.enums import TaskStatus
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.dashboard import DashboardStats


class DashboardService:
    def __init__(
        self,
        session: AsyncSession,
        projects: ProjectRepository,
        tasks: TaskRepository,
        redis: Redis | None = None,
    ) -> None:
        self.session = session
        self.projects = projects
        self.tasks = tasks
        self.redis = redis

    async def get_stats(self, user: User) -> DashboardStats:
        async def loader() -> DashboardStats:
            return await self._load_stats(user)

        return await get_or_set(
            dashboard_key(user.id),
            DASHBOARD_TTL_SECONDS,
            loader,
            self.redis,
            dumps=lambda value: value.model_dump_json(),
            loads=DashboardStats.model_validate_json,
        )

    async def _load_stats(self, user: User) -> DashboardStats:
        project_ids = await self.projects.list_ids_for_user(user.id)
        status_counts = await self.tasks.count_by_status(project_ids)
        active_projects = await self.tasks.count_active_projects(project_ids)
        completed = status_counts[TaskStatus.COMPLETED.value]
        total_tasks = sum(status_counts.values())
        return DashboardStats(
            total_projects=len(project_ids),
            active_projects=active_projects,
            total_tasks=total_tasks,
            completed_tasks=completed,
            pending_tasks=total_tasks - completed,
            tasks_by_status=status_counts,
        )
