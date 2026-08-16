from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.events.dispatcher import EventDispatcher
from app.models.user import User
from app.policies.engine import PolicyEngine
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: DbSession,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated")

    user_id = decode_access_token(credentials.credentials)
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_auth_service(session: DbSession, settings: SettingsDep) -> AuthService:
    return AuthService(
        session=session,
        users=UserRepository(session),
        tokens=RefreshTokenRepository(session),
        settings=settings,
    )


def get_refresh_cookie(request: Request, settings: SettingsDep) -> str | None:
    return request.cookies.get(settings.cookie_name)


def get_policy_engine(request: Request) -> PolicyEngine:
    return request.app.state.policy_engine


def get_event_dispatcher(request: Request) -> EventDispatcher:
    return request.app.state.event_dispatcher


def get_redis(request: Request) -> Redis | None:
    return getattr(request.app.state, "redis", None)


PolicyEngineDep = Annotated[PolicyEngine, Depends(get_policy_engine)]
EventDispatcherDep = Annotated[EventDispatcher, Depends(get_event_dispatcher)]
RedisDep = Annotated[Redis | None, Depends(get_redis)]
