from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.schemas.common import PaginationParams
from app.utils.pagination import offset_for


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, entry: AuditLog) -> AuditLog:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_for_project(
        self,
        project_id: UUID,
        params: PaginationParams,
    ) -> tuple[list[AuditLog], int]:
        filters = [AuditLog.project_id == project_id]
        return await self._paginated(filters, params)

    async def list_for_user(
        self,
        user_id: UUID,
        params: PaginationParams,
    ) -> tuple[list[AuditLog], int]:
        filters = [AuditLog.actor_id == user_id]
        return await self._paginated(filters, params)

    async def _paginated(
        self,
        filters: list,
        params: PaginationParams,
    ) -> tuple[list[AuditLog], int]:
        count_stmt = select(func.count()).select_from(AuditLog).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()
        stmt = (
            select(AuditLog)
            .where(*filters)
            .options(selectinload(AuditLog.actor))
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset_for(params))
            .limit(params.page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total
