from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import verify_password
from app.models import AuditLog, Device, EndUserSession, License, RefreshToken, User, UserCredential, UserDevice, UserEntitlement


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.execute(select(User).where(User.username == username)).scalars().first()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.execute(select(User).where(User.id == user_id)).scalars().first()

    def get_user_credential(self, user_id: int) -> UserCredential | None:
        return self.db.execute(select(UserCredential).where(UserCredential.user_id == user_id)).scalars().first()

    def get_license(self, user_id: int) -> License | None:
        return self.db.execute(select(License).where(License.user_id == user_id)).scalars().first()

    def get_entitlements(self, user_id: int) -> list[str]:
        return list(self.db.execute(select(UserEntitlement.entitlement).where(UserEntitlement.user_id == user_id)).scalars().all())

    def get_or_create_device(self, device_id: str, *, client_version: str) -> Device:
        device = self.db.execute(select(Device).where(Device.device_id == device_id)).scalars().first()
        now = datetime.utcnow()
        if device is None:
            device = Device(device_id=device_id, client_version=client_version, status='bound', first_seen_at=now, last_seen_at=now)
            self.db.add(device)
            self.db.flush()
        else:
            device.client_version = client_version
            device.last_seen_at = now
        return device

    def get_device_by_device_id(self, device_id: str) -> Device | None:
        return self.db.execute(select(Device).where(Device.device_id == device_id)).scalars().first()

    def get_binding(self, user_id: int, device_pk: int) -> UserDevice | None:
        return self.db.execute(select(UserDevice).where(UserDevice.user_id == user_id, UserDevice.device_id == device_pk, UserDevice.binding_status == 'bound')).scalars().first()

    def get_active_binding_for_user(self, user_id: int) -> UserDevice | None:
        return self.db.execute(
            select(UserDevice)
            .options(joinedload(UserDevice.device))
            .where(UserDevice.user_id == user_id, UserDevice.binding_status == 'bound')
            .order_by(UserDevice.id.asc())
        ).scalars().first()

    def get_binding_by_user_and_device_id(self, user_id: int, device_id: str) -> UserDevice | None:
        return self.db.execute(
            select(UserDevice)
            .options(joinedload(UserDevice.device))
            .join(Device, UserDevice.device_id == Device.id)
            .where(UserDevice.user_id == user_id, Device.device_id == device_id)
            .order_by(UserDevice.id.desc())
        ).scalars().first()

    def list_bindings_for_user(self, user_id: int) -> list[UserDevice]:
        return list(
            self.db.execute(
                select(UserDevice)
                .options(joinedload(UserDevice.device))
                .where(UserDevice.user_id == user_id)
                .order_by(UserDevice.id.asc())
            ).scalars().all()
        )

    def list_bindings_for_device(self, device_pk: int) -> list[UserDevice]:
        return list(
            self.db.execute(
                select(UserDevice)
                .options(joinedload(UserDevice.user), joinedload(UserDevice.device))
                .where(UserDevice.device_id == device_pk)
                .order_by(UserDevice.id.asc())
            ).scalars().all()
        )

    def create_binding(self, user_id: int, device_pk: int) -> UserDevice:
        now = datetime.utcnow()
        binding = UserDevice(user_id=user_id, device_id=device_pk, binding_status='bound', bound_at=now, last_auth_at=now)
        self.db.add(binding)
        self.db.flush()
        return binding

    def touch_binding(self, binding: UserDevice) -> None:
        binding.last_auth_at = datetime.utcnow()

    def set_binding_status(self, binding: UserDevice, *, status: str) -> None:
        now = datetime.utcnow()
        binding.binding_status = status
        if status == 'bound':
            binding.bound_at = binding.bound_at or now
            binding.unbound_at = None
            binding.last_auth_at = now
        else:
            binding.unbound_at = now

    def create_session(self, *, session_id: str, user_id: int, device_pk: int, access_token_hash: str, expires_at: datetime) -> EndUserSession:
        session = EndUserSession(session_id=session_id, user_id=user_id, device_id=device_pk, access_token_hash=access_token_hash, expires_at=expires_at)
        self.db.add(session)
        self.db.flush()
        return session

    def list_sessions_for_user(self, user_id: int) -> list[EndUserSession]:
        return list(
            self.db.execute(
                select(EndUserSession)
                .options(joinedload(EndUserSession.device), joinedload(EndUserSession.user))
                .where(EndUserSession.user_id == user_id)
                .order_by(EndUserSession.id.asc())
            ).scalars().all()
        )

    def list_sessions_for_device(self, device_pk: int) -> list[EndUserSession]:
        return list(
            self.db.execute(
                select(EndUserSession)
                .options(joinedload(EndUserSession.device), joinedload(EndUserSession.user))
                .where(EndUserSession.device_id == device_pk)
                .order_by(EndUserSession.id.asc())
            ).scalars().all()
        )

    def get_session_by_session_id(self, session_id: str) -> EndUserSession | None:
        return self.db.execute(
            select(EndUserSession)
            .options(joinedload(EndUserSession.user), joinedload(EndUserSession.device))
            .where(EndUserSession.session_id == session_id)
        ).scalars().first()

    def create_refresh_token(self, *, session_pk: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(session_id=session_pk, token_hash=token_hash, expires_at=expires_at)
        self.db.add(refresh_token)
        self.db.flush()
        return refresh_token

    def get_refresh_token_with_session(self, refresh_token: str) -> RefreshToken | None:
        candidates = self.db.execute(
            select(RefreshToken)
            .options(
                joinedload(RefreshToken.session).joinedload(EndUserSession.user),
                joinedload(RefreshToken.session).joinedload(EndUserSession.device),
            )
            .order_by(RefreshToken.id.desc())
        ).scalars().all()
        for candidate in candidates:
            if verify_password(refresh_token, candidate.token_hash):
                return candidate
        return None

    def rotate_refresh_token(self, *, source: RefreshToken, new_token_hash: str, expires_at: datetime) -> RefreshToken:
        source.revoked_at = datetime.utcnow()
        source.revoke_reason = 'rotated'
        rotated = RefreshToken(
            session_id=source.session_id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            rotated_from_id=source.id,
        )
        self.db.add(rotated)
        self.db.flush()
        return rotated

    def revoke_refresh_token(self, refresh_token: RefreshToken, *, reason: str) -> None:
        if refresh_token.revoked_at is None:
            refresh_token.revoked_at = datetime.utcnow()
            refresh_token.revoke_reason = reason

    def revoke_refresh_tokens_for_session(self, session_pk: int, *, reason: str) -> None:
        tokens = self.db.execute(select(RefreshToken).where(RefreshToken.session_id == session_pk)).scalars().all()
        for token in tokens:
            self.revoke_refresh_token(token, reason=reason)

    def update_session_access(self, session: EndUserSession, *, access_token_hash: str, expires_at: datetime) -> None:
        now = datetime.utcnow()
        session.access_token_hash = access_token_hash
        session.expires_at = expires_at
        session.last_seen_at = now
        session.auth_state = 'authenticated_active'

    def touch_session(self, session: EndUserSession) -> None:
        session.last_seen_at = datetime.utcnow()

    def revoke_session(self, session: EndUserSession, *, reason: str) -> None:
        if session.revoked_at is None:
            session.revoked_at = datetime.utcnow()
        session.auth_state = f'revoked:{reason}'

    def set_session_auth_state(self, session: EndUserSession, *, auth_state: str) -> None:
        session.auth_state = auth_state

    def get_session_by_access_token_hash(self, access_token_hash: str) -> EndUserSession | None:
        return self.db.execute(
            select(EndUserSession)
            .options(joinedload(EndUserSession.user), joinedload(EndUserSession.device))
            .where(EndUserSession.access_token_hash == access_token_hash)
        ).scalars().first()

    def list_audit_logs_for_user(
        self,
        user_id: int,
        *,
        event_types: set[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[AuditLog]:
        query = select(AuditLog).where(AuditLog.target_user_id == str(user_id))
        if event_types:
            query = query.where(AuditLog.event_type.in_(sorted(event_types)))
        query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return list(self.db.execute(query).scalars().all())

    def count_audit_logs_for_user(
        self,
        user_id: int,
        *,
        event_types: set[str] | None = None,
    ) -> int:
        query = select(func.count()).select_from(AuditLog).where(AuditLog.target_user_id == str(user_id))
        if event_types:
            query = query.where(AuditLog.event_type.in_(sorted(event_types)))
        return self.db.execute(query).scalar_one()

    def touch_device(self, device: Device, *, client_version: str | None = None) -> None:
        now = datetime.utcnow()
        if client_version:
            device.client_version = client_version
        device.last_seen_at = now

    def set_device_status(self, device: Device, *, status: str) -> None:
        device.status = status

    def write_audit_log(self, *, event_type: str, actor_type: str, actor_id: str | None, target_user_id: str | None, target_device_id: str | None, target_session_id: str | None, request_id: str | None, trace_id: str | None, details_json: str | None) -> None:
        self.db.add(AuditLog(event_type=event_type, actor_type=actor_type, actor_id=actor_id, target_user_id=target_user_id, target_device_id=target_device_id, target_session_id=target_session_id, request_id=request_id, trace_id=trace_id, details_json=details_json))
