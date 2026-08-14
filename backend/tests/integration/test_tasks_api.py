from tests.conftest import auth_client_headers


async def _create_project(client, headers, name: str = "Board") -> str:
    response = await client.post(
        "/api/v1/projects", headers=headers, json={"name": name}
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_member_can_create_and_list_tasks(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    project_id = await _create_project(client, owner_headers)

    created = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Write tests", "priority": "high"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Write tests"
    assert body["status"] == "todo"
    assert body["priority"] == "high"
    assert body["creator"]["email"] == "owner@example.com"

    listed = await client.get(
        f"/api/v1/projects/{project_id}/tasks", headers=owner_headers
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == body["id"]


async def test_non_member_cannot_create_or_view_tasks(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    _outsider, outsider_headers = await auth_client_headers(client, "out@example.com")
    project_id = await _create_project(client, owner_headers)

    created = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=outsider_headers,
        json={"title": "Nope"},
    )
    assert created.status_code == 403

    listed = await client.get(
        f"/api/v1/projects/{project_id}/tasks", headers=outsider_headers
    )
    assert listed.status_code == 403


async def test_filter_search_and_pagination(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    project_id = await _create_project(client, headers)

    titles = ["Alpha login", "Beta dashboard", "Alpha search"]
    for title in titles:
        response = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=headers,
            json={"title": title, "priority": "medium"},
        )
        assert response.status_code == 201

    in_progress = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Gamma", "status": "in_progress", "priority": "high"},
    )
    assert in_progress.status_code == 201

    filtered = await client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        params={"status": "todo", "priority": "medium", "search": "Alpha"},
    )
    assert filtered.status_code == 200
    data = filtered.json()
    assert data["total"] == 2
    assert {item["title"] for item in data["items"]} == {"Alpha login", "Alpha search"}

    page = await client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        params={"page": 1, "page_size": 2},
    )
    assert page.json()["page"] == 1
    assert page.json()["page_size"] == 2
    assert len(page.json()["items"]) == 2
    assert page.json()["total"] == 4


async def test_creator_and_assignee_can_update_others_cannot(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, member_headers = await auth_client_headers(
        client, "member@example.com", "Member"
    )
    _other, other_headers = await auth_client_headers(
        client, "other@example.com", "Other"
    )
    project_id = await _create_project(client, owner_headers)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "other@example.com"},
    )

    created = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=member_headers,
        json={"title": "Owned by member", "assignee_id": member["id"]},
    )
    task_id = created.json()["id"]

    by_creator = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=member_headers,
        json={"title": "Updated"},
    )
    assert by_creator.status_code == 200
    assert by_creator.json()["title"] == "Updated"

    by_other = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=other_headers,
        json={"title": "Hijack"},
    )
    assert by_other.status_code == 403

    by_owner = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"title": "Owner edited"},
    )
    assert by_owner.status_code == 200
    assert by_owner.json()["title"] == "Owner edited"


async def test_complete_denied_without_required_fields(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    project_id = await _create_project(client, headers)
    created = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Incomplete"},
    )
    task_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert response.status_code == 403


async def test_complete_allowed_with_required_fields(client) -> None:
    owner, headers = await auth_client_headers(client, "owner@example.com")
    project_id = await _create_project(client, headers)
    created = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={
            "title": "Ready",
            "assignee_id": owner["id"],
            "priority": "high",
            "due_date": "2026-09-01",
        },
    )
    task_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_only_owner_can_delete_todo_tasks(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, member_headers = await auth_client_headers(client, "member@example.com")
    project_id = await _create_project(client, owner_headers)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    todo = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=member_headers,
        json={"title": "Todo task"},
    )
    todo_id = todo.json()["id"]
    started = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=member_headers,
        json={"title": "Started", "status": "in_progress"},
    )
    started_id = started.json()["id"]

    member_delete = await client.delete(
        f"/api/v1/tasks/{todo_id}", headers=member_headers
    )
    assert member_delete.status_code == 403

    in_progress_delete = await client.delete(
        f"/api/v1/tasks/{started_id}", headers=owner_headers
    )
    assert in_progress_delete.status_code == 403

    owner_delete = await client.delete(
        f"/api/v1/tasks/{todo_id}", headers=owner_headers
    )
    assert owner_delete.status_code == 204

    missing = await client.get(f"/api/v1/tasks/{todo_id}", headers=owner_headers)
    assert missing.status_code == 404


async def test_task_list_query_count_does_not_grow_with_page_size(
    client, query_counter
) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    project_id = await _create_project(client, headers)
    for index in range(8):
        response = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=headers,
            json={"title": f"Task {index}"},
        )
        assert response.status_code == 201

    before = query_counter()
    listed = await client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        params={"page_size": 8},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 8
    queries = query_counter() - before
    assert queries <= 10


async def test_removing_member_transfers_task_ownership_to_project_owner(
    client,
) -> None:
    owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, member_headers = await auth_client_headers(client, "member@example.com")
    project_id = await _create_project(client, owner_headers)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    created = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=member_headers,
        json={"title": "Member's task"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["creator_id"] == member["id"]

    removed = await client.delete(
        f"/api/v1/projects/{project_id}/members/{member['id']}",
        headers=owner_headers,
    )
    assert removed.status_code == 204

    task = await client.get(f"/api/v1/tasks/{task_id}", headers=owner_headers)
    assert task.status_code == 200
    assert task.json()["creator_id"] == owner["id"]
    assert task.json()["creator"]["email"] == "owner@example.com"

    still_editable = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"title": "Now owned by owner"},
    )
    assert still_editable.status_code == 200

    member_blocked = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=member_headers,
        json={"title": "Former member edit"},
    )
    assert member_blocked.status_code == 403
