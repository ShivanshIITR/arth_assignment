from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        family_id: UUID,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            family_id=family_id,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def revoke_if_active(self, token_hash: str) -> RefreshToken | None:
        """Atomically revoke an active, unexpired token and return it."""
        now = datetime.now(UTC)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
            .values(revoked=True, revoked_at=now)
            .returning(RefreshToken)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_family(self, family_id: UUID) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True, revoked_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True, revoked_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def get_newest_active_in_family(self, family_id: UUID) -> RefreshToken | None:
        now = datetime.now(UTC)
        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
            .order_by(RefreshToken.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_family_origin_created_at(self, family_id: UUID) -> datetime | None:
        stmt = select(func.min(RefreshToken.created_at)).where(
            RefreshToken.family_id == family_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
