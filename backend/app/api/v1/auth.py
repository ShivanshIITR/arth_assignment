from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import (
    CurrentUser,
    SettingsDep,
    get_auth_service,
    get_refresh_cookie,
)
from app.core.config import Settings
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=f"{settings.api_v1_prefix}/auth",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        path=f"{settings.api_v1_prefix}/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, service: AuthServiceDep) -> UserRead:
    user = await service.register(body)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
) -> TokenResponse:
    _user, access_token, refresh_token = await service.login(body)
    _set_refresh_cookie(response, refresh_token, settings)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    raw_refresh: Annotated[str | None, Depends(get_refresh_cookie)],
) -> TokenResponse:
    _user, access_token, refresh_token = await service.refresh(raw_refresh)
    _set_refresh_cookie(response, refresh_token, settings)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    raw_refresh: Annotated[str | None, Depends(get_refresh_cookie)],
) -> None:
    await service.logout(raw_refresh)
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
