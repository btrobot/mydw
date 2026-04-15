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
