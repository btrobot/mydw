# 得物掘金工具

**版本**: 0.2.0
**技术栈**: Electron + React + Vite + FastAPI + Playwright + FFmpeg

得物平台自动化视频发布系统，支持多账号管理、智能素材剪辑、任务定时发布。

## 当前推荐阅读入口

请优先按下面顺序阅读当前文档真相：

1. `docs/README.md` — 文档导航首页
2. `docs/current-architecture-baseline.md` — 当前架构总入口
3. `docs/current-runtime-truth.md` — 当前运行事实清单
4. `docs/epic-7-doc-authority-matrix.md` — 文档职责边界
5. `docs/dev-guide.md` — 开发与启动指南

## 功能特性

- **账号管理**: 多账号 cookie 加密存储，浏览器上下文隔离
- **素材管理**: 视频、文案、封面、话题、音频素材分类管理
- **AI 剪辑**: 基于 FFmpeg 的智能视频剪辑，高光检测，背景音乐添加
- **任务发布**: 可视化任务配置，定时发布，发布日志记录
- **Electron 桌面**: 原生窗口控制，系统托盘，后台运行

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.10+
- FFmpeg (用于 AI 剪辑功能)
- Git

### 安装依赖

```bash
# 使用启动脚本（推荐）
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

> Electron 运行时不再应直接依赖 Python venv / exe 路径布局。  
> 详见 `docs/startup-protocol.md`。

### 访问地址

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 当前文档边界

- 文档导航首页：`docs/README.md`
- 当前架构总览：`docs/current-architecture-baseline.md`
- 当前运行事实：`docs/current-runtime-truth.md`
- 旧的详细架构说明、API 参考、数据模型字典在 Epic 7 / PR2 后会被视为 **stale / archival reference**，阅读时请先以当前入口文档为准。

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

详见 `docs/dev-guide.md`
