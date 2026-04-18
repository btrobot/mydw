from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.observability import get_request_context
from app.models import Device, License, User
from app.repositories.auth import AuthRepository
from app.utils.time import utc_now_naive


class ControlServiceError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthorizationPolicyService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def minimum_supported_version(self) -> str:
        return self.settings.MINIMUM_SUPPORTED_VERSION

    def offline_grace_until(self, license_record: License) -> datetime | None:
        if license_record.expires_at is None:
            return None
        grace_hours = license_record.offline_grace_hours
        if grace_hours is None:
            grace_hours = self.settings.DEFAULT_OFFLINE_GRACE_HOURS
        return license_record.expires_at + timedelta(hours=grace_hours)


class SessionControlService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def revoke_session_by_public_id(self, session_id: str, *, reason: str) -> None:
        session = self.repository.get_session_by_session_id(session_id)
        if session is None:
            raise ControlServiceError(f'Unknown session id: {session_id}')
        self.repository.revoke_session(session, reason=reason)
        self.repository.revoke_refresh_tokens_for_session(session.id, reason=reason)

    def revoke_user_sessions(self, user_id: int, *, reason: str) -> None:
        for session in self.repository.list_sessions_for_user(user_id):
            self.repository.revoke_session(session, reason=reason)
            self.repository.revoke_refresh_tokens_for_session(session.id, reason=reason)

    def revoke_device_sessions(self, device_pk: int, *, reason: str) -> None:
        for session in self.repository.list_sessions_for_device(device_pk):
            self.repository.revoke_session(session, reason=reason)
            self.repository.revoke_refresh_tokens_for_session(session.id, reason=reason)

    def set_user_sessions_auth_state(self, user_id: int, *, auth_state: str) -> None:
        for session in self.repository.list_sessions_for_user(user_id):
            if session.revoked_at is None:
                self.repository.set_session_auth_state(session, auth_state=auth_state)

    def set_device_sessions_auth_state(self, device_pk: int, *, auth_state: str) -> None:
        for session in self.repository.list_sessions_for_device(device_pk):
            if session.revoked_at is None:
                self.repository.set_session_auth_state(session, auth_state=auth_state)


