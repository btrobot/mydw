# Startup Protocol

> Version: 1.1.0 | Updated: 2026-04-21
> Owner: Codex
> Status: Active

当前 canonical 启动协议用于回答三件事：

1. **推荐怎么启动**
2. **不同服务默认绑定到哪里**
3. **哪些方式是推荐路径，哪些只是兼容 / 手动路径**

## Canonical launcher sequence

1. 读取 launcher contract：`docs/specs/backend-launcher-contract.json`
2. 通过 launcher-compatible 入口启动 backend（dev 或 prod）
3. 等待 `/health` 满足 readiness 保证
4. readiness 成立后再创建 Electron window / tray

配套冻结说明见：`docs/guides/startup-assumptions-checklist.md`

## Recommended startup modes

### Mode A：最快本地起步

```powershell
cd E:\ais\mydw
.\dev.bat
```

用途：
- 本地 frontend + backend 快速起步
- 不包含 remote 系统

当前行为：
- 检查 `node` / `python` 是否存在
- 首次安装 `frontend` 依赖
- 首次创建 `backend/venv`
- 安装 backend 依赖与浏览器运行时
- 通过 `backend/run.bat` 拉起本地 backend
- 在当前窗口启动 Vite dev server

### Mode B：推荐联调模式（4 服务）

```powershell
cd E:\ais\mydw

.\scripts\start-backend.bat
.\scripts\start-frontend.bat
.\scripts\start-remote.bat
```

用途：
- 本地桌面工作台 + remote 授权控制面联调
- 长时间运行 / 多窗口排障 / 端口状态检查

### Mode C：兼容 / 手动模式

按层手动启动，仅在单层调试或脚本排障时使用。

本地 backend：

```powershell
cd E:\ais\mydw\backend
.\run.bat
```

本地 frontend：

```powershell
cd E:\ais\mydw\frontend
npm run dev
```

remote-backend：

```powershell
cd E:\ais\mydw\remote\remote-backend
python -c "from app.migrations.runner import upgrade; upgrade()"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

remote-admin：

```powershell
cd E:\ais\mydw
npm --prefix remote\remote-admin run build
python -m http.server 4173 --bind 127.0.0.1 --directory remote/remote-admin
```

## Service / port / responsibility matrix

| Service | Default bind / URL | Primary startup path | Responsibility | Notes |
|---|---|---|---|---|
| Local backend | `127.0.0.1:8000` | `.\dev.bat` / `.\scripts\start-backend.bat` / `backend\run.bat` | 本地业务 API、调度、素材、Creative、auth enforcement | `backend/run.bat` 支持 `BACKEND_HOST` / `BACKEND_PORT`，默认 `127.0.0.1:8000` |
| Local frontend | `http://localhost:5173` | `.\dev.bat` / `.\scripts\start-frontend.bat` / `cd frontend && npm run dev` | React + Vite 本地工作台 | `start-frontend.bat` 若发现 `8000` 未监听会尝试先拉起 backend |
| remote-backend | `http://127.0.0.1:8100` | `.\scripts\start-remote.bat` / 手动 `uvicorn` | remote auth / device / session / admin API | `start-remote.bat` 启动前会先跑 migration 和 bootstrap admin |
| remote-admin | `http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100` | `.\scripts\start-remote.bat` / build + `python -m http.server` | remote 管理控制台 | 当前本地模式下是 build 后静态页面，而不是单独 dev server |

## Recommended environment baseline

- Node.js 22+
- Python 3.11+
- FFmpeg 6+（需在 PATH 中）
- Git 2.40+

说明：
- 这是**文档承诺的推荐基线**
- 当前脚本主要检查可执行程序是否存在，不直接做版本硬门禁
- 如需统一 onboarding / CI / team 协议，应按这组版本要求执行

## Production expectation

Production Electron 必须通过 launcher adapter 启动打包后的 backend，而不是在 `frontend/electron/main.ts` 中硬编码：

- `backend/venv/Scripts/python.exe`
- `backend.exe`
- `uvicorn main:app`

开发态与生产态都必须遵循同一份 launcher contract，只是 `mode=dev` 与 `mode=prod` 的实现不同。

## Guarantees

- Electron 不应直接依赖 Python venv / exe 路径布局
- `README.md`、`docs/guides/dev-guide.md`、本文件、`scripts/start-*.bat` 应描述同一套启动协议
- `dev.bat` 是**本地双服务起步协议**
- `scripts/start-backend.bat + start-frontend.bat + start-remote.bat` 是**全量 4 服务联调协议**
- remote-admin 本地运行协议当前为：**先 build，再由 Python `http.server` 提供静态页面**
