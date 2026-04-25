from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.rate_limit import InMemoryRateLimiter, create_rate_limiter
from app.repositories.auth import AuthRepository
from app.schemas.auth import (
    AuthSuccessResponse,
    ErrorResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
)
from app.services.auth_service import AuthService, AuthServiceError

router = APIRouter(prefix='', tags=['auth'])
settings = get_settings()
login_rate_limiter = create_rate_limiter(
    backend=settings.LOGIN_RATE_LIMIT_BACKEND,
    scope='auth_login',
    window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    max_attempts=settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    sqlite_path=settings.LOGIN_RATE_LIMIT_SQLITE_PATH,
)
refresh_rate_limiter = InMemoryRateLimiter(window_seconds=settings.REFRESH_RATE_LIMIT_WINDOW_SECONDS, max_attempts=settings.REFRESH_RATE_LIMIT_MAX_ATTEMPTS)
bearer_auth = HTTPBearer(auto_error=False, scheme_name='BearerAuth')


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    service = AuthService(AuthRepository(db))
    service.ensure_seed_user()
    return service


def _error_response(exc: AuthServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=str(exc),
            details=exc.details,
        ).model_dump(),
    )


def _rate_limited(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error_code='too_many_requests',
            message=message,
        ).model_dump(),
    )


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        return ''
    return credentials.credentials.strip()


@router.post('/login', response_model=AuthSuccessResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}, 429: {'model': ErrorResponse}})
def login(payload: LoginRequest, request: Request, service: AuthService = Depends(get_auth_service)) -> AuthSuccessResponse | JSONResponse:
    client_ip = request.client.host if request.client else 'unknown'
    if not login_rate_limiter.allow(f'{client_ip}:{payload.username}'):
        return _rate_limited('Too many login attempts, please retry later.')
    try:
        return service.login(payload, client_ip=client_ip)
    except AuthServiceError as exc:
        return _error_response(exc)


@router.post('/refresh', response_model=AuthSuccessResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}, 429: {'model': ErrorResponse}})
def refresh(payload: RefreshRequest, request: Request, service: AuthService = Depends(get_auth_service)) -> AuthSuccessResponse | JSONResponse:
    client_ip = request.client.host if request.client else 'unknown'
    if not refresh_rate_limiter.allow(f'{client_ip}:{payload.device_id}'):
        return _rate_limited('Too many refresh attempts, please retry later.')
    try:
        return service.refresh(payload, client_ip=client_ip)
    except AuthServiceError as exc:
        return _error_response(exc)


@router.post('/logout', response_model=LogoutResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
def logout(payload: LogoutRequest, service: AuthService = Depends(get_auth_service)) -> LogoutResponse | JSONResponse:
    try:
        return service.logout(payload)
    except AuthServiceError as exc:
        return _error_response(exc)


@router.get('/me', response_model=MeResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
def me(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AuthService = Depends(get_auth_service),
) -> MeResponse | JSONResponse:
    try:
        return service.me(_extract_bearer_token(credentials))
    except AuthServiceError as exc:
        return _error_response(exc)
