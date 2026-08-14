from uuid import UUID

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.enums import TaskPriority, TaskStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.schemas.common import PaginationParams
from app.utils.pagination import offset_for


def escape_ilike(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _detail_options() -> tuple:
        return (
            selectinload(Task.assignee),
            selectinload(Task.creator),
            joinedload(Task.project).options(
                joinedload(Project.owner),
                selectinload(Project.members).selectinload(ProjectMember.user),
            ),
        )

    async def get_by_id(self, task_id: UUID) -> Task | None:
        stmt = select(Task).where(Task.id == task_id).options(*self._detail_options())
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_filtered(
        self,
        project_id: UUID,
        params: PaginationParams,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        filters = [Task.project_id == project_id]
        if status is not None:
            filters.append(Task.status == status)
        if priority is not None:
            filters.append(Task.priority == priority)
        if search:
            pattern = f"%{escape_ilike(search)}%"
            filters.append(Task.title.ilike(pattern, escape="\\"))

        count_stmt = select(func.count()).select_from(Task).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt: Select[tuple[Task]] = (
            select(Task)
            .where(*filters)
            .options(selectinload(Task.assignee), selectinload(Task.creator))
            .order_by(Task.created_at.desc(), Task.id)
            .offset(offset_for(params))
            .limit(params.page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all()), total

    async def add(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        return task

    async def reassign_creator(
        self,
        *,
        project_id: UUID,
        from_user_id: UUID,
        to_user_id: UUID,
    ) -> int:
        """Transfer task ownership when a member leaves the project."""
        stmt = (
            update(Task)
            .where(
                Task.project_id == project_id,
                Task.creator_id == from_user_id,
            )
            .values(creator_id=to_user_id)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def delete_if_todo(self, task_id: UUID) -> UUID | None:
        stmt = (
            delete(Task)
            .where(Task.id == task_id, Task.status == TaskStatus.TODO)
            .returning(Task.id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_status(self, project_ids: list[UUID]) -> dict[str, int]:
        counts = {status.value: 0 for status in TaskStatus}
        if not project_ids:
            return counts
        stmt = (
            select(Task.status, func.count())
            .where(Task.project_id.in_(project_ids))
            .group_by(Task.status)
        )
        result = await self.session.execute(stmt)
        for status, count in result.all():
            counts[status.value] = count
        return counts

    async def count_active_projects(self, project_ids: list[UUID]) -> int:
        if not project_ids:
            return 0
        stmt = select(func.count(func.distinct(Task.project_id))).where(
            Task.project_id.in_(project_ids),
            Task.status != TaskStatus.COMPLETED,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
