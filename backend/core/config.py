"""Application settings and runtime security baseline."""
from __future__ import annotations

import json
from pathlib import Path
from secrets import token_urlsafe
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_COOKIE_ENCRYPT_KEY = "your-secret-key-change-in-production"
DEFAULT_REMOTE_AUTH_ENCRYPT_KEY = "your-remote-auth-key-change-in-production"
LOCAL_SECRET_FIELDS = {
    "COOKIE_ENCRYPT_KEY": DEFAULT_COOKIE_ENCRYPT_KEY,
    "REMOTE_AUTH_ENCRYPT_KEY": DEFAULT_REMOTE_AUTH_ENCRYPT_KEY,
}
LOCAL_SECRET_STORE = Path("data/runtime-secrets.json")


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "得物掘金工具"
    APP_VERSION: str = "0.2.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "electron://local",
    ]

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/dewugojin.db"

    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_BROWSER: str = "chromium"

    MATERIAL_BASE_PATH: str = "D:/系统/桌面/得物剪辑/待上传数据"

    COOKIE_ENCRYPT_KEY: str = DEFAULT_COOKIE_ENCRYPT_KEY

    PUBLISH_INTERVAL_MINUTES: int = 30
    PUBLISH_START_HOUR: int = 9
    PUBLISH_END_HOUR: int = 22
    MAX_PUBLISH_PER_ACCOUNT_PER_DAY: int = 5

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    SESSION_TTL_HOURS: int = 24
    HEALTH_CHECK_INTERVAL_MINUTES: int = 30

    BATCH_HEALTH_CHECK_MAX_CONCURRENCY: int = 3
    BATCH_HEALTH_CHECK_DEFAULT_INTERVAL: int = 2
    BATCH_HEALTH_CHECK_TIMEOUT: int = 30
    BATCH_HEALTH_CHECK_MAX_ACCOUNTS: int = 100

    COZE_API_TOKEN: str = ""
    COZE_API_BASE: str = "https://api.coze.cn"
    COZE_POLL_INTERVAL: int = 10
    COZE_MAX_RETRY: int = 3
    COZE_UPLOAD_TIMEOUT: int = 300

    REMOTE_AUTH_BASE_URL: str = ""
    REMOTE_AUTH_TIMEOUT: int = 15
    REMOTE_AUTH_ENCRYPT_KEY: str = DEFAULT_REMOTE_AUTH_ENCRYPT_KEY
    REMOTE_AUTH_DEFAULT_OFFLINE_GRACE_HOURS: int = 24
    REMOTE_AUTH_SECRET_STORE_PATH: str = "data/remote_auth_secrets.json"
    REMOTE_AUTH_DEVICE_ID_PATH: str = "data/remote_auth_device.json"
    REMOTE_AUTH_PROACTIVE_REFRESH_MINUTES: int = 5

    @property
    def is_production_like(self) -> bool:
        return self.APP_ENV.lower() in {"production", "staging"} or not self.DEBUG


settings = Settings()


def _uses_insecure_default(value: str, placeholder: str) -> bool:
    return not value or value == placeholder


def _load_or_create_local_runtime_secrets() -> dict[str, str]:
    LOCAL_SECRET_STORE.parent.mkdir(parents=True, exist_ok=True)

    if LOCAL_SECRET_STORE.exists():
        try:
            payload = json.loads(LOCAL_SECRET_STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = {}

    updated = False
    for field_name in LOCAL_SECRET_FIELDS:
        current = payload.get(field_name)
        if not isinstance(current, str) or len(current) < 32:
            payload[field_name] = token_urlsafe(48)
            updated = True

    if updated or not LOCAL_SECRET_STORE.exists():
        LOCAL_SECRET_STORE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {field_name: payload[field_name] for field_name in LOCAL_SECRET_FIELDS}


def _apply_runtime_security_baseline() -> None:
    insecure_fields = [
        field_name
        for field_name, placeholder in LOCAL_SECRET_FIELDS.items()
        if _uses_insecure_default(getattr(settings, field_name), placeholder)
    ]

    if not insecure_fields:
        return

    if settings.is_production_like:
        joined = ", ".join(insecure_fields)
        raise RuntimeError(
            f"{joined} must be set explicitly in .env or the runtime environment for production-like runs."
        )

    local_secrets = _load_or_create_local_runtime_secrets()
    for field_name in insecure_fields:
        setattr(settings, field_name, local_secrets[field_name])


# Ensure required directories exist.
def ensure_dirs() -> None:
    dirs = [
        Path("data"),
        Path("logs"),
        Path(settings.MATERIAL_BASE_PATH),
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


_apply_runtime_security_baseline()
ensure_dirs()
