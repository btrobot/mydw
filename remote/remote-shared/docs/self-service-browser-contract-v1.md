# Self-Service Browser Contract v1

## Purpose

Freeze the browser-facing auth/session assumptions required by the future
`remote-portal` before any portal UI work begins.

This document is part of **PR-B0.1** and applies only to the self-service
surface.

## Canonical route set

Portal work must target:

- `GET /self/me`
- `GET /self/devices`
- `GET /self/sessions`
- `GET /self/activity`
- `POST /self/sessions/{session_id}/revoke`

`GET /me` remains a legacy compatibility route during B0, but it is not the
canonical portal bootstrap route.

## Browser token model

- the browser uses bearer-token authorization for `/self/*` requests
- portal bootstrap sequence is:
  1. `POST /login`
  2. persist access + refresh token according to Program B implementation rules
  3. `GET /self/me` to fetch current portal-facing auth context
- refresh continues through `POST /refresh`
- logout continues through `POST /logout`

## Current-user scope rule

All `/self/*` routes are scoped to the currently signed-in managed user.

They must not require admin credentials and must not expose admin-operator
session semantics.

## Legacy compatibility rule

- `/self/me` is canonical for Program B and any future portal work
- `/me` may remain for compatibility while legacy clients migrate
- `/me` and `/self/me` must preserve the same managed-user auth/session/error
  behavior during B0
- legacy-only payload extras may differ while compatibility is being preserved;
  portal-facing fields are frozen by `/self/me`

## Program C exclusion rule

The self-service browser contract must not freeze:

- `tenant_id`
- org hierarchy
- SSO semantics
- MFA semantics
- enterprise identity assumptions

If legacy managed-user routes still carry compatibility fields such as
`tenant_id`, Program B must treat them as non-contractual and must not depend on
them.

## Recent activity rule

`GET /self/activity` exists so the future portal can render recent activity
without depending on admin audit APIs.

The response is a redacted self-service projection:

- allowed event types:
  - `login_succeeded`
  - `login_failed`
  - `session_refreshed`
  - `session_revoked`
  - `device_bound`
  - `device_unbound`
- required fields:
  - `id`
  - `event_type`
  - `created_at`
  - `summary`
- optional fields:
  - `device_id`
  - `session_id`
- no admin-only fields
- no raw audit payloads
- no internal-only request metadata

## Separation from admin surface

The portal/browser contract must not depend on:

- `/admin/*` routes
- admin audit response shapes
- admin RBAC semantics
- admin session assumptions

## Reviewer checklist

After reading this document, a reviewer should be able to answer:

1. which routes are canonical for portal bootstrap?
2. how does `/self/me` relate to legacy `/me`?
3. what browser token assumptions are frozen by B0?
4. how does the portal get recent activity without using admin APIs?
5. which Program C fields are intentionally excluded?
