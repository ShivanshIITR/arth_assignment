from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.repositories.audit_repository import AuditRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.audit import AuditLogRead
from app.schemas.common import Page, PaginationParams
from app.services.audit_service import AuditService
from app.utils.pagination import pagination_params

project_router = APIRouter(
    prefix="/projects/{project_id}/audit-logs", tags=["audit"]
)
me_router = APIRouter(prefix="/users/me/audit-logs", tags=["audit"])


def get_audit_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuditService:
    return AuditService(
        session=session,
        audits=AuditRepository(session),
        projects=ProjectRepository(session),
    )


AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]


@project_router.get("", response_model=Page[AuditLogRead])
async def list_project_audit_logs(
    project_id: UUID,
    current_user: CurrentUser,
    service: AuditServiceDep,
    params: Annotated[PaginationParams, Depends(pagination_params)],
) -> Page[AuditLogRead]:
    items, total = await service.list_for_project(current_user, project_id, params)
    return Page(
        items=[AuditLogRead.from_entry(entry) for entry in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@me_router.get("", response_model=Page[AuditLogRead])
async def list_my_audit_logs(
    current_user: CurrentUser,
    service: AuditServiceDep,
    params: Annotated[PaginationParams, Depends(pagination_params)],
) -> Page[AuditLogRead]:
    items, total = await service.list_for_user(current_user, params)
    return Page(
        items=[AuditLogRead.from_entry(entry) for entry in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
