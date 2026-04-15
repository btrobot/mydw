from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.observability import get_request_context
from app.core.security import fingerprint_token, hash_password, issue_token, verify_password
from app.models import Device, License, User, UserCredential, UserDevice, UserEntitlement
from app.repositories.auth import AuthRepository
from app.services.control_service import AuthorizationPolicyService
from app.schemas.auth import (
    AuthSuccessResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    UserIdentity,
)

class AuthServiceError(Exception):
    def __init__(self, error_code: str, message: str, *, status_code: int, details: dict | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


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
        self.repository.db.add(UserCredential(user_id=user.id, password_hash=hash_password('secret')))
        self.repository.db.add(
            License(
                user_id=user.id,
                license_status='active',
                plan_code='starter',
                starts_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
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
        if credential is None or not verify_password(payload.password, credential.password_hash):
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
        device, binding = self._ensure_allowed_device(user, payload.device_id, payload.client_version, failure_event='auth_login_failed')
        access_token = issue_token('access')
        refresh_token = issue_token('refresh')
        expires_at = datetime.utcnow() + timedelta(seconds=self.settings.ACCESS_TOKEN_TTL_SECONDS)
        session = self.repository.create_session(
            session_id=issue_token('sess'),
            user_id=user.id,
            device_pk=device.id,
            access_token_hash=fingerprint_token(access_token),
            expires_at=expires_at,
        )
        self.repository.create_refresh_token(
            session_pk=session.id,
            token_hash=hash_password(refresh_token),
            expires_at=datetime.utcnow() + timedelta(seconds=self.settings.REFRESH_TOKEN_TTL_SECONDS),
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
        if refresh_token.expires_at <= datetime.utcnow():
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
        expires_at = datetime.utcnow() + timedelta(seconds=self.settings.ACCESS_TOKEN_TTL_SECONDS)
        self.repository.rotate_refresh_token(
            source=refresh_token,
            new_token_hash=hash_password(next_refresh_token),
            expires_at=datetime.utcnow() + timedelta(seconds=self.settings.REFRESH_TOKEN_TTL_SECONDS),
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
        if refresh_token.expires_at <= datetime.utcnow():
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
        if not access_token:
            self._raise_with_audit(
                event_type='auth_me_failed',
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                details={'reason': 'token_expired'},
            )

        session = self.repository.get_session_by_access_token_hash(fingerprint_token(access_token))
        if session is None:
            self._raise_with_audit(
                event_type='auth_me_failed',
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
                event_type='auth_me_failed',
                error_code='revoked',
                message='Remote authorization revoked',
                status_code=403,
                target_user_id=str(user.id),
                target_device_id=device.device_id,
                target_session_id=session.session_id,
                details={'reason': 'revoked'},
            )
        if session.expires_at <= datetime.utcnow():
            self._raise_with_audit(
                event_type='auth_me_failed',
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
                event_type='auth_me_failed',
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
            failure_event='auth_me_failed',
            target_device_id=device.device_id,
            target_session_id=session.session_id,
        )

        binding = self.repository.get_active_binding_for_user(user.id)
        if binding is None or binding.device is None or binding.device.device_id != device.device_id:
            self._raise_device_mismatch(
                failure_event='auth_me_failed',
                device_id=device.device_id,
                target_user_id=str(user.id),
                target_session_id=session.session_id,
            )
        self._assert_device_allowed(
            device,
            failure_event='auth_me_failed',
            device_id=device.device_id,
            target_user_id=str(user.id),
            target_session_id=session.session_id,
        )

        self.repository.touch_session(session)
        self.repository.touch_binding(binding)
        self.repository.touch_device(device)
        entitlements = self.repository.get_entitlements(user.id)
        response = self._build_me_response(user=user, license_record=license_record, entitlements=entitlements, device=device)
        self._write_audit(
            'auth_me_succeeded',
            target_user_id=str(user.id),
            target_device_id=device.device_id,
            target_session_id=session.session_id,
            details={'reason': 'me'},
        )
        self.repository.db.commit()
        return response

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
        target_user_id: str | None,
        target_device_id: str | None,
        target_session_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        context = get_request_context()
        self.repository.write_audit_log(
            event_type=event_type,
            actor_type='managed_user',
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
        return tuple(int(part) for part in version.split('.'))
