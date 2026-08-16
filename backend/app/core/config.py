from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Project Management API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/project_management"
    )
    database_url_sync: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/project_management"
    )
    test_database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/project_management_test"
    )

    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_token_reuse_grace_seconds: int = 10
    refresh_token_absolute_max_days: int = 30

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
    )

    cookie_secure: bool = False
    cookie_samesite: str = "strict"
    cookie_name: str = "refresh_token"

    db_pool_size: int = 5
    db_max_overflow: int = 5

    redis_url: str = "redis://localhost:6379/0"
    arq_max_tries: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
