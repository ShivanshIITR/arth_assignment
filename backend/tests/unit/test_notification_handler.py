from uuid import uuid4

import pytest

from app.events.events import MemberAdded, TaskAssigned, TaskCompleted
from app.events.handlers.notification_handler import NotificationHandler


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple]] = []

    async def enqueue_job(self, name: str, *args: object) -> None:
        self.jobs.append((name, args))

    async def aclose(self, close_connection_pool: bool | None = None) -> None:
        return None


@pytest.mark.asyncio
async def test_member_added_enqueues_for_the_new_member() -> None:
    pool = FakeArqPool()
    handler = NotificationHandler(lambda: pool)
    actor = uuid4()
    member = uuid4()
    project = uuid4()
    await handler.on_member_added(
        MemberAdded(project_id=project, user_id=member, actor_id=actor)
    )
    assert pool.jobs == [("send_email", ("member_added", str(member), str(project)))]


@pytest.mark.asyncio
async def test_self_notifications_are_skipped() -> None:
    pool = FakeArqPool()
    handler = NotificationHandler(lambda: pool)
    user = uuid4()
    await handler.on_member_added(
        MemberAdded(project_id=uuid4(), user_id=user, actor_id=user)
    )
    await handler.on_task_assigned(
        TaskAssigned(
            task_id=uuid4(), project_id=uuid4(), assignee_id=user, actor_id=user
        )
    )
    await handler.on_task_completed(
        TaskCompleted(
            task_id=uuid4(),
            project_id=uuid4(),
            actor_id=user,
            owner_id=user,
        )
    )
    assert pool.jobs == []
