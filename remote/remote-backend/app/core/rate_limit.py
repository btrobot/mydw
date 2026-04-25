from __future__ import annotations

import sqlite3
from collections import defaultdict, deque
from pathlib import Path
from time import monotonic, time
from typing import Callable, Protocol


class RateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...

    def reset(self) -> None: ...


class InMemoryRateLimiter:
    def __init__(
        self,
        *,
        window_seconds: int,
        max_attempts: int,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_attempts = max_attempts
        self._clock = clock or monotonic
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self._clock()
        bucket = self._attempts[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_attempts:
            return False
        bucket.append(now)
        return True

    def reset(self) -> None:
        self._attempts.clear()


class SqliteRateLimiter:
    def __init__(
        self,
        *,
        db_path: str | Path,
        scope: str,
        window_seconds: int,
        max_attempts: int,
        clock: Callable[[], float] | None = None,
        fallback_limiter: InMemoryRateLimiter | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.scope = scope
        self.window_seconds = window_seconds
        self.max_attempts = max_attempts
        self._clock = clock or time
        self._fallback_limiter = fallback_limiter or InMemoryRateLimiter(
            window_seconds=window_seconds,
            max_attempts=max_attempts,
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_storage()

    def allow(self, key: str) -> bool:
        try:
            return self._allow_sqlite(key)
        except sqlite3.Error:
            return self._fallback_limiter.allow(key)

    def reset(self) -> None:
        self._fallback_limiter.reset()
        try:
            with self._connect() as connection:
                connection.execute(
                    "DELETE FROM rate_limit_attempts WHERE scope = ?",
                    (self.scope,),
                )
                connection.commit()
        except sqlite3.Error:
            return

    def _allow_sqlite(self, key: str) -> bool:
        now = self._clock()
        window_start = now - self.window_seconds
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM rate_limit_attempts WHERE scope = ? AND attempted_at <= ?",
                (self.scope, window_start),
            )
            current_attempts = connection.execute(
                """
                SELECT COUNT(*)
                FROM rate_limit_attempts
                WHERE scope = ? AND limiter_key = ? AND attempted_at > ?
                """,
                (self.scope, key, window_start),
            ).fetchone()
            assert current_attempts is not None
            if current_attempts[0] >= self.max_attempts:
                connection.commit()
                return False
            connection.execute(
                """
                INSERT INTO rate_limit_attempts (scope, limiter_key, attempted_at)
                VALUES (?, ?, ?)
                """,
                (self.scope, key, now),
            )
            connection.commit()
            return True

    def _initialize_storage(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limit_attempts (
                    scope TEXT NOT NULL,
                    limiter_key TEXT NOT NULL,
                    attempted_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_rate_limit_attempts_scope_key_time
                ON rate_limit_attempts(scope, limiter_key, attempted_at)
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=5)


def create_rate_limiter(
    *,
    backend: str,
    scope: str,
    window_seconds: int,
    max_attempts: int,
    sqlite_path: str | Path | None = None,
) -> RateLimiter:
    normalized_backend = backend.strip().lower()
    if normalized_backend == "sqlite" and sqlite_path is not None:
        return SqliteRateLimiter(
            db_path=sqlite_path,
            scope=scope,
            window_seconds=window_seconds,
            max_attempts=max_attempts,
        )
    return InMemoryRateLimiter(
        window_seconds=window_seconds,
        max_attempts=max_attempts,
    )
