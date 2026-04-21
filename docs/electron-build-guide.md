# Electron 构建指南

> 适用仓库：`E:\ais\mydw`
>  
> 当前项目不是“只打前端”即可发布的纯前端桌面壳，而是：
> - 前端：`React + Vite + Electron`
> - 后端：`FastAPI`
> - 打包方式：`PyInstaller + electron-builder`

---

## 1. 构建目标

构建结果包括两类产物：

1. **后端可执行包**
   - 位置：`backend/dist/backend/`
   - 核心文件：`backend/dist/backend/backend.exe`

2. **Electron 安装包 / 免安装目录**
   - 安装包：`frontend/dist-electron/得物掘金工具 Setup 0.2.0.exe`
   - 免安装目录：`frontend/dist-electron/win-unpacked/`

---

## 2. 仓库内的关键配置

### 前端打包脚本

`frontend/package.json`

```json
"build:electron": "tsc && cross-env ELECTRON_BUILD=true vite build && cd electron && tsc && cd .. && electron-builder"
```

### Electron 打包时会额外带上后端

`frontend/package.json`

```json
"extraResources": [
  {
    "from": "../backend/dist/backend",
    "to": "backend",
    "filter": ["**/*"]
  }
]
```

这意味着：

- Electron 打包前，必须先生成 `backend/dist/backend`
- 否则安装包虽然可能开始构建，但最终会缺少后端运行文件

### 后端打包规格

后端使用：

- `backend/backend.spec`
- `backend/pyinstaller_entry.py`

来生成 `backend.exe`。

---

## 3. 构建前提

建议环境：

- Windows
- Node.js 22+
- npm 10+
- Python 3.11+（当前仓库实测可用 3.13）
- 已安装 backend 虚拟环境：`backend/venv`

前端依赖目录：

- `frontend/node_modules`

后端依赖目录：

- `backend/venv/Lib/site-packages`

---

## 4. 标准构建步骤

### 第一步：构建后端可执行包

```powershell
cd E:\ais\mydw\backend
.\venv\Scripts\python.exe -m pip install pyinstaller
.\venv\Scripts\python.exe -m PyInstaller backend.spec
```

构建完成后应确认：

```text
backend/dist/backend/backend.exe
```

存在。

---

### 第二步：构建 Electron 安装包

```powershell
cd E:\ais\mydw\frontend
npm install
npm run build:electron
```

该命令会依次完成：

1. TypeScript 编译
2. Vite 前端生产构建
3. Electron 主进程 / preload 编译
4. `electron-builder` 打包

---

## 5. 构建产物位置

### 安装包

```text
frontend/dist-electron/得物掘金工具 Setup 0.2.0.exe
```

### 免安装目录

```text
frontend/dist-electron/win-unpacked/
```

可直接运行：

```text
frontend/dist-electron/win-unpacked/得物掘金工具.exe
```

### 打包后的后端资源

Electron 安装包内部会包含：

```text
frontend/dist-electron/win-unpacked/resources/backend/backend.exe
```

这说明后端已被正确带入安装包。

---

## 6. 推荐的完整命令清单

从仓库根目录执行：

```powershell
cd E:\ais\mydw\backend
.\venv\Scripts\python.exe -m pip install pyinstaller
.\venv\Scripts\python.exe -m PyInstaller backend.spec

cd E:\ais\mydw\frontend
npm install
npm run build:electron
```

---

## 7. 如何验证构建成功

至少检查以下几点：

### 7.1 后端产物存在

```text
backend/dist/backend/backend.exe
```

### 7.2 安装包存在

```text
frontend/dist-electron/得物掘金工具 Setup 0.2.0.exe
```

### 7.3 免安装版可启动

优先直接测试：

```text
frontend/dist-electron/win-unpacked/得物掘金工具.exe
```

如果免安装版能正常打开，再测试安装包。

### 7.4 安装后的资源目录包含 backend

检查：

```text
resources/backend/backend.exe
```

是否随安装包一同部署。

---

## 8. 常见问题排查

### 8.1 白屏 / 启动后无内容

本仓库曾出现过：

```text
Not allowed to load local resource: file:///D:/#/D:/dewugojin-tool/resources/app.asar/dist/index.html
```

根因是 `frontend/index.html` 里用于 `HashRouter` 的跳转修复脚本，在 `file://` 协议下错误改写了 Electron 本地页面路径。

已修复策略：

- `file://` 下不做 hash 重写
- 打开 `index.html` 时不重写
- 仅在 http(s) 静态托管 deep-link 场景下重写

如果再次出现类似问题，优先检查：

- `frontend/index.html`
- Electron 生产环境 `loadFile(...)`
- `HashRouter` 相关跳转脚本

---

### 8.2 只执行了 `npm run build`

`npm run build` 只会生成前端静态资源：

```text
frontend/dist/
```

它**不是**完整的 Electron 发布构建。

真正的桌面程序构建命令是：

```powershell
npm run build:electron
```

---

### 8.3 缺少 backend/dist/backend

如果没有先跑 PyInstaller，Electron 打包会缺少后端资源来源：

```text
../backend/dist/backend
```

因此必须先构建 backend。

---

### 8.4 图标未生效

构建日志里若出现：

```text
default Electron icon is used
```

说明 Electron Builder 没有成功使用项目配置图标。应继续检查：

- `frontend/package.json` 中 `build.win.icon`
- 图标文件实际是否存在
- 图标格式是否符合 Windows `.ico` 要求

该问题不一定阻塞构建，但会影响安装包与程序显示效果。

---

## 9. 与开发模式的区别

### 开发模式

```powershell
cd E:\ais\mydw\frontend
npm run dev:electron
```

开发模式下：

- 前端走 Vite dev server
- Electron 连接 `http://localhost:5173`
- backend 走开发启动路径

### 生产构建模式

```powershell
npm run build:electron
```

生产构建下：

- 前端加载 `dist/index.html`
- Electron 从打包资源里启动 backend
- backend 来源于 `resources/backend/backend.exe`

---

## 10. 建议的发布前检查清单

- [ ] `backend/dist/backend/backend.exe` 已生成
- [ ] `frontend/dist-electron/得物掘金工具 Setup 0.2.0.exe` 已生成
- [ ] `frontend/dist-electron/win-unpacked/得物掘金工具.exe` 可启动
- [ ] 启动后页面不白屏
- [ ] Electron 能拉起 backend
- [ ] `/health` 正常
- [ ] 关键页面可打开
- [ ] 图标、标题、资源路径无异常

---

## 11. 当前仓库的一句话总结

这个项目的 Electron 发布流程，本质上是：

> **先把 FastAPI 后端打成 `backend.exe`，再由 Electron Builder 将前端与后端一起封装为桌面应用。**

