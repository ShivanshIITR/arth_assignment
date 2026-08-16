from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest

_SESSION_EXPIRED = "Session expired"


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        tokens: RefreshTokenRepository,
        settings: Settings,
    ) -> None:
        self.session = session
        self.users = users
        self.tokens = tokens
        self.settings = settings

    async def register(self, data: RegisterRequest) -> User:
        user = User(
            email=str(data.email).lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
        )
        try:
            async with self.session.begin_nested():
                await self.users.add(user)
        except IntegrityError as exc:
            raise ConflictError("Email already registered") from exc
        return user

    async def login(self, data: LoginRequest) -> tuple[User, str, str]:
        user = await self.users.get_by_email(str(data.email).lower())
        if user is None or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        access_token = create_access_token(user.id, self.settings)
        refresh_token = await self._issue_refresh_token(user, family_id=uuid4())
        return user, access_token, refresh_token

    async def refresh(self, raw_refresh_token: str | None) -> tuple[User, str, str]:
        if not raw_refresh_token:
            raise UnauthorizedError(_SESSION_EXPIRED)

        token_hash = hash_token(raw_refresh_token)
        claimed = await self.tokens.revoke_if_active(token_hash)
        if claimed is not None:
            await self._enforce_absolute_max_age(claimed)
            return await self._rotate(claimed)

        stored = await self.tokens.get_by_hash(token_hash)
        if stored is None:
            raise UnauthorizedError(_SESSION_EXPIRED)

        if self._within_reuse_grace(stored):
            newest = await self.tokens.get_newest_active_in_family(stored.family_id)
            if newest is not None:
                await self._enforce_absolute_max_age(newest)
                return await self._issue_grace_tokens(newest)

        if stored.revoked:
            await self.tokens.revoke_family(stored.family_id)
        raise UnauthorizedError(_SESSION_EXPIRED)

    async def logout(self, raw_refresh_token: str | None) -> None:
        if not raw_refresh_token:
            return
        stored = await self.tokens.get_by_hash(hash_token(raw_refresh_token))
        if stored is not None and not stored.revoked:
            stored.revoked = True
            stored.revoked_at = datetime.now(UTC)

    async def logout_all(self, user: User) -> None:
        await self.tokens.revoke_all_for_user(user.id)

    def _within_reuse_grace(self, stored: RefreshToken) -> bool:
        if not stored.revoked or stored.revoked_at is None:
            return False
        grace = timedelta(seconds=self.settings.refresh_token_reuse_grace_seconds)
        return datetime.now(UTC) - stored.revoked_at <= grace

    async def _enforce_absolute_max_age(self, token: RefreshToken) -> None:
        origin = await self.tokens.get_family_origin_created_at(token.family_id)
        if origin is None:
            origin = token.created_at
        max_age = timedelta(days=self.settings.refresh_token_absolute_max_days)
        if datetime.now(UTC) - origin > max_age:
            await self.tokens.revoke_family(token.family_id)
            raise UnauthorizedError(_SESSION_EXPIRED)

    async def _rotate(self, claimed: RefreshToken) -> tuple[User, str, str]:
        user = await self.users.get_by_id(claimed.user_id)
        if user is None:
            raise UnauthorizedError(_SESSION_EXPIRED)
        access_token = create_access_token(user.id, self.settings)
        refresh_token = await self._issue_refresh_token(
            user, family_id=claimed.family_id
        )
        return user, access_token, refresh_token

    async def _issue_grace_tokens(self, sibling: RefreshToken) -> tuple[User, str, str]:
        """Hashed tokens cannot be returned, so issue a sibling in the same family."""
        return await self._rotate(sibling)

    async def _issue_refresh_token(self, user: User, *, family_id: UUID) -> str:
        raw = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        await self.tokens.add(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=expires_at,
            family_id=family_id,
        )
        return raw
