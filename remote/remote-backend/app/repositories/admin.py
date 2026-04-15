from __future__ import annotations

from datetime import datetime

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import AdminSession, AdminUser, AuditLog, Device, EndUserSession, License, User, UserDevice, UserEntitlement


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_admin_user_by_username(self, username: str) -> AdminUser | None:
        return self.db.execute(select(AdminUser).where(AdminUser.username == username)).scalars().first()

    def get_admin_user_by_id(self, admin_user_id: int) -> AdminUser | None:
        return self.db.execute(select(AdminUser).where(AdminUser.id == admin_user_id)).scalars().first()

    def create_admin_session(
        self,
        *,
        session_id: str,
        admin_user_id: int,
        access_token_hash: str,
        expires_at: datetime,
    ) -> AdminSession:
        session = AdminSession(
            session_id=session_id,
            admin_user_id=admin_user_id,
            access_token_hash=access_token_hash,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_admin_session_by_access_token_hash(self, access_token_hash: str) -> AdminSession | None:
        return self.db.execute(
            select(AdminSession)
            .options(joinedload(AdminSession.admin_user))
            .where(AdminSession.access_token_hash == access_token_hash)
        ).scalars().first()

    def touch_admin_session(self, session: AdminSession) -> None:
        session.last_seen_at = datetime.utcnow()

    def list_users(self) -> list[User]:
        return list(
            self.db.execute(
                select(User).options(
                    joinedload(User.license),
                    joinedload(User.entitlements),
                    joinedload(User.bindings).joinedload(UserDevice.device),
                    joinedload(User.sessions),
                )
            ).unique().scalars().all()
        )

    def get_user_detail(self, user_id: int) -> User | None:
        return self.db.execute(
            select(User)
            .options(
                joinedload(User.license),
                joinedload(User.entitlements),
                joinedload(User.bindings).joinedload(UserDevice.device),
                joinedload(User.sessions),
            )
            .where(User.id == user_id)
        ).unique().scalars().first()

    def list_devices(self) -> list[Device]:
        return list(
            self.db.execute(
                select(Device).options(joinedload(Device.bindings).joinedload(UserDevice.user))
            ).unique().scalars().all()
        )

    def get_device_detail(self, device_id: str) -> Device | None:
        return self.db.execute(
            select(Device)
            .options(joinedload(Device.bindings).joinedload(UserDevice.user))
            .where(Device.device_id == device_id)
        ).unique().scalars().first()

    def list_sessions(self) -> list[EndUserSession]:
        return list(
            self.db.execute(
                select(EndUserSession).options(joinedload(EndUserSession.user), joinedload(EndUserSession.device))
            ).unique().scalars().all()
        )

    def get_session_detail(self, session_id: str) -> EndUserSession | None:
        return self.db.execute(
            select(EndUserSession)
            .options(joinedload(EndUserSession.user), joinedload(EndUserSession.device))
            .where(EndUserSession.session_id == session_id)
        ).unique().scalars().first()

    def list_audit_logs(
        self,
        *,
        event_type: str | None = None,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if target_user_id:
            query = query.where(AuditLog.target_user_id == target_user_id)
        if target_device_id:
            query = query.where(AuditLog.target_device_id == target_device_id)
        if created_from:
            query = query.where(AuditLog.created_at >= created_from)
        if created_to:
            query = query.where(AuditLog.created_at <= created_to)
        return list(self.db.execute(query).scalars().all())

    def count_active_sessions(self) -> int:
        return sum(
            1
            for session in self.list_sessions()
            if session.revoked_at is None and session.auth_state == 'authenticated_active'
        )

    def replace_entitlements(self, user_id: int, entitlements: list[str]) -> None:
        existing = self.db.execute(select(UserEntitlement).where(UserEntitlement.user_id == user_id)).scalars().all()
        for row in existing:
            self.db.delete(row)
        for entitlement in entitlements:
            self.db.add(UserEntitlement(user_id=user_id, entitlement=entitlement, source='admin_patch'))

    def ensure_license(self, user_id: int) -> License:
        license_record = self.db.execute(select(License).where(License.user_id == user_id)).scalars().first()
        if license_record is None:
            license_record = License(user_id=user_id, license_status='active')
            self.db.add(license_record)
            self.db.flush()
        return license_record

    def write_audit_log(
        self,
        *,
        event_type: str,
        actor_type: str,
        actor_id: str | None,
        target_user_id: str | None,
        target_device_id: str | None,
        target_session_id: str | None,
        request_id: str | None,
        trace_id: str | None,
        details_json: str | None,
    ) -> None:
        self.db.add(
            AuditLog(
                event_type=event_type,
                actor_type=actor_type,
                actor_id=actor_id,
                target_user_id=target_user_id,
                target_device_id=target_device_id,
                target_session_id=target_session_id,
                request_id=request_id,
                trace_id=trace_id,
                details_json=details_json,
            )
        )
