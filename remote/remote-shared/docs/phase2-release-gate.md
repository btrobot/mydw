# Phase 2 Release Gate

## Purpose

PR2.5 closes Phase 2 with an executable supportability gate on top of the
Phase 1 release gate.

## Required gate signals

The Phase 2 release gate is green only when all of the following pass:

- full backend regression through PR2.5
- Phase 1 compatibility/export gate remains green
- remote-admin typecheck/build/test remains green
- admin audit endpoint returns destructive-action coverage
- admin metrics summary endpoint returns supportability aggregates

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
  backend/tests/test_remote_phase2_pr5_gate.py -q
```

### 2. Keep compatibility/export green

```bash
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
```

### 3. Run remote-admin gate

```bash
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

## Phase 2 supportability rule

Before Phase 2 is considered complete, operators must be able to:

- query destructive actions from `/admin/audit-logs`
- filter audit logs by at least one meaningful dimension
- read operational summary counts from `/admin/metrics/summary`
- inspect users / devices / sessions through the admin console

## Failure policy

If any gate fails:

- do not ship the Phase 2 control plane
- fix runtime/spec/supportability drift before merge
