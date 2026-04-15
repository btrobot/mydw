# End-user Auth API Contract v1

## Endpoints

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /me`

## Required success payload fields

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

## Error semantics

Must align with `error-code-matrix.md`.

### Additional operational auth error

- `too_many_requests` - returned when login rate limiting is triggered
