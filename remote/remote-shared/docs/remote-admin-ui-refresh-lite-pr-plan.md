# Remote Admin UI Refresh Lite PR Plan

## Purpose

This document defines a **lightweight, UI-first PR plan** for improving `remote-admin` visual quality and usability **without starting a heavy platform-architecture refactor first**.

The goal of this plan is to make the current pages look more professional, more consistent, and easier to use, while staying aligned with the existing technical stack and current backend contracts.

---

## Why this lighter plan exists

The earlier enterprise-platform refactor plan is valid, but it is heavy for the immediate problem.

The current pain is primarily:
- the UI looks rough
- visual hierarchy is weak
- styles are inconsistent
- list/detail/form experience feels unpolished
- layout density and spacing are not yet at a professional admin-console level

This plan optimizes for:
- fast visible improvement
- low-risk incremental changes
- minimal architectural churn
- compatibility with the existing codebase shape

---

## Current stack assumptions

The current `remote-admin` stack is:

- static `index.html`
- vanilla TypeScript
- `src/app/App.ts` string-based rendering
- `src/main.ts` runtime/bootstrap logic
- no React/Vue runtime
- no Tailwind build pipeline in `remote-admin`
- current scripts:
  - `npm --prefix remote/remote-admin run typecheck`
  - `npm --prefix remote/remote-admin run build`
  - `npm --prefix remote/remote-admin run test`

This plan therefore follows **current-stack best practices**, not framework migration best practices.

---

## Scope

### In scope
- visual refresh of the current admin shell and pages
- extracting inline styles into dedicated CSS
- establishing a lightweight design token layer
- introducing reusable render helpers and CSS classes
- improving page layout, tables, cards, forms, badges, and detail panels
- improving empty/error/loading states
- improving responsive behavior and basic accessibility polish

### Out of scope
- switching frameworks
- migrating to React/Vue
- introducing a heavy state-management layer
- re-architecting the entire app into a multi-module platform shell first
- changing backend API contracts
- major route model redesign

---

## Design principles

1. **UI first** — prioritize visible improvement before deeper platform restructuring.
2. **Current stack friendly** — stay inside the current vanilla TypeScript + static frontend model.
3. **Minimal disruption** — preserve existing routes, fetch flows, and backend contracts.
4. **Reusable enough, not over-engineered** — extract only the helpers and CSS needed to make the UI coherent.
5. **One reviewable PR at a time** — every PR must be testable, reversible, and visually meaningful.

---

## Proposed file direction

These files or paths are likely to be introduced or touched during the refresh:

- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/src/main.ts`
- `remote/remote-admin/index.html`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/src/styles/tokens.css` *(optional if styles are split)*
- `remote/remote-admin/src/components/` *(lightweight render helpers if needed)*
- `remote/remote-admin/tests/app.test.mjs`

Note: this plan does **not** require all of these files to exist up front. They are likely touchpoints, not mandatory targets.

---

# PR Sequence

## PR-01 — Extract visual foundation and design tokens

### PR title
`refactor(remote-admin): extract UI styles and establish visual foundation`

### Objective
Move inline visual styling out of `App.ts` into a dedicated stylesheet and define a consistent baseline for color, spacing, typography, cards, buttons, forms, badges, and layout.

### Change scope
Primary targets:
- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/index.html`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/tests/app.test.mjs` *(only if selectors or structure checks need updates)*

Expected changes:
- remove or reduce the large inline `<style>` block from rendered markup
- introduce shared CSS variables/tokens
- establish base styles for:
  - body / app shell background
  - typography
  - cards
  - buttons
  - inputs / selects / textareas
  - tags / badges
  - empty / error / success blocks

### Test method
Commands:
- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

Verification:
- app still renders successfully through `index.html`
- no route logic changes
- no text-regression in key screens unless intentionally updated
- visual classes load from CSS successfully

### Rollback strategy
- revert the stylesheet introduction and the corresponding `App.ts` markup/class changes as one unit
- since no route/data contract changes are involved, rollback is low-risk

### Merge gate
- inline style burden is materially reduced
- admin UI uses a shared visual baseline instead of per-view ad hoc styling
- build/test/typecheck stay green

---

## PR-02 — Refresh shell, navigation, and shared page chrome

### PR title
`feat(remote-admin): refresh shell layout and shared page chrome`

### Objective
Make the app feel like a more professional admin console by improving the shell, topbar, sidebar, page headers, spacing rhythm, and common content framing.

### Change scope
Primary targets:
- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/tests/app.test.mjs`

Expected changes:
- restyle sidebar and navigation states
- improve topbar layout
- improve page header hierarchy
- unify content container spacing
- establish better shell structure for authenticated routes
- improve current role / session / sign-out presentation

### Test method
Commands:
- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

Verification:
- all current authenticated routes still render
- current route highlighting still works
- logout control still appears and remains wired
- route labels / shell chrome still match expected text

### Rollback strategy
- revert shell layout and shared CSS changes together
- because page logic is not deeply changed yet, rollback remains isolated to presentation

### Merge gate
- all pages render within a cleaner, more consistent shell
- sidebar / topbar / page-header presentation is improved across the app
- no route or auth-flow regressions

---

## PR-03 — Rebuild Dashboard and Users for a professional admin look

### PR title
`feat(remote-admin): polish dashboard and users workspace`

### Objective
Upgrade the two most visible surfaces first:
- Dashboard should become easier to scan
- Users should become more professional and structured

### Change scope
Primary targets:
- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/tests/app.test.mjs`

