from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger("app.events")

SyncHandler = Callable[[Any, AsyncSession], Awaitable[None]]
PostCommitHandler = Callable[[Any], Awaitable[None]]

_AFTER_COMMIT_KEY = "after_commit_events"


class EventDispatcher:
    """In-process pub/sub with two dispatch points.

    `publish` runs same-transaction handlers and lets exceptions propagate so
    the triggering write rolls back with them. `publish_after_commit` queues
    events on the session and runs them only after a successful commit;
    handler failures are logged and never fail the already-committed request.
    """

    def __init__(self) -> None:
        self._sync: dict[type, list[SyncHandler]] = defaultdict(list)
        self._post_commit: dict[type, list[PostCommitHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: SyncHandler) -> None:
        self._sync[event_type].append(handler)

    def subscribe_after_commit(
        self, event_type: type, handler: PostCommitHandler
    ) -> None:
        self._post_commit[event_type].append(handler)

    async def publish(self, event: object, session: AsyncSession) -> None:
        for handler in self._sync[type(event)]:
            await handler(event, session)

    async def publish_after_commit(
        self,
        event: object,
        session: AsyncSession | None = None,
    ) -> None:
        if session is not None:
            pending = session.info.setdefault(_AFTER_COMMIT_KEY, [])
            pending.append(event)
            return
        await self._dispatch_after_commit(event)

    async def drain_after_commit(self, session: AsyncSession) -> None:
        events = list(session.info.pop(_AFTER_COMMIT_KEY, []))
        for event in events:
            await self._dispatch_after_commit(event)

    def clear_queued(self, session: AsyncSession) -> None:
        session.info.pop(_AFTER_COMMIT_KEY, None)

    async def _dispatch_after_commit(self, event: object) -> None:
        for handler in self._post_commit[type(event)]:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "after_commit_handler_failed",
                    event_type=type(event).__name__,
                    handler=getattr(handler, "__qualname__", repr(handler)),
                )
