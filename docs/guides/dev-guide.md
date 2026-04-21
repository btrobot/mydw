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

该脚本会自动检查 Node / Python 环境、按需安装依赖，并启动**本地开发双服务**：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

> `dev.bat` **不负责启动 remote 系统**。  
> 如果你需要本地端 + remote 联调，请使用下面的“拆分启动”方式。

### 推荐拆分启动（本地 + remote 联调）

```powershell
cd E:\ais\mydw

.\scripts\start-backend.bat
.\scripts\start-frontend.bat
.\scripts\start-remote.bat
```

这组脚本会收口成 4 个服务：

- 本地 backend：`http://127.0.0.1:8000`
- 本地 frontend：`http://localhost:5173`
- remote-backend：`http://127.0.0.1:8100`
- remote-admin：`http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100`

### 兼容 / 手动启动方式

当你只想单独调试某一层时，可按下面方式手动启动。

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

#### remote-backend

```powershell
cd E:\ais\mydw\remote\remote-backend
python -c "from app.migrations.runner import upgrade; upgrade()"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

#### remote-admin

```powershell
cd E:\ais\mydw
npm --prefix remote\remote-admin run build
python -m http.server 4173 --bind 127.0.0.1 --directory remote/remote-admin
```

打开：

```text
http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100
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
- `start-frontend.bat`：启动本地前端；若 `8000` 未监听会尝试先拉起本地后端
- `start-remote.bat`：构建 `remote-admin`、bootstrap 默认 admin，并启动 `remote-backend + remote-admin`
- `status-all.bat`：查看当前服务状态
- `stop-all.bat`：停止已启动服务

---

## Recommended Baseline

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 22+ | Frontend / Electron / remote-admin build |
| Python | 3.11+ | Local backend / remote-backend runtime |
| Git | 2.40+ | Version control |
| FFmpeg | 6+ | Video processing (must be in PATH) |

补充说明：

- 这是**当前推荐开发基线**，同时也是 README / 当前文档入口采用的统一口径。
- `dev.bat`、`scripts/start-*.bat` 当前主要检查可执行程序是否存在，**不会直接阻止较低版本运行**。
- 但当前仓库的稳定维护与文档承诺，统一按 **Node 22+ / Python 3.11+ / FFmpeg 6+** 进行。

## Service / Port / Responsibility Matrix

| Service | Startup path | Default bind / URL | Responsibility | Notes |
|---|---|---|---|---|
| Local backend | `.\dev.bat` / `.\scripts\start-backend.bat` / `cd backend && .\run.bat` | `127.0.0.1:8000` | 本地业务 API、调度、素材、Creative、auth enforcement | `backend/run.bat` 支持 `BACKEND_HOST` / `BACKEND_PORT` 覆盖，默认 `127.0.0.1:8000` |
| Local frontend | `.\dev.bat` / `.\scripts\start-frontend.bat` / `cd frontend && npm run dev` | `http://localhost:5173` | React + Vite 本地工作台 | `start-frontend.bat` 若发现 `8000` 未监听，会尝试先拉起本地 backend |
| remote-backend | `.\scripts\start-remote.bat` / `cd remote\\remote-backend && python -m uvicorn ... --port 8100` | `http://127.0.0.1:8100` | 远程授权、设备/会话、admin control plane API | `start-remote.bat` 启动前会先跑 migration 和 bootstrap admin |
| remote-admin | `.\scripts\start-remote.bat` / build + `python -m http.server 4173 ...` | `http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100` | 远程管理控制台静态壳 | 当前本地模式下是 build 后的静态页面，由 Python `http.server` 提供 |

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

# Install browser runtime used by the current bootstrap scripts
python -m playwright install chromium

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
│   ├── main.ts          # Electron main source of truth
│   ├── preload.ts       # Context bridge source of truth
│   ├── backendLauncher.ts
│   ├── main.js          # generated runtime mirror
│   └── preload.js       # generated runtime mirror
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

日常建议按下面三档理解：

1. **最快本地起步**：`.\dev.bat`
2. **全量联调**：`.\scripts\start-backend.bat` + `.\scripts\start-frontend.bat` + `.\scripts\start-remote.bat`
3. **单层排障 / 兼容模式**：分别执行 `backend/run.bat`、`npm run dev`、`python -m uvicorn ... --port 8100`

如果你只是做本地业务功能开发，通常先跑：

1. `.\dev.bat`
2. 打开 `http://localhost:5173`
3. 访问 `http://localhost:8000/docs` 确认 backend 正常

如果你在做授权 / remote 联调，再补跑：

4. `.\scripts\start-remote.bat`
5. 打开 `http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100`

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
| Startup Protocol | `docs/guides/startup-protocol.md` | 启动协议、服务矩阵、dev/prod 边界 |
| Runtime Truth | `docs/current/runtime-truth.md` | 当前端口、运行事实、canonical runtime 结论 |
| API Reference | `docs/archive/reference/api-reference.md` | Historical endpoint reference |
| Data Model | `docs/archive/reference/data-model.md` | Historical schema reference |
| System Architecture | `docs/archive/reference/system-architecture.md` | Historical architecture deep-dive |
| Coding & Workflow Conventions | `AGENTS.md`, `backend/CLAUDE.md` | Current repo-wide coding and collaboration expectations |
