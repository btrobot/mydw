from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminIdentity(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    role: str


class AdminLoginResponse(BaseModel):
    access_token: str
    session_id: str
    expires_at: datetime
    token_type: str
    user: AdminIdentity


class AdminCurrentSessionResponse(BaseModel):
    session_id: str
    expires_at: datetime
    user: AdminIdentity


class AdminUserResponse(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    email: str | None = None
    tenant_id: str | None = None
    status: str | None = None
    license_status: str | None = None
    license_expires_at: datetime | None = None
    entitlements: list[str] = Field(default_factory=list)
    device_count: int | None = None
    last_seen_at: datetime | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int


class AdminUserUpdateRequest(BaseModel):
    display_name: str | None = None
    license_status: str | None = None
    license_expires_at: datetime | None = None
    entitlements: list[str] | None = None


class AdminActionResponse(BaseModel):
    success: bool


class AdminDeviceResponse(BaseModel):
    device_id: str
    user_id: str | None = None
    device_status: str
    first_bound_at: datetime | None = None
    last_seen_at: datetime | None = None
    client_version: str | None = None


class AdminDeviceListResponse(BaseModel):
    items: list[AdminDeviceResponse]
    total: int


class AdminDeviceRebindRequest(BaseModel):
    user_id: str
    client_version: str | None = None


class AdminSessionResponse(BaseModel):
    session_id: str
    user_id: str | None = None
    device_id: str | None = None
    auth_state: str
    issued_at: datetime
    expires_at: datetime
    last_seen_at: datetime


class AdminSessionListResponse(BaseModel):
    items: list[AdminSessionResponse]
    total: int


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    actor_type: str | None = None
    actor_id: str | None = None
    target_user_id: str | None = None
    target_device_id: str | None = None
    target_session_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    created_at: datetime
    details: dict = Field(default_factory=dict)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int


class AdminMetricsSummaryResponse(BaseModel):
    active_sessions: int
    login_failures: int
    device_mismatches: int
    destructive_actions: int
    generated_at: datetime
    recent_failures: list[AuditLogResponse] = Field(default_factory=list)
    recent_destructive_actions: list[AuditLogResponse] = Field(default_factory=list)
