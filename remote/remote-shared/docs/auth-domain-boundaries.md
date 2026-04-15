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
- end-user remote sessions
- end-user token lifecycle
- end-user license / entitlement / device truth

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

## Repo boundary

`remote/` is an independent remote-system workspace.

It must not runtime-import business logic from the existing local backend/frontend.

The only allowed coupling to the local app is through:

- frozen contracts
- compatibility harness
- documentation
