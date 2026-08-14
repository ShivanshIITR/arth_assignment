from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.utils.pagination import PaginationParams, offset_for


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _detail_options() -> tuple:
        return (
            joinedload(Project.owner),
            selectinload(Project.members).selectinload(ProjectMember.user),
        )

    async def get_by_id(self, project_id: UUID) -> Project | None:
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(*self._detail_options())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        params: PaginationParams,
    ) -> tuple[list[Project], int]:
        member_filter = Project.id.in_(
            select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
        )
        total_stmt = select(func.count()).select_from(Project).where(member_filter)
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = (
            select(Project)
            .where(member_filter)
            .options(*self._detail_options())
            .order_by(Project.created_at.desc(), Project.id)
            .offset(offset_for(params))
            .limit(params.page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all()), total

    async def list_ids_for_user(self, user_id: UUID) -> list[UUID]:
        stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def add_member(self, project_id: UUID, user_id: UUID) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id)
        self.session.add(member)
        await self.session.flush()
        return member

    async def remove_member(self, project_id: UUID, user_id: UUID) -> bool:
        stmt = delete(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()
