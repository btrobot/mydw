# Remote Workspace

This directory contains the remote authorization center MVP workspace.

## Layout

- `remote-backend/` - FastAPI remote auth/admin backend
- `remote-admin/` - protected admin console
- `remote-shared/` - OpenAPI, compatibility harness, release docs, runbooks
- `.env.example` - shared env template for dev/staging bootstrap

## Phase 3 status

Phase 3 now includes:

- remote auth core and admin runtime
- admin RBAC hardening + actor-level audit
- dashboard / audit operational UX
- users / devices / sessions rich operations UX
- phase release-gate docs and workflow assets
- admin bootstrap + staging/support runbooks

## Local startup

### 1. Prepare env

Copy `remote/.env.example` to the repo-root `.env` and adjust values.

### 2. Start the backend

```bash
python -c "from app.migrations.runner import upgrade; upgrade()"
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

### 4. Build and open the admin console

```bash
npm --prefix remote/remote-admin run build
```

Then open:

```text
remote/remote-admin/index.html?apiBase=http://127.0.0.1:8100
```

## Phase 3 release gate quickstart

```bash
pytest backend/tests/test_remote_phase0_bootstrap.py backend/tests/test_remote_phase0_contract_freeze.py backend/tests/test_remote_phase0_compatibility_gate.py backend/tests/test_remote_phase1_pr1_login.py backend/tests/test_remote_phase1_pr2_lifecycle.py backend/tests/test_remote_phase1_pr3_admin.py backend/tests/test_remote_phase1_pr4_gate.py backend/tests/test_remote_phase2_pr1_control_backbone.py backend/tests/test_remote_phase2_pr2_admin_users.py backend/tests/test_remote_phase2_pr3_admin_devices.py backend/tests/test_remote_phase2_pr4_admin_sessions.py backend/tests/test_remote_phase2_pr5_supportability.py backend/tests/test_remote_phase2_pr5_gate.py backend/tests/test_remote_phase3_pr1_admin_rbac.py backend/tests/test_remote_phase3_pr2_dashboard_audit.py backend/tests/test_remote_phase3_pr3_operations_ux.py backend/tests/test_remote_phase3_pr4_gate.py -q
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

See:

- `remote/remote-shared/docs/phase3-release-gate.md`
- `remote/remote-shared/docs/staging-deploy-checklist.md`
- `remote/remote-shared/docs/support-runbook.md`

Workflow green alone is not enough for release readiness; complete the staging checklist and capture staging-backed evidence before promotion.
