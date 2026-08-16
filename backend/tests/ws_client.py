import asyncio
import json
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI


class AsyncWSClient:
    """Drive a WebSocket ASGI endpoint on the current event loop."""

    def __init__(self, app: FastAPI, path: str) -> None:
        self.app = app
        self.path = path
        self.close_code: int | None = None
        self._outgoing: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._incoming: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> "AsyncWSClient":
        scope: dict[str, Any] = {
            "type": "websocket",
            "asgi": {"spec_version": "2.3", "version": "3.0"},
            "scheme": "ws",
            "http_version": "1.1",
            "path": self.path,
            "raw_path": self.path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"host", b"test")],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "subprotocols": [],
            "state": {},
            "extensions": {},
            "app": self.app,
        }

        async def receive() -> Mapping[str, Any]:
            return await self._outgoing.get()

        async def send(message: Mapping[str, Any]) -> None:
            payload = dict(message)
            if payload["type"] == "websocket.close":
                self.close_code = int(payload.get("code") or 1000)
            await self._incoming.put(payload)

        self._task = asyncio.create_task(self.app(scope, receive, send))
        await self._outgoing.put({"type": "websocket.connect"})
        first = await asyncio.wait_for(self._incoming.get(), timeout=2)
        assert first["type"] == "websocket.accept", first
        return self

    async def send_json(self, data: dict[str, Any]) -> None:
        await self._outgoing.put(
            {"type": "websocket.receive", "text": json.dumps(data)}
        )

    async def receive(self, timeout: float = 2.0) -> dict[str, Any]:
        return await asyncio.wait_for(self._incoming.get(), timeout=timeout)

    async def receive_json(self, timeout: float = 2.0) -> dict[str, Any]:
        message = await self.receive(timeout=timeout)
        assert message["type"] == "websocket.send", message
        if "text" in message:
            return json.loads(message["text"])
        return json.loads(message["bytes"])

    async def __aexit__(self, *_exc: object) -> None:
        await self._outgoing.put({"type": "websocket.disconnect", "code": 1000})
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=2)
            except (TimeoutError, asyncio.CancelledError):
                self._task.cancel()
