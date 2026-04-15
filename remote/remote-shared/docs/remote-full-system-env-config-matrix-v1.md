# Remote Full System v1 - Env / Config / Secret Matrix

## Purpose

Define the canonical environment, config, and secret discipline for
**Remote Full System v1** across:

- `remote-backend`
- `remote-admin`
- planned `remote-portal`

This document is the primary source of truth for **A0.2**.

## Scope

### In Scope
- single-tenant config baseline
- dev / staging / prod environment expectations
- secret vs non-secret classification
- portal placeholder config baseline
- config loading and promotion discipline

### Out of Scope
- tenant-scoped config
- SSO / MFA provider secrets
- enterprise identity configuration

## Classification Rules

### Required secrets
Values that must never rely on committed defaults outside local development.

Examples:
- bootstrap/admin passwords
- compatibility harness admin/user passwords when targeting staging/prod
- any future portal credential or session secret

### Required non-secret runtime config
Values that are environment-specific but not secret.

Examples:
- app env
- host / port
- public base URLs
- API base URLs
- CORS origins

### Optional dev-only config
Values that may be kept simple or use convenience defaults in local development.

Examples:
- development bootstrap usernames
- local loopback base URLs
- local sqlite paths

## Canonical naming conventions

### Shared prefix
- `REMOTE_` for shared/system-level env

### Backend
- `REMOTE_BACKEND_*`

### Admin frontend
- `REMOTE_ADMIN_*`

### Portal frontend
- `REMOTE_PORTAL_*`

### Compatibility / smoke
- `REMOTE_COMPAT_*`

## Component matrix

## 1. Shared / system-level

| Variable | Classification | Required in | Notes |
|---|---|---|---|
| `REMOTE_ENV` | non-secret | dev/staging/prod | Top-level environment label |
| `REMOTE_STAGING_PUBLIC_BASE_URL` | non-secret | staging | Candidate backend public URL |
| `REMOTE_STAGING_ADMIN_BASE_URL` | non-secret | staging | Admin frontend URL |
| `REMOTE_STAGING_PORTAL_BASE_URL` | non-secret | staging when portal exists | Reserved for portal rollout |

## 2. Backend

| Variable | Classification | Required in | Notes |
|---|---|---|---|
| `REMOTE_BACKEND_APP_ENV` | non-secret | all envs | Must be explicit in staging/prod |
| `REMOTE_BACKEND_HOST` | non-secret | all envs | Bind host |
| `REMOTE_BACKEND_PORT` | non-secret | all envs | Bind port |
| `REMOTE_BACKEND_DATABASE_URL` | non-secret/runtime-sensitive | all envs | Production must use managed DB, not local sqlite |
| `REMOTE_BACKEND_CORS_ALLOW_ORIGINS` | non-secret | all envs | Must match admin/portal origins |
| `REMOTE_BACKEND_ADMIN_BOOTSTRAP_USERNAME` | non-secret | dev; explicit override in staging/prod | Must not stay on development default |
| `REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD` | secret | dev only if local convenience is accepted; override everywhere else | Must never remain a staging/prod default |
| `REMOTE_BACKEND_MINIMUM_SUPPORTED_VERSION` | non-secret | all envs | Auth policy value |
| `REMOTE_BACKEND_DEFAULT_OFFLINE_GRACE_HOURS` | non-secret | all envs | Auth policy value |

## 3. Admin frontend

| Variable | Classification | Required in | Notes |
|---|---|---|---|
| `REMOTE_ADMIN_PORT` | non-secret | dev/staging/prod if locally hosted | Static serving port or metadata |
| `REMOTE_ADMIN_API_BASE_URL` | non-secret | all envs | Must point to the correct backend |

## 4. Planned portal frontend

| Variable | Classification | Required in | Notes |
|---|---|---|---|
| `REMOTE_PORTAL_PORT` | non-secret | when portal exists | Reserved in v1 baseline |
| `REMOTE_PORTAL_API_BASE_URL` | non-secret | when portal exists | Must point to the same backend truth center |
| `REMOTE_PORTAL_PUBLIC_BASE_URL` | non-secret | staging/prod when portal exists | Public portal URL |

## 5. Compatibility / release smoke

| Variable | Classification | Required in | Notes |
|---|---|---|---|
| `REMOTE_COMPAT_BASE_URL` | non-secret | staging/prod smoke | HTTP-mode gate target |
| `REMOTE_COMPAT_USERNAME` | non-secret-ish fixture input | local/staging smoke | Use dedicated smoke user where appropriate |
| `REMOTE_COMPAT_PASSWORD` | secret | staging/prod smoke | Do not commit real values |
| `REMOTE_COMPAT_DEVICE_ID` | non-secret | smoke | Stable smoke device id |
| `REMOTE_COMPAT_ADMIN_USERNAME` | non-secret | staging/prod smoke | Dedicated smoke admin preferred |
| `REMOTE_COMPAT_ADMIN_PASSWORD` | secret | staging/prod smoke | Must come from env/secret store |

## Config loading discipline

1. Runtime behavior must depend only on explicit env/config, not implied deployment guesses.
2. Staging and prod must not inherit development bootstrap defaults.
3. Secret-bearing values must come from environment injection or secret manager materialization, not committed files.
4. Documentation examples may show placeholder values, but must label them as placeholders.
5. New component config must extend this matrix instead of inventing parallel conventions.

## Secret rotation baseline

- Bootstrap/admin secrets must be rotatable without editing database rows by hand.
- Rotation instructions must be documented in runbooks.
- Staging and prod must use non-default values.
- Future portal secrets must follow the same rule from day one.

## Config promotion baseline

- Dev -> staging promotion must explicitly review env differences.
- Staging -> prod promotion must reference captured release evidence.
- The environment matrix and promotion checklist must remain aligned.

## A0 / B0 boundary note

This matrix may reserve names for the future portal, but it does **not** freeze:

- browser auth semantics
- portal session contract
- self-service route contract

Those belong to **B0**.
