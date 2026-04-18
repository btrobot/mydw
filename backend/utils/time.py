from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """Return the current UTC time normalized to a naive datetime for legacy DB fields."""
    return utc_now().replace(tzinfo=None)


def utc_day_start_naive(reference: datetime | None = None) -> datetime:
    """Return the start of the UTC day as a naive datetime."""
    base = reference if reference is not None else utc_now_naive()
    if base.tzinfo is not None:
        base = base.astimezone(UTC).replace(tzinfo=None)
    return base.replace(hour=0, minute=0, second=0, microsecond=0)
