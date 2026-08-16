from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.policies.engine import PolicyEngine
from app.repositories.activity_repository import ActivityRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import PaginationParams


class ActivityService:
    def __init__(
        self,
        session: AsyncSession,
        activities: ActivityRepository,
        projects: ProjectRepository,
        policies: PolicyEngine,
    ) -> None:
        self.session = session
        self.activities = activities
        self.projects = projects
        self.policies = policies

    async def list_for_project(
        self,
        user: User,
        project_id: UUID,
        params: PaginationParams,
    ):
        project = await self.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        self.policies.authorize(user, "timeline:view", project)
        return await self.activities.list_for_project(project_id, params)
