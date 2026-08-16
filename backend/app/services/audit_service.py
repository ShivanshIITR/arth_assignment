from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import PaginationParams


class AuditService:
    def __init__(
        self,
        session: AsyncSession,
        audits: AuditRepository,
        projects: ProjectRepository,
    ) -> None:
        self.session = session
        self.audits = audits
        self.projects = projects

    async def list_for_project(
        self,
        user: User,
        project_id: UUID,
        params: PaginationParams,
    ):
        project = await self.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        if project.owner_id != user.id:
            raise ForbiddenError("Not allowed to view project audit logs")
        return await self.audits.list_for_project(project_id, params)

    async def list_for_user(self, user: User, params: PaginationParams):
        return await self.audits.list_for_user(user.id, params)
