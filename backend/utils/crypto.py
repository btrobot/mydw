"""
得物掘金工具 - 加密工具
"""
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from core.config import settings


class CryptoHelper:
    """加密解密辅助类"""

    def __init__(self, key: str = None):
        # 如果没有提供密钥，使用配置的密钥
        key_str = key or settings.COOKIE_ENCRYPT_KEY
        # 生成盐值（使用固定盐便于测试，生产环境应随机生成并存储）
        salt = b"dewugojin-tool-salt-v1"
        self._key = self._derive_key(key_str, salt)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """从密码派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key for AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str) -> str:
        """加密数据，返回 Base64 编码的密文"""
        if not plaintext:
            return ""

        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM

        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

        # 返回 nonce + ciphertext，并 Base64 编码
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, encrypted: str) -> str:
        """解密数据"""
        if not encrypted:
            return ""

        try:
            data = base64.b64decode(encrypted.encode())
            nonce = data[:12]
            ciphertext = data[12:]

            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()

        except Exception as e:
            raise ValueError(f"解密失败: {e}")


# 全局加密实例
_crypto = CryptoHelper()


def encrypt_data(data: str) -> str:
    """加密数据"""
    return _crypto.encrypt(data)


def decrypt_data(data: str) -> str:
    """解密数据"""
    return _crypto.decrypt(data)


def mask_phone(phone: str) -> str:
    """将手机号脱敏，例如 13812348000 → 138****8000。"""
    if len(phone) == 11:
        return phone[:3] + "****" + phone[7:]
    return "***"
