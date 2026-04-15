# Remote Database Schema Draft

## Purpose

Freeze the Phase 0 data-model responsibilities and key relationships for the remote system before runtime implementation begins.

## Canonical scope

Phase 0 freezes:

- table responsibilities
- key relationships
- identity/session/token separation
- minimum recommended indexes

Phase 0 does not freeze final SQL migrations.

---

## Tables and responsibilities

### `users`

Managed-user records for local desktop auth.

Key responsibility:
- identity for end-user auth domain

Key fields:
- `id`
- `username`
- `display_name`
- `email`
- `phone`
- `status`
- `tenant_id` (optional)
- `created_at`
- `updated_at`

### `user_credentials`

Credential storage for managed users.

Key responsibility:
- authentication secret material only

Key fields:
- `user_id`
- `password_hash`
- `password_algo`
- `password_updated_at`
- `mfa_enabled`
- `mfa_secret` (optional)

### `licenses`

License truth for a managed user.

Key responsibility:
- license and grace policy

Key fields:
- `id`
- `user_id`
- `license_status`
- `plan_code`
- `starts_at`
- `expires_at`
- `offline_grace_hours`
- `revoked_at`
- `disabled_at`
- `created_at`
- `updated_at`

### `user_entitlements`

Fine-grained capability records for a managed user.

Key responsibility:
- entitlement membership

Key fields:
- `id`
- `user_id`
- `entitlement`
- `source`
- `created_at`

### `devices`

Physical/logical device registry.

Key responsibility:
- device identity and platform metadata

Key fields:
- `id`
- `device_id`
- `device_name`
- `platform`
- `client_version`
- `status`
- `first_seen_at`
- `last_seen_at`
- `created_at`
- `updated_at`

### `user_devices`

Binding relation between a managed user and a device.

Key responsibility:
- current and historical device binding truth

Key fields:
- `id`
- `user_id`
- `device_id`
- `binding_status`
- `bound_at`
- `unbound_at`
- `last_auth_at`
- `created_at`
- `updated_at`

### `sessions`

Server-side end-user auth sessions.

Key responsibility:
- current managed-user remote session truth

Key fields:
- `id`
- `session_id`
- `user_id`
- `device_id`
- `auth_state`
- `issued_at`
- `expires_at`
- `last_seen_at`
- `revoked_at`
- `created_at`
- `updated_at`

### `refresh_tokens`

Tracked refresh-token records.

Key responsibility:
- refresh rotation and revocation lineage

Key fields:
- `id`
- `session_id`
- `token_hash`
- `issued_at`
- `expires_at`
- `rotated_from_id`
- `revoked_at`
- `revoke_reason`

### `admin_users`

Admin-operator identity records.

Key responsibility:
- identity for admin auth domain

Key fields:
- `id`
- `username`
- `display_name`
- `status`
- `created_at`
- `updated_at`

### `admin_roles`

Admin role catalog.

Key responsibility:
- RBAC role definitions

Key fields:
- `id`
- `role_name`
- `description`

### `admin_user_roles`

Role assignments for admin users.

Key responsibility:
- admin RBAC relationship

Key fields:
- `admin_user_id`
- `admin_role_id`
- `created_at`

### `audit_logs`

Audit trail for auth/admin behavior.

Key responsibility:
- immutable operational trace for sensitive actions

Key fields:
- `id`
- `event_type`
- `actor_type`
- `actor_id`
- `target_user_id`
- `target_device_id`
- `target_session_id`
- `request_id`
- `trace_id`
- `details_json`
- `created_at`

---

## Key relationships

```text
users ──< user_credentials
users ──< licenses
users ──< user_entitlements
users ──< user_devices >── devices
users ──< sessions >── devices
sessions ──< refresh_tokens

admin_users ──< admin_user_roles >── admin_roles

audit_logs -> actor / target references
```

### Freeze rules for relationships

- `sessions.user_id` references a managed user, not an admin user
- `sessions.device_id` references a device record
- `refresh_tokens.session_id` references an end-user session
- `admin_user_roles` exists only for admin-operator auth domain
- `audit_logs` may point to either managed-user or admin actors via `actor_type`

---

## Identity-domain freeze

The schema itself reflects two auth domains:

- managed-user domain:
  - `users`
  - `user_credentials`
  - `licenses`
  - `user_entitlements`
  - `user_devices`
  - `sessions`
  - `refresh_tokens`

- admin-operator domain:
  - `admin_users`
  - `admin_roles`
  - `admin_user_roles`

These domains must not silently collapse into one session model during Phase 1.

---

## Minimum index recommendations

- `users.username`
- `licenses.user_id`
- `licenses.license_status`
- `devices.device_id`
- `user_devices.user_id`
- `user_devices.device_id`
- `sessions.session_id`
- `sessions.user_id`
- `sessions.device_id`
- `refresh_tokens.session_id`
- `audit_logs.created_at`
- `audit_logs.event_type`
- `audit_logs.target_user_id`

---

## Schema freeze vs migration rule

- This document freezes the schema draft only.
- Real business migrations are generated in Phase 1.
- Phase 1 migrations must not silently redefine these responsibilities/relationships without updating the frozen docs first.
