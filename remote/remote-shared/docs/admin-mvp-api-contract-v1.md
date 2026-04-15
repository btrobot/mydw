# Admin MVP API Contract v1

## Scope

Phase 0 freezes only the admin MVP surface, not the full admin platform.

## Endpoints

- `POST /admin/login`
- `GET /admin/session`
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}`
- `POST /admin/users/{user_id}/revoke`
- `POST /admin/users/{user_id}/restore`
- `GET /admin/devices`
- `GET /admin/devices/{device_id}`
- `POST /admin/devices/{device_id}/unbind`
- `POST /admin/devices/{device_id}/disable`
- `POST /admin/devices/{device_id}/rebind`
- `GET /admin/sessions`
- `POST /admin/sessions/{session_id}/revoke`
- `GET /admin/audit-logs`

## Admin auth mechanism freeze

Admin APIs must be protected by an admin-operator auth domain that is independent from managed-user auth.

For Phase 1 PR1.3, the minimum admin auth surface is:

- `POST /admin/login`
- `GET /admin/session`

These endpoints establish the protected remote-admin shell without mixing semantics with end-user `/login`.
