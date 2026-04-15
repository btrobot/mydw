# Compatibility Harness

Phase 0 provides a dry-run compatibility harness for frozen artifacts.

## Contents

- `fixtures/` - golden request/response examples
- `validate_phase0_gate.py` - validates fixtures, contract surface, and manifest
- `build_phase0_manifest.py` - regenerates the manifest from frozen artifacts

## Phase 0 expectation

This harness does not call a real remote backend yet.

Instead, it validates:

- contract completeness
- fixture completeness
- error-code coverage
- generated artifact reproducibility

## Phase 1 expectation

Phase 1 adds live-runtime verification scripts:

- `export_phase1_openapi.py` - exports the current FastAPI runtime OpenAPI JSON
- `build_phase1_manifest.py` - regenerates the Phase 1 generated-artifact manifest
- `validate_phase1_gate.py` - checks source/runtime drift, fixture alignment, and live compatibility scenarios

`validate_phase1_gate.py` supports two modes:

- default: in-process FastAPI runtime with isolated temporary SQLite state
- staging: set `REMOTE_COMPAT_BASE_URL` (and optional credential env vars) to run the same harness over HTTP

The Phase 1 gate verifies the implemented surface:

- `/login`
- `/refresh`
- `/logout`
- `/me`
- `/admin/login`
- `/admin/session`
