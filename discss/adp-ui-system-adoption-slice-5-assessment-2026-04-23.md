# ADP UI System Adoption Slice 5 Assessment

## Scope

Slice 5 covers only the StatisticCard / ProCard assessment gate from:

- `.omx/plans/prd-adp-ui-system-adoption-2026-04-23.md`
- `.omx/plans/test-spec-adp-ui-system-adoption-2026-04-23.md`

It must not change shell, drawer, detail, Workbench query state, diagnostics behavior, or backend/API contracts.

## Candidate 1: WorkbenchSummaryCard

File: `frontend/src/features/creative/components/workbench/WorkbenchSummaryCard.tsx`

### Current implementation summary

- One outer AntD `Card`.
- Header area uses `Flex + Space + Button`.
- Runtime diagnostics notice uses `Alert`.
- Summary metrics use a compact `Flex` row with five AntD `Statistic` items.

### Expected simplification

Replacing the five inline statistics with `StatisticCard.Group` would introduce an additional ProCard wrapper inside the existing card and require extra `colSpan` / `ghost` decisions. The current implementation is already short and has minimal layout boilerplate.

### Decision

No-op.

### Reason

The replacement would be longer and visually riskier than the existing `Flex + Statistic` row. It also does not materially improve consistency because this card is primarily a Workbench entry/diagnostics summary, not a dashboard metric grid.

## Candidate 2: Dashboard

File: `frontend/src/pages/Dashboard.tsx`

### Current implementation summary

- Task metrics use eight repeated `Col + Statistic` pairs.
- System metrics use two repeated `Col + Statistic` pairs.
- Each metric repeats responsive column props and embeds statistic props inline.

### Expected simplification

`StatisticCard.Group` can own the metric-grid shell while data arrays hold the metric definitions. This could align Dashboard metric blocks with ADP's statistic card system.

### Decision

No-op.

### Reason

The current Dashboard metric blocks are repetitive but intentionally compact. A trial `StatisticCard.Group` migration required additional data arrays, `colSpan` mapping, and `ghost` wrapper decisions; the resulting code was longer than the existing `Row + Col + Statistic` structure. That hits Slice 5's no-op condition, so the safer outcome is to keep the existing implementation and record the assessment.

### Acceptance tests

- Dashboard success/empty/error state E2E remains green.
- Workbench summary and Dashboard metric behavior remain unchanged.
- Typecheck and build pass.
