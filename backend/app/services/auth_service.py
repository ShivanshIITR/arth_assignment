from datetime import UTC, datetime, timedelta

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
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


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
        refresh_token = await self._issue_refresh_token(user)
        return user, access_token, refresh_token

    async def refresh(self, raw_refresh_token: str | None) -> tuple[User, str, str]:
        if not raw_refresh_token:
            raise UnauthorizedError("Missing refresh token")

        stored = await self.tokens.get_by_hash(hash_token(raw_refresh_token))
        now = datetime.now(UTC)
        if stored is None or stored.revoked or stored.expires_at <= now:
            raise UnauthorizedError("Invalid refresh token")

        stored.revoked = True
        user = await self.users.get_by_id(stored.user_id)
        if user is None:
            raise UnauthorizedError("Invalid refresh token")

        access_token = create_access_token(user.id, self.settings)
        new_refresh_token = await self._issue_refresh_token(user)
        return user, access_token, new_refresh_token

    async def logout(self, raw_refresh_token: str | None) -> None:
        if not raw_refresh_token:
            return
        stored = await self.tokens.get_by_hash(hash_token(raw_refresh_token))
        if stored is not None and not stored.revoked:
            stored.revoked = True

    async def _issue_refresh_token(self, user: User) -> str:
        raw = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days)
        await self.tokens.add(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=expires_at,
        )
        return raw
