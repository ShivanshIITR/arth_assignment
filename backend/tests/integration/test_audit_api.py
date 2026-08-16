from tests.conftest import auth_client_headers, register_user


async def test_owner_can_view_project_audit_logs(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Alpha"}
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}/audit-logs", headers=headers
    )
    assert response.status_code == 200
    types = [item["event_type"] for item in response.json()["items"]]
    assert "PROJECT_CREATED" in types
    assert "LOGIN" not in types


async def test_non_owner_cannot_view_project_audit_logs(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, member_headers = await auth_client_headers(client, "member@example.com")
    created = await client.post(
        "/api/v1/projects", headers=owner_headers, json={"name": "Team"}
    )
    project_id = created.json()["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )

    response = await client.get(
        f"/api/v1/projects/{project_id}/audit-logs", headers=member_headers
    )
    assert response.status_code == 403


async def test_self_audit_logs_do_not_leak_other_users(client) -> None:
    await register_user(client, email="ada@example.com")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "password123"},
    )
    _other, other_headers = await auth_client_headers(client, "other@example.com")

    mine = await client.get("/api/v1/users/me/audit-logs", headers=other_headers)
    assert mine.status_code == 200
    emails = {
        item["actor"]["email"]
        for item in mine.json()["items"]
        if item.get("actor")
    }
    assert emails <= {"other@example.com"}
    assert "ada@example.com" not in emails
