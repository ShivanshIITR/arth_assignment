from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """In-memory per-process project rooms. Sufficient for a single API replica."""

    def __init__(self) -> None:
        self._rooms: dict[UUID, dict[UUID, set[WebSocket]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._meta: dict[WebSocket, tuple[UUID, UUID]] = {}

    def register(
        self, project_id: UUID, user_id: UUID, websocket: WebSocket
    ) -> None:
        self.unregister(websocket)
        self._rooms[project_id][user_id].add(websocket)
        self._meta[websocket] = (project_id, user_id)

    def unregister(self, websocket: WebSocket) -> None:
        meta = self._meta.pop(websocket, None)
        if meta is None:
            return
        project_id, user_id = meta
        sockets = self._rooms[project_id][user_id]
        sockets.discard(websocket)
        if not sockets:
            del self._rooms[project_id][user_id]
        if not self._rooms[project_id]:
            del self._rooms[project_id]

    def has_connections(self, project_id: UUID) -> bool:
        return bool(self._rooms.get(project_id))

    async def broadcast(self, project_id: UUID, message: dict) -> None:
        rooms = self._rooms.get(project_id, {})
        for sockets in list(rooms.values()):
            for websocket in list(sockets):
                try:
                    await websocket.send_json(message)
                except Exception:
                    self.unregister(websocket)

    async def disconnect_user(self, project_id: UUID, user_id: UUID) -> None:
        sockets = list(self._rooms.get(project_id, {}).get(user_id, ()))
        for websocket in sockets:
            try:
                await websocket.close(code=4403)
            except Exception:
                pass
            self.unregister(websocket)
