# Creative Domain Model Realignment Phase 1 PR3 Evidence Pack

> Status: draft implementation evidence  
> Scope: migration parity / compatibility fixtures / generated artifact parity  
> Boundary: Phase 1 PR3 only, not Phase 2 semantic cutover

## 1. Dual-write mapping boundary

- `input_items` remains the Phase 1 authoritative creative-input surface.
- `input_snapshot` remains the compatibility readback carrier.
- Legacy `video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids` stay available for compatibility,
  but repeated legacy ids are normalized before they are projected back into authoritative items.
- Duplicate-preserving authoring semantics therefore remain exclusive to `input_items`.

## 2. Rollback boundary

- PR3 must be independently revertible from PR1 / PR2 runtime behavior.
- Allowed rollback targets in this PR:
  - parity tests
  - generated artifact refresh
  - compatibility fixture/mock refresh
  - evidence packaging
- If PR3 evidence reveals ambiguity or drift, stop before Phase 2 planning instead of widening PR3 into semantic cutover work.

## 3. Phase 1 exit proof checklist

- [x] Migration 033 remains additive when applied after legacy snapshot carriers exist.
- [x] Legacy snapshot columns and snapshot rows remain readable after 033.
- [x] `creative_input_items` is not implicitly backfilled by migration-only parity work.
- [x] Checked-in `frontend/openapi.local.json` remains aligned with live creative Phase 1 contracts.
- [x] Frontend E2E compatibility mocks include additive Phase 1 fields while preserving existing `video_ids`/snapshot-shaped flows.
- [x] No workbench / review / version / publish UI semantic cutover was introduced in PR3.

## 4. Recommended verification commands

- `pytest backend/tests/test_creative_schema_contract.py backend/tests/test_creative_input_snapshot_contract.py backend/tests/test_openapi_contract_parity.py -q`
- `python frontend/scripts/export_openapi.py`
- `npm --prefix frontend run generated:check`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run test:e2e -- e2e/creative-main-entry/creative-main-entry.spec.ts e2e/ai-clip-workflow/ai-clip-responsive.spec.ts`

## 5. Explicit non-goals

- No new frontend semantic source-of-truth switch.
- No removal of legacy fixture shapes.
- No E2E rewrite around `input_items`-first authoring.
- No Phase 2 retirement/deprecation gates.
