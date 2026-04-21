# 得物掘金工具

**版本**: 0.2.0
**技术栈**: Electron + React + Vite + FastAPI + Patchright/Playwright + FFmpeg

得物平台自动化视频发布系统，支持多账号管理、智能素材剪辑、任务定时发布。

## 当前推荐阅读入口

请优先按下面顺序阅读当前文档真相：

1. `docs/README.md` — 文档导航首页
2. `docs/current/architecture.md` — 当前架构总入口
3. `docs/current/runtime-truth.md` — 当前运行事实清单
4. `docs/governance/authority-matrix.md` — 文档职责边界
5. `docs/guides/dev-guide.md` — 开发与启动指南
6. `docs/governance/verification-baseline.md` — 最小可信回归基线 / 日常开发必跑 / 阶段发布必跑

## 功能特性

- **账号管理**: 多账号 cookie 加密存储，浏览器上下文隔离
- **素材管理**: 视频、文案、封面、话题、音频素材分类管理
- **AI 剪辑**: 基于 FFmpeg 的智能视频剪辑，高光检测，背景音乐添加
- **任务发布**: 可视化任务配置，定时发布，发布日志记录
- **Electron 桌面**: 原生窗口控制，系统托盘，后台运行

## 快速开始

### 环境要求

- Node.js 22+
- Python 3.11+
- FFmpeg 6+（需在 PATH 中）
- Git 2.40+

> 当前仓库的启动脚本主要检查可执行程序是否存在，**不直接做版本硬门禁**；  
> 文档推荐基线以 `docs/guides/dev-guide.md` 为准。

### 安装依赖

```bash
# 使用启动脚本（推荐起步方式：本地 frontend + backend）
.\dev.bat

# 或手动安装

# 前端依赖
cd frontend
npm install

# 后端依赖
cd ../backend
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python -m playwright install chromium
```

### 启动服务

```bash
# Windows
.\dev.bat

# 或按协议拆开运行
# 终端1: 后端（通过统一启动脚本）
cd backend
.\run.bat

# 终端2: 前端
cd frontend
npm run dev
```

### 推荐：3 个脚本启动 4 个服务

```powershell
cd E:\ais\mydw

.\scripts\start-backend.bat
.\scripts\start-frontend.bat
.\scripts\start-remote.bat
```

说明：
- `.\dev.bat`：最快启动**本地 frontend + backend**
- `.\scripts\start-backend.bat` + `.\scripts\start-frontend.bat` + `.\scripts\start-remote.bat`：用于**本地 + remote 全量联调**

脚本说明：

- `scripts\start-backend.bat`
  - 启动本地 `backend`
- `scripts\start-frontend.bat`
  - 一键启动本地前端
  - 若 `backend:8000` 未启动，会自动先启动后端
- `scripts\start-remote.bat`
  - 一键启动 `remote-backend + remote-admin`
  - 会自动 build `remote-admin` 并 bootstrap admin 账号

配套辅助脚本：

```powershell
.\scripts\status-all.bat
.\scripts\stop-all.bat
```

- `scripts\status-all.bat`
  - 查看 4 个服务当前状态、端口和访问地址
- `scripts\stop-all.bat`
  - 按端口停止 `backend / frontend / remote-backend / remote-admin`

> Electron 运行时不再应直接依赖 Python venv / exe 路径布局。  
> 详见 `docs/guides/startup-protocol.md`。

### 访问地址

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- remote-backend: http://127.0.0.1:8100
- remote-admin: http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100

## 当前文档边界

- 文档导航首页：`docs/README.md`
- 当前架构总览：`docs/current/architecture.md`
- 当前运行事实：`docs/current/runtime-truth.md`
- runtime/local 资产边界：`docs/governance/runtime-local-artifact-policy.md`（`.codex/`、`.omx/`、`.omc/`、本地 runtime 输出目录不属于主文档入口）
- 当前验证基线：`docs/governance/verification-baseline.md`
- 旧的详细架构说明、API 参考、数据模型字典在 Epic 7 / PR2 后会被视为 **stale / archival reference**，位于 `docs/archive/reference/` 下；阅读时请先以当前入口文档为准。

## 数据安全

- Cookie 使用 AES-256-GCM 加密存储
- 密钥由环境变量 `SECRET_KEY` 配置
- 数据库文件位于 `backend/data/dewugojin.db`

## 构建应用

```bash
cd frontend
npm run build
```

打包后的应用位于 `frontend/dist-electron/` 目录。

## 开发指南

详见 `docs/guides/dev-guide.md`
