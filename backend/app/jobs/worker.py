from arq.connections import RedisSettings
from arq.worker import func

from app.core.config import get_settings
from app.core.email.factory import get_email_provider
from app.jobs.tasks import health_job, send_email_job


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


async def startup(ctx: dict) -> None:
    ctx["email_provider"] = get_email_provider(get_settings())


class WorkerSettings:
    functions = [
        func(health_job, name="health", max_tries=get_settings().arq_max_tries),
        func(send_email_job, name="send_email", max_tries=get_settings().arq_max_tries),
    ]
    redis_settings = _redis_settings()
    on_startup = startup
    max_jobs = 10
    job_timeout = 60
    keep_result = 60
