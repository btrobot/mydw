# Phase 4 / PR1 — Electron/backend startup assumptions checklist

> 目的：冻结当前 Electron 与 backend 启动链里已经存在的环境假设，作为后续 launcher layer 改造的基线。

## 当前硬编码依赖

### Electron main process
来源：`frontend/electron/main.ts`

- [x] 开发模式硬编码 backend 根目录为 `../../backend`
- [x] 开发模式硬编码 Python 解释器为 `../../backend/venv/Scripts/python.exe`
- [x] 开发模式硬编码命令行为 `python -m uvicorn main:app --port 8000 --host 127.0.0.1`
- [x] 生产模式硬编码打包后可执行文件为 `process.resourcesPath/backend/backend.exe`
- [x] Electron 直接持有 backend spawn 的 `cwd`、`stdio`、`shell`、`detached` 细节
- [x] Electron 当前不等待 `/health` 就默认 backend 可用

## 当前 workflow / docs 假设

### README
- [x] 假设开发者按 Windows 虚拟环境路径手动激活 `backend\\venv\\Scripts\\activate`
- [x] 假设 backend 可直接通过 `uvicorn main:app` 启动

### `dev.bat`
- [x] 假设系统存在 `python`
- [x] 假设可创建并使用 `backend\\venv`
- [x] 假设 Playwright 浏览器安装路径与当前环境兼容
- [x] 假设 dev 模式通过单独 `start` 启动 backend，再由 frontend 单独运行

### `backend/run.bat`
- [x] 假设 `venv\\Scripts\\activate.bat` 可用
- [x] 假设 backend 直接以 `uvicorn main:app --reload` 运行

### `backend/setup.bat`
- [x] 假设依赖安装直接使用当前 Python / 当前 venv

## 风险归类

### 环境布局耦合
- [x] Python 路径依赖 Windows venv 目录结构
- [x] packaged exe 路径依赖 Electron resources 目录结构

### 协议缺失
- [x] 目前没有 machine-readable launcher contract
- [x] dev/prod 启动协议没有统一入口

### Readiness 缺失
- [x] `/health` 存在但没有被 Electron 正式纳入启动协议
- [x] window 创建与 backend readiness 没有明确定义关系

## 后续移除目标

这些假设应在 Phase 4 后续 PR 中被逐步移除或隔离：

- [ ] Electron 直接引用 `backend/venv/Scripts/python.exe`
- [ ] Electron 直接引用 `backend.exe`
- [ ] Electron 直接拼接 `uvicorn main:app ...`
- [ ] docs/scripts/runtime 各自定义不同启动规则
- [ ] readiness 语义依靠隐式默认而非协议化等待

## PR2 之前的冻结点

进入 Phase 4 / PR2 前应满足：

- [x] 上述 assumptions 已被完整记录
- [x] machine-readable launcher contract 已存在
- [x] 后续 PR 不再争论“当前 Electron 具体耦合了什么”
