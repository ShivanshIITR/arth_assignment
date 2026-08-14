from tests.conftest import auth_client_headers, register_user


async def test_create_and_list_projects_scoped_to_membership(client) -> None:
    owner, owner_headers = await auth_client_headers(
        client, "owner@example.com", "Owner"
    )
    _other, other_headers = await auth_client_headers(
        client, "other@example.com", "Other"
    )

    created = await client.post(
        "/api/v1/projects",
        headers=owner_headers,
        json={"name": "Alpha", "description": "First project"},
    )
    assert created.status_code == 201
    project = created.json()
    assert project["name"] == "Alpha"
    assert project["owner"]["email"] == "owner@example.com"
    assert any(m["email"] == "owner@example.com" for m in project["members"])

    owner_list = await client.get("/api/v1/projects", headers=owner_headers)
    assert owner_list.status_code == 200
    assert owner_list.json()["total"] == 1

    other_list = await client.get("/api/v1/projects", headers=other_headers)
    assert other_list.json()["total"] == 0
    assert other_list.json()["items"] == []


async def test_non_member_cannot_view_project(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    _outsider, outsider_headers = await auth_client_headers(client, "out@example.com")
    created = await client.post(
        "/api/v1/projects",
        headers=owner_headers,
        json={"name": "Secret"},
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}", headers=outsider_headers
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_member_can_view_but_not_update_or_delete(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    member, member_headers = await auth_client_headers(
        client, "member@example.com", "Member"
    )
    created = await client.post(
        "/api/v1/projects",
        headers=owner_headers,
        json={"name": "Team"},
    )
    project_id = created.json()["id"]

    added = await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    assert added.status_code == 201

    viewed = await client.get(f"/api/v1/projects/{project_id}", headers=member_headers)
    assert viewed.status_code == 200

    updated = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=member_headers,
        json={"name": "Hijacked"},
    )
    assert updated.status_code == 403

    deleted = await client.delete(
        f"/api/v1/projects/{project_id}", headers=member_headers
    )
    assert deleted.status_code == 403


async def test_owner_can_update_and_delete(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Old"}
    )
    project_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"name": "New", "description": "updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "New"

    deleted = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert missing.status_code == 404


async def test_add_member_conflict_and_unknown_user(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    await register_user(client, email="member@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Team"}
    )
    project_id = created.json()["id"]

    first = await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=headers,
        json={"email": "member@example.com"},
    )
    assert first.status_code == 201

    duplicate = await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=headers,
        json={"email": "member@example.com"},
    )
    assert duplicate.status_code == 409

    unknown = await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=headers,
        json={"email": "ghost@example.com"},
    )
    assert unknown.status_code == 404


async def test_cannot_remove_owner_and_can_remove_member(client) -> None:
    owner, headers = await auth_client_headers(client, "owner@example.com")
    member, _member_headers = await auth_client_headers(client, "member@example.com")
    created = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Team"}
    )
    project_id = created.json()["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=headers,
        json={"email": "member@example.com"},
    )

    remove_owner = await client.delete(
        f"/api/v1/projects/{project_id}/members/{owner['id']}",
        headers=headers,
    )
    assert remove_owner.status_code == 409

    remove_member = await client.delete(
        f"/api/v1/projects/{project_id}/members/{member['id']}",
        headers=headers,
    )
    assert remove_member.status_code == 204

    detail = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    emails = [m["email"] for m in detail.json()["members"]]
    assert "member@example.com" not in emails


async def test_unauthenticated_project_access_is_rejected(client) -> None:
    response = await client.get("/api/v1/projects")
    assert response.status_code == 401
