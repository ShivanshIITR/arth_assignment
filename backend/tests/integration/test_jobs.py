from unittest.mock import AsyncMock

import pytest
from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker, func
from redis.asyncio import Redis

from app.core.config import get_settings
from app.jobs.enqueue import enqueue
from app.jobs.tasks import health_job


@pytest.mark.asyncio
async def test_enqueue_skips_when_pool_is_missing() -> None:
    await enqueue(None, "health")


@pytest.mark.asyncio
async def test_enqueue_swallows_pool_errors() -> None:
    pool = AsyncMock()
    pool.enqueue_job.side_effect = ConnectionError("redis down")
    await enqueue(pool, "health")
    pool.enqueue_job.assert_awaited_once()


async def _redis_available(url: str) -> bool:
    client = Redis.from_url(url)
    try:
        await client.ping()
        return True
    except Exception:
        return False
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_enqueue_runs_health_job_against_redis() -> None:
    url = get_settings().redis_url
    if not await _redis_available(url):
        pytest.skip("Redis is not available for job integration tests")

    pool = await create_pool(RedisSettings.from_dsn(url))
    try:
        job = await pool.enqueue_job("health")
        assert job is not None
        worker = Worker(
            functions=[func(health_job, name="health")],
            redis_pool=pool,
            burst=True,
            keep_result=60,
        )
        await worker.async_run()
        result = await job.result(timeout=5)
        assert result == "ok"
    finally:
        await pool.aclose(close_connection_pool=True)
