from __future__ import annotations

import pytest

from app.services.admin_authz import (
    ADMIN_PERMISSION_AUDIT_READ,
    ADMIN_PERMISSION_DEVICES_READ,
    ADMIN_PERMISSION_DEVICES_WRITE,
    ADMIN_PERMISSION_METRICS_READ,
    ADMIN_PERMISSION_SESSION_READ,
    ADMIN_PERMISSION_SESSIONS_READ,
    ADMIN_PERMISSION_SESSIONS_REVOKE,
    ADMIN_PERMISSION_USERS_READ,
    ADMIN_PERMISSION_USERS_WRITE,
    AdminPermissionError,
    require_permission,
)


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        ("super_admin", ADMIN_PERMISSION_SESSION_READ),
        ("super_admin", ADMIN_PERMISSION_USERS_READ),
        ("super_admin", ADMIN_PERMISSION_USERS_WRITE),
        ("super_admin", ADMIN_PERMISSION_DEVICES_READ),
        ("super_admin", ADMIN_PERMISSION_DEVICES_WRITE),
        ("super_admin", ADMIN_PERMISSION_SESSIONS_READ),
        ("super_admin", ADMIN_PERMISSION_SESSIONS_REVOKE),
        ("super_admin", ADMIN_PERMISSION_AUDIT_READ),
        ("super_admin", ADMIN_PERMISSION_METRICS_READ),
        ("auth_admin", ADMIN_PERMISSION_USERS_WRITE),
        ("auth_admin", ADMIN_PERMISSION_DEVICES_WRITE),
        ("auth_admin", ADMIN_PERMISSION_SESSIONS_REVOKE),
        ("support_readonly", ADMIN_PERMISSION_USERS_READ),
        ("support_readonly", ADMIN_PERMISSION_DEVICES_READ),
        ("support_readonly", ADMIN_PERMISSION_SESSIONS_READ),
        ("support_readonly", ADMIN_PERMISSION_AUDIT_READ),
        ("support_readonly", ADMIN_PERMISSION_METRICS_READ),
    ],
)
def test_role_permissions_allow_expected_access(role: str, permission: str) -> None:
    policy = require_permission(role, permission)

    assert policy.role == role
    assert policy.allows(permission) is True


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        ("support_readonly", ADMIN_PERMISSION_USERS_WRITE),
        ("support_readonly", ADMIN_PERMISSION_DEVICES_WRITE),
        ("support_readonly", ADMIN_PERMISSION_SESSIONS_REVOKE),
        ("unknown_role", ADMIN_PERMISSION_USERS_READ),
    ],
)
def test_role_permissions_reject_unexpected_access(role: str, permission: str) -> None:
    with pytest.raises(AdminPermissionError):
        require_permission(role, permission)
