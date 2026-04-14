"""
Auth observability helpers for request-scoped tracing.

Provides a lightweight contextvar-based trace context so auth events emitted
inside FastAPI request handlers can carry the same trace/request metadata.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass
from typing import Iterator
from uuid import uuid4


@dataclass(frozen=True)
class AuthTraceContext:
    trace_id: str
    request_id: str | None = None
    route_name: str | None = None
    method: str | None = None
    path: str | None = None


_CURRENT_AUTH_TRACE_CONTEXT: ContextVar[AuthTraceContext | None] = ContextVar(
    "current_auth_trace_context",
    default=None,
)


def build_auth_trace_context(
    *,
    request_id: str | None = None,
    trace_id: str | None = None,
    route_name: str | None = None,
    method: str | None = None,
    path: str | None = None,
) -> AuthTraceContext:
    """Build a normalized auth trace context."""
    normalized_trace_id = trace_id or request_id or uuid4().hex
    return AuthTraceContext(
        trace_id=normalized_trace_id,
        request_id=request_id,
        route_name=route_name,
        method=method,
        path=path,
    )


def get_current_auth_trace_context() -> AuthTraceContext | None:
    """Return the currently-active auth trace context, if any."""
    return _CURRENT_AUTH_TRACE_CONTEXT.get()


def get_current_auth_trace_context_dict() -> dict[str, str]:
    """Return the active auth trace context as a compact dict."""
    context = get_current_auth_trace_context()
    if context is None:
        return {}
    return {
        key: value
        for key, value in asdict(context).items()
        if value is not None
    }


def set_current_auth_trace_context(context: AuthTraceContext) -> Token[AuthTraceContext | None]:
    """Set the current auth trace context and return the reset token."""
    return _CURRENT_AUTH_TRACE_CONTEXT.set(context)


def reset_current_auth_trace_context(token: Token[AuthTraceContext | None]) -> None:
    """Reset the auth trace context using a previous token."""
    _CURRENT_AUTH_TRACE_CONTEXT.reset(token)


@contextmanager
def auth_trace_scope(context: AuthTraceContext) -> Iterator[AuthTraceContext]:
    """Context manager for binding an auth trace context to the current task."""
    token = set_current_auth_trace_context(context)
    try:
        yield context
    finally:
        reset_current_auth_trace_context(token)
