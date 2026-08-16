from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity_log import ActivityLog
from app.schemas.common import PaginationParams
from app.utils.pagination import offset_for


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, entry: ActivityLog) -> ActivityLog:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_for_project(
        self,
        project_id: UUID,
        params: PaginationParams,
    ) -> tuple[list[ActivityLog], int]:
        filters = [ActivityLog.project_id == project_id]
        count_stmt = select(func.count()).select_from(ActivityLog).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(ActivityLog)
            .where(*filters)
            .options(selectinload(ActivityLog.actor))
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .offset(offset_for(params))
            .limit(params.page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total
