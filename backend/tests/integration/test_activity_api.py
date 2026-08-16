from tests.conftest import auth_client_headers


async def test_member_can_list_project_activity(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Alpha"}
    )
    project_id = created.json()["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "First task"},
    )

    response = await client.get(
        f"/api/v1/projects/{project_id}/activity", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    types = [item["event_type"] for item in body["items"]]
    assert "TASK_CREATED" in types
    assert "PROJECT_CREATED" in types
    assert body["items"][0]["actor"]["email"] == "owner@example.com"


async def test_non_member_cannot_view_activity(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    _outsider, outsider_headers = await auth_client_headers(client, "out@example.com")
    created = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Secret"}
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}/activity", headers=outsider_headers
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
