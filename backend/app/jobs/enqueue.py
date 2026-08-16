import structlog
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

logger = structlog.get_logger("app.jobs")


async def create_arq_pool(redis_url: str) -> ArqRedis | None:
    try:
        return await create_pool(RedisSettings.from_dsn(redis_url))
    except Exception:
        logger.warning("arq_pool_create_failed", exc_info=True)
        return None


async def close_arq_pool(pool: ArqRedis | None) -> None:
    if pool is None:
        return
    await pool.aclose(close_connection_pool=True)


async def enqueue(pool: ArqRedis | None, job_name: str, *args: object) -> None:
    """Enqueue a job. Failures are logged and never raised to the caller."""
    if pool is None:
        logger.warning("arq_enqueue_skipped", job_name=job_name)
        return
    try:
        await pool.enqueue_job(job_name, *args)
    except Exception:
        logger.warning("arq_enqueue_failed", job_name=job_name, exc_info=True)
