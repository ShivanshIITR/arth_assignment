from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.core.security import generate_refresh_token, hash_token
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import RefreshTokenRepository
from tests.conftest import register_user
from tests.test_factories import make_user


async def _login(client, email: str = "ada@example.com"):
    await register_user(client, email=email, full_name="Ada Lovelace")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response


async def test_refresh_rotates_and_immediate_reuse_is_grace(client) -> None:
    login_response = await _login(client)
    original = login_response.cookies.get("refresh_token")
    assert original

    rotated = await client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200
    newest = rotated.cookies.get("refresh_token")
    assert newest != original

    client.cookies.clear()
    replay = await client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": original}
    )
    assert replay.status_code == 200
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {replay.json()['access_token']}"},
    )
    assert me.status_code == 200


async def test_reuse_outside_grace_revokes_family(client, db_session) -> None:
    login_response = await _login(client)
    original = login_response.cookies.get("refresh_token")
    rotated = await client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200
    newest = rotated.cookies.get("refresh_token")

    await db_session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(original))
        .values(revoked_at=datetime.now(UTC) - timedelta(seconds=30))
    )
    await db_session.flush()

    client.cookies.clear()
    replay = await client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": original}
    )
    assert replay.status_code == 401

    client.cookies.clear()
    with_newest = await client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": newest}
    )
    assert with_newest.status_code == 401


async def test_revoke_if_active_second_caller_loses(db_session) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.flush()
    repo = RefreshTokenRepository(db_session)
    raw = generate_refresh_token()
    await repo.add(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        family_id=user.id,
    )
    first = await repo.revoke_if_active(hash_token(raw))
    second = await repo.revoke_if_active(hash_token(raw))
    assert first is not None
    assert first.revoked is True
    assert second is None


async def test_two_refreshes_of_the_same_token_both_succeed(client) -> None:
    """Loser of the atomic revoke is served through the reuse-detection grace window."""
    login_response = await _login(client)
    original = login_response.cookies.get("refresh_token")

    first = await client.post("/api/v1/auth/refresh")
    assert first.status_code == 200
    client.cookies.clear()
    second = await client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": original}
    )
    assert second.status_code == 200
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {second.json()['access_token']}"},
    )
    assert me.status_code == 200


async def test_logout_all_revokes_refresh_family(client) -> None:
    login_response = await _login(client)
    access = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    logout = await client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout.status_code == 204

    refresh = await client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401
