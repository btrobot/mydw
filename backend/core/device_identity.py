"""
Local device identity foundation for remote auth lifecycle work.
"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from core.config import settings


class FileDeviceIdentityStore:
    """Simple file-backed local device identity store."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or settings.REMOTE_AUTH_DEVICE_ID_PATH)

    def get_device_id(self) -> str | None:
        payload = self._load_payload()
        return payload.get("device_id")

    def get_or_create(self, seed: str | None = None) -> str:
        existing = self.get_device_id()
        if existing:
            return existing

        device_id = seed.strip() if seed and seed.strip() else f"device-{uuid4()}"
        self.set_device_id(device_id)
        return device_id

    def set_device_id(self, device_id: str) -> str:
        normalized = device_id.strip()
        if not normalized:
            raise ValueError("device_id must not be empty")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"device_id": normalized}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return normalized

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _load_payload(self) -> dict[str, str]:
        if not self.path.exists():
            return {}

        text = self.path.read_text(encoding="utf-8").strip()
        if not text:
            return {}

        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("device identity file must contain an object payload")
        if "device_id" in data and not isinstance(data["device_id"], str):
            raise ValueError("device identity file must store device_id as a string")
        return data


def create_device_identity_store() -> FileDeviceIdentityStore:
    return FileDeviceIdentityStore()
