# Remote Full System v1 - Deployment Topology and Runtime Health Baseline

## Purpose

Define the minimum deployable shape of **Remote Full System v1** and the
runtime health semantics operators must use during cold start, restart, and
dependency failure handling.

This document is the primary source of truth for **PR-A0.3**.

## Scope

### In Scope
- backend service topology
- admin static serving baseline
- planned portal static serving baseline
- reverse proxy / TLS termination expectations
- database dependency and startup ordering
- liveness, readiness, and startup semantics
- example deploy skeleton artifacts

### Out of Scope
- browser-facing portal route contract
- tenant/org-specific deploy shapes
- SSO/MFA or identity-provider deployment assumptions
- full production automation or platform-specific IaC

## Topology Baseline

Remote Full System v1 assumes the following deployable shape:

1. **`remote-backend`**
   - the only authoritative auth/API service
   - serves public auth APIs, admin APIs, and future self-service APIs
   - must run behind reverse proxy / TLS for exposed environments
2. **`remote-admin`**
   - a static frontend build served separately from backend runtime
   - consumes backend truth through configured API base URL only
3. **`remote-portal` (planned)**
   - a static frontend build that will consume the same backend truth center
   - hosting envelope is defined here, but browser/session contract remains B0-owned
4. **Authoritative backing database**
   - required dependency for backend correctness
   - may be managed externally or provisioned by the target platform
   - must be reachable before the system is considered ready
5. **Reverse proxy / TLS termination layer**
   - terminates TLS
   - routes backend API traffic to `remote-backend`
   - serves or proxies frontend static assets

## Environment Interpretation

### Dev
- local convenience is allowed
- static frontends may be opened directly from local build artifacts
- development bootstrap behavior may exist only in explicitly local flows

### Staging
- mirrors production topology as closely as practical
- uses explicit env and non-default secrets
- must prove startup order, backend health, admin access, and compatibility smoke

### Prod
- follows the same topology shape as staging
- must not rely on development bootstrap defaults
- requires promotion, rollback, and evidence rules defined elsewhere in A0

## Example Baseline Artifacts

The following A0.3 assets provide a lightweight deploy skeleton:

- `../deploy/docker-compose.a0-baseline.yml`
- `../deploy/nginx.remote-full-system-a0.conf`

They are **illustrative topology templates**, not final production automation.
They exist so reviewers and operators can infer service boundaries, proxy
relationships, and startup order without guessing.

## Runtime Health Contract

## 1. Liveness / health

Current runtime baseline:

- `remote-backend` exposes `GET /health`
- expected response body is `{"status": "ok"}`

Interpretation:

- a successful `/health` response means the backend process is running and can
  answer a minimal HTTP probe
- `/health` is a **liveness** signal
- `/health` alone does **not** prove database readiness, migration completion,
  admin bootstrap completion, or release readiness

## 2. Readiness

For A0.3, readiness is an **operator-gated condition** rather than a separate
HTTP endpoint contract.

The system is considered ready only after all of the following are true:

1. environment variables and secrets are injected explicitly
2. the authoritative database is reachable
3. migrations have completed successfully
4. backend startup completes and `/health` responds successfully
5. admin bootstrap is complete when the environment requires it
6. frontend API base URLs point to the intended backend origin
7. reverse proxy wiring targets the live backend and static frontend artifacts
8. compatibility or smoke checks for the environment have passed

## 3. Startup ordering expectations

Operators should bring the system up in this order:

1. prepare env/config/secrets from the A0.2 matrix
2. provision or confirm the authoritative database dependency
3. run backend migrations
4. start `remote-backend`
5. confirm `GET /health` returns `{"status": "ok"}`
6. run admin bootstrap when needed for the target environment
7. build/serve `remote-admin`
8. attach reverse proxy / TLS routing to the validated backend/admin targets
9. enable the planned `remote-portal` only when its artifact exists and B0/B
   contract work has landed
10. run compatibility smoke and environment-specific checks

## 4. Healthy vs ready

The distinction is intentional:

- **healthy** = process is alive and answering minimal probes
- **ready** = dependencies, migrations, config, bootstrap, and routing are all
  in an operator-approved state

No release or promotion decision may rely on `/health` alone.

## Operator Expectations

### Cold start
- expect backend readiness to lag behind process start until migrations and
  dependency checks are complete
- do not route public traffic until readiness conditions are satisfied

### Restart
- temporarily remove or drain backend traffic at the reverse proxy when restart
  behavior is uncertain
- re-check `/health`, env wiring, and smoke evidence before restoring traffic

### Dependency failure
- treat database outage or migration failure as **not ready** even if the
  backend process is still alive
- treat broken frontend API base wiring as **not ready** for operator release
  decisions

## A0 / B0 Boundary Note

This document defines:

- service shape
- dependency ordering
- proxy/TLS expectations
- health/readiness semantics

It does **not** freeze:

- portal URL structure
- browser session semantics
- self-service route contract

Those remain owned by **B0**.

## Related Documents

- `remote-full-system-operating-model-v1.md`
- `remote-full-system-env-config-matrix-v1.md`
- `staging-deploy-checklist.md`
- `admin-bootstrap-runbook.md`

## Reviewer Checklist

After reading this document and the example deploy assets, a reviewer should be
able to answer:

1. what components must exist in the deployable topology?
2. what depends on the authoritative database?
3. what is the required startup order?
4. why is `/health` insufficient as a readiness or release signal?
5. which browser-facing decisions are intentionally deferred to B0?
