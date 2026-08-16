from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, PolicyEngineDep, get_db
from app.repositories.activity_repository import ActivityRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.activity import ActivityLogRead
from app.schemas.common import Page, PaginationParams
from app.services.activity_service import ActivityService
from app.utils.pagination import pagination_params

router = APIRouter(prefix="/projects/{project_id}/activity", tags=["activity"])


def get_activity_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    policies: PolicyEngineDep,
) -> ActivityService:
    return ActivityService(
        session=session,
        activities=ActivityRepository(session),
        projects=ProjectRepository(session),
        policies=policies,
    )


ActivityServiceDep = Annotated[ActivityService, Depends(get_activity_service)]


@router.get("", response_model=Page[ActivityLogRead])
async def list_project_activity(
    project_id: UUID,
    current_user: CurrentUser,
    service: ActivityServiceDep,
    params: Annotated[PaginationParams, Depends(pagination_params)],
) -> Page[ActivityLogRead]:
    items, total = await service.list_for_project(current_user, project_id, params)
    return Page(
        items=[ActivityLogRead.from_entry(entry) for entry in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
