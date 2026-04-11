# Generated Artifact Policy

> PR-B governance closeout  
> 目的：明确哪些文件是 source of truth，哪些只是 generated artifact，并给出统一 regenerate / review 规则，避免 review 时猜测“这是不是正常生成差异”。

## Boundary matrix

| Surface | Classification | Source of truth | Commit policy | Regenerate command | Notes |
|---|---|---|---|---|---|
| `backend/api/**`, `backend/schemas/**`, `backend/main.py` | handwritten source | backend Python code | commit direct edits | n/a | OpenAPI contract starts here |
| `frontend/openapi.local.json` | tracked generated artifact | `frontend/scripts/export_openapi.py` importing backend `main.app.openapi()` | commit when backend contract/version changes affect exported schema | `cd frontend && npm run api:export` | local snapshot for deterministic frontend generation |
| `frontend/src/api/**` | tracked generated artifact | `frontend/openapi.local.json` + `frontend/openapi.config.ts` | commit regenerated diff together with API contract changes | `cd frontend && npm run api:generate` | files carry `auto-generated` header; do not hand-edit |
| `frontend/electron/main.ts`, `frontend/electron/preload.ts`, `frontend/electron/backendLauncher.ts` | handwritten source | TypeScript sources | commit direct edits | n/a | canonical Electron TS sources |
| `frontend/electron/main.js`, `frontend/electron/preload.js`, `frontend/electron/backendLauncher.js` | tracked generated artifact | corresponding `.ts` file + `frontend/electron/tsconfig.json` | commit regenerated diff whenever Electron TS sources change | `cd frontend && tsc -p electron/tsconfig.json` | runtime JS mirrors consumed by Electron/package entrypoints |
| `frontend/electron/main.js.map`, `frontend/electron/preload.js.map`, `frontend/electron/backendLauncher.js.map` | tracked generated artifact | same as corresponding JS mirror | commit whenever Electron JS mirrors are regenerated | `cd frontend && tsc -p electron/tsconfig.json` | must stay aligned with the JS mirrors |
| `frontend/dist/**`, `frontend/dist-electron/**`, `backend/dist/**`, `node_modules/**` | local/generated build output | build tools / package managers | do **not** commit as part of this governance lane | rebuild locally when needed | non-canonical outputs; review should ignore them unless a packaging lane explicitly asks for them |

## Rules

1. **Edit sources, not mirrors.**
   - Backend contract changes start from backend code.
   - Electron main-process/runtime changes start from `frontend/electron/*.ts`.
   - Do not hand-edit `frontend/src/api/**`, `frontend/openapi.local.json`, `frontend/electron/main.js`, `frontend/electron/main.js.map`, `frontend/electron/preload.js`, `frontend/electron/preload.js.map`, `frontend/electron/backendLauncher.js`, or `frontend/electron/backendLauncher.js.map`.
2. **Tracked generated artifacts must be reproducible.**
   - If a PR changes a source-of-truth surface and that change affects a tracked generated artifact, commit the regenerated artifact in the same PR.
3. **Non-tracked build outputs must be rebuilt, not reviewed.**
   - `dist/`, packaged outputs, and dependency install artifacts are not review surfaces for this lane.
4. **Untracked/generated build outputs must be regenerated locally.**
   - 这些文件必须通过命令重建，不应靠手工补丁维持一致性。

## Standard regenerate flow

From `frontend/`:

```bash
npm run generated:regenerate
```

This expands to:

```bash
npm run api:generate
tsc -p electron/tsconfig.json
```

If you only need part of the pipeline:

```bash
npm run api:export
npm run api:generate
tsc -p electron/tsconfig.json
```

## Predictable-diff review check

From `frontend/`:

```bash
npm run generated:check
```

That command:

1. regenerates the tracked artifacts in scope;
2. compares both content manifests and `git status --short --untracked-files=all` for the tracked generated surfaces before/after regeneration.

Pass condition:

- the file contents and git status of `openapi.local.json`, `src/api`, and the tracked Electron JS mirrors/maps are unchanged by a fresh regenerate run.

If the command fails:

1. inspect the diff;
2. either commit the regenerated artifact (if the source-of-truth change was intentional),
3. or revert/fix the source change until regeneration becomes stable again.

## Review checklist

- `frontend/openapi.local.json`: generated snapshot, tracked for reviewability, never hand-edited.
- `frontend/src/api/**`: generated client tree, tracked for deterministic API consumption, never hand-edited.
- `frontend/electron/main.ts`, `preload.ts`, `backendLauncher.ts`: source of truth.
- `frontend/electron/main.js`/`.map`, `preload.js`/`.map`, `backendLauncher.js`/`.map`: tracked generated mirrors of the Electron TS sources.
- build outputs (`dist`, packaged output, install artifacts): regenerated locally, not committed for this governance lane.
