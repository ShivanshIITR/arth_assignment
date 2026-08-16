from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.events.dispatcher import EventDispatcher
from app.events.events import ProjectCreated, TaskCreated


def _project_created() -> ProjectCreated:
    owner_id = uuid4()
    return ProjectCreated(project_id=uuid4(), owner_id=owner_id, actor_id=owner_id)


class _FakeTransaction:
    def __init__(self, session: "_FakeSession") -> None:
        self._session = session

    async def __aenter__(self) -> "_FakeSession":
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self._session.rolled_back = True
            return False
        self._session.committed = True
        return False


class _FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.writes: list[str] = []
        self.info: dict = {}

    def begin(self) -> _FakeTransaction:
        return _FakeTransaction(self)


@pytest.mark.asyncio
async def test_publish_invokes_sync_subscribers() -> None:
    dispatcher = EventDispatcher()
    seen: list[object] = []
    session = MagicMock()

    async def handler(event: ProjectCreated, _session) -> None:
        seen.append(event)

    dispatcher.subscribe(ProjectCreated, handler)
    event = _project_created()
    await dispatcher.publish(event, session)
    assert seen == [event]


@pytest.mark.asyncio
async def test_publish_after_commit_runs_immediately_without_session() -> None:
    dispatcher = EventDispatcher()
    seen: list[object] = []

    async def handler(event: ProjectCreated) -> None:
        seen.append(event)

    dispatcher.subscribe_after_commit(ProjectCreated, handler)
    event = _project_created()
    await dispatcher.publish_after_commit(event)
    assert seen == [event]


@pytest.mark.asyncio
async def test_publish_after_commit_queues_until_drain() -> None:
    dispatcher = EventDispatcher()
    seen: list[object] = []
    session = _FakeSession()

    async def handler(event: ProjectCreated) -> None:
        seen.append(event)

    dispatcher.subscribe_after_commit(ProjectCreated, handler)
    event = _project_created()
    await dispatcher.publish_after_commit(event, session=session)
    assert seen == []
    await dispatcher.drain_after_commit(session)
    assert seen == [event]


@pytest.mark.asyncio
async def test_sync_handler_raise_rolls_back_transaction() -> None:
    dispatcher = EventDispatcher()
    session = _FakeSession()

    async def write_then_fail(event: TaskCreated, sess: _FakeSession) -> None:
        sess.writes.append("activity")
        raise RuntimeError("handler failed")

    dispatcher.subscribe(TaskCreated, write_then_fail)
    event = TaskCreated(task_id=uuid4(), project_id=uuid4(), actor_id=uuid4())

    with pytest.raises(RuntimeError, match="handler failed"):
        async with session.begin():
            session.writes.append("task")
            await dispatcher.publish(event, session)  # type: ignore[arg-type]

    assert session.rolled_back is True
    assert session.committed is False
    assert session.writes == ["task", "activity"]


@pytest.mark.asyncio
async def test_after_commit_handler_failure_is_swallowed() -> None:
    dispatcher = EventDispatcher()
    ran: list[str] = []

    async def boom(_event: ProjectCreated) -> None:
        raise RuntimeError("broadcast failed")

    async def ok(_event: ProjectCreated) -> None:
        ran.append("ok")

    dispatcher.subscribe_after_commit(ProjectCreated, boom)
    dispatcher.subscribe_after_commit(ProjectCreated, ok)
    await dispatcher.publish_after_commit(_project_created())
    assert ran == ["ok"]


@pytest.mark.asyncio
async def test_unrelated_event_type_is_ignored() -> None:
    dispatcher = EventDispatcher()
    handler = AsyncMock()
    dispatcher.subscribe(ProjectCreated, handler)
    await dispatcher.publish(
        TaskCreated(task_id=uuid4(), project_id=uuid4(), actor_id=uuid4()),
        MagicMock(),
    )
    handler.assert_not_awaited()
