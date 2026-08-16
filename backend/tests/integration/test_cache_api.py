import pytest
from redis.asyncio import Redis

from app.core.cache import dashboard_key, project_detail_key
from app.main import create_app
from tests.conftest import auth_client_headers
from tests.unit.test_cache import FakeRedis


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def app(fake_redis: FakeRedis):
    application = create_app()
    application.state.redis = fake_redis
    return application


async def test_dashboard_stats_reflect_task_create_immediately(
    client, fake_redis: FakeRedis
) -> None:
    owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Cached"}
    )
    project_id = created.json()["id"]

    before = await client.get("/api/v1/dashboard/stats", headers=headers)
    assert before.status_code == 200
    assert before.json()["total_tasks"] == 0
    assert dashboard_key(owner["id"]) in fake_redis.store

    added = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "New work"},
    )
    assert added.status_code == 201
    assert dashboard_key(owner["id"]) not in fake_redis.store

    after = await client.get("/api/v1/dashboard/stats", headers=headers)
    assert after.status_code == 200
    assert after.json()["total_tasks"] == 1
    assert after.json()["total_projects"] == 1


async def test_project_detail_cache_invalidates_on_update(
    client, fake_redis: FakeRedis
) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Original"}
    )
    project_id = created.json()["id"]

    first = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert first.status_code == 200
    assert first.json()["name"] == "Original"
    assert project_detail_key(project_id) in fake_redis.store

    updated = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"name": "Renamed"},
    )
    assert updated.status_code == 200
    assert project_detail_key(project_id) not in fake_redis.store

    second = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert second.status_code == 200
    assert second.json()["name"] == "Renamed"


async def test_redis_down_still_returns_correct_data(client, app) -> None:
    app.state.redis = Redis.from_url(
        "redis://127.0.0.1:1/0",
        decode_responses=True,
        socket_connect_timeout=0.05,
    )
    owner, headers = await auth_client_headers(client, "down@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Still works"}
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    detail = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Still works"

    await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task"},
    )
    stats = await client.get("/api/v1/dashboard/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["total_projects"] == 1
    assert stats.json()["total_tasks"] == 1
    assert owner["id"]
