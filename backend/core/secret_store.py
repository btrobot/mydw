"""
远程认证 secret storage 抽象与首版文件适配器。

说明：
- Step 1 / PR2 只提供本地 secret storage abstraction 与首版 file adapter。
- 不涉及远程认证协议，不涉及 machine-session 编排。
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from core.auth_crypto import AuthCrypto
from core.config import settings


class SecretStore(ABC):
    """认证 secret storage 抽象。"""

    @abstractmethod
    def set_secret(self, key: str, value: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def delete_secret(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_secrets(self, secrets: dict[str, str]) -> None:
        """Atomically store multiple secrets to ensure consistency.

        PR2: Required for atomic token rotation - both access_token and
        refresh_token must be updated together.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class FileSecretStore(SecretStore):
    """首版文件型 secret store。"""

    def __init__(self, path: str | Path | None = None, crypto: AuthCrypto | None = None) -> None:
        self.path = Path(path or settings.REMOTE_AUTH_SECRET_STORE_PATH)
        self.crypto = crypto or AuthCrypto()

    def set_secret(self, key: str, value: str) -> None:
        payload = self._load_payload()
        payload[key] = self.crypto.encrypt(value)
        self._write_payload(payload)

    def get_secret(self, key: str) -> str | None:
        payload = self._load_payload()
        encrypted = payload.get(key)
        if encrypted is None:
            return None
        return self.crypto.decrypt(encrypted)

    def delete_secret(self, key: str) -> None:
        payload = self._load_payload()
        if key in payload:
            del payload[key]
            self._write_payload(payload)

    def set_secrets(self, secrets: dict[str, str]) -> None:
        """Atomically store multiple secrets.

        PR2: Ensures token rotation consistency - both tokens updated together.
        """
        payload = self._load_payload()
        for key, value in secrets.items():
            payload[key] = self.crypto.encrypt(value)
        self._write_payload(payload)

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
            raise ValueError("secret store 文件格式无效：根节点必须是对象")

        invalid = [k for k, v in data.items() if not isinstance(k, str) or not isinstance(v, str)]
        if invalid:
            raise ValueError("secret store 文件格式无效：键和值必须是字符串")
        return data

    def _write_payload(self, payload: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def create_secret_store() -> SecretStore:
    """创建默认 secret store。"""
    return FileSecretStore()

