# Startup Protocol

> Phase 4 / PR4 workflow summary

## Canonical startup sequence

1. Resolve launcher contract (`docs/backend-launcher-contract.json`)
2. Invoke launcher adapter for `dev` or `prod`
3. Wait for `/health` to satisfy the readiness guarantee
4. Only then create the Electron window / tray

## Recommended developer path

### Windows

```bash
.\dev.bat
```

What it does:
- ensures frontend dependencies exist
- ensures backend Python environment exists
- starts the backend through the launcher-compatible dev flow
- starts the frontend Vite dev server
- expects Electron dev startup to use the same backend launch protocol

### Manual backend-only startup

```bash
cd backend
.\run.bat
```

This path is for backend development/debugging only.

## Production expectation

Production Electron must launch the packaged backend via the prod launcher adapter, not by hardcoding executable paths in `main.ts`.

## Guarantees

- Electron should not directly reference:
  - `backend/venv/Scripts/python.exe`
  - `backend.exe`
  - `uvicorn main:app`
- Docs, scripts, and runtime should describe the same startup protocol
