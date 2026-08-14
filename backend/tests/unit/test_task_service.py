from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, ValidationError
from app.models.enums import TaskPriority, TaskStatus
from app.policies.engine import PolicyEngine
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService
from tests.test_factories import make_project, make_task, make_user


@pytest.fixture
def owner():
    return make_user(email="owner@example.com")


@pytest.fixture
def member():
    return make_user(email="member@example.com")


@pytest.fixture
def project(owner, member):
    return make_project(owner, members=[owner, member])


@pytest.fixture
def service(project) -> TaskService:
    session = MagicMock()
    session.flush = AsyncMock()
    tasks = AsyncMock()
    projects = AsyncMock()
    projects.get_by_id.return_value = project
    return TaskService(
        session=session,
        tasks=tasks,
        projects=projects,
        policies=PolicyEngine(),
    )


@pytest.mark.asyncio
async def test_create_rejects_non_member_assignee(
    service: TaskService, owner, project
) -> None:
    outsider = make_user(email="out@example.com")
    with pytest.raises(ValidationError, match="project member"):
        await service.create(
            owner,
            project.id,
            TaskCreate(title="Work", assignee_id=outsider.id),
        )


@pytest.mark.asyncio
async def test_complete_requires_assignee_and_due_date(
    service, member, project
) -> None:
    task = make_task(project, creator=member, assignee=None, due_date=None)
    service.tasks.get_by_id.return_value = task
    with pytest.raises(ForbiddenError):
        await service.update(
            member,
            task.id,
            TaskUpdate(status=TaskStatus.COMPLETED),
        )


@pytest.mark.asyncio
async def test_complete_succeeds_when_required_fields_present(
    service, member, project
) -> None:
    task = make_task(
        project,
        creator=member,
        assignee=member,
        title="Ship",
        priority=TaskPriority.HIGH,
        due_date=date(2026, 9, 1),
    )
    service.tasks.get_by_id.return_value = task
    updated = await service.update(
        member, task.id, TaskUpdate(status=TaskStatus.COMPLETED)
    )
    assert updated.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_delete_conflict_when_status_changed_concurrently(
    service, owner, member, project
) -> None:
    task = make_task(project, creator=member, status=TaskStatus.TODO)
    service.tasks.get_by_id.return_value = task
    service.tasks.delete_if_todo.return_value = None
    with pytest.raises(ConflictError):
        await service.delete(owner, task.id)
