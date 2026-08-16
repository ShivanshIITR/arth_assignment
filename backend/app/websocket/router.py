import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_session_factory
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()

AUTH_TIMEOUT_SECONDS = 5.0
HEARTBEAT_SECONDS = 30.0
MAX_MISSED_PONGS = 2


def _app(websocket: WebSocket):
    return websocket.scope["app"]


@asynccontextmanager
async def _handshake_session(websocket: WebSocket) -> AsyncIterator[AsyncSession]:
    existing = getattr(_app(websocket).state, "handshake_session", None)
    if existing is not None:
        yield existing
        return
    factory = get_session_factory()
    async with factory() as session:
        yield session


@router.websocket("/ws/projects/{project_id}")
async def project_socket(websocket: WebSocket, project_id: UUID) -> None:
    await websocket.accept()
    user_id = await _authenticate(websocket)
    if user_id is None:
        return

    async with _handshake_session(websocket) as session:
        user = await UserRepository(session).get_by_id(user_id)
        if user is None:
            await websocket.close(code=4401)
            return
        project = await ProjectRepository(session).get_by_id(project_id)
        if project is None:
            await websocket.close(code=4403)
            return
        try:
            _app(websocket).state.policy_engine.authorize(
                user, "project:view", project
            )
        except ForbiddenError:
            await websocket.close(code=4403)
            return

    manager = _app(websocket).state.ws_manager
    manager.register(project_id, user.id, websocket)
    missed_pongs = 0
    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_json(), timeout=HEARTBEAT_SECONDS
                )
            except TimeoutError:
                missed_pongs += 1
                if missed_pongs > MAX_MISSED_PONGS:
                    break
                await websocket.send_json({"type": "ping"})
                continue
            except WebSocketDisconnect:
                break
            if isinstance(message, dict) and message.get("type") == "pong":
                missed_pongs = 0
    except WebSocketDisconnect:
        pass
    finally:
        manager.unregister(websocket)


async def _authenticate(websocket: WebSocket) -> UUID | None:
    try:
        first = await asyncio.wait_for(
            websocket.receive_json(), timeout=AUTH_TIMEOUT_SECONDS
        )
    except Exception:
        await websocket.close(code=4401)
        return None
    if not isinstance(first, dict) or first.get("type") != "auth":
        await websocket.close(code=4401)
        return None
    token = first.get("token")
    if not isinstance(token, str) or not token:
        await websocket.close(code=4401)
        return None
    try:
        return decode_access_token(token)
    except UnauthorizedError:
        await websocket.close(code=4401)
        return None
