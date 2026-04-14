"""
得物掘金工具 - 配置管理
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # 应用基本信息
    APP_NAME: str = "得物掘金工具"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True

    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "electron://local"
    ]

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/dewugojin.db"

    # Playwright 配置
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_BROWSER: str = "chromium"  # chromium, firefox, webkit

    # 素材目录
    MATERIAL_BASE_PATH: str = "D:/系统/桌面/得物剪辑/待上传数据"

    # Cookie 加密密钥 (生产环境应从环境变量读取)
    COOKIE_ENCRYPT_KEY: str = "your-secret-key-change-in-production"

    # 发布配置
    PUBLISH_INTERVAL_MINUTES: int = 30
    PUBLISH_START_HOUR: int = 9
    PUBLISH_END_HOUR: int = 22
    MAX_PUBLISH_PER_ACCOUNT_PER_DAY: int = 5

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # 账号会话配置
    SESSION_TTL_HOURS: int = 24
    HEALTH_CHECK_INTERVAL_MINUTES: int = 30

    # 批量健康检查
    BATCH_HEALTH_CHECK_MAX_CONCURRENCY: int = 3
    BATCH_HEALTH_CHECK_DEFAULT_INTERVAL: int = 2
    BATCH_HEALTH_CHECK_TIMEOUT: int = 30
    BATCH_HEALTH_CHECK_MAX_ACCOUNTS: int = 100

    # 扣子（Coze）集成
    COZE_API_TOKEN: str = ""
    COZE_API_BASE: str = "https://api.coze.cn"
    COZE_POLL_INTERVAL: int = 10
    COZE_MAX_RETRY: int = 3
    COZE_UPLOAD_TIMEOUT: int = 300

    # 远程认证（Step 1 / PR1 foundation）
    REMOTE_AUTH_BASE_URL: str = ""
    REMOTE_AUTH_TIMEOUT: int = 15
    REMOTE_AUTH_ENCRYPT_KEY: str = "your-remote-auth-key-change-in-production"
    REMOTE_AUTH_DEFAULT_OFFLINE_GRACE_HOURS: int = 24
    REMOTE_AUTH_SECRET_STORE_PATH: str = "data/remote_auth_secrets.json"
    REMOTE_AUTH_DEVICE_ID_PATH: str = "data/remote_auth_device.json"
    # PR2: Proactive refresh buffer (minutes before expiry to trigger refresh)
    REMOTE_AUTH_PROACTIVE_REFRESH_MINUTES: int = 5


# 创建配置实例
settings = Settings()

# 安全检查：默认加密密钥警告
if settings.COOKIE_ENCRYPT_KEY == "your-secret-key-change-in-production":
    import warnings
    warnings.warn(
        "COOKIE_ENCRYPT_KEY 使用默认值，请在 .env 中配置安全密钥",
        stacklevel=1,
    )

# 确保必要目录存在
def ensure_dirs():
    """确保必要目录存在"""
    dirs = [
        Path("data"),
        Path("logs"),
        Path(settings.MATERIAL_BASE_PATH),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# 应用启动时调用
ensure_dirs()
