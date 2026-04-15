from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdminRolePolicy:
    role: str
    permissions: frozenset[str]

    def allows(self, permission: str) -> bool:
        return permission in self.permissions


ADMIN_PERMISSION_SESSION_READ = 'admin.session.read'
ADMIN_PERMISSION_USERS_READ = 'users.read'
ADMIN_PERMISSION_USERS_WRITE = 'users.write'
ADMIN_PERMISSION_DEVICES_READ = 'devices.read'
ADMIN_PERMISSION_DEVICES_WRITE = 'devices.write'
ADMIN_PERMISSION_SESSIONS_READ = 'sessions.read'
ADMIN_PERMISSION_SESSIONS_REVOKE = 'sessions.revoke'
ADMIN_PERMISSION_AUDIT_READ = 'audit.read'
ADMIN_PERMISSION_METRICS_READ = 'metrics.read'

ALL_ADMIN_PERMISSIONS = frozenset(
    {
        ADMIN_PERMISSION_SESSION_READ,
        ADMIN_PERMISSION_USERS_READ,
        ADMIN_PERMISSION_USERS_WRITE,
        ADMIN_PERMISSION_DEVICES_READ,
        ADMIN_PERMISSION_DEVICES_WRITE,
        ADMIN_PERMISSION_SESSIONS_READ,
        ADMIN_PERMISSION_SESSIONS_REVOKE,
        ADMIN_PERMISSION_AUDIT_READ,
        ADMIN_PERMISSION_METRICS_READ,
    }
)
ADMIN_READ_PERMISSIONS = frozenset(
    {
        ADMIN_PERMISSION_SESSION_READ,
        ADMIN_PERMISSION_USERS_READ,
        ADMIN_PERMISSION_DEVICES_READ,
        ADMIN_PERMISSION_SESSIONS_READ,
        ADMIN_PERMISSION_AUDIT_READ,
        ADMIN_PERMISSION_METRICS_READ,
    }
)
ADMIN_WRITE_PERMISSIONS = frozenset(
    {
        ADMIN_PERMISSION_USERS_WRITE,
        ADMIN_PERMISSION_DEVICES_WRITE,
        ADMIN_PERMISSION_SESSIONS_REVOKE,
    }
)


ADMIN_PERMISSION_MATRIX: dict[str, AdminRolePolicy] = {
    'super_admin': AdminRolePolicy(
        role='super_admin',
        permissions=ADMIN_READ_PERMISSIONS | ADMIN_WRITE_PERMISSIONS,
    ),
    'auth_admin': AdminRolePolicy(
        role='auth_admin',
        permissions=ADMIN_READ_PERMISSIONS | ADMIN_WRITE_PERMISSIONS,
    ),
    'support_readonly': AdminRolePolicy(
        role='support_readonly',
        permissions=ADMIN_READ_PERMISSIONS,
    ),
}


class AdminPermissionError(Exception):
    def __init__(self, role: str, permission: str) -> None:
        super().__init__(f'role={role} lacks permission={permission}')
        self.role = role
        self.permission = permission


def require_permission(role: str, permission: str) -> AdminRolePolicy:
    policy = ADMIN_PERMISSION_MATRIX.get(role)
    if policy is None or not policy.allows(permission):
        raise AdminPermissionError(role, permission)
    return policy
