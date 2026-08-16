from arq.connections import RedisSettings
from arq.worker import func

from app.core.config import get_settings
from app.jobs.tasks import health_job


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    functions = [
        func(health_job, name="health", max_tries=get_settings().arq_max_tries),
    ]
    redis_settings = _redis_settings()
    max_jobs = 10
    job_timeout = 60
    keep_result = 60
