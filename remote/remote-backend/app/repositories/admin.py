from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, cast, func, literal, or_, select
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

    @staticmethod
    def _apply_user_filters(query, *, q: str | None = None, status: str | None = None, license_status: str | None = None):
        if q:
            pattern = f'%{q.lower()}%'
            query = query.where(
                or_(
                    func.lower(User.username).like(pattern),
                    func.lower(func.coalesce(User.display_name, '')).like(pattern),
                    func.lower(func.coalesce(User.email, '')).like(pattern),
                    func.lower(literal('u_') + cast(User.id, String)).like(pattern),
                )
            )
        if status:
            query = query.where(User.status == status)
        if license_status:
            query = query.where(License.license_status == license_status)
        return query

    def list_users(
        self,
        *,
        q: str | None = None,
        status: str | None = None,
        license_status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
        query = self._apply_user_filters(
            (
            select(User)
            .outerjoin(License)
            .options(
                joinedload(User.license),
                joinedload(User.entitlements),
                joinedload(User.bindings).joinedload(UserDevice.device),
                joinedload(User.sessions),
            )
            .order_by(User.updated_at.desc(), User.id.desc())
            ),
            q=q,
            status=status,
            license_status=license_status,
        )
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return list(self.db.execute(query).unique().scalars().all())

    def count_users(
        self,
        *,
        q: str | None = None,
        status: str | None = None,
        license_status: str | None = None,
    ) -> int:
        filtered = self._apply_user_filters(
            select(User.id).outerjoin(License),
            q=q,
            status=status,
            license_status=license_status,
        ).distinct().subquery()
        return self.db.execute(select(func.count()).select_from(filtered)).scalar_one()

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

    @staticmethod
    def _apply_device_filters(query, *, q: str | None = None, device_status: str | None = None, user_id: int | None = None):
        if q:
            pattern = f'%{q.lower()}%'
            query = query.where(
                or_(
                    func.lower(Device.device_id).like(pattern),
                    func.lower(func.coalesce(Device.client_version, '')).like(pattern),
                    func.lower(func.coalesce(User.username, '')).like(pattern),
                    func.lower(func.coalesce(User.display_name, '')).like(pattern),
                    func.lower(literal('u_') + cast(User.id, String)).like(pattern),
                )
            )
        if device_status:
            query = query.where(Device.status == device_status)
        if user_id is not None:
            query = query.where(UserDevice.binding_status == 'bound', User.id == user_id)
        return query

    def list_devices(
        self,
        *,
        q: str | None = None,
        device_status: str | None = None,
        user_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Device]:
        query = self._apply_device_filters(
            (
            select(Device)
            .outerjoin(UserDevice)
            .outerjoin(User)
            .options(joinedload(Device.bindings).joinedload(UserDevice.user))
            .order_by(Device.updated_at.desc(), Device.id.desc())
            ),
            q=q,
            device_status=device_status,
            user_id=user_id,
        )
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return list(self.db.execute(query).unique().scalars().all())

    def count_devices(
        self,
        *,
        q: str | None = None,
        device_status: str | None = None,
        user_id: int | None = None,
    ) -> int:
        filtered = self._apply_device_filters(
            select(Device.id).outerjoin(UserDevice).outerjoin(User),
            q=q,
            device_status=device_status,
            user_id=user_id,
        ).distinct().subquery()
        return self.db.execute(select(func.count()).select_from(filtered)).scalar_one()

    def get_device_detail(self, device_id: str) -> Device | None:
        return self.db.execute(
            select(Device)
            .options(joinedload(Device.bindings).joinedload(UserDevice.user))
            .where(Device.device_id == device_id)
        ).unique().scalars().first()

    @staticmethod
    def _apply_session_filters(query, *, q: str | None = None, auth_state: str | None = None, user_id: int | None = None, device_id: str | None = None):
        if q:
            pattern = f'%{q.lower()}%'
            query = query.where(
                or_(
                    func.lower(EndUserSession.session_id).like(pattern),
                    func.lower(Device.device_id).like(pattern),
                    func.lower(User.username).like(pattern),
                    func.lower(literal('u_') + cast(User.id, String)).like(pattern),
                )
            )
        if auth_state:
            query = query.where(EndUserSession.auth_state == auth_state)
        if user_id is not None:
            query = query.where(User.id == user_id)
        if device_id:
            query = query.where(Device.device_id == device_id)
        return query

    def list_sessions(
        self,
        *,
        q: str | None = None,
        auth_state: str | None = None,
        user_id: int | None = None,
        device_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[EndUserSession]:
        query = self._apply_session_filters(
            (
            select(EndUserSession)
            .join(User)
            .join(Device)
            .options(joinedload(EndUserSession.user), joinedload(EndUserSession.device))
            .order_by(EndUserSession.last_seen_at.desc(), EndUserSession.id.desc())
            ),
            q=q,
            auth_state=auth_state,
            user_id=user_id,
            device_id=device_id,
        )
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return list(self.db.execute(query).unique().scalars().all())

    def count_sessions(
        self,
        *,
        q: str | None = None,
        auth_state: str | None = None,
        user_id: int | None = None,
        device_id: str | None = None,
    ) -> int:
        filtered = self._apply_session_filters(
            select(EndUserSession.id).join(User).join(Device),
            q=q,
            auth_state=auth_state,
            user_id=user_id,
            device_id=device_id,
        ).subquery()
        return self.db.execute(select(func.count()).select_from(filtered)).scalar_one()

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
        target_session_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[AuditLog]:
        query = self._apply_audit_filters(
            select(AuditLog),
            event_type=event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            created_from=created_from,
            created_to=created_to,
        ).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return list(self.db.execute(query).scalars().all())

    @staticmethod
    def _apply_audit_filters(
        query,
        *,
        event_type: str | None = None,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        detail_reason: str | None = None,
        event_types: set[str] | None = None,
    ):
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        if event_types:
            query = query.where(AuditLog.event_type.in_(sorted(event_types)))
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if target_user_id:
            query = query.where(AuditLog.target_user_id == target_user_id)
        if target_device_id:
            query = query.where(AuditLog.target_device_id == target_device_id)
        if target_session_id:
            query = query.where(AuditLog.target_session_id == target_session_id)
        if created_from:
            query = query.where(AuditLog.created_at >= created_from)
        if created_to:
            query = query.where(AuditLog.created_at <= created_to)
        if detail_reason:
            query = query.where(AuditLog.details_json.contains(f'"reason": "{detail_reason}"'))
        return query

    def count_audit_logs(
        self,
        *,
        event_type: str | None = None,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        detail_reason: str | None = None,
        event_types: set[str] | None = None,
    ) -> int:
        filtered = self._apply_audit_filters(
            select(AuditLog.id),
            event_type=event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            created_from=created_from,
            created_to=created_to,
            detail_reason=detail_reason,
            event_types=event_types,
        ).subquery()
        return self.db.execute(select(func.count()).select_from(filtered)).scalar_one()

    def list_recent_audit_logs(
        self,
        *,
        event_types: set[str],
        limit: int = 5,
    ) -> list[AuditLog]:
        query = self._apply_audit_filters(
            select(AuditLog),
            event_types=event_types,
        ).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
        return list(self.db.execute(query).scalars().all())

    def count_active_sessions(self) -> int:
        query = select(func.count()).select_from(EndUserSession).where(
            EndUserSession.revoked_at.is_(None),
            EndUserSession.auth_state == 'authenticated_active',
        )
        return self.db.execute(query).scalar_one()

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
