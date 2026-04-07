# Dev Guide

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Active

Quick start guide for DewuGoJin development environment.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 22+ | Frontend build |
| Python | 3.11+ | Backend runtime |
| Git | 2.40+ | Version control |
| FFmpeg | 6+ | Video processing (must be in PATH) |

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\venv\Scripts\activate.bat

# Install dependencies (with mirror for CN)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install Playwright browser
playwright install chromium

# Create .env file
cp .env.example .env
# Edit .env: set COOKIE_ENCRYPT_KEY

# Start dev server
uvicorn main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### Backend Project Structure

```
backend/
├── main.py              # FastAPI entry point
├── api/                 # Route handlers (thin controllers)
├── models/__init__.py   # SQLAlchemy models (single file)
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic layer
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── browser.py       # Playwright browser manager
│   └── dewu_client.py   # Dewu platform client
├── utils/
│   └── crypto.py        # AES-256-GCM encryption
├── migrations/          # DB migrations (run at startup)
├── data/                # SQLite database (auto-created)
└── logs/                # Application logs
```

### Key Backend Commands

```bash
# Run with auto-reload
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Type check
.\venv\Scripts\python.exe -m mypy .

# Run specific script
.\venv\Scripts\python.exe script.py
```

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (React only)
npm run dev

# Start with Electron
npm run dev:electron

# Type check
npm run typecheck

# Generate API client from OpenAPI
npm run api:generate
```

Frontend dev server at `http://localhost:5173`

### Frontend Project Structure

```
frontend/
├── electron/            # Electron main process
│   ├── main.js          # Main window, backend lifecycle
│   └── preload.js       # Context bridge
├── src/
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Account.tsx
│   │   ├── Task.tsx
│   │   ├── Material.tsx
│   │   ├── AIClip.tsx
│   │   └── Settings.tsx
│   ├── components/      # Shared components
│   ├── services/        # API service layer
│   │   └── api.ts
│   ├── stores/          # Zustand state stores
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Utility functions
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### Key Frontend Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Vite dev server |
| `npm run dev:electron` | Electron + Vite |
| `npm run build` | Production build |
| `npm run typecheck` | TypeScript check |
| `npm run api:generate` | Regenerate API client |
| `npm run test:e2e` | Run Playwright E2E tests |

---

## Database

- Type: SQLite (async via aiosqlite)
- Location: `backend/data/dewugojin.db` (auto-created on first run)
- Migrations: `backend/migrations/` (run automatically at startup, idempotent)
- Schema: see `docs/data-model.md`

To reset the database, delete `backend/data/dewugojin.db` and restart the backend.

---

## Environment Variables

Backend `.env` file (in `backend/` directory):

| Variable | Required | Description |
|----------|----------|-------------|
| COOKIE_ENCRYPT_KEY | yes | AES-256 encryption key for credentials |
| DATABASE_URL | no | SQLite URL (default: `sqlite+aiosqlite:///data/dewugojin.db`) |
| DEBUG | no | Enable debug mode (default: false) |
| MATERIAL_BASE_PATH | no | Base path for material files |
| CORS_ORIGINS | no | Allowed CORS origins (default: localhost) |

---

## Development Workflow

1. Start backend: `cd backend && .\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173` in browser
4. API docs at `http://localhost:8000/docs`

### Code Standards

| Domain | Rules |
|--------|-------|
| Python | Type annotations, loguru (not print), Pydantic v2, async/await |
| TypeScript | Strict mode, no `any`, functional components, Zustand for state |
| Security | AES-256-GCM for credentials, no secrets in code, Pydantic validation |

See `.claude/rules/` for detailed coding standards.

---

## Useful References

| Document | Path | What it covers |
|----------|------|----------------|
| API Reference | `docs/api-reference.md` | All endpoints |
| Data Model | `docs/data-model.md` | Database schemas |
| System Architecture | `docs/system-architecture.md` | Component diagram |
| Coding Rules | `.claude/rules/` | Language-specific standards |
