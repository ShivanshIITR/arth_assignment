from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.websocket.connection_manager import ConnectionManager


def _socket() -> MagicMock:
    websocket = MagicMock()
    websocket.send_json = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.mark.asyncio
async def test_register_broadcast_and_unregister() -> None:
    manager = ConnectionManager()
    project_id = uuid4()
    user_id = uuid4()
    first = _socket()
    second = _socket()
    manager.register(project_id, user_id, first)
    manager.register(project_id, uuid4(), second)

    payload = {"type": "task_changed", "action": "updated"}
    await manager.broadcast(project_id, payload)
    first.send_json.assert_awaited_once_with(payload)
    second.send_json.assert_awaited_once_with(payload)

    manager.unregister(first)
    first.send_json.reset_mock()
    second.send_json.reset_mock()
    await manager.broadcast(project_id, payload)
    first.send_json.assert_not_awaited()
    second.send_json.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_disconnect_user_closes_only_that_member() -> None:
    manager = ConnectionManager()
    project_id = uuid4()
    removed = uuid4()
    kept = uuid4()
    gone = _socket()
    stays = _socket()
    manager.register(project_id, removed, gone)
    manager.register(project_id, kept, stays)

    await manager.disconnect_user(project_id, removed)
    gone.close.assert_awaited_once_with(code=4403)
    stays.close.assert_not_awaited()

    payload = {"type": "task_changed", "action": "deleted"}
    await manager.broadcast(project_id, payload)
    gone.send_json.assert_not_awaited()
    stays.send_json.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_broadcast_to_empty_room_is_noop() -> None:
    manager = ConnectionManager()
    await manager.broadcast(uuid4(), {"type": "task_changed"})
