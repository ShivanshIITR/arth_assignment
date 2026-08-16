import asyncio
from uuid import UUID

import pytest

from tests.conftest import auth_client_headers
from tests.ws_client import AsyncWSClient


def _token(headers: dict[str, str]) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


async def _wait_connected(app, project_id: str) -> None:
    deadline = asyncio.get_event_loop().time() + 2
    pid = UUID(project_id)
    while asyncio.get_event_loop().time() < deadline:
        if app.state.ws_manager.has_connections(pid):
            return
        await asyncio.sleep(0.01)
    raise AssertionError("websocket did not register")


async def test_websocket_requires_auth_frame(client, app) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Live"}
    )
    project_id = created.json()["id"]

    async with AsyncWSClient(app, f"/api/v1/ws/projects/{project_id}") as ws:
        await ws.send_json({"type": "pong"})
        closed = await ws.receive()
    assert closed["type"] == "websocket.close"
    assert closed["code"] == 4401


async def test_websocket_rejects_non_members(client, app) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    _outsider, outsider_headers = await auth_client_headers(
        client, "out@example.com"
    )
    created = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Live"}
    )
    project_id = created.json()["id"]

    async with AsyncWSClient(app, f"/api/v1/ws/projects/{project_id}") as ws:
        await ws.send_json({"type": "auth", "token": _token(outsider_headers)})
        closed = await ws.receive()
    assert closed["type"] == "websocket.close"
    assert closed["code"] == 4403


async def test_websocket_member_connects(client, app) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Live"}
    )
    project_id = created.json()["id"]

    async with AsyncWSClient(app, f"/api/v1/ws/projects/{project_id}") as ws:
        await ws.send_json({"type": "auth", "token": _token(headers)})
        await ws.send_json({"type": "pong"})
        with pytest.raises(TimeoutError):
            await ws.receive(timeout=0.2)
    assert ws.close_code in {None, 1000}


async def test_websocket_receives_task_broadcast(client, app) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Live"}
    )
    project_id = created.json()["id"]

    async with AsyncWSClient(app, f"/api/v1/ws/projects/{project_id}") as ws:
        await ws.send_json({"type": "auth", "token": _token(headers)})
        await _wait_connected(app, project_id)
        task = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=headers,
            json={"title": "Live task"},
        )
        assert task.status_code == 201
        message = await ws.receive_json()
    assert message["type"] == "task_changed"
    assert message["action"] == "created"
    assert message["task_id"] == task.json()["id"]
