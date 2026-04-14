"""
远程认证专用加密适配层。

说明：
- 仅服务于 auth secret（refresh/access token 等）的本地加密存储。
- 这是 auth-specific adapter，不直接把调用方耦合到 utils.crypto。
"""
from __future__ import annotations

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import settings


class AuthCrypto:
    """远程认证 secret 的加解密器。"""

    _SALT = b"dewugojin-remote-auth-salt-v1"

    def __init__(self, key: str | None = None) -> None:
        key_str = key or settings.REMOTE_AUTH_ENCRYPT_KEY
        self._key = self._derive_key(key_str, self._SALT)

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return kdf.derive(password.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        if plaintext == "":
            return ""

        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str) -> str:
        if encrypted == "":
            return ""

        try:
            data = base64.b64decode(encrypted.encode("utf-8"))
            nonce = data[:12]
            ciphertext = data[12:]
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"auth secret 解密失败: {exc}") from exc

