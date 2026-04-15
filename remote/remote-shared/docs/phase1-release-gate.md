# Phase 1 Release Gate

## Purpose

PR1.4 closes Phase 1 with executable release checks instead of relying on
manual judgement.

## Required gate signals

The Phase 1 release gate is green only when all of the following pass:

- backend auth/admin regression tests
- compatibility harness against the live Phase 1 implementation surface
- OpenAPI source/runtime drift check
- generated artifact reproducibility
- remote-admin typecheck/build/test

## Local gate commands

### 1. Export runtime OpenAPI

```bash
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
```

### 2. Regenerate the Phase 1 manifest

```bash
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
```

### 3. Run the Phase 1 compatibility gate

```bash
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
```

### 3.1 Run the same harness against staging

```bash
REMOTE_COMPAT_BASE_URL=https://remote-staging.example.com \
REMOTE_COMPAT_USERNAME=alice \
REMOTE_COMPAT_PASSWORD=secret \
REMOTE_COMPAT_DEVICE_ID=device_ci \
REMOTE_COMPAT_ADMIN_USERNAME=admin \
REMOTE_COMPAT_ADMIN_PASSWORD=admin-secret \
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
```

The script uses the in-process FastAPI app by default.
When `REMOTE_COMPAT_BASE_URL` is set, it switches to HTTP mode and runs the
same compatibility checks against the target deployment.

### 4. Run backend regression

```bash
pytest backend/tests/test_remote_phase0_bootstrap.py \
  backend/tests/test_remote_phase0_contract_freeze.py \
  backend/tests/test_remote_phase0_compatibility_gate.py \
  backend/tests/test_remote_phase1_pr1_login.py \
  backend/tests/test_remote_phase1_pr2_lifecycle.py \
  backend/tests/test_remote_phase1_pr3_admin.py \
  backend/tests/test_remote_phase1_pr4_gate.py -q
```

### 5. Run remote-admin gate

```bash
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

## staging-backed compatibility rule

Phase 1 is not considered release-ready until the same compatibility harness
has been run against a staging deployment at least once.

The checked-in CI gate proves local/runtime reproducibility.
The staging-backed run proves deployment wiring and environment parity.

## Non-goals of this gate

This gate does **not** implement the future admin users/devices/sessions/audit
management APIs. It validates the implemented Phase 1 surface only:

- `/login`
- `/refresh`
- `/logout`
- `/me`
- `/admin/login`
- `/admin/session`

## Failure policy

If any gate fails:

- do not advance the release tag
- regenerate generated artifacts if drift is intentional
- otherwise fix runtime/spec drift before merge
