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
