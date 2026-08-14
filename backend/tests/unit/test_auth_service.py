from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, hash_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


def _settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


def _user(**overrides) -> User:
    now = datetime.now(UTC)
    data = {
        "id": uuid4(),
        "email": "ada@example.com",
        "hashed_password": hash_password("password123"),
        "full_name": "Ada Lovelace",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return User(**data)


@pytest.fixture
def service() -> AuthService:
    session = MagicMock()
    session.flush = AsyncMock()
    users = AsyncMock()
    tokens = AsyncMock()
    return AuthService(session=session, users=users, tokens=tokens, settings=_settings())


@pytest.mark.asyncio
async def test_register_creates_user(service: AuthService) -> None:
    created = _user()

    async def add(user: User) -> User:
        user.id = created.id
        user.created_at = created.created_at
        user.updated_at = created.updated_at
        return user

    service.users.add.side_effect = add
    result = await service.register(
        RegisterRequest(email="Ada@example.com", password="password123", full_name="Ada Lovelace")
    )
    assert result.email == "ada@example.com"
    assert verify_password("password123", result.hashed_password)
    service.users.add.assert_awaited()


@pytest.mark.asyncio
async def test_register_conflict_on_duplicate_email(service: AuthService) -> None:
    service.users.add.side_effect = IntegrityError("stmt", {}, Exception("dup"))
    with pytest.raises(ConflictError):
        await service.register(
            RegisterRequest(email="ada@example.com", password="password123", full_name="Ada")
        )


@pytest.mark.asyncio
async def test_login_rejects_bad_password(service: AuthService) -> None:
    service.users.get_by_email.return_value = _user()
    with pytest.raises(UnauthorizedError):
        await service.login(LoginRequest(email="ada@example.com", password="wrong-pass"))


@pytest.mark.asyncio
async def test_login_issues_tokens(service: AuthService) -> None:
    user = _user()
    service.users.get_by_email.return_value = user
    service.tokens.add.return_value = MagicMock()
    returned_user, access, refresh = await service.login(
        LoginRequest(email="ada@example.com", password="password123")
    )
    assert returned_user.id == user.id
    assert access
    assert refresh
    service.tokens.add.assert_awaited()


@pytest.mark.asyncio
async def test_refresh_rotates_and_revokes_old_token(service: AuthService) -> None:
    user = _user()
    stored = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("old-token"),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked=False,
    )
    service.tokens.get_by_hash.return_value = stored
    service.users.get_by_id.return_value = user
    service.tokens.add.return_value = MagicMock()

    _user_out, access, new_refresh = await service.refresh("old-token")
    assert stored.revoked is True
    assert access
    assert new_refresh != "old-token"


@pytest.mark.asyncio
async def test_refresh_rejects_revoked_token(service: AuthService) -> None:
    stored = RefreshToken(
        user_id=uuid4(),
        token_hash=hash_token("old-token"),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked=True,
    )
    service.tokens.get_by_hash.return_value = stored
    with pytest.raises(UnauthorizedError):
        await service.refresh("old-token")