Expected changes:
- Dashboard:
  - improved KPI card layout
  - clearer section hierarchy
  - better recent events presentation
- Users:
  - improved filter toolbar styling
  - cleaner list/detail presentation
  - stronger status badge semantics
  - more readable edit form and action section

Possible light helper extraction if needed:
- `remote/remote-admin/src/components/` for small rendering helpers

### Test method
Commands:
- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

Verification:
- Dashboard KPI and recent event content still render correctly
- Users filters still map to the same query behavior
- readonly-role behavior still remains obvious and intact
- user detail/edit areas still show expected fields and controls

### Rollback strategy
- revert Dashboard and Users visual restructuring together
- keep shell and style foundation from earlier PRs intact

### Merge gate
- Dashboard looks materially more polished and easier to scan
- Users page feels like a professional admin page, not a prototype
- no change to backend contract or filter semantics

---

## PR-04 — Rebuild Devices and Sessions pages

### PR title
`feat(remote-admin): polish devices and sessions workspaces`

### Objective
Bring Devices and Sessions up to the same UI quality as Users, with clearer tables/cards, better metadata hierarchy, and more professional destructive-action presentation.

### Change scope
Primary targets:
- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/tests/app.test.mjs`

Expected changes:
- Devices:
  - cleaner binding/status presentation
  - improved action grouping
  - better visual separation between summary and destructive actions
- Sessions:
  - clearer auth-state presentation
  - stronger revoke affordance styling
  - better timestamp readability

### Test method
Commands:
- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

Verification:
- device action controls still render with correct disabled states
- session revoke controls still behave correctly in rendered output
- filters and selection behavior remain unchanged unless explicitly improved

### Rollback strategy
- revert Devices/Sessions page markup + styling changes together
- preserve prior shell and shared style improvements

### Merge gate
- Devices and Sessions visually match the improved Users page quality
- destructive actions remain clear and role-aware
- no contract or action-flow regressions

---

## PR-05 — Rebuild Audit Logs as a usable investigation page

### PR title
`feat(remote-admin): polish audit logs investigation experience`

### Objective
Turn Audit Logs into a clearer investigation surface with better filtering layout, row readability, detail presentation, and JSON/detail readability.

### Change scope
Primary targets:
- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/tests/app.test.mjs`

Expected changes:
- improve audit filter panel layout
- improve result list readability
- improve selected-event detail block
- improve code/JSON formatting and hierarchy
- improve pagination button presentation and query preview readability

### Test method
Commands:
- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

Verification:
- audit filters still render and map to current query-building behavior
- query preview still appears as expected
- selected audit row/detail behavior still works
- JSON/detail section still renders safely

### Rollback strategy
- revert audit page visual restructuring only
- keep previous shell/foundation PRs merged

### Merge gate
- Audit Logs is materially easier to use and inspect
- filtering and detail reading feel professional
- no regression in audit query behavior

---

## PR-06 — Responsive polish, state polish, and final cleanup

### PR title
`refactor(remote-admin): finish responsive polish, state polish, and UI cleanup`

### Objective
Close out the lightweight refresh by improving mobile/medium-width behavior, focus states, empty/error/loading polish, and any remaining visual inconsistency.

### Change scope
Primary targets:
- `remote/remote-admin/src/app/App.ts`
- `remote/remote-admin/src/styles/admin.css`
- `remote/remote-admin/index.html` *(only if minor polish is needed)*
- `remote/remote-admin/tests/app.test.mjs`

Expected changes:
- improve responsive spacing and overflow handling
- improve empty states
- improve error/retry presentation
- improve loading states
- improve focus/disabled states
- remove leftover visual duplication or dead CSS fragments

### Test method
Commands:
- `npm --prefix remote/remote-admin run lint`
- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

Verification:
- all main routes still render correctly
- no selector breakage from final cleanup
- empty/error/loading states remain present and understandable
- no obvious responsive regressions in key layouts

### Rollback strategy
- revert final cleanup as one PR if the finishing pass introduces instability
- because this PR should avoid business-logic changes, rollback is safe

### Merge gate
- UI feels visually coherent end-to-end
- main pages are cleaner, more consistent, and easier to use
- build/test/typecheck/lint remain green

---

# Merge order

Recommended merge order:

1. PR-01 — visual foundation
2. PR-02 — shell and shared chrome
3. PR-03 — Dashboard + Users
4. PR-04 — Devices + Sessions
5. PR-05 — Audit Logs
6. PR-06 — responsive/state/final polish

---

# Verification baseline for every PR

Minimum verification for each PR:

- `npm --prefix remote/remote-admin run typecheck`
- `npm --prefix remote/remote-admin run build`
- `npm --prefix remote/remote-admin run test`

For the final polish PR, also run:

- `npm --prefix remote/remote-admin run lint`

---

# Rollback policy

Each PR must remain:
- focused
- reviewable
- reversible

Rollback rule:
- if a PR introduces visual regression or structural instability, revert the PR as a unit
- do not spread one design decision across multiple PRs unless the dependency is explicit
- keep route/backend behavior unchanged unless intentionally documented

---

# Recommended success criteria

This lightweight plan is successful if, after PR-06:

1. `remote-admin` looks materially more professional
2. visual language is consistent across all pages
3. filters, tables, detail panels, and forms are easier to use
4. current backend contracts remain unchanged
5. current technical stack remains intact
6. the codebase is cleaner, but not over-engineered

---

# Recommended next step

If execution should start immediately, begin with:

- **PR-01 — Extract visual foundation and design tokens**

That PR creates the base needed for all later visual improvements while keeping risk low.
