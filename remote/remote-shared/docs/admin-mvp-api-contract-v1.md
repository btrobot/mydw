# Admin MVP API Contract v1

## Scope

Phase 0 freezes only the admin MVP surface, not the full admin platform.

## Endpoints

- `POST /admin/login`
- `GET /admin/session`
- `GET /admin/users`
- `POST /admin/users`
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

## Additive list query contract in `v1`

The following optional query parameters are part of the implemented `v1` admin surface:

- `GET /admin/users`
  - `q`
  - `status`
  - `license_status`
  - `limit`
  - `offset`
- `GET /admin/devices`
  - `q`
  - `device_status`
  - `user_id`
  - `limit`
  - `offset`
- `GET /admin/sessions`
  - `q`
  - `auth_state`
  - `user_id`
  - `device_id`
  - `limit`
  - `offset`
- `GET /admin/audit-logs`
  - `event_type`
  - `actor_id`
  - `target_user_id`
  - `target_device_id`
  - `target_session_id`
  - `created_from`
  - `created_to`
  - `limit`
  - `offset`

These query parameters are optional additive `v1` extensions and must stay source/runtime aligned.

## Admin auth mechanism freeze

Admin APIs must be protected by an admin-operator auth domain that is independent from managed-user auth.

For Phase 1 PR1.3, the minimum admin auth surface is:

- `POST /admin/login`
- `GET /admin/session`

These endpoints establish the protected remote-admin shell without mixing semantics with end-user `/login`.
