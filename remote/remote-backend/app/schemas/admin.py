from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.pagination import PageMetadata


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


class AdminStepUpVerifyRequest(BaseModel):
    password: str
    scope: str


class AdminStepUpVerifyResponse(BaseModel):
    step_up_token: str
    scope: str
    expires_at: datetime
    method: str


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


class AdminUserListResponse(PageMetadata):
    items: list[AdminUserResponse]


class AdminUserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=256)
    display_name: str | None = Field(default=None, max_length=256)
    email: str | None = Field(default=None, max_length=256)
    tenant_id: str | None = Field(default=None, max_length=128)
    license_status: Literal['active', 'revoked', 'disabled'] = 'active'
    license_expires_at: datetime | None = None
    entitlements: list[str] = Field(default_factory=list)


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


class AdminDeviceListResponse(PageMetadata):
    items: list[AdminDeviceResponse]


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


class AdminSessionListResponse(PageMetadata):
    items: list[AdminSessionResponse]


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


class AuditLogListResponse(PageMetadata):
    items: list[AuditLogResponse]


class AdminMetricsSummaryResponse(BaseModel):
    active_sessions: int
    login_failures: int
    device_mismatches: int
    destructive_actions: int
    generated_at: datetime
    recent_failures: list[AuditLogResponse] = Field(default_factory=list)
    recent_destructive_actions: list[AuditLogResponse] = Field(default_factory=list)
