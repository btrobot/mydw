# Compatibility Gate

## Purpose

The Phase 0 compatibility gate ensures the remote system cannot drift away from
the frozen contract before implementation starts.

Phase 1 extends this discipline to the implemented live runtime surface.

## Gate responsibilities

The gate must verify:

- OpenAPI artifact parses successfully
- required auth/admin paths exist
- golden fixtures exist and match the frozen contract shape
- error-code fixtures match the frozen error-code matrix
- generated artifact manifest is reproducible

## Generated artifact discipline

- `remote/remote-shared/openapi/phase0-manifest.json` is a generated artifact
- it must be reproducible from:
  - frozen contract docs
  - OpenAPI v1 artifact
  - golden fixtures
- it must not be hand-edited

## Phase 0 rule

If any contract/schema/error-matrix change causes fixture or manifest drift,
the gate must fail until artifacts are regenerated and reviewed together.

## Phase 1 rule

The Phase 1 gate adds:

- runtime OpenAPI export reproducibility
- source-vs-runtime drift detection for implemented endpoints
- fixture-vs-runtime compatibility validation against the real FastAPI app
- remote-admin build/typecheck/test release checks

## Phase 4 contract-hardening rule

Once Phase 2 / Phase 3 admin filters and metrics/audit expansions exist, the gate must also keep these additive surfaces aligned:

- optional query parameters on implemented admin list endpoints
- `HTTPValidationError` coverage for validation-backed routes
- additive audit fields such as `request_id` / `trace_id`
- additive metrics fields such as `generated_at` / recent summary lists

Phase 4 hardening should close drift, not silently redefine the existing runtime contract.
