"""
Step 3 / PR1 tests for shared backend auth enforcement primitives.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
from types import MappingProxyType

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.auth_dependencies import (
    AUTH_POLICY_MATRIX,
    AuthPolicyDecision,
    POLICY_ACTIVE_REQUIRED,
    POLICY_GRACE_READONLY_ALLOWED,
    LocalAuthorizationError,
    enforce_machine_session_policy,
    evaluate_machine_session_policy,
    get_auth_policy_definition,
    get_auth_state_priority,
    load_machine_session_summary,
    pick_stricter_machine_session_summary,
    require_active_machine_session,
    require_grace_readonly_machine_session,
)
from models import Base, RemoteAuthSession
from schemas.auth import LocalAuthSessionSummary


@pytest_asyncio.fixture()
async def auth_policy_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _summary(
    auth_state: str,
    *,
    denial_reason: str | None = None,
) -> LocalAuthSessionSummary:
    return LocalAuthSessionSummary(
        auth_state=auth_state,
        remote_user_id="u_123" if auth_state.startswith("authenticated") else None,
        display_name="Alice" if auth_state.startswith("authenticated") else None,
        denial_reason=denial_reason,
    )


def test_auth_policy_matrix_freezes_active_and_grace_readonly_policies() -> None:
    active = get_auth_policy_definition(POLICY_ACTIVE_REQUIRED)
    grace = get_auth_policy_definition(POLICY_GRACE_READONLY_ALLOWED)

    assert isinstance(AUTH_POLICY_MATRIX, MappingProxyType)
    assert set(AUTH_POLICY_MATRIX) == {
        POLICY_ACTIVE_REQUIRED,
        POLICY_GRACE_READONLY_ALLOWED,
    }
    assert active.allowed_states == frozenset({"authenticated_active"})
    assert active.allows_high_risk_writes is True
    assert active.allows_new_background_tasks is True
    assert active.allows_grace_readonly is False
    assert grace.allowed_states == frozenset({"authenticated_active", "authenticated_grace"})
    assert grace.allows_high_risk_writes is False
    assert grace.allows_new_background_tasks is False
    assert grace.allows_grace_readonly is True

    with pytest.raises(TypeError):
        AUTH_POLICY_MATRIX[POLICY_ACTIVE_REQUIRED] = grace  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        active.description = "mutated"  # type: ignore[misc]


def test_get_auth_policy_definition_rejects_unknown_policy() -> None:
    with pytest.raises(ValueError, match="Unknown auth policy"):
        get_auth_policy_definition("public_open")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("auth_state", "policy", "expected_allowed", "expected_status", "expected_error"),
    [
        ("authenticated_active", POLICY_ACTIVE_REQUIRED, True, None, None),
        ("authenticated_active", POLICY_GRACE_READONLY_ALLOWED, True, None, None),
        (
            "authenticated_grace",
            POLICY_ACTIVE_REQUIRED,
            False,
            403,
            "auth_grace_restricted",
        ),
        ("authenticated_grace", POLICY_GRACE_READONLY_ALLOWED, True, None, None),
        ("unauthenticated", POLICY_ACTIVE_REQUIRED, False, 401, "unauthenticated"),
        ("authorizing", POLICY_ACTIVE_REQUIRED, False, 401, "authorization_in_progress"),
        ("refresh_required", POLICY_ACTIVE_REQUIRED, False, 401, "refresh_required"),
        ("expired", POLICY_ACTIVE_REQUIRED, False, 401, "expired"),
        ("revoked", POLICY_ACTIVE_REQUIRED, False, 403, "revoked"),
        ("device_mismatch", POLICY_ACTIVE_REQUIRED, False, 403, "device_mismatch"),
        ("error", POLICY_ACTIVE_REQUIRED, False, 401, "auth_error"),
    ],
)
def test_evaluate_machine_session_policy_maps_states_to_frozen_decisions(
    auth_state: str,
    policy: str,
    expected_allowed: bool,
    expected_status: int | None,
    expected_error: str | None,
) -> None:
    decision = evaluate_machine_session_policy(
        _summary(auth_state, denial_reason="network_timeout"),
        policy=policy,
    )

    assert decision.allowed is expected_allowed
    assert decision.auth_state == auth_state
    assert decision.status_code == expected_status
    assert decision.error_code == expected_error


def test_enforce_machine_session_policy_raises_rich_local_authorization_error() -> None:
    with pytest.raises(LocalAuthorizationError) as exc_info:
        enforce_machine_session_policy(
            _summary("revoked", denial_reason="disabled"),
            policy=POLICY_ACTIVE_REQUIRED,
        )

    error = exc_info.value
    assert error.status_code == 403
    assert error.error_code == "revoked"
    assert error.reason_code == "disabled"
    assert error.as_detail() == {
        "error_code": "revoked",
        "message": "Remote authorization has been revoked.",
        "auth_state": "revoked",
        "policy": POLICY_ACTIVE_REQUIRED,
        "reason_code": "disabled",
    }


def test_local_authorization_error_rejects_allowed_decision() -> None:
    with pytest.raises(ValueError, match="denied decision"):
        LocalAuthorizationError(
            evaluate_machine_session_policy(
                _summary("authenticated_active"),
                policy=POLICY_ACTIVE_REQUIRED,
            )
        )


def test_local_authorization_error_requires_denial_metadata() -> None:
    with pytest.raises(ValueError, match="Denied auth decisions must carry"):
        LocalAuthorizationError(
            AuthPolicyDecision(
                allowed=False,
                policy=POLICY_ACTIVE_REQUIRED,
                auth_state="revoked",
            )
        )


def test_unknown_auth_state_falls_back_to_invalid_state_error() -> None:
    decision = evaluate_machine_session_policy(
        _summary("mystery_state"),
        policy=POLICY_ACTIVE_REQUIRED,
    )

    assert decision.allowed is False
    assert decision.status_code == 401
    assert decision.error_code == "auth_state_invalid"
    assert "mystery_state" in (decision.message or "")


def test_get_auth_state_priority_matches_frozen_precedence() -> None:
    assert get_auth_state_priority("revoked") < get_auth_state_priority("device_mismatch")
    assert get_auth_state_priority("device_mismatch") < get_auth_state_priority("expired")
    assert get_auth_state_priority("expired") < get_auth_state_priority("unauthenticated")
    assert get_auth_state_priority("expired") < get_auth_state_priority("authenticated_grace")
    assert get_auth_state_priority("authenticated_grace") < get_auth_state_priority("authenticated_active")


def test_pick_stricter_machine_session_summary_prefers_more_restrictive_state() -> None:
    stricter = pick_stricter_machine_session_summary(
        _summary("authenticated_active"),
        _summary("revoked", denial_reason="remote_auth_revoked"),
    )

    assert stricter.auth_state == "revoked"
    assert stricter.denial_reason == "remote_auth_revoked"


@pytest.mark.asyncio
async def test_load_machine_session_summary_returns_unauthenticated_when_no_row(
    auth_policy_db_session: AsyncSession,
) -> None:
    summary = await load_machine_session_summary(auth_policy_db_session)

    assert summary.auth_state == "unauthenticated"


@pytest.mark.asyncio
async def test_load_machine_session_summary_transitions_expired_active_session(
    auth_policy_db_session: AsyncSession,
) -> None:
    auth_policy_db_session.add(
        RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            display_name="Alice",
            expires_at=datetime(2000, 1, 1, 0, 0, 0),
        )
    )
    await auth_policy_db_session.commit()

    summary = await load_machine_session_summary(auth_policy_db_session)

    assert summary.auth_state == "refresh_required"


@pytest.mark.asyncio
async def test_load_machine_session_summary_expires_grace_after_window_closes(
    auth_policy_db_session: AsyncSession,
) -> None:
    auth_policy_db_session.add(
        RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            display_name="Alice",
            expires_at=datetime(2000, 1, 1, 0, 0, 0),
            offline_grace_until=datetime(2000, 1, 1, 1, 0, 0),
            denial_reason="network_timeout",
        )
    )
    await auth_policy_db_session.commit()

    summary = await load_machine_session_summary(auth_policy_db_session)

    assert summary.auth_state == "expired"
    assert summary.denial_reason == "offline_grace_expired"


@pytest.mark.asyncio
async def test_require_active_machine_session_allows_authenticated_active(
    auth_policy_db_session: AsyncSession,
) -> None:
    now = datetime.now().replace(microsecond=0)
    auth_policy_db_session.add(
        RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            display_name="Alice",
            expires_at=now + timedelta(hours=1),
            offline_grace_until=now + timedelta(hours=2),
        )
    )
    await auth_policy_db_session.commit()

    summary = await require_active_machine_session(auth_policy_db_session)

    assert summary.auth_state == "authenticated_active"
    assert summary.remote_user_id == "u_123"


@pytest.mark.asyncio
async def test_require_grace_readonly_machine_session_allows_grace(
    auth_policy_db_session: AsyncSession,
) -> None:
    now = datetime.now().replace(microsecond=0)
    auth_policy_db_session.add(
        RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            display_name="Alice",
            expires_at=now - timedelta(minutes=10),
            offline_grace_until=now + timedelta(hours=2),
            denial_reason="network_timeout",
        )
    )
    await auth_policy_db_session.commit()

    summary = await require_grace_readonly_machine_session(auth_policy_db_session)

    assert summary.auth_state == "authenticated_grace"
    assert summary.denial_reason == "network_timeout"


@pytest.mark.asyncio
async def test_require_active_machine_session_raises_http_exception_for_grace(
    auth_policy_db_session: AsyncSession,
) -> None:
    auth_policy_db_session.add(
        RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            display_name="Alice",
            denial_reason="network_timeout",
        )
    )
    await auth_policy_db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await require_active_machine_session(auth_policy_db_session)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error_code"] == "auth_grace_restricted"
    assert exc_info.value.detail["reason_code"] == "network_timeout"
