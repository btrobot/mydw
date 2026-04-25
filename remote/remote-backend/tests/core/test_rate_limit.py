from __future__ import annotations

from pathlib import Path

from app.core.rate_limit import SqliteRateLimiter


def test_sqlite_rate_limiter_blocks_after_max_attempts(tmp_path: Path) -> None:
    now = [1000.0]
    limiter = SqliteRateLimiter(
        db_path=tmp_path / "rate_limits.sqlite3",
        scope="admin_login",
        window_seconds=60,
        max_attempts=2,
        clock=lambda: now[0],
    )

    assert limiter.allow("10.0.0.1:admin") is True
    assert limiter.allow("10.0.0.1:admin") is True
    assert limiter.allow("10.0.0.1:admin") is False


def test_sqlite_rate_limiter_expires_old_attempts_after_window(tmp_path: Path) -> None:
    now = [1000.0]
    limiter = SqliteRateLimiter(
        db_path=tmp_path / "rate_limits.sqlite3",
        scope="auth_login",
        window_seconds=60,
        max_attempts=1,
        clock=lambda: now[0],
    )

    assert limiter.allow("10.0.0.1:alice") is True
    assert limiter.allow("10.0.0.1:alice") is False

    now[0] += 61

    assert limiter.allow("10.0.0.1:alice") is True


def test_sqlite_rate_limiter_persists_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "rate_limits.sqlite3"
    now = [1000.0]

    first_limiter = SqliteRateLimiter(
        db_path=db_path,
        scope="auth_login",
        window_seconds=60,
        max_attempts=1,
        clock=lambda: now[0],
    )
    second_limiter = SqliteRateLimiter(
        db_path=db_path,
        scope="auth_login",
        window_seconds=60,
        max_attempts=1,
        clock=lambda: now[0],
    )

    assert first_limiter.allow("10.0.0.1:alice") is True
    assert second_limiter.allow("10.0.0.1:alice") is False
