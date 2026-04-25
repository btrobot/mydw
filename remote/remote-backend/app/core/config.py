from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR.parent / ".env"),
        env_prefix="REMOTE_BACKEND_",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "remote-backend"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8100
    DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'remote_auth.db').as_posix()}"
    LOGIN_RATE_LIMIT_BACKEND: str = "sqlite"
    LOGIN_RATE_LIMIT_SQLITE_PATH: str = str(DATA_DIR / "login_rate_limits.sqlite3")
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    REFRESH_RATE_LIMIT_WINDOW_SECONDS: int = 60
    REFRESH_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    ADMIN_LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    CORS_ALLOW_ORIGINS: str = "http://127.0.0.1:4173,http://localhost:4173,null"
    REQUEST_ID_HEADER: str = "x-request-id"
    TRACE_ID_HEADER: str = "x-trace-id"
    ACCESS_TOKEN_TTL_SECONDS: int = 900
    REFRESH_TOKEN_TTL_SECONDS: int = 1209600
    ADMIN_ACCESS_TOKEN_TTL_SECONDS: int = 3600
    MINIMUM_SUPPORTED_VERSION: str = "0.2.0"
    DEFAULT_OFFLINE_GRACE_HOURS: int = 24
    ADMIN_BOOTSTRAP_USERNAME: str = "admin"
    ADMIN_BOOTSTRAP_PASSWORD: str = "admin-secret"
    PASSWORD_HASH_ITERATIONS: int = 120000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    if settings.DATABASE_URL.startswith("sqlite:///") or settings.LOGIN_RATE_LIMIT_BACKEND.strip().lower() == "sqlite":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        Path(settings.LOGIN_RATE_LIMIT_SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
    return settings


def reset_settings_cache() -> None:
    get_settings.cache_clear()
