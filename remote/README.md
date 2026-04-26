# Remote Workspace

This directory contains the remote authorization center MVP workspace.

## Layout

- `remote-backend/` - FastAPI remote auth/admin backend
- `remote-admin/` - protected admin console
- `remote-shared/` - OpenAPI, compatibility harness, release docs, runbooks
- `.env.example` - shared env template for dev/staging bootstrap

## Current status

The current remote system includes the MVP and Phase 4 hardening assets:

- remote auth core and admin runtime
- admin RBAC hardening + actor-level audit
- dashboard / audit operational UX
- users / devices / sessions rich operations UX
- release-gate docs and workflow assets
- admin bootstrap + staging/support runbooks
- Phase 4 hardening of contracts, runtime reliability, UX resilience, and release readiness

## Remote Full System v1 planning baseline

Authoritative planning assets for the next upgrade stage:

- `.omx/plans/prd-remote-full-system.md`
- `.omx/plans/test-spec-remote-full-system.md`
- `.omx/plans/prd-remote-full-system-a0-pr-plan.md`
- `remote/remote-shared/docs/remote-full-system-operating-model-v1.md`
- `remote/remote-shared/docs/remote-full-system-env-config-matrix-v1.md`
- `remote/remote-shared/docs/remote-full-system-deployment-topology-v1.md`
- `remote/remote-shared/docs/linux-deployment-runbook.md`
- `remote/remote-shared/docs/staging-env-dry-run-artifact-v1.md`
- `remote/remote-shared/docs/restore-recovery-runbook.md`
- `remote/remote-shared/docs/release-governance-tabletop-record-v1.md`

## Local startup

### 1. Prepare env

Copy `remote/.env.example` to the repo-root `.env` and adjust values.

For a Linux host deployment baseline, prefer `remote/.env.linux.example`.

### 2. Start the backend

```bash
python remote/remote-backend/scripts/migrate.py ensure-head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

Working directory:

```bash
cd remote/remote-backend
```

### 3. Bootstrap the first admin user

```bash
set BOOTSTRAP_ADMIN_PASSWORD=admin-secret
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
```

See `remote/remote-shared/docs/admin-bootstrap-runbook.md` for dev/staging/prod notes.

### Database schema changes

Schema changes must go through Alembic revisions under `remote/remote-backend/migrations/versions/`.
Do not add new database changes through deleted runner code paths or manual `schema_migrations` updates.

### 4. Build and open the admin console

```bash
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run build:react
```

Then open:

```text
remote/remote-admin/dist-react/index.html?apiBase=http://127.0.0.1:8100
```

## Linux deployment

For a Linux host deployment baseline, copy `remote/.env.linux.example` to the
repo-root `.env`, then use:

```bash
remote/remote-shared/deploy/deploy.sh
```

If you directly run `docker compose -f remote/remote-shared/deploy/docker-compose.linux.yml ...`
without a repo-root `.env`, the compose file now falls back to
`remote/.env.linux.example` instead of failing on a missing env file. That
fallback is only a bootstrap convenience; replace the placeholder values before
real staging/prod deployment.

See:

- `remote/.env.linux.example`
- `remote/remote-shared/docs/linux-deployment-runbook.md`
- `remote/remote-shared/deploy/deploy.sh`
- `remote/remote-shared/deploy/upgrade.sh`
- `remote/remote-shared/deploy/rollback.sh`
- `remote/remote-shared/deploy/nginx.remote-full-system-linux.conf`
- `remote/remote-shared/deploy/nginx.remote-full-system-https.conf.template`
- `remote/remote-shared/deploy/remote-compose.service`

## Phase 4 release gate quickstart

```bash
pytest backend/tests/test_remote_phase0_bootstrap.py backend/tests/test_remote_phase0_contract_freeze.py backend/tests/test_remote_phase0_compatibility_gate.py backend/tests/test_remote_phase1_pr1_login.py backend/tests/test_remote_phase1_pr2_lifecycle.py backend/tests/test_remote_phase1_pr3_admin.py backend/tests/test_remote_phase1_pr4_gate.py backend/tests/test_remote_phase2_pr1_control_backbone.py backend/tests/test_remote_phase2_pr2_admin_users.py backend/tests/test_remote_phase2_pr3_admin_devices.py backend/tests/test_remote_phase2_pr4_admin_sessions.py backend/tests/test_remote_phase2_pr5_supportability.py backend/tests/test_remote_phase2_pr5_gate.py backend/tests/test_remote_phase3_pr1_admin_rbac.py backend/tests/test_remote_phase3_pr2_dashboard_audit.py backend/tests/test_remote_phase3_pr3_operations_ux.py backend/tests/test_remote_phase3_pr4_gate.py backend/tests/test_remote_phase4_pr1_contract_hardening.py backend/tests/test_remote_phase4_pr2_runtime_reliability.py backend/tests/test_remote_phase4_pr4_gate.py backend/tests/test_remote_a0_pr1_operating_model.py backend/tests/test_remote_a0_pr2_env_discipline.py backend/tests/test_remote_a0_pr3_topology_health.py backend/tests/test_remote_a0_pr4_release_governance.py -q
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/build_phase0_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase0_gate.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

See:

- `remote/remote-shared/docs/phase4-release-gate.md`
- `remote/remote-shared/docs/staging-deploy-checklist.md`
- `remote/remote-shared/docs/staging-promotion-checklist.md`
- `remote/remote-shared/docs/rollback-runbook.md`
- `remote/remote-shared/docs/restore-recovery-runbook.md`
- `remote/remote-shared/docs/support-runbook.md`

Workflow green alone is not enough for release readiness; complete the staging checklist and capture staging-backed evidence before promotion.
