from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, PolicyEngineDep, get_db
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.common import Page, PaginationParams
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService
from app.utils.pagination import pagination_params

nested_router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])
router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    policies: PolicyEngineDep,
) -> TaskService:
    return TaskService(
        session=session,
        tasks=TaskRepository(session),
        projects=ProjectRepository(session),
        policies=policies,
    )


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


@nested_router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: UUID,
    body: TaskCreate,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> TaskRead:
    task = await service.create(current_user, project_id, body)
    return TaskRead.model_validate(task)


@nested_router.get("", response_model=Page[TaskRead])
async def list_tasks(
    project_id: UUID,
    current_user: CurrentUser,
    service: TaskServiceDep,
    params: Annotated[PaginationParams, Depends(pagination_params)],
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
) -> Page[TaskRead]:
    items, total = await service.list_for_project(
        current_user,
        project_id,
        params,
        status=status_filter,
        priority=priority,
        search=search,
    )
    return Page(
        items=[TaskRead.model_validate(task) for task in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: UUID,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> TaskRead:
    task = await service.get(current_user, task_id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> TaskRead:
    task = await service.update(current_user, task_id, body)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> None:
    await service.delete(current_user, task_id)
