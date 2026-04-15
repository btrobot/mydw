# Token and Session Model

## Purpose

Freeze the token/session semantics for Phase 0 so later implementation cannot drift.

## Managed-user auth model

### Access token

- short-lived bearer token
- used by the local desktop client for `/me`
- may be stateless or weak-state

### Refresh token

- long-lived relative to access token
- rotatable
- revocable
- must be persisted server-side in tracked form

### End-user remote session

- server-side session truth for a local desktop client user
- linked to a user and a device
- revoking a session invalidates its refresh path

## Admin auth model

### Admin session

- independent from end-user remote sessions
- used by `remote-admin`
- must not be treated as the same semantic class as a managed-user session

## Freeze rules

- access token semantics cannot silently change in Phase 1
- refresh token rotation rules cannot silently change in Phase 1
- admin session must remain separate from end-user remote session
- contract changes affecting token/session semantics require version review
