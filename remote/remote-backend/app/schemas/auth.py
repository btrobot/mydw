from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    device_id: str
    client_version: str


class RefreshRequest(BaseModel):
    refresh_token: str
    device_id: str
    client_version: str


class LogoutRequest(BaseModel):
    refresh_token: str
    device_id: str


class UserIdentity(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    tenant_id: str | None = None


class AuthSuccessResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str
    user: UserIdentity
    license_status: str
    entitlements: list[str]
    device_id: str
    device_status: str
    offline_grace_until: datetime | None = None
    minimum_supported_version: str | None = None


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict = Field(default_factory=dict)


class LogoutResponse(BaseModel):
    success: bool


class MeResponse(BaseModel):
    user: UserIdentity
    license_status: str
    entitlements: list[str]
    device_id: str
    device_status: str
    offline_grace_until: datetime | None = None
    minimum_supported_version: str | None = None


class SelfUserIdentity(BaseModel):
    id: str
    username: str
    display_name: str | None = None


class SelfMeResponse(BaseModel):
    user: SelfUserIdentity
    license_status: str
    entitlements: list[str]
    device_id: str
    device_status: str
    offline_grace_until: datetime | None = None
    minimum_supported_version: str | None = None


class SelfDeviceResponse(BaseModel):
    device_id: str
    device_status: str
    client_version: str | None = None
    first_bound_at: datetime | None = None
    last_seen_at: datetime | None = None
    is_current: bool


class SelfDeviceListResponse(BaseModel):
    items: list[SelfDeviceResponse]
    total: int


class SelfSessionResponse(BaseModel):
    session_id: str
    device_id: str | None = None
    auth_state: str
    issued_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    is_current: bool


class SelfSessionListResponse(BaseModel):
    items: list[SelfSessionResponse]
    total: int


class SelfActivityResponse(BaseModel):
    id: str
    event_type: str
    created_at: datetime
    summary: str
    device_id: str | None = None
    session_id: str | None = None


class SelfActivityListResponse(BaseModel):
    items: list[SelfActivityResponse]
    total: int


class SelfSessionRevokeResponse(BaseModel):
    success: bool
    session_id: str
    auth_state: str
    already_revoked: bool
