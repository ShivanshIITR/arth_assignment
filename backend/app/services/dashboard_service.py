from sqlalchemy.ext.asyncio import AsyncSession

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
    ) -> None:
        self.session = session
        self.projects = projects
        self.tasks = tasks

    async def get_stats(self, user: User) -> DashboardStats:
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