class ControlAuditMixin:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def _write_control_audit(
        self,
        event_type: str,
        *,
        actor_type: str,
        actor_id: str | None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        context = get_request_context()
        self.repository.write_audit_log(
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            request_id=context.request_id if context else None,
            trace_id=context.trace_id if context else None,
            details_json=json.dumps(details or {}, ensure_ascii=False),
        )


class UserControlService(ControlAuditMixin):
    def __init__(self, repository: AuthRepository, session_control: SessionControlService | None = None) -> None:
        super().__init__(repository)
        self.session_control = session_control or SessionControlService(repository)

    def revoke_user(self, user_id: int, *, actor_type: str = 'system', actor_id: str | None = None) -> None:
        user = self.repository.get_user_by_id(user_id)
        if user is None:
            raise ControlServiceError(f'Unknown user id: {user_id}')
        license_record = self.repository.get_license(user_id)
        if license_record is None:
            raise ControlServiceError(f'User {user_id} has no license record')

        license_record.license_status = 'revoked'
        license_record.revoked_at = utc_now_naive()
        user.status = 'active'
        self.session_control.revoke_user_sessions(user_id, reason='authorization_revoked')
        self._write_control_audit(
            'authorization_user_revoked',
            actor_type=actor_type,
            actor_id=actor_id,
            target_user_id=str(user.id),
            details={'reason': 'authorization_revoked'},
        )

    def restore_user(self, user_id: int, *, actor_type: str = 'system', actor_id: str | None = None) -> None:
        user = self.repository.get_user_by_id(user_id)
        if user is None:
            raise ControlServiceError(f'Unknown user id: {user_id}')
        license_record = self.repository.get_license(user_id)
        if license_record is None:
            raise ControlServiceError(f'User {user_id} has no license record')

        user.status = 'active'
        license_record.license_status = 'active'
        license_record.revoked_at = None
        license_record.disabled_at = None
        self.session_control.set_user_sessions_auth_state(user_id, auth_state='authenticated_active')
        self._write_control_audit(
            'authorization_user_restored',
            actor_type=actor_type,
            actor_id=actor_id,
            target_user_id=str(user.id),
            details={'reason': 'authorization_restored'},
        )

    def disable_user(self, user_id: int, *, actor_type: str = 'system', actor_id: str | None = None) -> None:
        user = self.repository.get_user_by_id(user_id)
        if user is None:
            raise ControlServiceError(f'Unknown user id: {user_id}')
        license_record = self.repository.get_license(user_id)
        if license_record is None:
            raise ControlServiceError(f'User {user_id} has no license record')

        user.status = 'disabled'
        license_record.license_status = 'disabled'
        license_record.disabled_at = utc_now_naive()
        self.session_control.set_user_sessions_auth_state(user_id, auth_state='authorization_disabled')
        self._write_control_audit(
            'authorization_user_disabled',
            actor_type=actor_type,
            actor_id=actor_id,
            target_user_id=str(user.id),
            details={'reason': 'authorization_disabled'},
        )


class DeviceControlService(ControlAuditMixin):
    def __init__(self, repository: AuthRepository, session_control: SessionControlService | None = None) -> None:
        super().__init__(repository)
        self.session_control = session_control or SessionControlService(repository)

    def unbind_device(self, user_id: int, device_id: str, *, actor_type: str = 'system', actor_id: str | None = None) -> None:
        binding = self.repository.get_binding_by_user_and_device_id(user_id, device_id)
        if binding is None or binding.device is None:
            raise ControlServiceError(f'Unknown device binding: user={user_id} device={device_id}')

        self.repository.set_binding_status(binding, status='unbound')
        self.repository.set_device_status(binding.device, status='unbound')
        self.session_control.set_device_sessions_auth_state(binding.device.id, auth_state='device_unbound')
        self._write_control_audit(
            'authorization_device_unbound',
            actor_type=actor_type,
            actor_id=actor_id,
            target_user_id=str(user_id),
            target_device_id=device_id,
            details={'reason': 'device_unbound'},
        )

    def disable_device(self, device_id: str, *, actor_type: str = 'system', actor_id: str | None = None) -> None:
        device = self.repository.get_device_by_device_id(device_id)
        if device is None:
            raise ControlServiceError(f'Unknown device: {device_id}')

        self.repository.set_device_status(device, status='disabled')
        self.session_control.set_device_sessions_auth_state(device.id, auth_state='device_disabled')
        self._write_control_audit(
            'authorization_device_disabled',
            actor_type=actor_type,
            actor_id=actor_id,
            target_device_id=device_id,
            details={'reason': 'device_disabled'},
        )

    def rebind_device(self, user_id: int, device_id: str, *, client_version: str = '0.2.0', actor_type: str = 'system', actor_id: str | None = None) -> None:
        device = self.repository.get_or_create_device(device_id, client_version=client_version)
        self.session_control.revoke_device_sessions(device.id, reason='device_rebound')
        for binding in self.repository.list_bindings_for_device(device.id):
            if binding.binding_status == 'bound':
                self.repository.set_binding_status(binding, status='unbound')
        for binding in self.repository.list_bindings_for_user(user_id):
            if binding.binding_status == 'bound':
                self.repository.set_binding_status(binding, status='unbound')
                if binding.device is not None:
                    self.repository.set_device_status(binding.device, status='unbound')
        binding = self.repository.get_binding_by_user_and_device_id(user_id, device_id)
        if binding is None:
            binding = self.repository.create_binding(user_id, device.id)
        self.repository.set_binding_status(binding, status='bound')
        self.repository.set_device_status(device, status='bound')
        self._write_control_audit(
            'authorization_device_rebound',
            actor_type=actor_type,
            actor_id=actor_id,
            target_user_id=str(user_id),
            target_device_id=device_id,
            details={'reason': 'device_rebound'},
        )
