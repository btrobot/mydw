from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """Return the current UTC time normalized to a naive datetime for legacy DB fields."""
    return utc_now().replace(tzinfo=None)
