from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import nested_router as project_tasks_router
from app.api.v1.tasks import router as tasks_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.session import dispose_engine
from app.policies.engine import load_policy_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.policy_engine = load_policy_engine()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.state.policy_engine = load_policy_engine()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(AppException)
    async def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(auth_router, prefix=settings.api_v1_prefix)
    application.include_router(projects_router, prefix=settings.api_v1_prefix)
    application.include_router(project_tasks_router, prefix=settings.api_v1_prefix)
    application.include_router(tasks_router, prefix=settings.api_v1_prefix)
    application.include_router(dashboard_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
