from tests.conftest import auth_client_headers


async def test_dashboard_stats_aggregate_across_member_projects(client) -> None:
    owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    _other, other_headers = await auth_client_headers(client, "other@example.com")

    empty = await client.get("/api/v1/dashboard/stats", headers=owner_headers)
    assert empty.status_code == 200
    assert empty.json() == {
        "total_projects": 0,
        "active_projects": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "pending_tasks": 0,
        "tasks_by_status": {"todo": 0, "in_progress": 0, "completed": 0},
    }

    first = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Active"}
    )
    second = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Idle"}
    )
    other_project = await client.post(
        "/api/v1/projects", headers=other_headers, json={"name": "Not mine"}
    )
    first_id = first.json()["id"]
    second_id = second.json()["id"]
    other_id = other_project.json()["id"]

    await client.post(
        f"/api/v1/projects/{first_id}/tasks",
        headers=owner_headers,
        json={"title": "Todo"},
    )
    await client.post(
        f"/api/v1/projects/{first_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Done",
            "assignee_id": owner["id"],
            "priority": "high",
            "due_date": "2026-09-01",
            "status": "in_progress",
        },
    )
    done = await client.post(
        f"/api/v1/projects/{first_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Done now",
            "assignee_id": owner["id"],
            "priority": "medium",
            "due_date": "2026-09-01",
        },
    )
    complete = await client.patch(
        f"/api/v1/tasks/{done.json()['id']}",
        headers=owner_headers,
        json={"status": "completed"},
    )
    assert complete.status_code == 200
    await client.post(
        f"/api/v1/projects/{other_id}/tasks",
        headers=other_headers,
        json={"title": "Should not count"},
    )

    stats = await client.get("/api/v1/dashboard/stats", headers=owner_headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_projects"] == 2
    assert body["active_projects"] == 1
    assert body["total_tasks"] == 3
    assert body["completed_tasks"] == 1
    assert body["pending_tasks"] == 2
    assert body["tasks_by_status"] == {"todo": 1, "in_progress": 1, "completed": 1}

    # second project exists but has no incomplete tasks, so it is not active
    assert second_id
