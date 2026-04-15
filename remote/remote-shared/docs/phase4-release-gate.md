# Phase 4 Release Gate

## Purpose

PR4.4 closes Phase 4 with release-readiness rules for promotion, rollback,
and manual staging evidence on top of the earlier runtime/supportability gates.

## Required gate signals

The Phase 4 gate is green only when all of the following hold:

- backend regression through Phase 4 implemented PRs passes
- Phase 0 / Phase 1 compatibility gates remain green
- remote-admin typecheck/build/test remains green
- bootstrap admin smoke remains green
- staging promotion checklist has been completed for the candidate build
- rollback checklist exists and is attached to the release notes
- release evidence has been captured before promotion

## Automated gate commands

### 1. Backend regression

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
  backend/tests/test_remote_phase3_pr4_gate.py \
  backend/tests/test_remote_phase4_pr1_contract_hardening.py \
  backend/tests/test_remote_phase4_pr2_runtime_reliability.py \
  backend/tests/test_remote_phase4_pr4_gate.py -q
```

### 2. Compatibility / generated artifacts

```bash
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/build_phase0_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase0_gate.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
```

### 3. Bootstrap smoke

```bash
set BOOTSTRAP_ADMIN_PASSWORD=ci-secret
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username ci-admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "CI Admin"
```

### 4. remote-admin gate

```bash
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

## Manual promotion requirements

Automation is necessary but not sufficient.

Before promotion, an operator must complete:

- `staging-promotion-checklist.md`
- `staging-deploy-checklist.md`
- `rollback-runbook.md`
- `support-runbook.md`

## Required release evidence

Attach or record:

- backend regression output
- compatibility gate output
- remote-admin gate output
- bootstrap smoke output
- staging candidate URL / environment identifier
- operator sign-off that promotion and rollback checklists were reviewed

## Failure policy

If any signal fails:

- do not promote the candidate
- do not treat workflow green as release-ready by itself
- fix drift, rerun gates, and refresh release evidence
