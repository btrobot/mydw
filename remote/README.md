# Remote Workspace

This directory contains the remote auth platform MVP workspace.

## Layout

- `remote-backend/` - remote authorization center backend
- `remote-admin/` - remote admin console frontend
- `remote-shared/` - artifact-only shared area for OpenAPI, generated types, docs, and scripts

## Current status

Phase 1 currently includes:

- runnable `remote-backend` auth/admin APIs
- runnable `remote-admin` protected shell
- shared OpenAPI/docs/fixtures compatibility assets
- release-gate scripts for compatibility/export validation

## Phase 1 release gate quickstart

```bash
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
pytest backend/tests/test_remote_phase0_bootstrap.py backend/tests/test_remote_phase0_contract_freeze.py backend/tests/test_remote_phase0_compatibility_gate.py backend/tests/test_remote_phase1_pr1_login.py backend/tests/test_remote_phase1_pr2_lifecycle.py backend/tests/test_remote_phase1_pr3_admin.py backend/tests/test_remote_phase1_pr4_gate.py -q
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

## Phase 2 supportability gate quickstart

```bash
pytest backend/tests/test_remote_phase0_bootstrap.py backend/tests/test_remote_phase0_contract_freeze.py backend/tests/test_remote_phase0_compatibility_gate.py backend/tests/test_remote_phase1_pr1_login.py backend/tests/test_remote_phase1_pr2_lifecycle.py backend/tests/test_remote_phase1_pr3_admin.py backend/tests/test_remote_phase1_pr4_gate.py backend/tests/test_remote_phase2_pr1_control_backbone.py backend/tests/test_remote_phase2_pr2_admin_users.py backend/tests/test_remote_phase2_pr3_admin_devices.py backend/tests/test_remote_phase2_pr4_admin_sessions.py backend/tests/test_remote_phase2_pr5_supportability.py backend/tests/test_remote_phase2_pr5_gate.py -q
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```
