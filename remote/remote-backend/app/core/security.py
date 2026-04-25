from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from .config import get_settings


PASSWORD_ALGO_PBKDF2_SHA256 = "pbkdf2_sha256"
PASSWORD_ALGO_ARGON2ID = "argon2id"


@dataclass(frozen=True)
class PasswordHashRecord:
    value: str
    algorithm: str


@dataclass(frozen=True)
class PasswordVerificationResult:
    verified: bool
    algorithm: str | None = None
    needs_rehash: bool = False


def _build_password_hasher() -> PasswordHasher:
    settings = get_settings()
    return PasswordHasher(
        time_cost=settings.PASSWORD_HASH_ARGON2_TIME_COST,
        memory_cost=settings.PASSWORD_HASH_ARGON2_MEMORY_COST_KB,
        parallelism=settings.PASSWORD_HASH_ARGON2_PARALLELISM,
        hash_len=settings.PASSWORD_HASH_ARGON2_HASH_LEN,
        salt_len=settings.PASSWORD_HASH_ARGON2_SALT_LEN,
    )


def _hash_pbkdf2_secret(secret: str) -> str:
    settings = get_settings()
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, settings.PASSWORD_HASH_ITERATIONS)
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=settings.PASSWORD_HASH_ITERATIONS,
        salt=base64.b64encode(salt).decode("ascii"),
        digest=base64.b64encode(digest).decode("ascii"),
    )


def _verify_pbkdf2_secret(secret: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        iteration_count = int(iterations)
    except (ValueError, TypeError):
        return False
    if algorithm != PASSWORD_ALGO_PBKDF2_SHA256:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, iteration_count)
    return hmac.compare_digest(base64.b64encode(derived).decode("ascii"), digest_b64)


def _detect_password_algorithm(stored: str) -> str | None:
    if stored.startswith(f"{PASSWORD_ALGO_PBKDF2_SHA256}$"):
        return PASSWORD_ALGO_PBKDF2_SHA256
    if stored.startswith("$argon2id$"):
        return PASSWORD_ALGO_ARGON2ID
    return None


def hash_account_password(password: str) -> PasswordHashRecord:
    settings = get_settings()
    algorithm = settings.PASSWORD_HASH_DEFAULT_ALGO.strip().lower()
    if algorithm == PASSWORD_ALGO_ARGON2ID:
        return PasswordHashRecord(value=_build_password_hasher().hash(password), algorithm=PASSWORD_ALGO_ARGON2ID)
    if algorithm == PASSWORD_ALGO_PBKDF2_SHA256:
        return PasswordHashRecord(value=_hash_pbkdf2_secret(password), algorithm=PASSWORD_ALGO_PBKDF2_SHA256)
    raise ValueError(f"Unsupported password hash algorithm: {settings.PASSWORD_HASH_DEFAULT_ALGO}")


def verify_account_password(
    password: str,
    stored: str,
    *,
    password_algo: str | None = None,
) -> PasswordVerificationResult:
    resolved_algorithm = (password_algo or _detect_password_algorithm(stored) or "").strip().lower() or None
    if resolved_algorithm == PASSWORD_ALGO_ARGON2ID:
        hasher = _build_password_hasher()
        try:
            verified = hasher.verify(stored, password)
        except (VerifyMismatchError, InvalidHashError, VerificationError):
            return PasswordVerificationResult(verified=False, algorithm=PASSWORD_ALGO_ARGON2ID)
        return PasswordVerificationResult(
            verified=bool(verified),
            algorithm=PASSWORD_ALGO_ARGON2ID,
            needs_rehash=bool(verified) and hasher.check_needs_rehash(stored),
        )
    if resolved_algorithm == PASSWORD_ALGO_PBKDF2_SHA256:
        verified = _verify_pbkdf2_secret(password, stored)
        settings = get_settings()
        needs_rehash = verified and settings.PASSWORD_HASH_DEFAULT_ALGO.strip().lower() != PASSWORD_ALGO_PBKDF2_SHA256
        return PasswordVerificationResult(
            verified=verified,
            algorithm=PASSWORD_ALGO_PBKDF2_SHA256,
            needs_rehash=needs_rehash,
        )
    return PasswordVerificationResult(verified=False, algorithm=resolved_algorithm)


def hash_refresh_token(token: str) -> str:
    return _hash_pbkdf2_secret(token)


def verify_refresh_token(token: str, stored: str) -> bool:
    return _verify_pbkdf2_secret(token, stored)


def issue_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def fingerprint_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
