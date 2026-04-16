# Auth Domain Boundaries

## Purpose

Freeze the identity and responsibility boundaries for the remote system before runtime implementation starts.

## Identity domains

### Managed-user auth domain

This domain serves end users who authenticate from the local desktop client.

It owns:

- `/login`
- `/refresh`
- `/logout`
- `/me`
- `/self/me`
- `/self/devices`
- `/self/sessions`
- `/self/activity`
- `/self/sessions/{session_id}/revoke`
- end-user remote sessions
- end-user token lifecycle
- end-user license / entitlement / device truth

For B0, `/self/*` is the canonical self-service namespace for the future portal.
`/me` may remain as a legacy compatibility route, but portal work must target
`/self/me`.

### Admin-operator auth domain

This domain serves operators who log in to `remote-admin`.

It owns:

- admin login entrypoint
- admin sessions
- admin RBAC
- admin-facing audit actions

## Separation rule

Managed-user auth and admin-operator auth **must not** share:

- login entrypoints
- session semantics
- permission evaluation
- token lifecycle rules

They may reuse storage primitives later, but they must remain architecturally distinct.

## Self-service projection rule

Portal-facing self-service routes must not depend on admin-only response shapes
or expose Program C identity fields such as `tenant_id`.

`GET /self/activity` is a self-service projection and must not reuse the raw
admin audit payload contract.

## Repo boundary

`remote/` is an independent remote-system workspace.

It must not runtime-import business logic from the existing local backend/frontend.

The only allowed coupling to the local app is through:

- frozen contracts
- compatibility harness
- documentation
