"""
Shared backend auth enforcement primitives for Step 3 / PR1.

This module is intentionally limited to:
- loading the local machine-session truth from AuthService
- freezing reusable policy definitions for router/service/scheduler gates
- mapping denied auth states to canonical local error payloads

It does not roll out any business-router enforcement by itself.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models import get_db
from schemas.auth import LocalAuthSessionSummary

AuthPolicyName = Literal["active_required", "grace_readonly_allowed"]

DEFAULT_UNAUTHENTICATED_STATE = "unauthenticated"
_CURRENT_AUTH_SUMMARY: ContextVar[LocalAuthSessionSummary | None] = ContextVar(
    "current_auth_summary",
    default=None,
)

POLICY_ACTIVE_REQUIRED: AuthPolicyName = "active_required"
POLICY_GRACE_READONLY_ALLOWED: AuthPolicyName = "grace_readonly_allowed"

_ACTIVE_ALLOWED_STATES = frozenset({"authenticated_active"})
_GRACE_READONLY_ALLOWED_STATES = frozenset({"authenticated_active", "authenticated_grace"})
RUNTIME_HARD_STOP_STATES = frozenset(
    {
        "unauthenticated",
        "authorizing",
        "refresh_required",
        "revoked",
        "device_mismatch",
        "expired",
        "error",
    }
)
RUNTIME_FAILURE_REASONS = MappingProxyType(
    {
        "revoked": "remote_auth_revoked",
        "device_mismatch": "remote_auth_device_mismatch",
        "expired": "remote_auth_expired",
        "unauthenticated": "remote_auth_unauthenticated",
        "refresh_required": "remote_auth_refresh_required",
        "authorizing": "remote_auth_authorizing",
        "error": "remote_auth_error",
    }
)

_STATE_PRIORITY = {
    "revoked": 1,
    "device_mismatch": 2,
    "expired": 3,
    "unauthenticated": 4,
    "refresh_required": 4,
    "error": 4,
    "authorizing": 4,
    "authenticated_grace": 5,
    "authenticated_active": 6,
}

_STATE_STATUS_CODE = {
    "unauthenticated": 401,
    "authorizing": 401,
    "refresh_required": 401,
    "expired": 401,
    "error": 401,
    "authenticated_grace": 403,
    "revoked": 403,
    "device_mismatch": 403,
}

_STATE_ERROR_CODE = {
    "unauthenticated": "unauthenticated",
    "authorizing": "authorization_in_progress",
    "refresh_required": "refresh_required",
    "expired": "expired",
    "error": "auth_error",
    "revoked": "revoked",
    "device_mismatch": "device_mismatch",
}

_STATE_MESSAGE = {
    "unauthenticated": "Remote auth is required before using local protected features.",
    "authorizing": "Remote auth is still being established.",
    "refresh_required": "Remote auth must be refreshed before continuing.",
    "expired": "Remote auth has expired and must be renewed.",
    "error": "Remote auth is currently unavailable.",
    "revoked": "Remote authorization has been revoked.",
    "device_mismatch": "This device is no longer authorized for the current session.",
}


@dataclass(frozen=True)
class AuthPolicyDefinition:
    name: AuthPolicyName
    allowed_states: frozenset[str]
    description: str
    allows_grace_readonly: bool
    allows_high_risk_writes: bool
    allows_new_background_tasks: bool


AUTH_POLICY_MATRIX = MappingProxyType(
    {
        POLICY_ACTIVE_REQUIRED: AuthPolicyDefinition(
            name=POLICY_ACTIVE_REQUIRED,
            allowed_states=_ACTIVE_ALLOWED_STATES,
            description="Only fully active machine sessions may proceed.",
            allows_grace_readonly=False,
            allows_high_risk_writes=True,
            allows_new_background_tasks=True,
        ),
        POLICY_GRACE_READONLY_ALLOWED: AuthPolicyDefinition(
            name=POLICY_GRACE_READONLY_ALLOWED,
            allowed_states=_GRACE_READONLY_ALLOWED_STATES,
            description="Grace mode may read existing local state but may not start high-risk work.",
            allows_grace_readonly=True,
            allows_high_risk_writes=False,
            allows_new_background_tasks=False,
        ),
    }
)

@dataclass(frozen=True)
class AuthPolicyDecision:
    allowed: bool
    policy: AuthPolicyName
    auth_state: str
    status_code: int | None = None
    error_code: str | None = None
    message: str | None = None
    reason_code: str | None = None


class LocalAuthorizationError(Exception):
    """Raised when a local machine-session does not satisfy a frozen auth policy."""

    def __init__(self, decision: AuthPolicyDecision) -> None:
        if decision.allowed:
            raise ValueError("LocalAuthorizationError requires a denied decision.")
        if decision.status_code is None or decision.error_code is None or decision.message is None:
            raise ValueError("Denied auth decisions must carry status, error code, and message.")

        super().__init__(decision.message)
        self.decision = decision
        self.status_code = decision.status_code
        self.error_code = decision.error_code
        self.auth_state = decision.auth_state
        self.policy = decision.policy
        self.reason_code = decision.reason_code

    def as_detail(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": str(self),
            "auth_state": self.auth_state,
            "policy": self.policy,
            "reason_code": self.reason_code,
        }

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=self.as_detail())


def _normalize_summary(summary: LocalAuthSessionSummary | None) -> LocalAuthSessionSummary:
    if summary is not None:
        return summary
    return LocalAuthSessionSummary(auth_state=DEFAULT_UNAUTHENTICATED_STATE)


def set_current_auth_summary(summary: LocalAuthSessionSummary | None) -> None:
    _CURRENT_AUTH_SUMMARY.set(summary)


def get_current_auth_summary() -> LocalAuthSessionSummary | None:
    return _CURRENT_AUTH_SUMMARY.get()


def get_auth_policy_definition(policy: AuthPolicyName) -> AuthPolicyDefinition:
    try:
        return AUTH_POLICY_MATRIX[policy]
    except KeyError as exc:
        raise ValueError(f"Unknown auth policy: {policy}") from exc


def get_auth_state_priority(auth_state: str) -> int:
    """Return the frozen Step 0 precedence rank for policy-sensitive auth states."""
    return _STATE_PRIORITY.get(auth_state, 999)


def pick_stricter_machine_session_summary(
    candidate: LocalAuthSessionSummary,
    current_truth: LocalAuthSessionSummary,
) -> LocalAuthSessionSummary:
    """Return the more restrictive summary, preferring persisted current truth on ties."""
    if get_auth_state_priority(candidate.auth_state) < get_auth_state_priority(current_truth.auth_state):
        return candidate
    return current_truth


def is_runtime_grace_state(auth_state: str) -> bool:
    return auth_state == "authenticated_grace"


def is_runtime_hard_stop_state(auth_state: str) -> bool:
    return auth_state in RUNTIME_HARD_STOP_STATES


def get_runtime_auth_failure_reason(summary: LocalAuthSessionSummary) -> str:
    return RUNTIME_FAILURE_REASONS.get(
        summary.auth_state,
        summary.denial_reason or "remote_auth_denied",
    )


def evaluate_machine_session_policy(
    summary: LocalAuthSessionSummary | None,
    *,
    policy: AuthPolicyName,
) -> AuthPolicyDecision:
    normalized = _normalize_summary(summary)
    definition = get_auth_policy_definition(policy)

    if normalized.auth_state in definition.allowed_states:
        return AuthPolicyDecision(
            allowed=True,
            policy=policy,
            auth_state=normalized.auth_state,
            reason_code=normalized.denial_reason,
        )

    if normalized.auth_state == "authenticated_grace":
        return AuthPolicyDecision(
            allowed=False,
            policy=policy,
            auth_state=normalized.auth_state,
            status_code=403,
            error_code="auth_grace_restricted",
            message="Offline grace mode is read-only and cannot start high-risk work.",
            reason_code=normalized.denial_reason or "offline_grace_restricted",
        )

    status_code = _STATE_STATUS_CODE.get(normalized.auth_state, 401)
    error_code = _STATE_ERROR_CODE.get(normalized.auth_state, "auth_state_invalid")
    message = _STATE_MESSAGE.get(
        normalized.auth_state,
        f"Local machine-session is in unsupported auth state: {normalized.auth_state}.",
    )

    return AuthPolicyDecision(
        allowed=False,
        policy=policy,
        auth_state=normalized.auth_state,
        status_code=status_code,
        error_code=error_code,
        message=message,
        reason_code=normalized.denial_reason,
    )


def enforce_machine_session_policy(
    summary: LocalAuthSessionSummary | None,
    *,
    policy: AuthPolicyName,
) -> LocalAuthSessionSummary:
    normalized = _normalize_summary(summary)
    decision = evaluate_machine_session_policy(normalized, policy=policy)
    if decision.allowed:
        return normalized
    raise LocalAuthorizationError(decision)


async def load_machine_session_summary(db: AsyncSession) -> LocalAuthSessionSummary:
    """Load the local machine-session truth without applying any business policy."""
    from services.auth_service import AuthService

    service = AuthService(db)
    summary = await service.restore_session()
    set_current_auth_summary(summary)
    return summary


async def get_machine_session_summary(
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    """FastAPI dependency wrapper for reading the current machine-session truth."""
    summary = await load_machine_session_summary(db)
    set_current_auth_summary(summary)
    return summary


async def require_machine_session_policy(
    *,
    policy: AuthPolicyName,
    db: AsyncSession,
) -> LocalAuthSessionSummary:
    summary = await load_machine_session_summary(db)
    return enforce_machine_session_policy(summary, policy=policy)


async def enforce_service_policy(
    db: AsyncSession,
    *,
    policy: AuthPolicyName,
    auth_summary: LocalAuthSessionSummary | None = None,
) -> LocalAuthSessionSummary:
    db_summary = await load_machine_session_summary(db)
    summary = (
        pick_stricter_machine_session_summary(auth_summary, db_summary)
        if auth_summary is not None
        else db_summary
    )
    return enforce_machine_session_policy(summary, policy=policy)


async def require_active_service_session(
    db: AsyncSession,
    *,
    auth_summary: LocalAuthSessionSummary | None = None,
) -> LocalAuthSessionSummary:
    return await enforce_service_policy(
        db,
        policy=POLICY_ACTIVE_REQUIRED,
        auth_summary=auth_summary,
    )


async def require_grace_readonly_service_session(
    db: AsyncSession,
    *,
    auth_summary: LocalAuthSessionSummary | None = None,
) -> LocalAuthSessionSummary:
    return await enforce_service_policy(
        db,
        policy=POLICY_GRACE_READONLY_ALLOWED,
        auth_summary=auth_summary,
    )


async def _require_machine_session_policy_as_http(
    *,
    policy: AuthPolicyName,
    db: AsyncSession,
) -> LocalAuthSessionSummary:
    try:
        summary = await require_machine_session_policy(policy=policy, db=db)
        set_current_auth_summary(summary)
        return summary
    except LocalAuthorizationError as exc:
        raise exc.to_http_exception() from exc


async def require_active_machine_session(
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    return await _require_machine_session_policy_as_http(
        policy=POLICY_ACTIVE_REQUIRED,
        db=db,
    )


async def require_grace_readonly_machine_session(
    db: AsyncSession = Depends(get_db),
) -> LocalAuthSessionSummary:
    return await _require_machine_session_policy_as_http(
        policy=POLICY_GRACE_READONLY_ALLOWED,
        db=db,
    )


ACTIVE_ROUTE_DEPENDENCIES = (Depends(require_active_machine_session),)
GRACE_READONLY_ROUTE_DEPENDENCIES = (Depends(require_grace_readonly_machine_session),)
