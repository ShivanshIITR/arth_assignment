from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.attachment import Attachment
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _detail_options() -> tuple:
        return (
            selectinload(Attachment.uploader),
            joinedload(Attachment.task).options(
                joinedload(Task.project).options(
                    joinedload(Project.owner),
                    selectinload(Project.members).selectinload(ProjectMember.user),
                )
            ),
        )

    async def get_by_id(self, attachment_id: UUID) -> Attachment | None:
        stmt = (
            select(Attachment)
            .where(Attachment.id == attachment_id)
            .options(*self._detail_options())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_for_task(self, task_id: UUID) -> list[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.task_id == task_id)
            .options(selectinload(Attachment.uploader))
            .order_by(Attachment.created_at.desc(), Attachment.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.flush()
        return attachment

    async def delete(self, attachment: Attachment) -> None:
        await self.session.delete(attachment)
        await self.session.flush()
