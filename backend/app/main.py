from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.activity import router as activity_router
from app.api.v1.attachments import nested_router as task_attachments_router
from app.api.v1.attachments import router as attachments_router
from app.api.v1.audit import me_router as my_audit_router
from app.api.v1.audit import project_router as project_audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import nested_router as project_tasks_router
from app.api.v1.tasks import router as tasks_router
from app.core.config import get_settings
from app.core.exception_handlers import (
    register_exception_handlers,
    register_request_context_middleware,
)
from app.core.logging import configure_logging
from app.core.redis import close_redis_client, create_redis_client
from app.core.storage.local_storage import LocalFilesystemStorage
from app.db.session import dispose_engine
from app.events.dispatcher import EventDispatcher
from app.events.registry import (
    register_all_handlers,
    register_cache_handlers,
    register_notification_handlers,
    register_websocket_handlers,
)
from app.jobs.enqueue import close_arq_pool, create_arq_pool
from app.policies.engine import load_policy_engine
from app.websocket.connection_manager import ConnectionManager
from app.websocket.router import router as ws_router


def _build_dispatcher() -> EventDispatcher:
    dispatcher = EventDispatcher()
    register_all_handlers(dispatcher)
    return dispatcher


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.policy_engine = load_policy_engine()
    if not getattr(app.state, "event_dispatcher", None):
        app.state.event_dispatcher = _build_dispatcher()
    if not hasattr(app.state, "redis"):
        app.state.redis = create_redis_client(settings)
    if not hasattr(app.state, "arq_pool"):
        app.state.arq_pool = await create_arq_pool(settings.redis_url)
    if not getattr(app.state, "ws_manager", None):
        app.state.ws_manager = ConnectionManager()
    yield
    await close_arq_pool(getattr(app.state, "arq_pool", None))
    await close_redis_client(getattr(app.state, "redis", None))
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.state.policy_engine = load_policy_engine()
    application.state.event_dispatcher = _build_dispatcher()
    register_cache_handlers(
        application.state.event_dispatcher,
        lambda: getattr(application.state, "redis", None),
    )
    register_notification_handlers(
        application.state.event_dispatcher,
        lambda: getattr(application.state, "arq_pool", None),
    )
    application.state.ws_manager = ConnectionManager()
    register_websocket_handlers(
        application.state.event_dispatcher,
        lambda: application.state.ws_manager,
    )
    application.state.storage = LocalFilesystemStorage(settings.upload_dir)
    register_request_context_middleware(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(auth_router, prefix=settings.api_v1_prefix)
    application.include_router(projects_router, prefix=settings.api_v1_prefix)
    application.include_router(project_tasks_router, prefix=settings.api_v1_prefix)
    application.include_router(activity_router, prefix=settings.api_v1_prefix)
    application.include_router(project_audit_router, prefix=settings.api_v1_prefix)
    application.include_router(my_audit_router, prefix=settings.api_v1_prefix)
    application.include_router(tasks_router, prefix=settings.api_v1_prefix)
    application.include_router(task_attachments_router, prefix=settings.api_v1_prefix)
    application.include_router(attachments_router, prefix=settings.api_v1_prefix)
    application.include_router(dashboard_router, prefix=settings.api_v1_prefix)
    application.include_router(ws_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
