from types import SimpleNamespace
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    PROJECT_DETAIL_TTL_SECONDS,
    get_or_set,
    project_detail_key,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.events.dispatcher import EventDispatcher
from app.events.events import (
    MemberAdded,
    MemberRemoved,
    ProjectCreated,
    ProjectDeleted,
    ProjectUpdated,
)
from app.models.project import Project
from app.models.user import User
from app.policies.engine import PolicyEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginationParams
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectRead,
    ProjectUpdate,
)


class ProjectService:
    def __init__(
        self,
        session: AsyncSession,
        projects: ProjectRepository,
        users: UserRepository,
        tasks: TaskRepository,
        policies: PolicyEngine,
        dispatcher: EventDispatcher,
        redis: Redis | None = None,
    ) -> None:
        self.session = session
        self.projects = projects
        self.users = users
        self.tasks = tasks
        self.policies = policies
        self.dispatcher = dispatcher
        self.redis = redis

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
        await self.dispatcher.emit(
            ProjectCreated(
                project_id=loaded.id,
                owner_id=user.id,
                actor_id=user.id,
                affected_user_ids=tuple(loaded.member_ids),
            ),
            self.session,
        )
        return loaded

    async def list_for_user(
        self,
        user: User,
        params: PaginationParams,
    ) -> tuple[list[Project], int]:
        return await self.projects.list_for_user(user.id, params)

    async def get(self, user: User, project_id: UUID) -> ProjectRead:
        async def loader() -> ProjectRead:
            project = await self._get_or_404(project_id)
            return ProjectRead.from_project(project)

        detail = await get_or_set(
            project_detail_key(project_id),
            PROJECT_DETAIL_TTL_SECONDS,
            loader,
            self.redis,
            dumps=lambda value: value.model_dump_json(),
            loads=ProjectRead.model_validate_json,
        )
        view = SimpleNamespace(
            owner_id=detail.owner_id,
            member_ids={member.user_id for member in detail.members},
        )
        self.policies.authorize(user, "project:view", view)
        return detail

    async def update(
        self, user: User, project_id: UUID, data: ProjectUpdate
    ) -> Project:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:update", project)
        if data.name is not None:
            project.name = data.name.strip()
        if data.description is not None:
            project.description = data.description
        await self.session.flush()
        loaded = await self.projects.get_by_id(project.id)
        assert loaded is not None
        await self.dispatcher.emit(
            ProjectUpdated(
                project_id=loaded.id,
                actor_id=user.id,
                affected_user_ids=tuple(loaded.member_ids),
            ),
            self.session,
        )
        return loaded

    async def delete(self, user: User, project_id: UUID) -> None:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:delete", project)
        event = ProjectDeleted(
            project_id=project.id,
            actor_id=user.id,
            affected_user_ids=tuple(project.member_ids),
        )
        await self.dispatcher.emit(event, self.session)
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
        await self.dispatcher.emit(
            MemberAdded(
                project_id=loaded.id,
                user_id=target.id,
                actor_id=user.id,
                affected_user_ids=tuple(loaded.member_ids),
            ),
            self.session,
        )
        return loaded

    async def remove_member(
        self, user: User, project_id: UUID, member_id: UUID
    ) -> None:
        project = await self._get_or_404(project_id)
        self.policies.authorize(user, "project:update", project)
        if member_id == project.owner_id:
            raise ConflictError("Cannot remove the project owner")
        if member_id not in project.member_ids:
            raise NotFoundError("Member not found")
        affected = tuple(project.member_ids)
        reassigned_count = await self.tasks.reassign_creator(
            project_id=project.id,
            from_user_id=member_id,
            to_user_id=project.owner_id,
        )
        await self.projects.remove_member(project.id, member_id)
        event = MemberRemoved(
            project_id=project.id,
            removed_user_id=member_id,
            project_owner_id=project.owner_id,
            actor_id=user.id,
            reassigned_task_count=reassigned_count,
            affected_user_ids=affected,
        )
        await self.dispatcher.emit(event, self.session)

    async def _get_or_404(self, project_id: UUID) -> Project:
        project = await self.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
