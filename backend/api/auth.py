"""
本地 Auth API surface（Step 1 / PR5）。
"""
from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.routing import APIRoute
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import require_active_machine_session
from core.observability import auth_trace_scope, build_auth_trace_context
from core.remote_auth_client import (
    RemoteAuthProtocolError,
    RemoteAuthResponseError,
    RemoteAuthTransportError,
)
from models import get_db
from schemas.auth import (
    AdminSessionResponse,
    AdminSessionRevokeResponse,
    AuthHealthResponse,
    AuthLoginRequest,
    AuthRefreshRequest,
    AuthStatusResponse,
    LocalAuthSessionSummary,
    RemoteAuthMePayload,
    SessionDetailsResponse,
)
from services.auth_service import AuthService


class AuthObservabilityRoute(APIRoute):
    """Route wrapper that attaches per-request trace context for auth APIs."""

    def get_route_handler(self):
        original_handler = super().get_route_handler()
        route_name = self.name or self.path

        async def traced_handler(request: Request) -> Response:
            trace_context = build_auth_trace_context(
                request_id=request.headers.get("x-request-id"),
                trace_id=request.headers.get("x-trace-id"),
                route_name=route_name,
                method=request.method,
                path=request.url.path,
            )
            started_at = perf_counter()

            with auth_trace_scope(trace_context):
                logger.bind(
                    is_auth_trace=True,
                    trace_id=trace_context.trace_id,
                    request_id=trace_context.request_id,
                    route_name=trace_context.route_name,
                    method=trace_context.method,
                    path=trace_context.path,
                ).info("auth_request_started")
                try:
                    response: Response = await original_handler(request)
                except Exception:
                    duration_ms = round((perf_counter() - started_at) * 1000, 2)
                    logger.bind(
                        is_auth_trace=True,
                        trace_id=trace_context.trace_id,
                        request_id=trace_context.request_id,
                        route_name=trace_context.route_name,
                        method=trace_context.method,
                        path=trace_context.path,
                        duration_ms=duration_ms,
                    ).exception("auth_request_failed")
                    raise

                duration_ms = round((perf_counter() - started_at) * 1000, 2)
                response.headers.setdefault("X-Trace-ID", trace_context.trace_id)
                if trace_context.request_id:
                    response.headers.setdefault("X-Request-ID", trace_context.request_id)
                logger.bind(
                    is_auth_trace=True,
                    trace_id=trace_context.trace_id,
                    request_id=trace_context.request_id,
                    route_name=trace_context.route_name,
                    method=trace_context.method,
                    path=trace_context.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                ).info("auth_request_completed")
                return response

        return traced_handler


router = APIRouter(route_class=AuthObservabilityRoute)
admin_router = APIRouter(
    route_class=AuthObservabilityRoute,
)


def require_auth_admin(
    summary: LocalAuthSessionSummary = Depends(require_active_machine_session),
) -> LocalAuthSessionSummary:
    """Minimal auth-admin gate for local session management surfaces."""
    if "auth:admin" not in summary.entitlements:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "forbidden",
                "message": "Admin privileges required.",
            },
        )
    return summary


def build_auth_service(db: AsyncSession) -> AuthService:
    """仅供 /api/auth/* 使用的本地 helper。"""
    return AuthService(db)


def _raise_http_error(exc: Exception) -> None:
    if isinstance(exc, RemoteAuthResponseError):
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    if isinstance(exc, RemoteAuthTransportError):
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
            },
        ) from exc
    if isinstance(exc, RemoteAuthProtocolError):
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": exc.error_code,
                "message": str(exc),
            },
        ) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=404 if "not found" in str(exc).lower() else 400,
            detail={
                "error_code": "not_found" if "not found" in str(exc).lower() else "bad_request",
                "message": str(exc),
            },
        ) from exc
    raise exc


@router.post("/login", response_model=LocalAuthSessionSummary)
async def login_auth(
    data: AuthLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    service = build_auth_service(db)
    try:
        return await service.login(
            username=data.username,
            password=data.password,
            device_id=data.device_id,
            client_version=data.client_version,
        )
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.post("/refresh", response_model=LocalAuthSessionSummary)
async def refresh_auth(
    data: AuthRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    service = build_auth_service(db)
    try:
        return await service.refresh_if_needed(client_version=data.client_version)
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.post("/logout", response_model=LocalAuthSessionSummary)
async def logout_auth(
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    service = build_auth_service(db)
    try:
        return await service.logout()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.get("/session", response_model=LocalAuthSessionSummary)
async def get_auth_session(
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    service = build_auth_service(db)
    try:
        return await service.get_session_summary()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.get("/me", response_model=RemoteAuthMePayload)
async def get_auth_me(
    db: AsyncSession = Depends(get_db),
) -> RemoteAuthMePayload:
    service = build_auth_service(db)
    try:
        return await service.get_me()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    db: AsyncSession = Depends(get_db),
) -> AuthStatusResponse:
    service = build_auth_service(db)
    try:
        return await service.get_status()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.get("/health", response_model=AuthHealthResponse)
async def get_auth_health(
    db: AsyncSession = Depends(get_db),
) -> AuthHealthResponse:
    service = build_auth_service(db)
    try:
        return await service.get_health()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@router.get("/session/details", response_model=SessionDetailsResponse)
async def get_auth_session_details(
    db: AsyncSession = Depends(get_db),
) -> SessionDetailsResponse:
    service = build_auth_service(db)
    try:
        return await service.get_session_details()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@admin_router.get("/admin/sessions", response_model=list[AdminSessionResponse])
async def list_admin_sessions(
    _admin: LocalAuthSessionSummary = Depends(require_auth_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSessionResponse]:
    service = build_auth_service(db)
    try:
        return await service.list_admin_sessions()
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)


@admin_router.post("/admin/sessions/{session_id}/revoke", response_model=AdminSessionRevokeResponse)
async def revoke_admin_session(
    session_id: int,
    _admin: LocalAuthSessionSummary = Depends(require_auth_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSessionRevokeResponse:
    service = build_auth_service(db)
    try:
        return await service.revoke_admin_session(session_id)
    except Exception as exc:  # noqa: BLE001
        _raise_http_error(exc)
