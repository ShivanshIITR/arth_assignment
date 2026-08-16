import pytest

from app.events.events import MemberRemoved, TaskCreated, TaskStatusChanged
from app.events.handlers.activity_handler import ActivityHandler
from app.models.enums import ActivityEventType
from app.repositories.activity_repository import ActivityRepository
from app.schemas.common import PaginationParams
from tests.test_factories import make_project, make_task, make_user


@pytest.mark.asyncio
async def test_activity_handler_writes_task_created(db_session) -> None:
    owner = make_user()
    db_session.add(owner)
    await db_session.flush()
    project = make_project(owner)
    db_session.add(project)
    await db_session.flush()
    task = make_task(project, owner)
    db_session.add(task)
    await db_session.flush()

    handler = ActivityHandler()
    await handler.on_task_created(
        TaskCreated(task_id=task.id, project_id=project.id, actor_id=owner.id),
        db_session,
    )
    items, total = await ActivityRepository(db_session).list_for_project(
        project.id, PaginationParams()
    )
    assert total == 1
    assert items[0].event_type == ActivityEventType.TASK_CREATED
    assert items[0].task_id == task.id
    assert items[0].actor_id == owner.id


@pytest.mark.asyncio
async def test_member_removed_writes_reassignment_summary(db_session) -> None:
    owner = make_user()
    member = make_user(email="member@example.com")
    db_session.add_all([owner, member])
    await db_session.flush()
    project = make_project(owner, members=[owner, member])
    db_session.add(project)
    await db_session.flush()

    handler = ActivityHandler()
    await handler.on_member_removed(
        MemberRemoved(
            project_id=project.id,
            removed_user_id=member.id,
            project_owner_id=owner.id,
            actor_id=owner.id,
            reassigned_task_count=2,
        ),
        db_session,
    )
    items, total = await ActivityRepository(db_session).list_for_project(
        project.id, PaginationParams()
    )
    assert total == 2
    types = {entry.event_type for entry in items}
    assert types == {
        ActivityEventType.MEMBER_REMOVED,
        ActivityEventType.TASK_REASSIGNED,
    }
    reassigned = next(
        entry
        for entry in items
        if entry.event_type == ActivityEventType.TASK_REASSIGNED
    )
    assert reassigned.actor_id is None
    assert reassigned.event_metadata["task_count"] == 2


@pytest.mark.asyncio
async def test_status_changed_stores_old_and_new(db_session) -> None:
    owner = make_user()
    db_session.add(owner)
    await db_session.flush()
    project = make_project(owner)
    db_session.add(project)
    await db_session.flush()
    task = make_task(project, owner)
    db_session.add(task)
    await db_session.flush()

    await ActivityHandler().on_task_status_changed(
        TaskStatusChanged(
            task_id=task.id,
            project_id=project.id,
            old_status="todo",
            new_status="in_progress",
            actor_id=owner.id,
        ),
        db_session,
    )
    items, _total = await ActivityRepository(db_session).list_for_project(
        project.id, PaginationParams()
    )
    assert items[0].event_metadata == {
        "old_status": "todo",
        "new_status": "in_progress",
    }
