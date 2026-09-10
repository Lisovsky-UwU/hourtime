from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from `HOURTIME_*` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="HOURTIME_",
        # The app is started from `backend/`, the shared .env lives at the repo root.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://hourtime:hourtime@localhost:5432/hourtime"
    sql_echo: bool = False

    # Recycle connections older than this so idle timeouts never surface.
    db_pool_recycle_seconds: int = 1800
    # Ping a pooled connection before reuse only once it has been idle this
    # long. 0 pings always (equivalent to pool_pre_ping), -1 never.
    db_ping_after_idle_seconds: int = 30

    redis_url: str = "redis://localhost:6379/0"
    cache_backend: Literal["redis", "memory"] = "redis"
    # How long an authenticated request may work from cached session/user rows.
    # Changes made through the app invalidate on commit; this bounds only the
    # staleness of edits made straight in the database.
    cache_ttl_seconds: int = 300

    # Leave off once your own account exists: the instance faces the open internet.
    allow_registration: bool = True
    password_min_length: int = 10

    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 30
    session_retention_days: int = 90
    session_purge_interval_hours: int = 24

    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
