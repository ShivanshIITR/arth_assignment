from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped session.

    The request is the unit of work: repositories never commit, and a
    service that performs multiple writes shares this session so they
    commit together or roll back together. After-commit event handlers
    run only once that commit succeeds.
    """
    factory = get_session_factory()
    dispatcher = getattr(request.app.state, "event_dispatcher", None)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            if dispatcher is not None:
                dispatcher.clear_queued(session)
            await session.rollback()
            raise
        else:
            if dispatcher is not None:
                await dispatcher.drain_after_commit(session)


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
