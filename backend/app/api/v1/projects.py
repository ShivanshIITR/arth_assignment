from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, PolicyEngineDep, get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page, PaginationParams
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import ProjectService
from app.utils.pagination import pagination_params

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    policies: PolicyEngineDep,
) -> ProjectService:
    return ProjectService(
        session=session,
        projects=ProjectRepository(session),
        users=UserRepository(session),
        policies=policies,
    )


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> ProjectRead:
    project = await service.create(current_user, body)
    return ProjectRead.from_project(project)


@router.get("", response_model=Page[ProjectRead])
async def list_projects(
    current_user: CurrentUser,
    service: ProjectServiceDep,
    params: Annotated[PaginationParams, Depends(pagination_params)],
) -> Page[ProjectRead]:
    items, total = await service.list_for_user(current_user, params)
    return Page(
        items=[ProjectRead.from_project(project) for project in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> ProjectRead:
    project = await service.get(current_user, project_id)
    return ProjectRead.from_project(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> ProjectRead:
    project = await service.update(current_user, project_id, body)
    return ProjectRead.from_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> None:
    await service.delete(current_user, project_id)


@router.post(
    "/{project_id}/members",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    body: ProjectMemberAdd,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> ProjectRead:
    project = await service.add_member(current_user, project_id, body)
    return ProjectRead.from_project(project)


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    service: ProjectServiceDep,
) -> None:
    await service.remove_member(current_user, project_id, user_id)
