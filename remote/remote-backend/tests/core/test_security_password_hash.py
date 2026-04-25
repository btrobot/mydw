from __future__ import annotations

from app.core.config import reset_settings_cache
from app.core.security import (
    PASSWORD_ALGO_ARGON2ID,
    PASSWORD_ALGO_PBKDF2_SHA256,
    hash_account_password,
    hash_refresh_token,
    hash_step_up_token,
    verify_account_password,
    verify_refresh_token,
    verify_step_up_token,
)


def test_hash_account_password_defaults_to_argon2_and_verifies(monkeypatch) -> None:
    monkeypatch.setenv("REMOTE_BACKEND_PASSWORD_HASH_DEFAULT_ALGO", PASSWORD_ALGO_ARGON2ID)
    reset_settings_cache()

    password_record = hash_account_password("secret")
    verification = verify_account_password("secret", password_record.value, password_algo=password_record.algorithm)

    assert password_record.algorithm == PASSWORD_ALGO_ARGON2ID
    assert password_record.value.startswith("$argon2id$")
    assert verification.verified is True
    assert verification.algorithm == PASSWORD_ALGO_ARGON2ID
    assert verification.needs_rehash is False

    reset_settings_cache()


def test_verify_account_password_marks_legacy_pbkdf2_for_rehash(monkeypatch) -> None:
    monkeypatch.setenv("REMOTE_BACKEND_PASSWORD_HASH_DEFAULT_ALGO", PASSWORD_ALGO_PBKDF2_SHA256)
    reset_settings_cache()
    legacy_record = hash_account_password("secret")

    monkeypatch.setenv("REMOTE_BACKEND_PASSWORD_HASH_DEFAULT_ALGO", PASSWORD_ALGO_ARGON2ID)
    reset_settings_cache()
    verification = verify_account_password("secret", legacy_record.value, password_algo=legacy_record.algorithm)

    assert legacy_record.algorithm == PASSWORD_ALGO_PBKDF2_SHA256
    assert verification.verified is True
    assert verification.algorithm == PASSWORD_ALGO_PBKDF2_SHA256
    assert verification.needs_rehash is True

    reset_settings_cache()


def test_refresh_token_hash_and_verify_remain_pbkdf2_compatible() -> None:
    token_hash = hash_refresh_token("refresh-token")

    assert token_hash.startswith("pbkdf2_sha256$")
    assert verify_refresh_token("refresh-token", token_hash) is True
    assert verify_refresh_token("wrong-token", token_hash) is False


def test_step_up_token_hash_and_verify_use_stable_fingerprint() -> None:
    token_hash = hash_step_up_token("step-up-token")

    assert token_hash == hash_step_up_token("step-up-token")
    assert verify_step_up_token("step-up-token", token_hash) is True
    assert verify_step_up_token("wrong-token", token_hash) is False
