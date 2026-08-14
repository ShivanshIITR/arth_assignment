from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project
from app.models.user import User
from app.policies.engine import PolicyEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginationParams
from app.schemas.project import ProjectCreate, ProjectMemberAdd, ProjectUpdate


class ProjectService:
    def __init__(
        self,
        session: AsyncSession,
        projects: ProjectRepository,
        users: UserRepository,
        policies: PolicyEngine,
    ) -> None:
        self.session = session
        self.projects = projects
        self.users = users
        self.policies = policies

    async def create(self, user: User, data: ProjectCreate) -> Project:
        project = Project(
            name=data.name.strip(),
            description=data.description,
            owner_id=user.id,
        )
        await self.projects.add(project)
        await self.projects.add_member(project.id, user.id)
        loaded = await self.projects.get_by_id(project.id)
        assert loaded is not None
        return loaded

    async def list_for_user(
        self,
        user: User,
        params: PaginationParams,
    ) -> tuple[list[Project], int]:
        return await self.projects.list_for_user(user.id, params)

    async def get(self, user: User, project_id: UUID) -> Project:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:view", project)
        return project

    async def update(self, user: User, project_id: UUID, data: ProjectUpdate) -> Project:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:update", project)
        if data.name is not None:
            project.name = data.name.strip()
        if data.description is not None:
            project.description = data.description
        await self.session.flush()
        return project

    async def delete(self, user: User, project_id: UUID) -> None:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:delete", project)
        await self.projects.delete(project)

    async def add_member(
        self,
        user: User,
        project_id: UUID,
        data: ProjectMemberAdd,
    ) -> Project:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:update", project)
        target = await self.users.get_by_email(str(data.email).lower())
        if target is None:
            raise NotFoundError("User not found")
        try:
            async with self.session.begin_nested():
                await self.projects.add_member(project.id, target.id)
        except IntegrityError as exc:
            raise ConflictError("User is already a member of this project") from exc
        loaded = await self.projects.get_by_id(project.id)
        assert loaded is not None
        return loaded

    async def remove_member(self, user: User, project_id: UUID, member_id: UUID) -> None:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:update", project)
        if member_id == project.owner_id:
            raise ConflictError("Cannot remove the project owner")
        removed = await self.projects.remove_member(project.id, member_id)
        if not removed:
            raise NotFoundError("Member not found")

    async def _get_or_404(self, project_id: UUID) -> Project:
        project = await self.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
