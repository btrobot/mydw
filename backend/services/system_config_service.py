"""
System runtime config service.

Phase 5 / PR2:
- introduce a narrow runtime config source for matrix-approved settings
- keep startup env config (from backend/core/config.py) distinct
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import settings

RUNTIME_CONFIG_PATH = Path("data/system_config.json")


class SystemConfigService:
    """File-backed runtime config for matrix-approved settings."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or RUNTIME_CONFIG_PATH

    def _read_raw(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}

    def _write_raw(self, payload: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get_config(self) -> dict[str, Any]:
        raw = self._read_raw()
        return {
            "material_base_path": raw.get("material_base_path", settings.MATERIAL_BASE_PATH),
            # Phase 5 matrix: auto_backup is not a supported runtime setting yet.
            "auto_backup": False,
            # Phase 5 matrix: log_level remains startup-env.
            "log_level": settings.LOG_LEVEL,
        }

    def update_config(
        self,
        *,
        material_base_path: str | None = None,
        auto_backup: bool | None = None,
        log_level: str | None = None,
    ) -> dict[str, Any]:
        unsupported: list[str] = []
        if auto_backup is not None:
            unsupported.append("auto_backup")
        if log_level is not None:
            unsupported.append("log_level")
        if unsupported:
            joined = ", ".join(unsupported)
            raise ValueError(f"以下设置当前不支持运行时修改: {joined}")

        if material_base_path is None:
            raise ValueError("material_base_path 是当前唯一支持的运行时设置项")

        current = self._read_raw()
        current["material_base_path"] = material_base_path
        self._write_raw(current)
        return self.get_config()
