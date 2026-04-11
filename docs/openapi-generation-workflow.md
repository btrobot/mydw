# OpenAPI Generation Workflow

> Phase 3 / PR2 baseline generation lane

## Goal

Make frontend client generation reproducible **without requiring a live backend server**.

## Authoritative flow

1. Update backend schemas / API contracts
2. Freeze high-value parity via `docs/schema-parity-checklist.md`
3. Export local OpenAPI snapshot
4. Regenerate frontend client
5. Fix compile breakages caused directly by regeneration
6. Run frontend typecheck / build
7. Only then proceed to higher-level hook/page migrations

## Commands

From `frontend/`:

```bash
npm run api:export
npm run api:generate
```

What happens:

- `api:export` runs `scripts/export-openapi.mjs`
- the node wrapper invokes `scripts/export_openapi.py`
- the Python script imports backend `main.app`
- it writes `frontend/openapi.local.json`
- `openapi-ts` then generates `frontend/src/api/*`

## Why local file input

`openapi.config.ts` now reads from:

```text
./openapi.local.json
```

This avoids dependence on:

- a running FastAPI server
- local port availability
- temporary manual export steps

## Notes

- `frontend/openapi.local.json` is a generated artifact and is ignored by git
- generation should happen only after schema parity is stable enough to avoid churn
- broader API adoption and manual axios exception governance belong to later Phase 3 PRs
- remaining allowed manual exceptions are tracked in `docs/manual-axios-exceptions.md`
