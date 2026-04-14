"""
Step 1 / PR2 tests for auth secret crypto adapter and SecretStore.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.auth_crypto import AuthCrypto
from core.secret_store import FileSecretStore


def test_auth_crypto_round_trip() -> None:
    crypto = AuthCrypto(key="unit-test-auth-key")

    encrypted = crypto.encrypt("refresh_token_secret")

    assert encrypted != "refresh_token_secret"
    assert crypto.decrypt(encrypted) == "refresh_token_secret"


def test_auth_crypto_rejects_wrong_key() -> None:
    crypto = AuthCrypto(key="unit-test-auth-key")
    wrong_crypto = AuthCrypto(key="different-auth-key")

    encrypted = crypto.encrypt("refresh_token_secret")

    with pytest.raises(ValueError, match="auth secret 解密失败"):
        wrong_crypto.decrypt(encrypted)


def test_file_secret_store_save_load_delete(tmp_path: Path) -> None:
    store_path = tmp_path / "remote_auth_secrets.json"
    store = FileSecretStore(path=store_path, crypto=AuthCrypto(key="unit-test-auth-key"))

    store.set_secret("refresh_token", "refresh_secret_value")

    assert store_path.exists()
    assert store.get_secret("refresh_token") == "refresh_secret_value"

    raw = store_path.read_text(encoding="utf-8")
    assert "refresh_secret_value" not in raw

    store.delete_secret("refresh_token")
    assert store.get_secret("refresh_token") is None


def test_file_secret_store_clear_supports_logout_cleanup(tmp_path: Path) -> None:
    store_path = tmp_path / "remote_auth_secrets.json"
    store = FileSecretStore(path=store_path, crypto=AuthCrypto(key="unit-test-auth-key"))

    store.set_secret("refresh_token", "refresh_secret_value")
    store.set_secret("access_token", "access_secret_value")

    assert store_path.exists()
    store.clear()
    assert not store_path.exists()


def test_file_secret_store_rejects_invalid_payload_shape(tmp_path: Path) -> None:
    store_path = tmp_path / "remote_auth_secrets.json"
    store_path.write_text(json.dumps(["bad", "shape"]), encoding="utf-8")
    store = FileSecretStore(path=store_path, crypto=AuthCrypto(key="unit-test-auth-key"))

    with pytest.raises(ValueError, match="root node must be object|根节点必须是对象"):
        store.get_secret("refresh_token")
