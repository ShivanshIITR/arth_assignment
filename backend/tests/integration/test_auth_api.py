from tests.conftest import register_user


async def test_register_login_me_and_logout(client) -> None:
    created = await register_user(
        client, email="ada@example.com", full_name="Ada Lovelace"
    )
    assert created["email"] == "ada@example.com"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert "refresh_token" in login_response.cookies

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204

    refresh = await client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401


async def test_register_duplicate_email_conflict(client) -> None:
    await register_user(client, email="dup@example.com")
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "password123",
            "full_name": "Dup",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_login_rejects_bad_credentials(client) -> None:
    await register_user(client, email="ada@example.com")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_refresh_rotates_token(client) -> None:
    await register_user(client, email="ada@example.com")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "password123"},
    )
    first_refresh = login_response.cookies.get("refresh_token")
    first_access = login_response.json()["access_token"]

    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"] != first_access
    assert refresh_response.cookies.get("refresh_token") != first_refresh

    # Old cookie was replaced on the client; replaying the old raw token is
    # not exposed here, but a second refresh with the new cookie succeeds.
    second = await client.post("/api/v1/auth/refresh")
    assert second.status_code == 200


async def test_me_requires_auth(client) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
