from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import (  # noqa: F401
    ActivityLog,
    AuditLog,
    Project,
    ProjectMember,
    RefreshToken,
    Task,
    User,
)

settings = get_settings()
TEST_DATABASE_URL = settings.test_database_url
TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace("+asyncpg", "+psycopg")


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    engine = create_engine(TEST_DATABASE_URL_SYNC)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        Base.metadata.drop_all(conn)
        Base.metadata.create_all(conn)
    yield
    with engine.begin() as conn:
        Base.metadata.drop_all(conn)
    engine.dispose()


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with db_engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
            join_transaction_mode="create_savepoint",
        )
        async with session_factory() as session:
            yield session
        await transaction.rollback()


@pytest.fixture
def app():
    application = create_app()
    # Tests skip the real Redis client unless a case injects a fake or live one.
    application.state.redis = None
    return application


@pytest.fixture
async def client(app, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        dispatcher = getattr(app.state, "event_dispatcher", None)
        try:
            yield db_session
        except Exception:
            if dispatcher is not None:
                dispatcher.clear_queued(db_session)
            raise
        else:
            if dispatcher is not None:
                await dispatcher.drain_after_commit(db_session)

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def query_counter(db_engine) -> Callable[[], int]:
    count = {"n": 0}

    def before_cursor_execute(*_args: Any, **_kwargs: Any) -> None:
        count["n"] += 1

    sync_engine = db_engine.sync_engine
    event.listen(sync_engine, "before_cursor_execute", before_cursor_execute)

    def current() -> int:
        return count["n"]

    yield current
    event.remove(sync_engine, "before_cursor_execute", before_cursor_execute)


async def register_user(
    client: AsyncClient,
    *,
    email: str,
    password: str = "password123",
    full_name: str = "Test User",
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login(
    client: AsyncClient, email: str, password: str = "password123"
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def auth_client_headers(
    client: AsyncClient,
    email: str,
    full_name: str = "Test User",
) -> tuple[dict, dict[str, str]]:
    user = await register_user(client, email=email, full_name=full_name)
    headers = await login(client, email)
    return user, headers
