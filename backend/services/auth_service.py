"""
本地 AuthService：把 remote auth client、secret store 与 non-secret session model 编排成 machine-session truth。
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_events import AuthEventReason, auth_event_emitter
from core.config import settings
from core.device_identity import FileDeviceIdentityStore, create_device_identity_store
from core.remote_auth_client import (
    RemoteAuthClient,
    RemoteAuthResponseError,
    RemoteAuthTransportError,
)
from core.secret_store import SecretStore, create_secret_store
from models import RemoteAuthSession
from schemas.auth import (
    AdminSessionResponse,
    AdminSessionRevokeResponse,
    AuthHealthResponse,
    AuthStatusResponse,
    LocalAuthSessionSummary,
    RemoteAuthMePayload,
    RemoteAuthSessionPayload,
    SessionDetailsResponse,
)


ACCESS_TOKEN_KEY = "remote_auth.access_token"
REFRESH_TOKEN_KEY = "remote_auth.refresh_token"


class AuthService:
    """本地认证服务编排层。"""

    def __init__(
        self,
        db: AsyncSession,
        *,
        secret_store: SecretStore | None = None,
        device_identity_store: FileDeviceIdentityStore | None = None,
        remote_client_factory: Callable[[], RemoteAuthClient] | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self.secret_store = secret_store or create_secret_store()
        self.device_identity_store = device_identity_store or create_device_identity_store()
        self.remote_client_factory = remote_client_factory or RemoteAuthClient
        self.now_fn = now_fn or (lambda: datetime.now(UTC).replace(tzinfo=None))

    async def login(
        self,
        *,
        username: str,
        password: str,
        device_id: str,
        client_version: str,
    ) -> LocalAuthSessionSummary:
        session = await self._get_or_create_session()
        resolved_device_id = self._resolve_device_id(device_id)
        session.auth_state = "authorizing"
        session.device_id = resolved_device_id
        session.denial_reason = None
        await self.db.commit()

        client = self.remote_client_factory()
        try:
            payload = await client.login(
                username=username,
                password=password,
                device_id=resolved_device_id,
                client_version=client_version,
            )
        except RemoteAuthResponseError as exc:
            previous_state = session.auth_state
            await self._apply_remote_rejection(session, exc, device_id=resolved_device_id)
            # Emit structured auth event for remote rejection
            auth_event_emitter.login_failed(
                device_id=resolved_device_id,
                reason_code=exc.error_code,
                auth_state=session.auth_state,
                error_message=str(exc),
                is_network_error=False,
            )
            self._emit_hard_deny_event(
                reason_code=exc.error_code,
                remote_user_id=session.remote_user_id,
                device_id=resolved_device_id,
                previous_state=previous_state,
            )
            raise
        except RemoteAuthTransportError as exc:
            session.auth_state = "error"
            session.denial_reason = exc.error_code
            await self.db.commit()
            # Emit structured auth event for network failure
            auth_event_emitter.login_failed(
                device_id=resolved_device_id,
                reason_code=exc.error_code,
                auth_state=session.auth_state,
                error_message=str(exc),
                is_network_error=True,
            )
            raise
        finally:
            await client.aclose()

        await self._store_tokens(payload.access_token, payload.refresh_token)
        await self._apply_success_payload(session, payload)
        # Emit structured auth event for successful login
        auth_event_emitter.login_succeeded(
            remote_user_id=payload.user.id,
            device_id=resolved_device_id,
            auth_state="authenticated_active",
        )
        return self._build_summary(session)

    async def restore_session(self) -> LocalAuthSessionSummary:
        """Restore session from persistence with lifecycle validation.

        PR2: Hardened startup restore semantics:
        - Check grace expiration and transition to expired
        - Check access token expiry and transition to refresh_required
        - Check for missing refresh token and transition to unauthenticated
        - Preserve device_id consistency
        """
        session = await self._get_session()
        if session is None:
            # Emit session restore failed event
            auth_event_emitter.session_restore_failed(
                reason_code=AuthEventReason.SESSION_NOT_FOUND,
                auth_state="unauthenticated",
            )
            return LocalAuthSessionSummary(auth_state="unauthenticated")

        now = self.now_fn()

        # PR2: Check grace expiration
        if session.auth_state == "authenticated_grace" and session.offline_grace_until and now > session.offline_grace_until:
            session.auth_state = "expired"
            session.denial_reason = "offline_grace_expired"
            await self.db.commit()
            # Emit expired event
            auth_event_emitter.expired(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                previous_state="authenticated_grace",
            )
            return self._build_summary(session)

        # PR2: Check access token expiry -> refresh_required
        if session.auth_state == "authenticated_active" and session.expires_at and now >= session.expires_at:
            session.auth_state = "refresh_required"
            await self.db.commit()
            return self._build_summary(session)

        # PR2: Check for missing refresh token (after expiry check for backward compatibility)
        refresh_token = self.secret_store.get_secret(REFRESH_TOKEN_KEY)
        if not refresh_token and session.auth_state == "refresh_required":
            session.auth_state = "unauthenticated"
            session.denial_reason = "missing_refresh_token"
            await self.db.commit()
            # Emit session restore failed event
            auth_event_emitter.session_restore_failed(
                reason_code=AuthEventReason.REFRESH_TOKEN_MISSING,
                auth_state="unauthenticated",
            )
            return self._build_summary(session)

        # PR2: Ensure device_id consistency
        persisted_device_id = self.device_identity_store.get_device_id()
        if session.device_id and persisted_device_id and session.device_id != persisted_device_id:
            # Device mismatch detected during restore
            session.auth_state = "device_mismatch"
            session.denial_reason = "device_mismatch"
            await self.db.commit()
            # Emit device mismatch event
            auth_event_emitter.device_mismatch(
                remote_user_id=session.remote_user_id or "unknown",
                expected_device_id=session.device_id,
                actual_device_id=persisted_device_id,
            )
            return self._build_summary(session)

        # Session restored successfully
        auth_event_emitter.session_restored(
            remote_user_id=session.remote_user_id,
            device_id=session.device_id,
            auth_state=session.auth_state,
        )
        return self._build_summary(session)

    async def logout(self) -> LocalAuthSessionSummary:
        """Logout and clear session state."""
        session = await self._get_session()
        if session is None:
            return LocalAuthSessionSummary(auth_state="unauthenticated")

        remote_user_id = session.remote_user_id
        device_id = session.device_id

        # Clear session state
        session.auth_state = "unauthenticated"
        session.remote_user_id = None
        session.display_name = None
        session.license_status = None
        session.entitlements_snapshot = None
        session.expires_at = None
        session.last_verified_at = None
        session.offline_grace_until = None
        session.denial_reason = None
        await self.db.commit()

        # Clear tokens
        self.secret_store.delete_secret(ACCESS_TOKEN_KEY)
        self.secret_store.delete_secret(REFRESH_TOKEN_KEY)

        # Emit logout completed event
        auth_event_emitter.logout_completed(
            remote_user_id=remote_user_id,
            device_id=device_id,
        )

        return self._build_summary(session)

    async def get_session_summary(self) -> LocalAuthSessionSummary:
        """Return the persisted machine-session summary without mutating state."""
        session = await self._get_session()
        if session is None:
            return LocalAuthSessionSummary(
                auth_state="unauthenticated",
                device_id=self.device_identity_store.get_device_id(),
            )
        return self._build_summary(session)

    async def get_status(self) -> AuthStatusResponse:
        """Return a detailed status view derived from the local machine session."""
        summary = await self.restore_session()
        token_expires_in_seconds = self._seconds_until(summary.expires_at)
        grace_remaining_seconds = self._seconds_until(summary.offline_grace_until)
        is_active = summary.auth_state == "authenticated_active"
        is_grace = summary.auth_state == "authenticated_grace"
        is_authenticated = is_active or is_grace
        can_read_local_data = is_authenticated
        can_run_protected_actions = is_active
        can_run_background_tasks = is_active
        requires_reauth = summary.auth_state in {
            "unauthenticated",
            "expired",
            "revoked",
            "device_mismatch",
            "error",
        }
        return AuthStatusResponse(
            auth_state=summary.auth_state,
            remote_user_id=summary.remote_user_id,
            display_name=summary.display_name,
            license_status=summary.license_status,
            device_id=summary.device_id,
            denial_reason=summary.denial_reason,
            expires_at=summary.expires_at,
            last_verified_at=summary.last_verified_at,
            offline_grace_until=summary.offline_grace_until,
            token_expires_in_seconds=token_expires_in_seconds,
            grace_remaining_seconds=grace_remaining_seconds,
            is_authenticated=is_authenticated,
            is_active=is_active,
            is_grace=is_grace,
            requires_reauth=requires_reauth,
            can_read_local_data=can_read_local_data,
            can_run_protected_actions=can_run_protected_actions,
            can_run_background_tasks=can_run_background_tasks,
        )

    async def get_health(self) -> AuthHealthResponse:
        """Return a health-oriented view of the local auth session."""
        status = await self.get_status()
        has_access_token = self.secret_store.get_secret(ACCESS_TOKEN_KEY) is not None
        has_refresh_token = self.secret_store.get_secret(REFRESH_TOKEN_KEY) is not None
        if status.is_active:
            overall_status = "healthy"
        elif status.is_grace:
            overall_status = "degraded"
        elif status.auth_state == "authorizing":
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return AuthHealthResponse(
            status=overall_status,
            auth_state=status.auth_state,
            denial_reason=status.denial_reason,
            has_access_token=has_access_token,
            has_refresh_token=has_refresh_token,
            token_expires_in_seconds=status.token_expires_in_seconds,
            grace_remaining_seconds=status.grace_remaining_seconds,
            last_verified_at=status.last_verified_at,
            can_read_local_data=status.can_read_local_data,
            can_run_protected_actions=status.can_run_protected_actions,
            can_run_background_tasks=status.can_run_background_tasks,
        )

    async def get_session_details(self) -> SessionDetailsResponse:
        """Return the persisted session record plus secret-presence metadata."""
        session = await self._get_session()
        has_access_token = self.secret_store.get_secret(ACCESS_TOKEN_KEY) is not None
        has_refresh_token = self.secret_store.get_secret(REFRESH_TOKEN_KEY) is not None
        if session is None:
            return SessionDetailsResponse(
                auth_state="unauthenticated",
                device_id=self.device_identity_store.get_device_id(),
                has_access_token=has_access_token,
                has_refresh_token=has_refresh_token,
            )

        summary = self._build_summary(session)
        return SessionDetailsResponse(
            session_id=session.id,
            auth_state=summary.auth_state,
            remote_user_id=summary.remote_user_id,
            display_name=summary.display_name,
            license_status=summary.license_status,
            entitlements=summary.entitlements,
            expires_at=summary.expires_at,
            last_verified_at=summary.last_verified_at,
            offline_grace_until=summary.offline_grace_until,
            denial_reason=summary.denial_reason,
            device_id=summary.device_id,
            has_access_token=has_access_token,
            has_refresh_token=has_refresh_token,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def list_admin_sessions(self) -> list[AdminSessionResponse]:
        """List persisted local auth sessions for the admin surface."""
        result = await self.db.execute(
            select(RemoteAuthSession).order_by(RemoteAuthSession.updated_at.desc(), RemoteAuthSession.id.desc())
        )
        sessions = list(result.scalars().all())
        current_session_id = self._resolve_current_admin_session_id(sessions, allow_single_fallback=True)
        has_access_token = self.secret_store.get_secret(ACCESS_TOKEN_KEY) is not None
        has_refresh_token = self.secret_store.get_secret(REFRESH_TOKEN_KEY) is not None

        responses: list[AdminSessionResponse] = []
        for session in sessions:
            responses.append(
                AdminSessionResponse(
                    session_id=session.id,
                    auth_state=session.auth_state,
                    remote_user_id=session.remote_user_id,
                    display_name=session.display_name,
                    license_status=session.license_status,
                    device_id=session.device_id,
                    denial_reason=session.denial_reason,
                    expires_at=session.expires_at,
                    last_verified_at=session.last_verified_at,
                    offline_grace_until=session.offline_grace_until,
                    has_access_token=has_access_token if session.id == current_session_id else False,
                    has_refresh_token=has_refresh_token if session.id == current_session_id else False,
                    is_current_session=session.id == current_session_id,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                )
            )
        return responses

    async def revoke_admin_session(self, session_id: int) -> AdminSessionRevokeResponse:
        """Revoke a persisted local auth session and clear tokens when it is current."""
        result = await self.db.execute(
            select(RemoteAuthSession).where(RemoteAuthSession.id == session_id)
        )
        session = result.scalars().first()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        current_session_id = self._resolve_current_admin_session_id([session], allow_single_fallback=False)
        is_current_session = current_session_id == session.id
        previous_state = session.auth_state
        session.auth_state = "revoked"
        session.denial_reason = "admin_revoked"
        await self.db.commit()

        if is_current_session:
            self.secret_store.delete_secret(ACCESS_TOKEN_KEY)
            self.secret_store.delete_secret(REFRESH_TOKEN_KEY)
        auth_event_emitter.revoked(
            remote_user_id=session.remote_user_id or "unknown",
            device_id=session.device_id or "unknown",
            previous_state=previous_state,
            reason_code="admin_revoked",
        )

        revoked_session = AdminSessionResponse(
            session_id=session.id,
            auth_state=session.auth_state,
            remote_user_id=session.remote_user_id,
            display_name=session.display_name,
            license_status=session.license_status,
            device_id=session.device_id,
            denial_reason=session.denial_reason,
            expires_at=session.expires_at,
            last_verified_at=session.last_verified_at,
            offline_grace_until=session.offline_grace_until,
            has_access_token=False if is_current_session else self.secret_store.get_secret(ACCESS_TOKEN_KEY) is not None,
            has_refresh_token=False if is_current_session else self.secret_store.get_secret(REFRESH_TOKEN_KEY) is not None,
            is_current_session=is_current_session,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        return AdminSessionRevokeResponse(
            success=True,
            revoked_session=revoked_session,
            current_session=await self.get_session_summary(),
        )

    async def refresh_if_needed(
        self,
        *,
        force: bool = False,
        client_version: str | None = None,
        **kwargs,
    ) -> LocalAuthSessionSummary:
        """Refresh access token if needed or forced.

        PR2: Hardened refresh semantics:
        - Check for refresh token before attempting
        - Update session state atomically with token storage
        - Grace state can attempt refresh to restore active
        """
        session = await self._get_or_create_session()
        now = self.now_fn()
        proactive_refresh_deadline = now + timedelta(
            minutes=settings.REMOTE_AUTH_PROACTIVE_REFRESH_MINUTES
        )
        should_attempt_proactive_refresh = (
            session.auth_state == "authenticated_active"
            and session.expires_at is not None
            and session.expires_at <= proactive_refresh_deadline
        )

        # Only refresh if in appropriate states or forced
        if not force and session.auth_state not in {
            "refresh_required",
            "authenticated_grace",  # PR4: Grace can attempt refresh
        } and not should_attempt_proactive_refresh:
            return self._build_summary(session)

        refresh_token = self.secret_store.get_secret(REFRESH_TOKEN_KEY)
        if not refresh_token:
            if session.auth_state == "authenticated_grace":
                auth_event_emitter.refresh_failed(
                    remote_user_id=session.remote_user_id,
                    device_id=session.device_id,
                    reason_code=AuthEventReason.REFRESH_TOKEN_MISSING,
                    auth_state=session.auth_state,
                    is_network_error=False,
                    is_remote_rejection=False,
                )
                return self._build_summary(session)

            session.auth_state = "unauthenticated"
            session.denial_reason = "missing_refresh_token"
            await self.db.commit()
            # Emit refresh failed event
            auth_event_emitter.refresh_failed(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                reason_code=AuthEventReason.REFRESH_TOKEN_MISSING,
                auth_state=session.auth_state,
                is_network_error=False,
                is_remote_rejection=False,
            )
            return self._build_summary(session)

        resolved_device_id = self._resolve_device_id(session.device_id)
        session.device_id = resolved_device_id
        await self.db.commit()
        resolved_client_version = client_version or settings.APP_VERSION

        # Emit refresh started event
        auth_event_emitter.refresh_started(
            remote_user_id=session.remote_user_id,
            device_id=session.device_id,
        )

        client = self.remote_client_factory()
        try:
            payload = await client.refresh(
                refresh_token=refresh_token,
                device_id=resolved_device_id,
                client_version=resolved_client_version,
            )
        except RemoteAuthResponseError as exc:
            previous_state = session.auth_state
            await self._apply_remote_rejection(session, exc, device_id=session.device_id)
            # Emit refresh failed event for remote rejection
            auth_event_emitter.refresh_failed(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                reason_code=exc.error_code,
                auth_state=session.auth_state,
                error_message=str(exc),
                is_network_error=False,
                is_remote_rejection=True,
            )
            self._emit_hard_deny_event(
                reason_code=exc.error_code,
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                previous_state=previous_state,
            )
            raise
        except RemoteAuthTransportError as exc:
            previous_state = session.auth_state
            grace_window_still_valid = (
                session.offline_grace_until is None
                or session.offline_grace_until >= now
            )

            # PR4: Network failure - enter/preserve grace when still inside grace window.
            if session.auth_state in {"authenticated_active", "refresh_required", "authenticated_grace"} and grace_window_still_valid:
                session.auth_state = "authenticated_grace"
                if session.offline_grace_until is None:
                    session.offline_grace_until = now + timedelta(
                        hours=settings.REMOTE_AUTH_DEFAULT_OFFLINE_GRACE_HOURS
                    )
                session.denial_reason = exc.error_code
                await self.db.commit()
                grace_remaining_minutes = max(
                    int((session.offline_grace_until - now).total_seconds() // 60),
                    0,
                ) if session.offline_grace_until else settings.REMOTE_AUTH_DEFAULT_OFFLINE_GRACE_HOURS * 60
                # Emit offline grace used event
                auth_event_emitter.offline_grace_used(
                    remote_user_id=session.remote_user_id,
                    device_id=session.device_id,
                    grace_remaining_minutes=grace_remaining_minutes,
                )
            else:
                session.auth_state = "expired"
                session.denial_reason = exc.error_code
                await self.db.commit()
                auth_event_emitter.expired(
                    remote_user_id=session.remote_user_id,
                    device_id=session.device_id,
                    previous_state=previous_state,
                )
            # Emit refresh failed event for network error
            auth_event_emitter.refresh_failed(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                reason_code=exc.error_code,
                auth_state=session.auth_state,
                error_message=str(exc),
                is_network_error=True,
                is_remote_rejection=False,
            )
            # Return grace state instead of raising (PR4 behavior)
            return self._build_summary(session)

        # Success: store new tokens and update session
        await self._store_tokens(payload.access_token, payload.refresh_token)
        await self._apply_success_payload(session, payload)

        # Emit refresh succeeded event
        auth_event_emitter.refresh_succeeded(
            remote_user_id=payload.user.id,
            device_id=session.device_id or "unknown",
            auth_state="authenticated_active",
        )

        return self._build_summary(session)

    async def get_me(self) -> RemoteAuthMePayload:
        """Call remote /me endpoint for validation and user info.

        PR2: Updates last_verified_at on success to track validation freshness.
        """
        session = await self._get_or_create_session()
        access_token = self.secret_store.get_secret(ACCESS_TOKEN_KEY)
        if not access_token:
            # Emit me validation failed event
            auth_event_emitter.me_validation_failed(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                reason_code=AuthEventReason.SESSION_NOT_FOUND,
                auth_state=session.auth_state,
                error_message="缺少 access token，无法调用 /me",
            )
            raise ValueError("缺少 access token，无法调用 /me")

        client = self.remote_client_factory()
        try:
            payload = await client.me(access_token=access_token)
        except RemoteAuthResponseError as exc:
            previous_state = session.auth_state
            await self._apply_remote_rejection(session, exc, device_id=session.device_id)
            # Emit me validation failed event
            auth_event_emitter.me_validation_failed(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                reason_code=exc.error_code,
                auth_state=session.auth_state,
                error_message=str(exc),
            )
            self._emit_hard_deny_event(
                reason_code=exc.error_code,
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                previous_state=previous_state,
            )
            raise
        except RemoteAuthTransportError as exc:
            # Emit me validation failed event for network error
            auth_event_emitter.me_validation_failed(
                remote_user_id=session.remote_user_id,
                device_id=session.device_id,
                reason_code=AuthEventReason.NETWORK_ERROR,
                auth_state=session.auth_state,
                error_message=str(exc),
            )
            raise
        finally:
            await client.aclose()

        session.remote_user_id = payload.user.id
        session.display_name = payload.user.display_name or payload.user.username
        session.license_status = payload.license_status
        session.entitlements_snapshot = json.dumps(payload.entitlements, ensure_ascii=False)
        session.device_id = self.device_identity_store.set_device_id(payload.device_id)
        session.last_verified_at = self.now_fn()
        session.offline_grace_until = payload.offline_grace_until
        await self.db.commit()

        return payload

    async def _get_session(self) -> RemoteAuthSession | None:
        current_device_id = self.device_identity_store.get_device_id()
        if current_device_id:
            result = await self.db.execute(
                select(RemoteAuthSession)
                .where(RemoteAuthSession.device_id == current_device_id)
                .order_by(RemoteAuthSession.updated_at.desc(), RemoteAuthSession.id.desc())
                .limit(1)
            )
            current = result.scalars().first()
            if current is not None:
                return current

        result = await self.db.execute(
            select(RemoteAuthSession).order_by(RemoteAuthSession.id.asc()).limit(1)
        )
        return result.scalars().first()

    async def _get_or_create_session(self) -> RemoteAuthSession:
        session = await self._get_session()
        if session is not None:
            return session

        session = RemoteAuthSession(auth_state="unauthenticated")
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _apply_success_payload(
        self,
        session: RemoteAuthSession,
        payload: RemoteAuthSessionPayload,
    ) -> None:
        session.auth_state = "authenticated_active"
        session.remote_user_id = payload.user.id
        session.display_name = payload.user.display_name or payload.user.username
        session.license_status = payload.license_status
        session.entitlements_snapshot = json.dumps(payload.entitlements, ensure_ascii=False)
        session.expires_at = payload.expires_at
        session.last_verified_at = self.now_fn()
        session.offline_grace_until = (
            payload.offline_grace_until
            or self.now_fn() + timedelta(hours=settings.REMOTE_AUTH_DEFAULT_OFFLINE_GRACE_HOURS)
        )
        session.denial_reason = None
        session.device_id = self.device_identity_store.set_device_id(payload.device_id)
        await self.db.commit()

    async def _apply_remote_rejection(
        self,
        session: RemoteAuthSession,
        exc: RemoteAuthResponseError,
        *,
        device_id: str | None,
    ) -> None:
        if exc.error_code == "device_mismatch":
            session.auth_state = "device_mismatch"
        elif exc.error_code in {"revoked", "disabled"}:
            session.auth_state = "revoked"
        elif exc.error_code == "token_expired":
            session.auth_state = "expired"
        else:
            session.auth_state = "error"
        session.denial_reason = exc.error_code
        if device_id:
            session.device_id = device_id
        await self.db.commit()

    def _emit_hard_deny_event(
        self,
        *,
        reason_code: str,
        remote_user_id: str | None,
        device_id: str | None,
        previous_state: str,
    ) -> None:
        """Emit the canonical hard-deny event for revoked/device mismatch states."""
        if reason_code in {"revoked", "disabled"}:
            auth_event_emitter.revoked(
                remote_user_id=remote_user_id or "unknown",
                device_id=device_id or "unknown",
                previous_state=previous_state,
                reason_code=reason_code,
            )
            return

        if reason_code == "device_mismatch":
            auth_event_emitter.device_mismatch(
                remote_user_id=remote_user_id or "unknown",
                expected_device_id=device_id or "unknown",
                actual_device_id=self.device_identity_store.get_device_id() or "unknown",
                previous_state=previous_state,
            )

    def _build_summary(self, session: RemoteAuthSession) -> LocalAuthSessionSummary:
        entitlements: list[str] = []
        if session.entitlements_snapshot:
            try:
                parsed = json.loads(session.entitlements_snapshot)
                if isinstance(parsed, list):
                    entitlements = [str(item) for item in parsed]
            except ValueError:
                entitlements = []

        return LocalAuthSessionSummary(
            auth_state=session.auth_state,
            remote_user_id=session.remote_user_id,
            display_name=session.display_name,
            license_status=session.license_status,
            entitlements=entitlements,
            expires_at=session.expires_at,
            last_verified_at=session.last_verified_at,
            offline_grace_until=session.offline_grace_until,
            denial_reason=session.denial_reason,
            device_id=session.device_id or self.device_identity_store.get_device_id(),
        )

    def _seconds_until(self, target: datetime | None) -> int | None:
        """Return non-negative remaining seconds until target."""
        if target is None:
            return None
        delta = int((target - self.now_fn()).total_seconds())
        return max(delta, 0)

    def _resolve_current_admin_session_id(
        self,
        sessions: list[RemoteAuthSession],
        *,
        allow_single_fallback: bool,
    ) -> int | None:
        """Best-effort identification of the current machine session row."""
        current_device_id = self.device_identity_store.get_device_id()
        if current_device_id:
            for session in sessions:
                if session.device_id == current_device_id:
                    return session.id
        return sessions[0].id if allow_single_fallback and len(sessions) == 1 else None

    async def _store_tokens(self, access_token: str, refresh_token: str) -> None:
        """Store tokens atomically to ensure consistency during rotation.

        PR2: Token rotation must be atomic - both tokens updated together
        to avoid leaving session with stale refresh material.
        """
        self.secret_store.set_secrets({
            ACCESS_TOKEN_KEY: access_token,
            REFRESH_TOKEN_KEY: refresh_token,
        })

    def _resolve_device_id(self, seed: str | None = None) -> str:
        return self.device_identity_store.get_or_create(seed)
