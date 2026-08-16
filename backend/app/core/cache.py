from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger("app.cache")

DASHBOARD_TTL_SECONDS = 60
PROJECT_DETAIL_TTL_SECONDS = 300


def dashboard_key(user_id: UUID) -> str:
    return f"dashboard:{user_id}"


def project_detail_key(project_id: UUID) -> str:
    return f"project:{project_id}:detail"


T = TypeVar("T")

Loader = Callable[[], Awaitable[T]]
Dumper = Callable[[T], str]
LoaderFromCache = Callable[[str], T]


async def get_or_set(
    key: str,
    ttl: int,
    loader: Loader[T],
    redis: Redis | None,
    *,
    dumps: Dumper[T],
    loads: LoaderFromCache[T],
) -> T:
    """Cache-aside helper. Redis failures fall through to the loader."""
    if redis is None:
        return await loader()

    try:
        cached = await redis.get(key)
    except Exception:
        logger.warning("cache_read_failed", key=key, exc_info=True)
        return await loader()

    if cached is not None:
        try:
            return loads(cached)
        except Exception:
            logger.warning("cache_deserialize_failed", key=key, exc_info=True)

    value = await loader()
    try:
        await redis.setex(key, ttl, dumps(value))
    except Exception:
        logger.warning("cache_write_failed", key=key, exc_info=True)
    return value


async def delete_key(key: str, redis: Redis | None) -> None:
    if redis is None:
        return
    try:
        await redis.delete(key)
    except Exception:
        logger.warning("cache_delete_failed", key=key, exc_info=True)
