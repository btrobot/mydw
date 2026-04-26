# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DewuGoJin — a desktop tool (Electron + React + FastAPI) for multi-account content management, browser automation, and video composition. See `docs/README.md` for the full documentation index.

## Architecture

```
Electron Shell (frontend/)
  ├─ Main Process: window/tray/backend lifecycle
  ├─ Preload: minimal electronAPI bridge
  └─ React Renderer (HashRouter, Ant Design, React Query)
        └─ Generated SDK (frontend/src/api/) ──► FastAPI (localhost:8000)

FastAPI Backend (backend/)
  ├─ api/         route handlers by domain
  ├─ services/    business logic (creative_service.py is the largest)
  ├─ core/        browser lifecycle, auth, encryption, scheduler
  ├─ models/      SQLAlchemy ORM (SQLite via aiosqlite)
  └─ migrations/  Alembic

Remote Control Plane (remote/)
  └─ remote-backend + remote-admin + remote-shared (auth, device trust)
```

Key facts:
- Default app entry is `/` → CreativeWorkbench (not accounts or tasks)
- Frontend API client is **generated** from the backend's OpenAPI schema — do not hand-edit `frontend/src/api/`
- SQLite is local; no external DB
- Browser automation uses Patchright (Playwright-compatible)
- Video composition uses local FFmpeg

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev              # Vite dev server (port 5173)
npm run dev:electron     # Full Electron + backend + frontend
npm run typecheck
```

### Tests
```bash
# Backend (pytest)
pytest backend/tests                              # all tests
pytest backend/tests/test_auth_api.py -v          # single file
pytest backend/tests/test_auth_api.py::test_foo   # single test

# Frontend E2E (Playwright)
cd frontend
npm run test:e2e
npm run test:e2e -- e2e/creative-main-entry/creative-main-entry.spec.ts
```

### Generated artifacts
After changing backend routes/schemas, regenerate the frontend SDK:
```bash
cd frontend
npm run api:generate       # export OpenAPI + regenerate SDK
npm run generated:check    # verify artifacts are current
# or both at once:
npm run generated:regenerate
```

## Key Policies (from AGENTS.md)

**Commit format — Lore protocol.** Every commit message leads with *why* (intent), not *what*. The diff shows what changed. Use git trailers (`Constraint:`, `Rejected:`, `Directive:`, `Tested:`, `Not-tested:`) when they add value. See `AGENTS.md` for the full format.

**Working agreements:**
- Write a cleanup plan before refactor/deslop work
- Lock behavior with regression tests before cleanup edits
- Prefer deletion over addition; reuse existing patterns before new abstractions
- No new dependencies without explicit request
- Keep diffs small, reviewable, reversible
- After a user-approved slice is implemented and verified, auto-commit without waiting for another confirmation

**Encoding hygiene:** All files must be UTF-8. Do not pipe CJK content through PowerShell heredocs — use `apply_patch` or Python with `encoding='utf-8'`. Verify multilingual files by reading back with Python after writing.

**Discussion/spec files:** Cross-cutting spec/規範 documents go under `discss/specs/`; discussion/analysis/backlog notes go in `discss/` root.

## Reference Documents

| Path | Purpose |
|------|---------|
| `docs/current/architecture.md` | System topology & responsibility boundaries |
| `docs/current/runtime-truth.md` | Live API surfaces & runtime facts |
| `docs/guides/dev-guide.md` | Environment setup & startup |
| `docs/governance/generated-artifact-policy.md` | What is generated vs hand-authored |
| `docs/governance/runtime-local-artifact-policy.md` | `.codex/`, `.omx/`, session artifact boundaries |
| `docs/guides/openapi-generation-workflow.md` | OpenAPI export & SDK generation workflow |
| `backend/CLAUDE.md` | Backend-specific conventions |
| `frontend/CLAUDE.md` | Frontend-specific conventions |
