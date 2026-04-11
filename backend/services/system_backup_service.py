"""
System backup service.

Phase 5 / PR3:
- provide a minimal but truthful backup artifact
- clearly scope what is included and excluded
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models import Account, Product, Task, Video, Copywriting, Cover, Audio, Topic
import services.system_config_service as system_config_service
from services.system_config_service import SystemConfigService

BACKUP_ROOT = Path("data/backups")


def resolve_sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url[len(prefix):]
    return Path(raw_path)


class SystemBackupService:
    def __init__(self, db: AsyncSession, backup_root: Path | None = None) -> None:
        self.db = db
        self.backup_root = backup_root or BACKUP_ROOT

    async def create_backup(self, *, include_logs: bool) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        manifest = await self._build_manifest(timestamp=timestamp, include_logs=include_logs)

        db_path = resolve_sqlite_path(settings.DATABASE_URL)
        if db_path and db_path.exists():
            db_copy = backup_dir / db_path.name
            shutil.copy2(db_path, db_copy)
            manifest["artifacts"]["database_snapshot"] = str(db_copy)
        else:
            manifest["artifacts"]["database_snapshot"] = None

        runtime_config_path = system_config_service.RUNTIME_CONFIG_PATH
        if runtime_config_path.exists():
            config_copy = backup_dir / runtime_config_path.name
            shutil.copy2(runtime_config_path, config_copy)
            manifest["artifacts"]["runtime_config_snapshot"] = str(config_copy)
        else:
            manifest["artifacts"]["runtime_config_snapshot"] = None

        if include_logs:
            log_path = Path(settings.LOG_DIR) / "app.log"
            if log_path.exists():
                log_copy = backup_dir / log_path.name
                shutil.copy2(log_path, log_copy)
                manifest["artifacts"]["log_snapshot"] = str(log_copy)
            else:
                manifest["artifacts"]["log_snapshot"] = None
        else:
            manifest["artifacts"]["log_snapshot"] = None

        manifest_path = backup_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest_path

    async def _build_manifest(self, *, timestamp: str, include_logs: bool) -> dict[str, Any]:
        return {
            "version": settings.APP_VERSION,
            "timestamp": timestamp,
            "backup_scope": {
                "includes": [
                    "database snapshot (when sqlite file exists)",
                    "runtime config snapshot",
                    "metadata manifest",
                ] + (["application log snapshot"] if include_logs else []),
                "excludes": [
                    "media files",
                    "full restore workflow",
                ],
            },
            "effective_system_config": SystemConfigService().get_config(),
            "counts": {
                "accounts": await self._count(Account),
                "tasks": await self._count(Task),
                "products": await self._count(Product),
                "videos": await self._count(Video),
                "copywritings": await self._count(Copywriting),
                "covers": await self._count(Cover),
                "audios": await self._count(Audio),
                "topics": await self._count(Topic),
            },
            "artifacts": {},
        }

    async def _count(self, model: type) -> int:
        result = await self.db.execute(select(func.count()).select_from(model))
        return result.scalar() or 0
