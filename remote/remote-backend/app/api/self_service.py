from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories.auth import AuthRepository
from app.schemas.auth import (
    ErrorResponse,
    SelfActivityListResponse,
    SelfDeviceListResponse,
    SelfMeResponse,
    SelfSessionRevokeResponse,
    SelfSessionListResponse,
)
from app.services.auth_service import AuthService, AuthServiceError


router = APIRouter(prefix='/self', tags=['self-service'])
bearer_auth = HTTPBearer(auto_error=False, scheme_name='BearerAuth')


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    service = AuthService(AuthRepository(db))
    service.ensure_seed_user()
    return service


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        return ''
    return credentials.credentials.strip()


def _error_response(exc: AuthServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=str(exc),
            details=exc.details,
        ).model_dump(),
    )


@router.get('/me', response_model=SelfMeResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
def self_me(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AuthService = Depends(get_auth_service),
) -> SelfMeResponse | JSONResponse:
    try:
        return service.self_me(_extract_bearer_token(credentials))
    except AuthServiceError as exc:
        return _error_response(exc)


@router.get('/devices', response_model=SelfDeviceListResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
def self_devices(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AuthService = Depends(get_auth_service),
) -> SelfDeviceListResponse | JSONResponse:
    try:
        return service.list_self_devices(_extract_bearer_token(credentials), limit=limit, offset=offset)
    except AuthServiceError as exc:
        return _error_response(exc)


@router.get('/sessions', response_model=SelfSessionListResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
def self_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AuthService = Depends(get_auth_service),
) -> SelfSessionListResponse | JSONResponse:
    try:
        return service.list_self_sessions(_extract_bearer_token(credentials), limit=limit, offset=offset)
    except AuthServiceError as exc:
        return _error_response(exc)


@router.get('/activity', response_model=SelfActivityListResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}})
def self_activity(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AuthService = Depends(get_auth_service),
) -> SelfActivityListResponse | JSONResponse:
    try:
        return service.list_self_activity(_extract_bearer_token(credentials), limit=limit, offset=offset)
    except AuthServiceError as exc:
        return _error_response(exc)


@router.post('/sessions/{session_id}/revoke', response_model=SelfSessionRevokeResponse, responses={401: {'model': ErrorResponse}, 403: {'model': ErrorResponse}, 404: {'model': ErrorResponse}})
def self_revoke_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
    service: AuthService = Depends(get_auth_service),
) -> SelfSessionRevokeResponse | JSONResponse:
    try:
        return service.revoke_self_session(_extract_bearer_token(credentials), session_id)
    except AuthServiceError as exc:
        return _error_response(exc)
