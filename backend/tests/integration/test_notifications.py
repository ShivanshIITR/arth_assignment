import pytest

from app.main import create_app
from tests.conftest import auth_client_headers
from tests.unit.test_notification_handler import FakeArqPool


@pytest.fixture
def fake_pool() -> FakeArqPool:
    return FakeArqPool()


@pytest.fixture
def app(fake_pool: FakeArqPool):
    application = create_app()
    application.state.redis = None
    application.state.arq_pool = fake_pool
    return application


async def test_member_added_enqueues_one_email(client, fake_pool: FakeArqPool) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, _member_headers = await auth_client_headers(client, "member@example.com")
    created = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Notify"}
    )
    project_id = created.json()["id"]

    added = await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    assert added.status_code == 201
    assert fake_pool.jobs == [
        ("send_email", ("member_added", member["id"], project_id))
    ]


async def test_task_assigned_and_completed_enqueue_correct_recipients(
    client, fake_pool: FakeArqPool
) -> None:
    owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, member_headers = await auth_client_headers(client, "member@example.com")
    created = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Notify"}
    )
    project_id = created.json()["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    fake_pool.jobs.clear()

    assigned = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Do the work",
            "assignee_id": member["id"],
            "priority": "high",
            "due_date": "2026-09-01",
        },
    )
    assert assigned.status_code == 201
    task_id = assigned.json()["id"]
    assert fake_pool.jobs == [
        ("send_email", ("task_assigned", member["id"], task_id))
    ]
    fake_pool.jobs.clear()

    completed = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=member_headers,
        json={"status": "completed"},
    )
    assert completed.status_code == 200
    assert fake_pool.jobs == [
        ("send_email", ("task_completed", owner["id"], task_id))
    ]
    fake_pool.jobs.clear()

    self_assigned = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Own work", "assignee_id": owner["id"]},
    )
    assert self_assigned.status_code == 201
    assert fake_pool.jobs == []
