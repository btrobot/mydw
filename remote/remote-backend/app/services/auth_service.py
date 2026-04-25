from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.observability import get_request_context
from app.core.security import (
    fingerprint_token,
    hash_account_password,
    hash_refresh_token,
    issue_token,
    verify_account_password,
)
from app.models import Device, License, User, UserCredential, UserDevice, UserEntitlement
from app.repositories.auth import AuthRepository
from app.services.control_service import AuthorizationPolicyService
from app.utils.pagination import resolve_page_metadata
from app.utils.time import utc_now_naive
from app.schemas.auth import (
    AuthSuccessResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    SelfActivityListResponse,
    SelfActivityResponse,
    SelfDeviceListResponse,
    SelfDeviceResponse,
    SelfMeResponse,
    SelfSessionRevokeResponse,
    SelfSessionListResponse,
    SelfSessionResponse,
    SelfUserIdentity,
    UserIdentity,
)

class AuthServiceError(Exception):
    def __init__(self, error_code: str, message: str, *, status_code: int, details: dict | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


SELF_ACTIVITY_EVENT_MAP = {
    'auth_login_succeeded': 'login_succeeded',
    'auth_login_failed': 'login_failed',
    'auth_refresh_succeeded': 'session_refreshed',
    'auth_logout_succeeded': 'session_revoked',
    'self_session_revoked': 'session_revoked',
    'authorization_device_rebound': 'device_bound',
    'authorization_device_unbound': 'device_unbound',
}

SELF_ACTIVITY_SUMMARY_MAP = {
    'login_succeeded': 'Signed in successfully',
    'login_failed': 'Sign-in attempt failed',
    'session_refreshed': 'Session was refreshed',
    'session_revoked': 'Session was revoked',
    'device_bound': 'Device was bound',
    'device_unbound': 'Device was unbound',
}


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository
        self.settings = get_settings()
        self.policy = AuthorizationPolicyService()

    def ensure_seed_user(self) -> None:
        if self.repository.get_user_by_username('alice') is not None:
            return
        user = User(username='alice', display_name='Alice', email='alice@example.com', status='active', tenant_id='tenant_1')
        self.repository.db.add(user)
        self.repository.db.flush()
        password_record = hash_account_password('secret')
        self.repository.db.add(
            UserCredential(
                user_id=user.id,
                password_hash=password_record.value,
                password_algo=password_record.algorithm,
            )
        )
        self.repository.db.add(
            License(
                user_id=user.id,
                license_status='active',
                plan_code='starter',
                starts_at=utc_now_naive(),
                expires_at=utc_now_naive() + timedelta(days=30),
                offline_grace_hours=self.settings.DEFAULT_OFFLINE_GRACE_HOURS,
            )
        )
        self.repository.db.add_all([
            UserEntitlement(user_id=user.id, entitlement='dashboard:view', source='seed'),
            UserEntitlement(user_id=user.id, entitlement='publish:run', source='seed'),
        ])
        self.repository.db.commit()

    def login(self, payload: LoginRequest, *, client_ip: str) -> AuthSuccessResponse:
        user = self.repository.get_user_by_username(payload.username)
        if user is None:
            self._raise_with_audit(
                event_type='auth_login_failed',
                error_code='invalid_credentials',
                message='Invalid username or password',
                status_code=401,
                target_device_id=payload.device_id,
                details={'reason': 'invalid_credentials'},
            )

        credential = self.repository.get_user_credential(user.id)
        verification = (
            verify_account_password(payload.password, credential.password_hash, password_algo=credential.password_algo)
            if credential is not None
            else None
        )
        if credential is None or verification is None or not verification.verified:
            self._raise_with_audit(
                event_type='auth_login_failed',
                error_code='invalid_credentials',
                message='Invalid username or password',
                status_code=401,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                details={'reason': 'invalid_credentials'},
            )

        license_record = self.repository.get_license(user.id)
        if license_record is None:
            self._raise_with_audit(
                event_type='auth_login_failed',
                error_code='disabled',
                message='User or license disabled',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                details={'reason': 'disabled'},
            )

        self._assert_user_allowed(
            user,
            license_record,
            client_version=payload.client_version,
            failure_event='auth_login_failed',
            target_device_id=payload.device_id,
        )
        if verification.needs_rehash:
            self._maybe_upgrade_password_hash(credential, payload.password)
        device, binding = self._ensure_allowed_device(user, payload.device_id, payload.client_version, failure_event='auth_login_failed')
        access_token = issue_token('access')
        refresh_token = issue_token('refresh')
        expires_at = utc_now_naive() + timedelta(seconds=self.settings.ACCESS_TOKEN_TTL_SECONDS)
        session = self.repository.create_session(
            session_id=issue_token('sess'),
            user_id=user.id,
            device_pk=device.id,
            access_token_hash=fingerprint_token(access_token),
            expires_at=expires_at,
        )
        self.repository.create_refresh_token(
            session_pk=session.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=utc_now_naive() + timedelta(seconds=self.settings.REFRESH_TOKEN_TTL_SECONDS),
        )
        self.repository.touch_binding(binding)
        self.repository.touch_device(device, client_version=payload.client_version)
        entitlements = self.repository.get_entitlements(user.id)
        response = self._build_auth_success(
            user=user,
            license_record=license_record,
            entitlements=entitlements,
            device=device,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        self._write_audit(
            'auth_login_succeeded',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'client_ip': client_ip},
        )
        self.repository.db.commit()
        return response

    def refresh(self, payload: RefreshRequest, *, client_ip: str) -> AuthSuccessResponse:
        refresh_token = self.repository.get_refresh_token_with_session(payload.refresh_token)
        if refresh_token is None:
            self._raise_with_audit(
                event_type='auth_refresh_failed',
                error_code='token_expired',
                message='Refresh token expired or invalid',
                status_code=401,
                target_device_id=payload.device_id,
                details={'reason': 'token_expired'},
            )

        session = refresh_token.session
        assert session is not None
        user = session.user
        device = session.device
        assert user is not None
        assert device is not None

        if refresh_token.revoked_at is not None or session.revoked_at is not None:
            self._raise_with_audit(
                event_type='auth_refresh_failed',
                error_code='revoked',
                message='Remote authorization revoked',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                target_session_id=session.session_id,
                details={'reason': 'revoked'},
            )
        if refresh_token.expires_at <= utc_now_naive():
            self._raise_with_audit(
                event_type='auth_refresh_failed',
                error_code='token_expired',
                message='Refresh token expired or invalid',
                status_code=401,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                target_session_id=session.session_id,
                details={'reason': 'token_expired'},
            )

        license_record = self.repository.get_license(user.id)
        if license_record is None:
            self._raise_with_audit(
                event_type='auth_refresh_failed',
                error_code='disabled',
                message='User or license disabled',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                target_session_id=session.session_id,
                details={'reason': 'disabled'},
            )

        self._assert_user_allowed(
            user,
            license_record,
            client_version=payload.client_version,
            failure_event='auth_refresh_failed',
            target_device_id=payload.device_id,
            target_session_id=session.session_id,
        )
        binding = self.repository.get_active_binding_for_user(user.id)
        if binding is None or binding.device is None or binding.device.device_id != payload.device_id or device.device_id != payload.device_id:
            self._raise_device_mismatch(
                failure_event='auth_refresh_failed',
                device_id=payload.device_id,
                target_user_id=str(user.id),
                target_session_id=session.session_id,
            )
        self._assert_device_allowed(
            binding.device,
            failure_event='auth_refresh_failed',
            device_id=payload.device_id,
            target_user_id=str(user.id),
            target_session_id=session.session_id,
        )

        access_token = issue_token('access')
        next_refresh_token = issue_token('refresh')
        expires_at = utc_now_naive() + timedelta(seconds=self.settings.ACCESS_TOKEN_TTL_SECONDS)
        self.repository.rotate_refresh_token(
            source=refresh_token,
            new_token_hash=hash_refresh_token(next_refresh_token),
            expires_at=utc_now_naive() + timedelta(seconds=self.settings.REFRESH_TOKEN_TTL_SECONDS),
        )
        self.repository.update_session_access(
            session,
            access_token_hash=fingerprint_token(access_token),
            expires_at=expires_at,
        )
        self.repository.touch_binding(binding)
        self.repository.touch_device(device, client_version=payload.client_version)
        entitlements = self.repository.get_entitlements(user.id)
        response = self._build_auth_success(
            user=user,
            license_record=license_record,
            entitlements=entitlements,
            device=device,
            access_token=access_token,
            refresh_token=next_refresh_token,
            expires_at=expires_at,
        )
        self._write_audit(
            'auth_refresh_succeeded',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'client_ip': client_ip},
        )
        self.repository.db.commit()
        return response

    def logout(self, payload: LogoutRequest) -> LogoutResponse:
        refresh_token = self.repository.get_refresh_token_with_session(payload.refresh_token)
        if refresh_token is None:
            self._raise_with_audit(
                event_type='auth_logout_failed',
                error_code='token_expired',
                message='Refresh token expired or invalid',
                status_code=401,
                target_device_id=payload.device_id,
                details={'reason': 'token_expired'},
            )

        session = refresh_token.session
        assert session is not None
        user = session.user
        device = session.device
        assert user is not None
        assert device is not None

        if refresh_token.revoked_at is not None or session.revoked_at is not None:
            self._raise_with_audit(
                event_type='auth_logout_failed',
                error_code='revoked',
                message='Remote authorization revoked',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                target_session_id=session.session_id,
                details={'reason': 'revoked'},
            )
        if refresh_token.expires_at <= utc_now_naive():
            self._raise_with_audit(
                event_type='auth_logout_failed',
                error_code='token_expired',
                message='Refresh token expired or invalid',
                status_code=401,
                target_user_id=str(user.id),
                target_device_id=payload.device_id,
                target_session_id=session.session_id,
                details={'reason': 'token_expired'},
            )

        binding = self.repository.get_active_binding_for_user(user.id)
        if binding is None or binding.device is None or binding.device.device_id != payload.device_id or device.device_id != payload.device_id:
            self._raise_device_mismatch(
                failure_event='auth_logout_failed',
                device_id=payload.device_id,
                target_user_id=str(user.id),
                target_session_id=session.session_id,
            )
        self._assert_device_allowed(
            binding.device,
            failure_event='auth_logout_failed',
            device_id=payload.device_id,
            target_user_id=str(user.id),
            target_session_id=session.session_id,
        )

        self.repository.revoke_refresh_token(refresh_token, reason='logout')
        self.repository.revoke_refresh_tokens_for_session(session.id, reason='logout')
        self.repository.revoke_session(session, reason='logout')
        self.repository.touch_device(device)
        self._write_audit(
            'auth_logout_succeeded',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'reason': 'logout'},
        )
        self.repository.db.commit()
        return LogoutResponse(success=True)

    def me(self, access_token: str) -> MeResponse:
        session, user, device, license_record, binding, entitlements = self._resolve_self_context(
            access_token,
            failure_event='auth_me_failed',
        )
        self._touch_authenticated_context(session=session, binding=binding, device=device)
        response = self._build_me_response(
            user=user,
            license_record=license_record,
            entitlements=entitlements,
            device=device,
        )
        self._write_audit(
            'auth_me_succeeded',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'reason': 'me'},
        )
        self.repository.db.commit()
        return response

    def self_me(self, access_token: str) -> SelfMeResponse:
        session, user, device, license_record, binding, entitlements = self._resolve_self_context(
            access_token,
            failure_event='auth_self_me_failed',
        )
        self._touch_authenticated_context(session=session, binding=binding, device=device)
        response = SelfMeResponse(
            user=self._build_self_user_identity(user),
            license_status=license_record.license_status,
            entitlements=entitlements,
            device_id=device.device_id,
            device_status=device.status,
            offline_grace_until=self.policy.offline_grace_until(license_record),
            minimum_supported_version=self.policy.minimum_supported_version,
        )
        self._write_audit(
            'auth_self_me_viewed',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'reason': 'self_me'},
        )
        self.repository.db.commit()
        return response

    def list_self_devices(self, access_token: str, *, limit: int = 20, offset: int = 0) -> SelfDeviceListResponse:
        session, user, device, _license_record, binding, _entitlements = self._resolve_self_context(
            access_token,
            failure_event='auth_self_devices_failed',
        )
        self._touch_authenticated_context(session=session, binding=binding, device=device)
        latest_by_device: dict[str, UserDevice] = {}
        for row in self.repository.list_bindings_for_user(user.id):
            if row.device is None:
                continue
            current = latest_by_device.get(row.device.device_id)
            if current is None or row.id > current.id:
                latest_by_device[row.device.device_id] = row

        ordered = sorted(
            latest_by_device.values(),
            key=lambda item: (
                item.device.device_id != device.device_id,
                -(item.device.last_seen_at.timestamp() if item.device and item.device.last_seen_at else 0),
                -item.id,
            ),
        )
        paged = ordered[offset: offset + limit]
        items = [
            SelfDeviceResponse(
                device_id=row.device.device_id,
                device_status=row.device.status,
                client_version=row.device.client_version,
                first_bound_at=row.bound_at,
                last_seen_at=row.device.last_seen_at,
                is_current=row.device.device_id == device.device_id,
            )
            for row in paged
            if row.device is not None
        ]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'auth_self_devices_listed',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'limit': limit, 'offset': offset, 'count': len(items), 'total': len(ordered)},
        )
        self.repository.db.commit()
        return SelfDeviceListResponse(items=items, total=len(ordered), page=page, page_size=page_size)

    def list_self_sessions(self, access_token: str, *, limit: int = 20, offset: int = 0) -> SelfSessionListResponse:
        session, user, device, _license_record, binding, _entitlements = self._resolve_self_context(
            access_token,
            failure_event='auth_self_sessions_failed',
        )
        self._touch_authenticated_context(session=session, binding=binding, device=device)
        ordered = sorted(
            self.repository.list_sessions_for_user(user.id),
            key=lambda item: (
                item.session_id != session.session_id,
                -(item.last_seen_at.timestamp() if item.last_seen_at else 0),
                -item.id,
            ),
        )
        paged = ordered[offset: offset + limit]
        items = [
            SelfSessionResponse(
                session_id=row.session_id,
                device_id=row.device.device_id if row.device is not None else None,
                auth_state=row.auth_state,
                issued_at=row.issued_at,
                expires_at=row.expires_at,
                last_seen_at=row.last_seen_at,
                is_current=row.session_id == session.session_id,
            )
            for row in paged
        ]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'auth_self_sessions_listed',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'limit': limit, 'offset': offset, 'count': len(items), 'total': len(ordered)},
        )
        self.repository.db.commit()
        return SelfSessionListResponse(items=items, total=len(ordered), page=page, page_size=page_size)

    def list_self_activity(self, access_token: str, *, limit: int = 20, offset: int = 0) -> SelfActivityListResponse:
        session, user, device, _license_record, binding, _entitlements = self._resolve_self_context(
            access_token,
            failure_event='auth_self_activity_failed',
        )
        self._touch_authenticated_context(session=session, binding=binding, device=device)
        raw_event_types = set(SELF_ACTIVITY_EVENT_MAP.keys())
        total = self.repository.count_audit_logs_for_user(user.id, event_types=raw_event_types)
        logs = self.repository.list_audit_logs_for_user(user.id, event_types=raw_event_types, limit=limit, offset=offset)
        items = [self._build_self_activity_response(row) for row in logs]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'auth_self_activity_listed',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'limit': limit, 'offset': offset, 'count': len(items), 'total': total},
        )
        self.repository.db.commit()
        return SelfActivityListResponse(items=items, total=total, page=page, page_size=page_size)

    def revoke_self_session(self, access_token: str, session_id: str) -> SelfSessionRevokeResponse:
        current_session, user, device, _license_record, binding, _entitlements = self._resolve_self_context(
            access_token,
            failure_event='auth_self_session_revoke_failed',
        )
        self._touch_authenticated_context(session=current_session, binding=binding, device=device)

        target_session = self.repository.get_session_by_session_id(session_id)
        if (
            target_session is None
            or target_session.user is None
            or target_session.user.id != user.id
        ):
            self._write_audit(
                'auth_self_session_revoke_masked',
                target_user_id=str(user.id),
                target_device_id=device.device_id,
                target_session_id=session_id,
                details={'reason': 'not_found_masked'},
            )
            self.repository.db.commit()
            raise AuthServiceError(
                'not_found',
                'Requested resource was not found.',
                status_code=404,
                details={'session_id': session_id},
            )

        already_revoked = target_session.revoked_at is not None or target_session.auth_state.startswith('revoked:')
        if not already_revoked:
            self.repository.revoke_session(target_session, reason='self_session_revoked')
            self.repository.revoke_refresh_tokens_for_session(target_session.id, reason='self_session_revoked')

        self._write_audit(
            'self_session_revoked',
            actor_type='user',
            target_user_id=str(user.id),
            target_device_id=target_session.device.device_id if target_session.device is not None else None,
            target_session_id=target_session.session_id,
            details={'reason': 'self_session_revoked', 'already_revoked': already_revoked},
        )
        self.repository.db.commit()
        return SelfSessionRevokeResponse(
            success=True,
            session_id=target_session.session_id,
            auth_state='revoked',
            already_revoked=already_revoked,
        )

    def _resolve_self_context(
        self,
        access_token: str,
        *,
        failure_event: str,
    ) -> tuple:
        if not access_token:
            self._raise_with_audit(
                event_type=failure_event,
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                details={'reason': 'token_expired'},
            )

        session = self.repository.get_session_by_access_token_hash(fingerprint_token(access_token))
        if session is None:
            self._raise_with_audit(
                event_type=failure_event,
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                details={'reason': 'token_expired'},
            )

        user = session.user
        device = session.device
        assert user is not None
        assert device is not None

        if session.revoked_at is not None:
            self._raise_with_audit(
                event_type=failure_event,
                error_code='revoked',
                message='Remote authorization revoked',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=device.device_id,
                target_session_id=session.session_id,
                details={'reason': 'revoked'},
            )
        if session.expires_at <= utc_now_naive():
            self._raise_with_audit(
                event_type=failure_event,
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                target_user_id=str(user.id),
                target_device_id=device.device_id,
                target_session_id=session.session_id,
                details={'reason': 'token_expired'},
            )

        license_record = self.repository.get_license(user.id)
        if license_record is None:
            self._raise_with_audit(
                event_type=failure_event,
                error_code='disabled',
                message='User or license disabled',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=device.device_id,
                target_session_id=session.session_id,
                details={'reason': 'disabled'},
            )
        self._assert_user_allowed(
            user,
            license_record,
            client_version=device.client_version or self.policy.minimum_supported_version,
            failure_event=failure_event,
            target_device_id=device.device_id,
            target_session_id=session.session_id,
        )

        binding = self.repository.get_active_binding_for_user(user.id)
        if binding is None or binding.device is None or binding.device.device_id != device.device_id:
            self._raise_device_mismatch(
                failure_event=failure_event,
                device_id=device.device_id,
                target_user_id=str(user.id),
                target_session_id=session.session_id,
            )
        self._assert_device_allowed(
            device,
            failure_event=failure_event,
            device_id=device.device_id,
            target_user_id=str(user.id),
            target_session_id=session.session_id,
        )
        entitlements = self.repository.get_entitlements(user.id)
        return session, user, device, license_record, binding, entitlements

    def _touch_authenticated_context(self, *, session, binding, device: Device) -> None:
        self.repository.touch_session(session)
        self.repository.touch_binding(binding)
        self.repository.touch_device(device)

    @staticmethod
    def _maybe_upgrade_password_hash(credential: UserCredential, password: str) -> None:
        try:
            password_record = hash_account_password(password)
        except Exception:
            return
        credential.password_hash = password_record.value
        credential.password_algo = password_record.algorithm
        credential.password_updated_at = utc_now_naive()

    def _ensure_allowed_device(self, user: User, device_id: str, client_version: str, *, failure_event: str) -> tuple[Device, UserDevice]:
        binding = self.repository.get_active_binding_for_user(user.id)
        if binding is None:
            device = self.repository.get_or_create_device(device_id, client_version=client_version)
            self._assert_device_allowed(device, failure_event=failure_event, device_id=device_id, target_user_id=str(user.id))
            created_binding = self.repository.create_binding(user.id, device.id)
            return device, created_binding
        if binding.device is None:
            self.repository.db.refresh(binding)
        assert binding.device is not None
        if binding.device.device_id != device_id:
            self._raise_device_mismatch(failure_event=failure_event, device_id=device_id, target_user_id=str(user.id))
        self._assert_device_allowed(binding.device, failure_event=failure_event, device_id=device_id, target_user_id=str(user.id))
        return binding.device, binding

    def _assert_user_allowed(
        self,
        user: User,
        license_record: License,
        *,
        client_version: str,
        failure_event: str,
        target_device_id: str | None,
        target_session_id: str | None = None,
    ) -> None:
        if self._version_tuple(client_version) < self._version_tuple(self.policy.minimum_supported_version):
            self._raise_with_audit(
                event_type=failure_event,
                error_code='minimum_version_required',
                message='Client version too old',
                status_code=403,
                details={'minimum_supported_version': self.policy.minimum_supported_version},
                target_user_id=str(user.id),
                target_device_id=target_device_id,
                target_session_id=target_session_id,
            )
        if user.status == 'disabled' or license_record.license_status == 'disabled':
            self._raise_with_audit(
                event_type=failure_event,
                error_code='disabled',
                message='User or license disabled',
                status_code=403,
                details={'reason': 'disabled'},
                target_user_id=str(user.id),
                target_device_id=target_device_id,
                target_session_id=target_session_id,
            )
        if license_record.license_status == 'revoked':
            self._raise_with_audit(
                event_type=failure_event,
                error_code='revoked',
                message='Remote authorization revoked',
                status_code=403,
                details={'reason': 'revoked'},
                target_user_id=str(user.id),
                target_device_id=target_device_id,
                target_session_id=target_session_id,
            )

    def _assert_device_allowed(
        self,
        device: Device,
        *,
        failure_event: str,
        device_id: str,
        target_user_id: str | None = None,
        target_session_id: str | None = None,
    ) -> None:
        if device.status != 'bound':
            self._raise_device_mismatch(
                failure_event=failure_event,
                device_id=device_id,
                target_user_id=target_user_id,
                target_session_id=target_session_id,
            )

    def _raise_device_mismatch(
        self,
        *,
        failure_event: str,
        device_id: str,
        target_user_id: str | None = None,
        target_session_id: str | None = None,
    ) -> None:
        self._raise_with_audit(
            event_type=failure_event,
            error_code='device_mismatch',
            message='Device does not match remote binding',
            status_code=403,
            target_user_id=target_user_id,
            target_device_id=device_id,
            target_session_id=target_session_id,
            details={'device_id': device_id},
        )

    def _build_auth_success(
        self,
        *,
        user: User,
        license_record: License,
        entitlements: list[str],
        device: Device,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
    ) -> AuthSuccessResponse:
        return AuthSuccessResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            token_type='Bearer',
            user=self._build_user_identity(user),
            license_status=license_record.license_status,
            entitlements=entitlements,
            device_id=device.device_id,
            device_status=device.status,
            offline_grace_until=self.policy.offline_grace_until(license_record),
            minimum_supported_version=self.policy.minimum_supported_version,
        )

    def _build_me_response(self, *, user: User, license_record: License, entitlements: list[str], device: Device) -> MeResponse:
        return MeResponse(
            user=self._build_user_identity(user),
            license_status=license_record.license_status,
            entitlements=entitlements,
            device_id=device.device_id,
            device_status=device.status,
            offline_grace_until=self.policy.offline_grace_until(license_record),
            minimum_supported_version=self.policy.minimum_supported_version,
        )

    @staticmethod
    def _build_user_identity(user: User) -> UserIdentity:
        return UserIdentity(
            id=f'u_{user.id}',
            username=user.username,
            display_name=user.display_name,
            tenant_id=user.tenant_id,
        )

    @staticmethod
    def _build_self_user_identity(user: User) -> SelfUserIdentity:
        return SelfUserIdentity(
            id=f'u_{user.id}',
            username=user.username,
            display_name=user.display_name,
        )

    @staticmethod
    def _build_self_activity_response(row) -> SelfActivityResponse:
        event_type = SELF_ACTIVITY_EVENT_MAP[row.event_type]
        return SelfActivityResponse(
            id=str(row.id),
            event_type=event_type,
            created_at=row.created_at,
            summary=SELF_ACTIVITY_SUMMARY_MAP[event_type],
            device_id=row.target_device_id,
            session_id=row.target_session_id,
        )

    def _raise_with_audit(
        self,
        *,
        event_type: str,
        error_code: str,
        message: str,
        status_code: int,
        details: dict | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
    ) -> None:
        self._write_audit(
            event_type,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            details=details,
        )
        self.repository.db.commit()
        raise AuthServiceError(error_code, message, status_code=status_code, details=details)

    def _write_audit(
        self,
        event_type: str,
        *,
        actor_type: str = 'managed_user',
        target_user_id: str | None,
        target_device_id: str | None,
        target_session_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        context = get_request_context()
        self.repository.write_audit_log(
            event_type=event_type,
            actor_type=actor_type,
            actor_id=target_user_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            request_id=context.request_id if context else None,
            trace_id=context.trace_id if context else None,
            details_json=json.dumps(details or {}, ensure_ascii=False),
        )

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        parts = re.findall(r'\d+', version or '')
        if not parts:
            return (0,)
        return tuple(int(part) for part in parts)
