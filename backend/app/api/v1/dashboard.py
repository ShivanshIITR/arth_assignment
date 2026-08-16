from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, RedisDep, get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.dashboard import DashboardStats
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: RedisDep,
) -> DashboardService:
    return DashboardService(
        session=session,
        projects=ProjectRepository(session),
        tasks=TaskRepository(session),
        redis=redis,
    )


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: CurrentUser,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> DashboardStats:
    return await service.get_stats(current_user)
