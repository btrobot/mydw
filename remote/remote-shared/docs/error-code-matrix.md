# Error Code Matrix

## Purpose

Freeze the first release error semantics for the remote auth system.

## Canonical error codes

| error_code | HTTP | Meaning |
|---|---:|---|
| `invalid_credentials` | 401 | Username/password invalid |
| `token_expired` | 401 | Access or refresh token expired |
| `revoked` | 403 | Remote authorization revoked |
| `disabled` | 403 | User or license disabled |
| `device_mismatch` | 403 | Device does not match remote binding |
| `minimum_version_required` | 403 | Client version below allowed minimum |
| `network_timeout` | 503 | Upstream unavailable / timeout |
| `too_many_requests` | 429 | Rate limit exceeded |
| `forbidden` | 403 | Admin access forbidden |
| `not_found` | 404 | Requested admin resource missing |

## Freeze rules

- The meaning of any code above is frozen for `v1`.
- Adding a new required code or changing the semantics of an existing one is a breaking change.
- Breaking changes require:
  - version review
  - OpenAPI update
  - fixture update
  - compatibility harness update

## Validation payload rule

- `422` validation failures use the FastAPI validation payload shape (`HTTPValidationError`).
- They are intentionally **not** part of the `error_code` matrix above.
- Converting a validation failure into an `ErrorResponse` with a new `error_code` is a breaking change for `v1`.

## Admin details semantics

- `forbidden` may include `details.required_permission` for admin authorization failures.
- `not_found` may include a target identifier such as `user_id`, `device_id`, or `session_id`.
- These `details` keys are additive diagnostics; callers must not depend on every key being present in every response.

## Self-service details semantics

- self-service routes reuse the same `v1` `error_code` matrix; B0 does not add a
  new self-service-specific code
- `422` validation failures remain FastAPI validation payloads, not a new
  `error_code`
