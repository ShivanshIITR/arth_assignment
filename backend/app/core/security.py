import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def create_access_token(user_id: UUID, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str, settings: Settings | None = None) -> UUID:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    if payload.get("type") != "access" or "sub" not in payload:
        raise UnauthorizedError("Invalid token")

    try:
        return UUID(payload["sub"])
    except ValueError as exc:
        raise UnauthorizedError("Invalid token") from exc
