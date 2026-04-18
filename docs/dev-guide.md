# Dev Guide

> Version: 1.0.0 | Updated: 2026-04-18
> Owner: Tech Lead
> Status: Active

Quick start guide for DewuGoJin development environment.

---

## Windows / PowerShell 快速运行与测试

### 最快启动方式

在仓库根目录执行：

```powershell
cd E:\ais\mydw
.\dev.bat
```

该脚本会自动检查 Node / Python 环境、按需安装依赖，并启动：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 手动分别启动前后端

#### 后端

```powershell
cd E:\ais\mydw\backend
.\setup.bat   # 首次运行可先执行
.\run.bat
```

#### 前端

```powershell
cd E:\ais\mydw\frontend
npm install   # 首次运行时执行
npm run dev
```

### 常用测试命令

```powershell
cd E:\ais\mydw\frontend
npm run typecheck
npm run build
```

E2E 首次需安装 Playwright Chromium：

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e:install
```

运行全部 E2E：

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e
```

运行单个测试文件（例如登录流程）：

```powershell
cd E:\ais\mydw\frontend
.\node_modules\.bin\playwright.cmd test --config=e2e/playwright.config.ts e2e\login\login.spec.ts
```

### Preview 模式说明

如果运行：

```powershell
cd E:\ais\mydw\frontend
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
```

同时看到 `127.0.0.1:8000 ECONNREFUSED`，通常不是前端 preview 自身故障，而是 **后端未启动**。当前前端会把 `/api/*` 请求代理到 `127.0.0.1:8000`，因此 preview 前请先启动后端：

```powershell
cd E:\ais\mydw\backend
.\run.bat
```

然后再访问：`http://127.0.0.1:4173`

### Electron 开发模式

```powershell
cd E:\ais\mydw\frontend
npm run dev:electron
```

### 辅助脚本

仓库根目录可直接使用以下脚本：

```powershell
.\scripts\start-backend.bat
.\scripts\start-frontend.bat
.\scripts\start-remote.bat
.\scripts\status-all.bat
.\scripts\stop-all.bat
```

其中：

- `start-backend.bat`：启动本地后端
- `start-frontend.bat`：启动本地前端；若后端未启动会尝试先拉起后端
- `start-remote.bat`：启动 remote 相关服务
- `status-all.bat`：查看当前服务状态
- `stop-all.bat`：停止已启动服务

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

# Install Patchright browser runtime (backend automation uses patchright.async_api)
python -m patchright install chromium

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
│   ├── browser.py       # Patchright browser manager
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
- Schema: see `docs/archive/reference/data-model.md`

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

See `AGENTS.md`, `backend/CLAUDE.md`, and the current OMX/Codex workflow surfaces for detailed coding and collaboration conventions.

---

## Useful References

| Document | Path | What it covers |
|----------|------|----------------|
| API Reference | `docs/archive/reference/api-reference.md` | Historical endpoint reference |
| Data Model | `docs/archive/reference/data-model.md` | Historical schema reference |
| System Architecture | `docs/archive/reference/system-architecture.md` | Historical architecture deep-dive |
| Coding & Workflow Conventions | `AGENTS.md`, `backend/CLAUDE.md` | Current repo-wide coding and collaboration expectations |
