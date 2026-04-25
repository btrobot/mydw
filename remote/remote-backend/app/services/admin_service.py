from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.observability import get_request_context
from app.core.security import (
    fingerprint_token,
    hash_account_password,
    issue_token,
    verify_account_password,
)
from app.models import AdminSession, AdminUser, User
from app.repositories.admin import AdminRepository
from app.repositories.auth import AuthRepository
from app.schemas.admin import (
    AdminMetricsSummaryResponse,
    AdminActionResponse,
    AdminCurrentSessionResponse,
    AdminDeviceListResponse,
    AdminDeviceRebindRequest,
    AdminDeviceResponse,
    AuditLogListResponse,
    AuditLogResponse,
    AdminIdentity,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSessionListResponse,
    AdminSessionResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from app.services.admin_authz import (
    ADMIN_PERMISSION_AUDIT_READ,
    ADMIN_PERMISSION_DEVICES_READ,
    ADMIN_PERMISSION_DEVICES_WRITE,
    ADMIN_PERMISSION_METRICS_READ,
    ADMIN_PERMISSION_SESSIONS_READ,
    ADMIN_PERMISSION_SESSIONS_REVOKE,
    ADMIN_PERMISSION_SESSION_READ,
    ADMIN_PERMISSION_USERS_READ,
    ADMIN_PERMISSION_USERS_WRITE,
    AdminPermissionError,
    require_permission,
)
from app.services.control_service import DeviceControlService, SessionControlService, UserControlService
from app.utils.pagination import resolve_page_metadata
from app.utils.time import utc_now_naive


class AdminServiceError(Exception):
    def __init__(self, error_code: str, message: str, *, status_code: int, details: dict | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class AdminService:
    def __init__(self, repository: AdminRepository) -> None:
        self.repository = repository
        self.settings = get_settings()
        self.auth_repository = AuthRepository(repository.db)
        self.session_control = SessionControlService(self.auth_repository)
        self.user_control = UserControlService(self.auth_repository, self.session_control)
        self.device_control = DeviceControlService(self.auth_repository, self.session_control)

    def ensure_seed_admin(self) -> None:
        if self.settings.APP_ENV.lower() not in {'development', 'test'}:
            return
        seed_users = [
            (self.settings.ADMIN_BOOTSTRAP_USERNAME, self.settings.ADMIN_BOOTSTRAP_PASSWORD, 'super_admin'),
            ('auth-admin', 'auth-admin-secret', 'auth_admin'),
            ('support', 'support-secret', 'support_readonly'),
        ]
        for username, password, role in seed_users:
            if self.repository.get_admin_user_by_username(username) is not None:
                continue
            password_record = hash_account_password(password)
            self.repository.db.add(
                AdminUser(
                    username=username,
                    display_name=username.replace('-', ' ').title(),
                    password_hash=password_record.value,
                    password_algo=password_record.algorithm,
                    role=role,
                    status='active',
                )
            )
        self.repository.db.commit()

    def login(self, payload: AdminLoginRequest, *, client_ip: str) -> AdminLoginResponse:
        admin_user = self.repository.get_admin_user_by_username(payload.username)
        verification = (
            verify_account_password(payload.password, admin_user.password_hash, password_algo=admin_user.password_algo)
            if admin_user is not None
            else None
        )
        if admin_user is None or verification is None or not verification.verified:
            self._raise_with_audit(
                event_type='admin_login_failed',
                error_code='invalid_credentials',
                message='Invalid username or password',
                status_code=401,
                target_user_id=None,
                details={'reason': 'invalid_credentials', 'client_ip': client_ip},
            )
        assert admin_user is not None
        if admin_user.status != 'active':
            self._raise_with_audit(
                event_type='admin_login_failed',
                error_code='forbidden',
                message='Admin access forbidden',
                status_code=403,
                target_user_id=f'admin_{admin_user.id}',
                details={'reason': 'forbidden', 'client_ip': client_ip},
            )
        if verification.needs_rehash:
            self._maybe_upgrade_password_hash(admin_user, payload.password)

        access_token = issue_token('admin_access')
        expires_at = utc_now_naive() + timedelta(seconds=self.settings.ADMIN_ACCESS_TOKEN_TTL_SECONDS)
        session = self.repository.create_admin_session(
            session_id=issue_token('admin_sess'),
            admin_user_id=admin_user.id,
            access_token_hash=fingerprint_token(access_token),
            expires_at=expires_at,
        )
        self._write_audit(
            'admin_login_succeeded',
            actor_id=f'admin_{admin_user.id}',
            target_user_id=f'admin_{admin_user.id}',
            target_session_id=session.session_id,
            details={'client_ip': client_ip},
        )
        self.repository.db.commit()
        return AdminLoginResponse(
            access_token=access_token,
            session_id=session.session_id,
            expires_at=expires_at,
            token_type='Bearer',
            user=self._build_identity(admin_user),
        )

    @staticmethod
    def _maybe_upgrade_password_hash(admin_user: AdminUser, password: str) -> None:
        try:
            password_record = hash_account_password(password)
        except Exception:
            return
        admin_user.password_hash = password_record.value
        admin_user.password_algo = password_record.algorithm

    def get_session(self, access_token: str) -> AdminCurrentSessionResponse:
        admin_user, session = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_SESSION_READ)
        self.repository.touch_admin_session(session)
        self._write_audit(
            'admin_session_checked',
            actor_id=f'admin_{admin_user.id}',
            target_user_id=f'admin_{admin_user.id}',
            target_session_id=session.session_id,
            details={'reason': 'session_lookup'},
        )
        self.repository.db.commit()
        return AdminCurrentSessionResponse(
            session_id=session.session_id,
            expires_at=session.expires_at,
            user=self._build_identity(admin_user),
        )

    def list_users(
        self,
        access_token: str,
        *,
        q: str | None = None,
        status: str | None = None,
        license_status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> AdminUserListResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_USERS_READ)
        total = self.repository.count_users(
            q=q,
            status=status,
            license_status=license_status,
        )
        items = [
            self._build_user_response(user)
            for user in self.repository.list_users(
                q=q,
                status=status,
                license_status=license_status,
                limit=limit,
                offset=offset,
            )
        ]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'admin_users_listed',
            actor_id=f'admin_{admin_user.id}',
            details={'count': len(items), 'total': total, 'q': q, 'status': status, 'license_status': license_status, 'limit': limit, 'offset': offset},
        )
        self.repository.db.commit()
        return AdminUserListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_user(self, access_token: str, user_id: str) -> AdminUserResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_USERS_READ)
        target = self._load_target_user(user_id)
        self._write_audit(
            'admin_user_detail_viewed',
            actor_id=f'admin_{admin_user.id}',
            target_user_id=str(target.id),
            details={'user_id': user_id},
        )
        self.repository.db.commit()
        return self._build_user_response(target)

    def update_user(self, access_token: str, user_id: str, payload: AdminUserUpdateRequest) -> AdminUserResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_USERS_WRITE)
        target = self._load_target_user(user_id)
        changed_fields = payload.model_dump(exclude_none=True)

        if payload.display_name is not None:
            target.display_name = payload.display_name

        license_record = self.repository.ensure_license(target.id)
        if payload.license_expires_at is not None:
            license_record.expires_at = payload.license_expires_at

        if payload.entitlements is not None:
            self.repository.replace_entitlements(target.id, payload.entitlements)

        if payload.license_status is not None:
            self._apply_license_status(target.id, payload.license_status, actor_id=f'admin_{admin_user.id}')
            target = self._load_target_user(user_id)
        self._write_audit(
            'admin_user_updated',
            actor_id=f'admin_{admin_user.id}',
            target_user_id=str(target.id),
            details={'user_id': user_id, 'fields': changed_fields},
        )

        self.repository.db.commit()
        return self._build_user_response(target)

    def revoke_user(self, access_token: str, user_id: str) -> AdminActionResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_USERS_WRITE)
        target = self._load_target_user(user_id)
        self.user_control.revoke_user(target.id, actor_type='admin', actor_id=f'admin_{admin_user.id}')
        self.repository.db.commit()
        return AdminActionResponse(success=True)

    def restore_user(self, access_token: str, user_id: str) -> AdminActionResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_USERS_WRITE)
        target = self._load_target_user(user_id)
        self.user_control.restore_user(target.id, actor_type='admin', actor_id=f'admin_{admin_user.id}')
        self.repository.db.commit()
        return AdminActionResponse(success=True)

    def list_devices(
        self,
        access_token: str,
        *,
        q: str | None = None,
        device_status: str | None = None,
        user_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> AdminDeviceListResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_DEVICES_READ)
        normalized_user_id = self._normalize_optional_user_filter(user_id)
        total = self.repository.count_devices(
            q=q,
            device_status=device_status,
            user_id=normalized_user_id,
        )
        items = [
            self._build_device_response(device)
            for device in self.repository.list_devices(
                q=q,
                device_status=device_status,
                user_id=normalized_user_id,
                limit=limit,
                offset=offset,
            )
        ]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'admin_devices_listed',
            actor_id=f'admin_{admin_user.id}',
            details={'count': len(items), 'total': total, 'q': q, 'device_status': device_status, 'user_id': user_id, 'limit': limit, 'offset': offset},
        )
        self.repository.db.commit()
        return AdminDeviceListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_device(self, access_token: str, device_id: str) -> AdminDeviceResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_DEVICES_READ)
        device = self._load_target_device(device_id)
        self._write_audit(
            'admin_device_detail_viewed',
            actor_id=f'admin_{admin_user.id}',
            target_device_id=device.device_id,
            details={'device_id': device_id},
        )
        self.repository.db.commit()
        return self._build_device_response(device)

    def unbind_device(self, access_token: str, device_id: str) -> AdminActionResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_DEVICES_WRITE)
        device = self._load_target_device(device_id)
        current_user_id = self._current_bound_user_id(device)
        if current_user_id is None:
            raise AdminServiceError('not_found', 'Requested admin resource missing', status_code=404, details={'device_id': device_id})
        self.device_control.unbind_device(current_user_id, device_id, actor_type='admin', actor_id=f'admin_{admin_user.id}')
        self.repository.db.commit()
        return AdminActionResponse(success=True)

    def disable_device(self, access_token: str, device_id: str) -> AdminActionResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_DEVICES_WRITE)
        self._load_target_device(device_id)
        self.device_control.disable_device(device_id, actor_type='admin', actor_id=f'admin_{admin_user.id}')
        self.repository.db.commit()
        return AdminActionResponse(success=True)

    def rebind_device(self, access_token: str, device_id: str, payload: AdminDeviceRebindRequest) -> AdminActionResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_DEVICES_WRITE)
        self._load_target_device(device_id)
        target_user = self._load_target_user(payload.user_id)
        self.device_control.rebind_device(
            target_user.id,
            device_id,
            client_version=payload.client_version or self.settings.MINIMUM_SUPPORTED_VERSION,
            actor_type='admin',
            actor_id=f'admin_{admin_user.id}',
        )
        self.repository.db.commit()
        return AdminActionResponse(success=True)

    def list_sessions(
        self,
        access_token: str,
        *,
        q: str | None = None,
        auth_state: str | None = None,
        user_id: str | None = None,
        device_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> AdminSessionListResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_SESSIONS_READ)
        normalized_user_id = self._normalize_optional_user_filter(user_id)
        total = self.repository.count_sessions(
            q=q,
            auth_state=auth_state,
            user_id=normalized_user_id,
            device_id=device_id,
        )
        items = [
            self._build_session_response(session)
            for session in self.repository.list_sessions(
                q=q,
                auth_state=auth_state,
                user_id=normalized_user_id,
                device_id=device_id,
                limit=limit,
                offset=offset,
            )
        ]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'admin_sessions_listed',
            actor_id=f'admin_{admin_user.id}',
            details={'count': len(items), 'total': total, 'q': q, 'auth_state': auth_state, 'user_id': user_id, 'device_id': device_id, 'limit': limit, 'offset': offset},
        )
        self.repository.db.commit()
        return AdminSessionListResponse(items=items, total=total, page=page, page_size=page_size)

    def revoke_session(self, access_token: str, session_id: str) -> AdminActionResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_SESSIONS_REVOKE)
        session = self.auth_repository.get_session_by_session_id(session_id)
        if session is None:
            raise AdminServiceError('not_found', 'Requested admin resource missing', status_code=404, details={'session_id': session_id})
        self.session_control.revoke_session_by_public_id(session_id, reason='admin_session_revoked')
        self._write_audit(
            'admin_session_revoked',
            actor_id=f'admin_{admin_user.id}',
            target_user_id=str(session.user.id) if session.user is not None else None,
            target_session_id=session_id,
            details={'session_id': session_id, 'reason': 'admin_session_revoked'},
        )
        self.repository.db.commit()
        return AdminActionResponse(success=True)

    def list_audit_logs(
        self,
        access_token: str,
        *,
        event_type: str | None = None,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_AUDIT_READ)
        normalized_created_from = self._normalize_audit_filter_datetime(created_from)
        normalized_created_to = self._normalize_audit_filter_datetime(created_to)
        total = self.repository.count_audit_logs(
            event_type=event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            created_from=normalized_created_from,
            created_to=normalized_created_to,
        )
        audit_rows = self.repository.list_audit_logs(
            event_type=event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            created_from=normalized_created_from,
            created_to=normalized_created_to,
            limit=limit,
            offset=offset,
        )
        items = [self._build_audit_response(row) for row in audit_rows]
        page, page_size = resolve_page_metadata(limit=limit, offset=offset, returned_count=len(items))
        self._write_audit(
            'admin_audit_logs_listed',
            actor_id=f'admin_{admin_user.id}',
            details={
                'count': len(items),
                'total': total,
                'event_type': event_type,
                'actor_id': actor_id,
                'target_user_id': target_user_id,
                'target_device_id': target_device_id,
                'target_session_id': target_session_id,
                'created_from': normalized_created_from.isoformat() if normalized_created_from else None,
                'created_to': normalized_created_to.isoformat() if normalized_created_to else None,
                'limit': limit,
                'offset': offset,
            },
        )
        self.repository.db.commit()
        return AuditLogListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_metrics_summary(self, access_token: str) -> AdminMetricsSummaryResponse:
        admin_user, _ = self._require_admin_session(access_token, permission=ADMIN_PERMISSION_METRICS_READ)
        generated_at = utc_now_naive()
        login_failures = self.repository.count_audit_logs(event_types={'auth_login_failed', 'admin_login_failed'})
        device_mismatches = self.repository.count_audit_logs(
            event_types={'auth_login_failed', 'auth_refresh_failed', 'auth_logout_failed', 'auth_me_failed'},
            detail_reason='device_mismatch',
        )
        destructive_actions = self.repository.count_audit_logs(
            event_types={
                'authorization_user_revoked',
                'authorization_user_disabled',
                'authorization_device_unbound',
                'authorization_device_disabled',
                'authorization_device_rebound',
                'admin_session_revoked',
            }
        )
        active_sessions = self.repository.count_active_sessions()
        self._write_audit(
            'admin_metrics_viewed',
            actor_id=f'admin_{admin_user.id}',
            details={
                'active_sessions': active_sessions,
                'login_failures': login_failures,
                'device_mismatches': device_mismatches,
                'destructive_actions': destructive_actions,
            },
        )
        self.repository.db.commit()
        return AdminMetricsSummaryResponse(
            active_sessions=active_sessions,
            login_failures=login_failures,
            device_mismatches=device_mismatches,
            destructive_actions=destructive_actions,
            generated_at=generated_at,
            recent_failures=self._build_audit_rows(
                self.repository.list_recent_audit_logs(event_types={'auth_login_failed', 'admin_login_failed'})
            ),
            recent_destructive_actions=self._build_audit_rows(
                self.repository.list_recent_audit_logs(
                    event_types={
                        'authorization_user_revoked',
                        'authorization_user_disabled',
                        'authorization_device_unbound',
                        'authorization_device_disabled',
                        'authorization_device_rebound',
                        'admin_session_revoked',
                    }
                )
            ),
        )

    def _apply_license_status(self, user_id: int, status: str, *, actor_id: str) -> None:
        if status == 'disabled':
            self.user_control.disable_user(user_id, actor_type='admin', actor_id=actor_id)
        elif status == 'active':
            self.user_control.restore_user(user_id, actor_type='admin', actor_id=actor_id)
        elif status == 'revoked':
            self.user_control.revoke_user(user_id, actor_type='admin', actor_id=actor_id)
        else:
            raise AdminServiceError('forbidden', f'Unsupported license_status update: {status}', status_code=403)

    def _load_target_user(self, user_id: str) -> User:
        try:
            normalized = int(user_id.removeprefix('u_'))
        except ValueError as exc:
            raise AdminServiceError('not_found', 'Requested admin resource missing', status_code=404, details={'user_id': user_id}) from exc
        target = self.repository.get_user_detail(normalized)
        if target is None:
            raise AdminServiceError('not_found', 'Requested admin resource missing', status_code=404, details={'user_id': user_id})
        return target

    def _load_target_device(self, device_id: str):
        target = self.repository.get_device_detail(device_id)
        if target is None:
            raise AdminServiceError('not_found', 'Requested admin resource missing', status_code=404, details={'device_id': device_id})
        return target

    @staticmethod
    def _normalize_optional_user_filter(user_id: str | None) -> int | None:
        if user_id is None or not user_id.strip():
            return None
        try:
            return int(user_id.strip().removeprefix('u_'))
        except ValueError as exc:
            raise AdminServiceError('not_found', 'Requested admin resource missing', status_code=404, details={'user_id': user_id}) from exc

    @staticmethod
    def _current_bound_user_id(device) -> int | None:
        for binding in device.bindings:
            if binding.binding_status == 'bound' and binding.user is not None:
                return binding.user.id
        return None

    def _require_admin_session(self, access_token: str, *, permission: str) -> tuple[AdminUser, AdminSession]:
        if not access_token:
            self._raise_with_audit(
                event_type='admin_session_failed',
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                details={'reason': 'token_expired'},
            )

        session = self.repository.get_admin_session_by_access_token_hash(fingerprint_token(access_token))
        if session is None:
            self._raise_with_audit(
                event_type='admin_session_failed',
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                details={'reason': 'token_expired'},
            )

        admin_user = session.admin_user
        assert admin_user is not None
        if session.revoked_at is not None or session.expires_at <= utc_now_naive():
            self._raise_with_audit(
                event_type='admin_session_failed',
                error_code='token_expired',
                message='Access token expired or invalid',
                status_code=401,
                actor_id=f'admin_{admin_user.id}',
                target_user_id=f'admin_{admin_user.id}',
                target_session_id=session.session_id,
                details={'reason': 'token_expired'},
            )
        if admin_user.status != 'active':
            self._raise_with_audit(
                event_type='admin_session_failed',
                error_code='forbidden',
                message='Admin access forbidden',
                status_code=403,
                actor_id=f'admin_{admin_user.id}',
                target_user_id=f'admin_{admin_user.id}',
                target_session_id=session.session_id,
                details={'reason': 'forbidden'},
            )
        try:
            policy = require_permission(admin_user.role, permission)
        except AdminPermissionError:
            self._raise_with_audit(
                event_type='admin_authorization_failed',
                error_code='forbidden',
                message='Admin access forbidden',
                status_code=403,
                actor_id=f'admin_{admin_user.id}',
                target_user_id=f'admin_{admin_user.id}',
                target_session_id=session.session_id,
                details={'reason': 'forbidden', 'required_permission': permission},
            )
        self._write_audit(
            'admin_authorization_checked',
            actor_id=f'admin_{admin_user.id}',
            target_user_id=f'admin_{admin_user.id}',
            target_session_id=session.session_id,
            details={'permission': permission, 'role': policy.role},
        )
        return admin_user, session

    @staticmethod
    def _build_identity(admin_user: AdminUser) -> AdminIdentity:
        return AdminIdentity(
            id=f'admin_{admin_user.id}',
            username=admin_user.username,
            display_name=admin_user.display_name,
            role=admin_user.role,
        )

    @staticmethod
    def _build_user_response(user: User) -> AdminUserResponse:
        last_seen_candidates = [session.last_seen_at for session in user.sessions if session.last_seen_at is not None]
        last_seen_at = max(last_seen_candidates) if last_seen_candidates else None
        device_count = sum(1 for binding in user.bindings if binding.binding_status == 'bound')
        entitlements = [row.entitlement for row in user.entitlements]
        license_record = user.license
        return AdminUserResponse(
            id=f'u_{user.id}',
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            tenant_id=user.tenant_id,
            status=user.status,
            license_status=license_record.license_status if license_record else None,
            license_expires_at=license_record.expires_at if license_record else None,
            entitlements=entitlements,
            device_count=device_count,
            last_seen_at=last_seen_at,
        )

    @staticmethod
    def _build_device_response(device) -> AdminDeviceResponse:
        current_binding = next((binding for binding in device.bindings if binding.binding_status == 'bound' and binding.user is not None), None)
        return AdminDeviceResponse(
            device_id=device.device_id,
            user_id=f'u_{current_binding.user.id}' if current_binding and current_binding.user is not None else None,
            device_status=device.status,
            first_bound_at=current_binding.bound_at if current_binding is not None else None,
            last_seen_at=device.last_seen_at,
            client_version=device.client_version,
        )

    @staticmethod
    def _build_session_response(session) -> AdminSessionResponse:
        return AdminSessionResponse(
            session_id=session.session_id,
            user_id=f'u_{session.user.id}' if session.user is not None else None,
            device_id=session.device.device_id if session.device is not None else None,
            auth_state=session.auth_state,
            issued_at=session.issued_at,
            expires_at=session.expires_at,
            last_seen_at=session.last_seen_at,
        )

    @staticmethod
    def _build_audit_response(row) -> AuditLogResponse:
        details = {}
        if row.details_json:
            try:
                details = json.loads(row.details_json)
            except json.JSONDecodeError:
                details = {'raw': row.details_json}
        return AuditLogResponse(
            id=str(row.id),
            event_type=row.event_type,
            actor_type=row.actor_type,
            actor_id=row.actor_id,
            target_user_id=row.target_user_id,
            target_device_id=row.target_device_id,
            target_session_id=row.target_session_id,
            request_id=row.request_id,
            trace_id=row.trace_id,
            created_at=row.created_at,
            details=details,
        )

    def _build_audit_rows(self, audit_rows) -> list[AuditLogResponse]:
        return [self._build_audit_response(row) for row in audit_rows]

    @staticmethod
    def _details_reason(row) -> str | None:
        if not row.details_json:
            return None
        try:
            details = json.loads(row.details_json)
        except json.JSONDecodeError:
            return None
        return details.get('reason')

    @staticmethod
    def _normalize_audit_filter_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def _raise_with_audit(
        self,
        *,
        event_type: str,
        error_code: str,
        message: str,
        status_code: int,
        details: dict | None = None,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_session_id: str | None = None,
    ) -> None:
        self._write_audit(
            event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_session_id=target_session_id,
            details=details,
        )
        self.repository.db.commit()
        raise AdminServiceError(error_code, message, status_code=status_code, details=details)

    def _write_audit(
        self,
        event_type: str,
        *,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        context = get_request_context()
        self.repository.write_audit_log(
            event_type=event_type,
            actor_type='admin',
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            request_id=context.request_id if context else None,
            trace_id=context.trace_id if context else None,
            details_json=json.dumps(details or {}, ensure_ascii=False, default=str),
        )
