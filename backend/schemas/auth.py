"""
远程认证相关 DTO / schema。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RemoteAuthUser(BaseModel):
    """远程认证用户信息。"""

    id: str
    username: str
    display_name: Optional[str] = None
    tenant_id: Optional[str] = None


class RemoteAuthSessionPayload(BaseModel):
    """远程认证登录/刷新成功负载。"""

    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    user: RemoteAuthUser
    license_status: str
    entitlements: list[str] = Field(default_factory=list)
    device_id: str
    device_status: str
    offline_grace_until: Optional[datetime] = None
    minimum_supported_version: Optional[str] = None


class RemoteAuthMePayload(BaseModel):
    """远程认证 /me 成功负载。"""

    user: RemoteAuthUser
    license_status: str
    entitlements: list[str] = Field(default_factory=list)
    device_id: str
    device_status: str
    offline_grace_until: Optional[datetime] = None
    minimum_supported_version: Optional[str] = None


class RemoteAuthLogoutPayload(BaseModel):
    """远程认证登出成功负载。"""

    success: bool


class RemoteAuthErrorPayload(BaseModel):
    """远程认证错误响应负载。"""

    error_code: str
    message: str
    details: Optional[dict] = None


class LocalAuthSessionSummary(BaseModel):
    """本地 machine-session 摘要。"""

    model_config = ConfigDict(from_attributes=True)

    auth_state: str
    remote_user_id: Optional[str] = None
    display_name: Optional[str] = None
    license_status: Optional[str] = None
    entitlements: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    offline_grace_until: Optional[datetime] = None
    denial_reason: Optional[str] = None
    device_id: Optional[str] = None


class AuthLoginRequest(BaseModel):
    """本地 auth login 请求。"""

    username: str
    password: str
    device_id: str
    client_version: str


class AuthRefreshRequest(BaseModel):
    """本地 auth refresh 请求。"""

    client_version: str


class AuthStatusResponse(BaseModel):
    """Detailed local auth status for frontend/admin polling."""

    auth_state: str
    remote_user_id: Optional[str] = None
    display_name: Optional[str] = None
    license_status: Optional[str] = None
    device_id: Optional[str] = None
    denial_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    offline_grace_until: Optional[datetime] = None
    token_expires_in_seconds: Optional[int] = None
    grace_remaining_seconds: Optional[int] = None
    is_authenticated: bool
    is_active: bool
    is_grace: bool
    requires_reauth: bool
    can_read_local_data: bool
    can_run_protected_actions: bool
    can_run_background_tasks: bool


class AuthHealthResponse(BaseModel):
    """Health-oriented auth status for diagnostics and support."""

    status: str
    auth_state: str
    denial_reason: Optional[str] = None
    has_access_token: bool
    has_refresh_token: bool
    token_expires_in_seconds: Optional[int] = None
    grace_remaining_seconds: Optional[int] = None
    last_verified_at: Optional[datetime] = None
    can_read_local_data: bool
    can_run_protected_actions: bool
    can_run_background_tasks: bool


class SessionDetailsResponse(BaseModel):
    """Full persisted machine-session details plus secret presence metadata."""

    session_id: Optional[int] = None
    auth_state: str
    remote_user_id: Optional[str] = None
    display_name: Optional[str] = None
    license_status: Optional[str] = None
    entitlements: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    offline_grace_until: Optional[datetime] = None
    denial_reason: Optional[str] = None
    device_id: Optional[str] = None
    has_access_token: bool = False
    has_refresh_token: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminSessionResponse(BaseModel):
    """Admin-facing view of a persisted local auth session."""

    session_id: int
    auth_state: str
    remote_user_id: Optional[str] = None
    display_name: Optional[str] = None
    license_status: Optional[str] = None
    device_id: Optional[str] = None
    denial_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    offline_grace_until: Optional[datetime] = None
    has_access_token: bool = False
    has_refresh_token: bool = False
    is_current_session: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminSessionRevokeResponse(BaseModel):
    """Response after revoking a local auth session."""

    success: bool
    revoked_session: AdminSessionResponse
    current_session: LocalAuthSessionSummary
