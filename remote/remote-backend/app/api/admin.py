from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.openapi_responses import error_responses
from app.core.config import get_settings
from app.core.db import get_db
from app.core.rate_limit import create_rate_limiter
from app.repositories.admin import AdminRepository
from app.schemas.admin import (
    AdminMetricsSummaryResponse,
    AdminActionResponse,
    AdminCurrentSessionResponse,
    AdminDeviceListResponse,
    AdminDeviceRebindRequest,
    AdminDeviceResponse,
    AuditLogListResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSessionListResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from app.schemas.auth import ErrorResponse
from app.services.admin_service import AdminService, AdminServiceError

router = APIRouter(prefix='/admin', tags=['admin'])
settings = get_settings()
admin_login_rate_limiter = create_rate_limiter(
    backend=settings.LOGIN_RATE_LIMIT_BACKEND,
    scope='admin_login',
    window_seconds=settings.ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    max_attempts=settings.ADMIN_LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    sqlite_path=settings.LOGIN_RATE_LIMIT_SQLITE_PATH,
)
bearer_auth = HTTPBearer(auto_error=False, scheme_name='BearerAuth')


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    service = AdminService(AdminRepository(db))
    service.ensure_seed_admin()
    return service


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        return ''
    return credentials.credentials.strip()


def _error_response(exc: AdminServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=str(exc),
            details=exc.details,
        ).model_dump(),
    )


@router.post('/login', response_model=AdminLoginResponse, responses=error_responses(401, 403, 429))
def admin_login(payload: AdminLoginRequest, request: Request, service: AdminService = Depends(get_admin_service)) -> AdminLoginResponse | JSONResponse:
    client_ip = request.client.host if request.client else 'unknown'
    if not admin_login_rate_limiter.allow(f'{client_ip}:{payload.username}'):
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error_code='too_many_requests',
                message='Too many admin login attempts, please retry later.',
            ).model_dump(),
        )
    try:
        return service.login(payload, client_ip=client_ip)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/session', response_model=AdminCurrentSessionResponse, responses=error_responses(401, 403))
def admin_session(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminCurrentSessionResponse | JSONResponse:
    try:
        return service.get_session(_extract_bearer_token(credentials))
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/users', response_model=AdminUserListResponse, responses=error_responses(401, 403))
def list_users(
    q: str | None = None,
    status: str | None = None,
    license_status: str | None = None,
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserListResponse | JSONResponse:
    try:
        return service.list_users(
            _extract_bearer_token(credentials),
            q=q,
            status=status,
            license_status=license_status,
            limit=limit,
            offset=offset,
        )
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/users/{user_id}', response_model=AdminUserResponse, responses=error_responses(401, 403, 404))
def get_user(
    user_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserResponse | JSONResponse:
    try:
        return service.get_user(_extract_bearer_token(credentials), user_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.patch('/users/{user_id}', response_model=AdminUserResponse, responses=error_responses(401, 403, 404))
def update_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserResponse | JSONResponse:
    try:
        return service.update_user(_extract_bearer_token(credentials), user_id, payload)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.post('/users/{user_id}/revoke', response_model=AdminActionResponse, responses=error_responses(401, 403, 404))
def revoke_user(
    user_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminActionResponse | JSONResponse:
    try:
        return service.revoke_user(_extract_bearer_token(credentials), user_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.post('/users/{user_id}/restore', response_model=AdminActionResponse, responses=error_responses(401, 403, 404))
def restore_user(
    user_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminActionResponse | JSONResponse:
    try:
        return service.restore_user(_extract_bearer_token(credentials), user_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/devices', response_model=AdminDeviceListResponse, responses=error_responses(401, 403))
def list_devices(
    q: str | None = None,
    device_status: str | None = None,
    user_id: str | None = None,
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminDeviceListResponse | JSONResponse:
    try:
        return service.list_devices(
            _extract_bearer_token(credentials),
            q=q,
            device_status=device_status,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/devices/{device_id}', response_model=AdminDeviceResponse, responses=error_responses(401, 403, 404))
def get_device(
    device_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminDeviceResponse | JSONResponse:
    try:
        return service.get_device(_extract_bearer_token(credentials), device_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.post('/devices/{device_id}/unbind', response_model=AdminActionResponse, responses=error_responses(401, 403, 404))
def unbind_device(
    device_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminActionResponse | JSONResponse:
    try:
        return service.unbind_device(_extract_bearer_token(credentials), device_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.post('/devices/{device_id}/disable', response_model=AdminActionResponse, responses=error_responses(401, 403, 404))
def disable_device(
    device_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminActionResponse | JSONResponse:
    try:
        return service.disable_device(_extract_bearer_token(credentials), device_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.post('/devices/{device_id}/rebind', response_model=AdminActionResponse, responses=error_responses(401, 403, 404))
def rebind_device(
    device_id: str,
    payload: AdminDeviceRebindRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminActionResponse | JSONResponse:
    try:
        return service.rebind_device(_extract_bearer_token(credentials), device_id, payload)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/sessions', response_model=AdminSessionListResponse, responses=error_responses(401, 403))
def list_sessions(
    q: str | None = None,
    auth_state: str | None = None,
    user_id: str | None = None,
    device_id: str | None = None,
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminSessionListResponse | JSONResponse:
    try:
        return service.list_sessions(
            _extract_bearer_token(credentials),
            q=q,
            auth_state=auth_state,
            user_id=user_id,
            device_id=device_id,
            limit=limit,
            offset=offset,
        )
    except AdminServiceError as exc:
        return _error_response(exc)


@router.post('/sessions/{session_id}/revoke', response_model=AdminActionResponse, responses=error_responses(401, 403, 404))
def revoke_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminActionResponse | JSONResponse:
    try:
        return service.revoke_session(_extract_bearer_token(credentials), session_id)
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/audit-logs', response_model=AuditLogListResponse, responses=error_responses(401, 403))
def list_audit_logs(
    event_type: str | None = None,
    actor_id: str | None = None,
    target_user_id: str | None = None,
    target_device_id: str | None = None,
    target_session_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AuditLogListResponse | JSONResponse:
    try:
        return service.list_audit_logs(
            _extract_bearer_token(credentials),
            event_type=event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get('/metrics/summary', response_model=AdminMetricsSummaryResponse, responses=error_responses(401, 403))
def metrics_summary(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AdminService = Depends(get_admin_service),
) -> AdminMetricsSummaryResponse | JSONResponse:
    try:
        return service.get_metrics_summary(_extract_bearer_token(credentials))
    except AdminServiceError as exc:
        return _error_response(exc)
