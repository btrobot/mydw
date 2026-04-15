# Phase 3 Release Gate

## Purpose

PR3.4 closes Phase 3 with a deploy/bootstrap/release checklist on top of the earlier runtime and supportability gates.

## Required gate signals

The Phase 3 gate is green only when all of the following pass:

- backend regression through PR3.4 scope
- Phase 1 compatibility/export gate remains green
- remote-admin typecheck/build/test remains green
- admin bootstrap script can create or update an admin user
- staging deploy checklist has been walked at least once before release promotion
- staging uses non-default bootstrap/admin secrets with development seeding disabled

## Local gate commands

### 1. Run backend regression

```bash
pytest backend/tests/test_remote_phase0_bootstrap.py \
  backend/tests/test_remote_phase0_contract_freeze.py \
  backend/tests/test_remote_phase0_compatibility_gate.py \
  backend/tests/test_remote_phase1_pr1_login.py \
  backend/tests/test_remote_phase1_pr2_lifecycle.py \
  backend/tests/test_remote_phase1_pr3_admin.py \
  backend/tests/test_remote_phase1_pr4_gate.py \
  backend/tests/test_remote_phase2_pr1_control_backbone.py \
  backend/tests/test_remote_phase2_pr2_admin_users.py \
  backend/tests/test_remote_phase2_pr3_admin_devices.py \
  backend/tests/test_remote_phase2_pr4_admin_sessions.py \
  backend/tests/test_remote_phase2_pr5_supportability.py \
  backend/tests/test_remote_phase2_pr5_gate.py \
  backend/tests/test_remote_phase3_pr1_admin_rbac.py \
  backend/tests/test_remote_phase3_pr2_dashboard_audit.py \
  backend/tests/test_remote_phase3_pr3_operations_ux.py \
  backend/tests/test_remote_phase3_pr4_gate.py -q
```

### 2. Keep compatibility/export green

```bash
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
```

### 3. Bootstrap an admin account

```bash
set BOOTSTRAP_ADMIN_PASSWORD=ci-secret
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username ci-admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "CI Admin"
```

### 4. Run remote-admin gate

```bash
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

### 5. Walk the staging checklist

Use:

- `admin-bootstrap-runbook.md`
- `staging-deploy-checklist.md`
- `support-runbook.md`

At least one staging-backed run should prove:

- backend can boot with configured env
- first admin can be bootstrapped
- admin console can point at staging
- compatibility harness can run against staging

## Governance note

The checked-in workflow only covers the automated gate.

Workflow green alone is insufficient for release readiness.
Promotion still requires manual staging-backed evidence from the checklist above.

## Failure policy

If any signal fails:

- do not promote the staging build
- do not tag the remote MVP as deploy-ready
- fix deploy/bootstrap/runtime drift before merge
