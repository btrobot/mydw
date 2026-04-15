# Support Runbook

## Purpose

Give operators one place to triage the most common remote-auth admin issues.

## 1. User cannot refresh / `/me` returns `revoked`

Check:

1. `/admin/users` -> locate the user
2. confirm `license_status`
3. inspect `/admin/audit-logs?target_user_id=<id>`

Likely causes:

- admin revoked the user
- license moved to `revoked`
- session was explicitly revoked

Operator action:

- use `Restore user` if the revoke was accidental
- ask the user to sign in again after restore

## 2. User sees `device_mismatch`

Check:

1. `/admin/devices` -> find the device
2. verify `device_status`
3. verify the currently bound `user_id`
4. inspect audit rows for `authorization_device_unbound`, `authorization_device_disabled`, or auth failure rows with `reason=device_mismatch`

Operator action:

- `Rebind device` to the intended user if ownership changed
- ask the user to sign in again after rebind

## 3. User is blocked by `authorization_disabled`

Check:

1. `/admin/users` status
2. `/admin/audit-logs?target_user_id=<id>`

Operator action:

- restore the user if the disable was accidental
- confirm `/me` and `/refresh` recover after re-login

## 4. Session must be cut off immediately

Use:

- `/admin/sessions`
- select the target session
- `Revoke session`

Expected result:

- session auth state changes
- subsequent `/me` or `/refresh` returns `revoked`
- audit contains `admin_session_revoked`

## 5. Read-only support role limitations

`support_readonly` can:

- view dashboard
- inspect users / devices / sessions / audit / metrics

`support_readonly` cannot:

- patch users
- revoke users
- disable/unbind/rebind devices
- revoke sessions

If a support operator needs to perform a write action, escalate to `auth_admin` or `super_admin`.
