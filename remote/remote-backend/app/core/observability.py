from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    trace_id: str


_REQUEST_CONTEXT: ContextVar[RequestContext | None] = ContextVar("remote_request_context", default=None)


def get_request_context() -> RequestContext | None:
    return _REQUEST_CONTEXT.get()


def set_request_context(context: RequestContext) -> Token[RequestContext | None]:
    return _REQUEST_CONTEXT.set(context)


def reset_request_context(token: Token[RequestContext | None]) -> None:
    _REQUEST_CONTEXT.reset(token)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]):
        settings = get_settings()
        request_id = request.headers.get(settings.REQUEST_ID_HEADER, uuid4().hex)
        trace_id = request.headers.get(settings.TRACE_ID_HEADER, request_id)
        token = set_request_context(RequestContext(request_id=request_id, trace_id=trace_id))
        try:
            response = await call_next(request)
        finally:
            reset_request_context(token)
        response.headers.setdefault("X-Request-ID", request_id)
        response.headers.setdefault("X-Trace-ID", trace_id)
        return response
