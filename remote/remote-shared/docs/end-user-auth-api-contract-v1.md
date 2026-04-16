# End-user Auth API Contract v1

## Managed-user auth endpoints

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /me`

## Canonical self-service endpoints for the future portal

- `GET /self/me`
- `GET /self/devices`
- `GET /self/sessions`
- `GET /self/activity`
- `POST /self/sessions/{session_id}/revoke`

## Canonical route rule

- `GET /self/me` is the canonical portal-facing current-user route.
- `GET /me` remains a legacy compatibility route during B0.
- `/me` and `/self/me` must keep the same managed-user auth/session/error
  behavior during B0.
- Legacy-only payload extras may remain on `/me` temporarily, but Program B and
  any future portal work must target `/self/me`.

## Required success payload fields

### `POST /login`

- `access_token`
- `refresh_token`
- `expires_at`
- `token_type`
- `user`
- `license_status`
- `entitlements`
- `device_id`
- `device_status`
- `offline_grace_until` (optional)
- `minimum_supported_version` (optional)

### `POST /refresh`

- `access_token`
- `refresh_token`
- `expires_at`
- `token_type`
- `user`
- `license_status`
- `entitlements`
- `device_id`
- `device_status`
- `offline_grace_until` (optional)
- `minimum_supported_version` (optional)

### `GET /self/me`

- `user`
- `license_status`
- `entitlements`
- `device_id`
- `device_status`
- `offline_grace_until` (optional)
- `minimum_supported_version` (optional)

### `GET /self/devices`

- `items`
- `total`

### `GET /self/sessions`

- `items`
- `total`

### `GET /self/activity`

- `items`
- `total`

### `POST /self/sessions/{session_id}/revoke`

- `success`
- `session_id`
- `auth_state`
- `already_revoked`

### `POST /self/sessions/{session_id}/revoke` semantics

- own existing active session -> `200`
- own existing already-revoked session -> `200` with `already_revoked=true`
- revoked / disabled / device-mismatch auth context -> `403`
- missing session -> `404`
- foreign session -> `404`

The response body shape is:

```json
{
  "success": true,
  "session_id": "sess_123",
  "auth_state": "revoked",
  "already_revoked": false
}
```

## Required request fields

### `POST /login`

- `username`
- `password`
- `device_id`
- `client_version`

### `POST /refresh`

- `refresh_token`
- `device_id`
- `client_version`

### `POST /logout`

- `refresh_token`
- `device_id`

### `POST /self/sessions/{session_id}/revoke`

- path parameter: `session_id`

## Self-service payload rules

- `/self/*` payloads are portal-safe and must not freeze `tenant_id` or any
  other Program C identity field.
- Program B must not depend on `tenant_id`, even if legacy `/me` compatibility
  continues to expose it temporarily.
- `/self/activity` is a redacted self-service projection, not the raw admin
  audit payload shape.

## `GET /self/activity` contract details

### Allowed event types

- `login_succeeded`
- `login_failed`
- `session_refreshed`
- `session_revoked`
- `device_bound`
- `device_unbound`

### Response fields

- `id`
- `event_type`
- `created_at`
- `summary`
- `device_id` (optional)
- `session_id` (optional)

### Ordering and pagination

- newest first
- `limit` + `offset`
- default `limit=20`
- maximum `limit=100`

### Redaction rule

- no admin-role fields
- no raw audit payloads
- no internal-only request metadata

## Error semantics

Must align with `error-code-matrix.md`.

### Additional operational auth error

- `too_many_requests` - returned when login rate limiting is triggered

## Self-service error semantics

The self-service surface reuses existing `v1` error codes.

- no self-service-specific `error_code` is introduced in B0
- `POST /self/sessions/{session_id}/revoke` may still return the standard
  self-service `403` error envelope when the current auth context is revoked,
  disabled, or device-mismatched
- `422` remains FastAPI validation payload shape, not a new `error_code`
- `POST /self/sessions/{session_id}/revoke` uses a `404` error envelope for both
  missing sessions and foreign-session masking

## Self-service audit semantics

`POST /self/sessions/{session_id}/revoke` must write:

- `event_type=self_session_revoked`
- `actor_type=user`
- `target_session_id=<public session id>`
- `details.already_revoked=<bool>`
