# Remote Full System v1 Operating Model

## Purpose

Define the authoritative operating model for **Remote Full System v1** so later
deployment, portal, and governance work use the same system assumptions.

## v1 Scope Statement

Remote Full System v1 is a **single-tenant productionized remote platform**.

It includes:

- `remote-backend`
- `remote-admin`
- a planned minimal end-user portal
- release/promotion/rollback evidence discipline

It does **not** include:

- multi-tenant runtime behavior
- org hierarchy
- SSO providers
- MFA flows
- enterprise identity expansion

Those belong to post-v1 **Platform Expansion** work.

## System Components

### `remote-backend`

Authoritative source of:

- auth truth
- device/session/license/entitlement state
- admin APIs
- self-service APIs (planned)
- audit and metrics

### `remote-admin`

Operator-facing frontend for:

- auth admins
- support users
- operational review and control

### `remote-portal` (planned)

End-user-facing frontend for:

- self-service authorization views
- self-service session/device actions

## Environment Model

### `dev`

- local engineering environment
- development bootstrap conveniences are allowed
- rapid iteration and local verification are the priority

### `staging`

- production-like validation environment
- no development auto-seeding behavior
- non-default secrets required
- promotion evidence and rollback validation required

### `prod`

- release target
- no development bootstrap behavior
- explicit release evidence required before promotion

## Trust Boundaries

### Public user-facing backend surface

- end-user auth routes
- future self-service routes

### Internal/operator-facing surface

- admin routes
- operator workflows
- promotion/rollback/runbook execution

### Frontend rule

Frontends display and operate on backend truth; they do not infer auth truth
locally beyond UI projection.

## Deployment Topology Baseline

Remote Full System v1 assumes:

- one backend service (`remote-backend`)
- one operator frontend (`remote-admin`) served as a static build
- one end-user portal frontend (planned) served as a static build
- one authoritative backing database
- reverse proxy / TLS termination in front of exposed HTTP surfaces

This document defines the **deployment envelope only**. It does not freeze the
self-service browser/session contract; that is owned by **B0**.

Detailed startup, liveness, readiness, and example topology assets live in:

- `remote-full-system-deployment-topology-v1.md`

## Configuration Ownership

### Application-owned configuration

- backend runtime config
- frontend API base wiring
- auth/session/license/device policy config exposed by the app

### Infrastructure-owned configuration

- reverse proxy / TLS
- hostnames
- deployment process
- secret injection and storage
- backup/restore scheduling

## A0 / B0 Boundary

### A0 owns

- infra/runtime model
- environment boundaries
- deployment envelope
- release evidence model

### B0 owns

- self-service contract
- browser-facing auth/session assumptions
- portal/backend route freeze

## Cross-Program Guardrails

- No A0 artifact may silently introduce Program C scope.
- No A0 PR may introduce runtime behavior changes unless explicitly called out
  and separately verified.
- Any future portal hosting assumptions must remain compatible with this
  document's deployment envelope or trigger re-planning.

## Reviewer Checklist

After reading this document, a reviewer should be able to answer:

1. What runs in each environment?
2. What is public vs internal?
3. What is explicitly out of scope for Complete System v1?
