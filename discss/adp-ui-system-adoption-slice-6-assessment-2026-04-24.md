# ADP UI System Adoption Slice 6 Assessment

## Scope

Slice 6 covers only the `TaskCreate` / `StepsForm` assessment gate from:

- `.omx/plans/prd-adp-ui-system-adoption-2026-04-23.md`
- `.omx/plans/test-spec-adp-ui-system-adoption-2026-04-23.md`

It must not change Workbench state ownership, diagnostics URL behavior, shell layout, drawer behavior, CreativeDetail behavior, backend/API contracts, submit payload semantics, or dependencies.

## Candidate: TaskCreate

File: `frontend/src/pages/task/TaskCreate.tsx`

## Current implementation summary

- The page is a compatibility / advanced task-creation entry, while daily creative work is directed to the creative workbench.
- It combines product quick import, manual material selection, a four-tab material basket, per-tab table selection, batch delete, clear-current-tab, optional account selection, optional profile selection, composition-mode guidance, semantic validation, and submit/navigation behavior.
- The material basket state is non-linear: users can import or manually add materials in any order, switch among video/copywriting/cover/audio tabs, delete selected rows, clear one tab, and then adjust configuration.
- The submit path validates the AntD form, validates basket semantics, builds the existing `useBatchAssemble` payload from basket arrays and optional form fields, then navigates to `/task/list` with a `creationSummary`.
- Existing task-create coverage lives in `frontend/e2e/task-composition/local-ffmpeg.spec.ts`, including local FFmpeg guidance, invalid multi-material combinations, successful creation, and task-list follow-up actions.

## Assessment questions

### Is the current flow naturally linear?

No. The page is closer to a compact configuration console than to a strict wizard. Users do not have to complete a fixed "choose type -> configure material -> confirm -> submit" sequence; they can iterate across import, tabbed basket editing, profile selection, and validation feedback.

### Would `StepsForm` make tabs / material basket / modal selection clearer?

Not enough to justify migration. `StepsForm` would likely wrap the current areas into artificial steps, but the hardest parts would remain:

- external modal material selection,
- tab-scoped table selection,
- per-material-type basket updates,
- cross-field semantic validation,
- submit disabled state derived from both basket and selected profile mode.

Those concerns are domain state, not form-container boilerplate.

### Would migration reduce complexity?

No. A `StepsForm` migration would add step progression, cross-step persistence, validation timing decisions, and back/forward behavior without removing the current basket/table/modal state model. It would also create new edge cases around when invalid basket combinations should block moving between steps versus blocking final submit.

### Would migration affect payload or submit semantics?

It should not, and preserving that contract is one of the reasons to avoid migration in this slice. The existing submit payload is directly derived from:

- `basket.videos`
- `basket.copywritings`
- `basket.covers`
- `basket.audios`
- optional `account_id`
- optional `profile_id`

Changing the page to a wizard would not simplify that payload; it would only distribute the same state across steps.

## Expected simplification if migrated

The only likely simplification would be a more guided visual shell around "materials" and "configuration". However, that gain is mostly presentational and does not remove meaningful code from the current implementation. The migration would need to keep the same basket state, modal state, selected row keys, tab state, semantic validation, and submit payload.

## Decision

No-op.

## Reason

`TaskCreate` is an advanced single-page configuration console rather than a naturally linear wizard. Migrating to `StepsForm` would increase state synchronization and validation complexity while offering limited UI consistency benefits. It also risks making the compatibility entry slower for power users who need to import, adjust, and submit from one screen.

This matches the approved no-op conditions:

- the current page is an advanced single-page console,
- forced steps would add state complexity,
- migration would not clearly reduce UI boilerplate,
- rewriting payload or submit behavior is out of scope.

## Acceptance tests

Because this slice is assessment-only and does not change production UI code, the required verification is:

- typecheck passes,
- production build passes,
- existing task creation E2E remains green,
- static diff hygiene passes,
- no production/source/dependency files are changed.

Recommended focused E2E command:

```powershell
cd frontend
npm run test:e2e -- e2e/task-composition/local-ffmpeg.spec.ts
```
