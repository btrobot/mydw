# 项目介绍与新同事上手导览

## 一句话总结
这是一个**面向得物平台的桌面端自动化发布工具**，核心目标是：**管理账号、管理素材、组装发布任务、按调度自动发布视频内容**。

同时，仓库中还在演进一条独立的 **remote 远程授权/管理中心** 主线，用于远程授权、设备控制、管理后台和审计。

---

## 项目定位
这个项目不是单纯爬虫，也不是单纯 CMS，而更像一个：

**带本地自动执行能力的内容发布运营工作台。**

它把以下能力整合在一起：

- 桌面化运行
- 浏览器自动化执行
- 素材与任务统一管理
- 调度与自动发布
- AI 剪辑与视频处理
- 授权门禁与远程控制能力

---

## 主要技术栈
主线项目使用的技术栈：

- **Electron**：桌面应用外壳
- **React + Vite**：前端界面
- **FastAPI**：本地后端 API
- **SQLite**：本地数据存储
- **Patchright / Playwright**：浏览器自动化
- **FFmpeg**：视频处理 / AI 剪辑

从当前文档与代码结构看，主架构仍然是：

**Electron + React + FastAPI + SQLite 的桌面应用。**

---

## 核心功能概览

### 1. 账号管理
- 多账号支持
- Cookie 加密存储
- 浏览器上下文隔离

### 2. 素材管理
- 视频素材
- 文案素材
- 封面素材
- 音频素材
- 话题素材
- 商品素材

### 3. 任务编排与发布
- 任务创建、列表、详情
- 调度配置
- 发布控制
- 发布状态与日志
- 定时自动发布

### 4. AI 剪辑
- 基于 FFmpeg 的视频处理能力
- AI 剪辑相关服务已进入后端主工程

### 5. Electron 桌面化运行
- 原生窗口控制
- 托盘能力
- 后端进程拉起与生命周期管理

---

## 仓库的两条主线

### 主线 A：本地桌面发布工具
这是当前更核心、完成度更高的一条线。

业务目标：
- 管理得物账号
- 管理素材
- 组装任务
- 调度与自动发布
- AI 剪辑与自动执行

### 主线 B：remote 远程授权/管理中心
这是一个相对独立的子系统，主要用于：
- 远程授权
- 远程设备 / 会话控制
- 管理后台
- 审计与指标

组成包括：
- `remote/remote-backend/`：远程认证 / 管理后端
- `remote/remote-admin/`：远程管理控制台
- `remote/remote-shared/`：共享协议、脚本、运行文档

---

## 目录导览

### `frontend/`
主前端工程。

重点内容：
- 页面路由
- 认证壳
- hooks 查询层
- 业务页面与组件

当前主要页面包括：
- Dashboard
- Account
- TaskList / TaskCreate / TaskDetail
- Material（视频 / 文案 / 封面 / 音频 / 话题 / 话题组）
- Product
- AIClip
- Settings
- ScheduleConfig
- ProfileManagement

### `backend/`
主后端工程。

主要分层：
- `api/`：路由层
- `services/`：业务逻辑层
- `models/`：数据模型
- `migrations/`：迁移
- `core/`：配置、浏览器、平台客户端等基础能力

当前路由覆盖的业务模块包括：
- auth
- account
- task
- publish
- schedule_config
- system
- ai
- product
- video
- copywriting
- cover
- audio
- topic
- profile

### `docs/`
当前可信文档入口。

仓库已经明确区分了：
- current / canonical 文档
- historical / archival 文档

阅读时应优先相信：
- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`

### `remote/`
远程授权中心相关工程。

建议在理解主线 A 之后再进入这一部分。

### `remote-docs/`
remote 子系统的架构与设计文档。

---

## 推荐阅读顺序
如果你是第一次接手项目，推荐按下面顺序阅读：

1. `README.md`
2. `docs/README.md`
3. `docs/current/architecture.md`
4. `docs/current/runtime-truth.md`
5. `docs/guides/dev-guide.md`

这几份文档能回答：
- 项目是什么
- 当前真实架构是什么
- 哪些旧文档已经降级
- 如何启动系统

---

## 启动方式

### 最简单启动
根目录提供：

- `dev.bat`

它会自动完成：
1. 检查 Node / Python
2. 安装 `frontend` 依赖
3. 创建 `backend/venv`
4. 安装后端依赖
5. 启动后端
6. 启动前端

推荐直接使用：

```powershell
.\dev.bat
```

### 手动分开启动
为了便于排查问题，也可以分终端启动。

后端：

```powershell
cd backend
.\run.bat
```

前端：

```powershell
cd frontend
npm run dev
```

访问地址：
- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

### Electron 开发模式
如果需要完整桌面应用行为：

```powershell
cd frontend
npm run dev:electron
```

---

## 新同事 30 分钟快速建立地图
建议先看这三个入口文件：

1. `frontend/src/App.tsx`
2. `backend/main.py`
3. `frontend/electron/main.js`

### 为什么先看它们

#### `frontend/src/App.tsx`
适合快速理解：
- 产品页面结构
- 路由结构
- 登录保护壳
- 主要业务入口

#### `backend/main.py`
适合快速理解：
- FastAPI 如何启动
- 注册了哪些路由
- 系统有哪些后端模块

#### `frontend/electron/main.js`
适合快速理解：
- Electron 窗口怎么创建
- 后端怎么被拉起
- 托盘如何工作
- dev / packaged 模式区别

---

## 建议优先深入的业务主链路

### 1. 调度配置
建议阅读：
- `frontend/src/hooks/useScheduleConfig.ts`
- `backend/api/schedule_config.py`
- `backend/services/schedule_config_service.py`
- `backend/services/scheduler.py`

关键理解：
- 前端当前使用 canonical API：`/api/schedule-config`
- 调度配置的真相来源是：`ScheduleConfig`

### 2. 发布控制
建议阅读：
- `frontend/src/hooks/usePublish.ts`
- `backend/api/publish.py`
- `backend/services/scheduler.py`
- `backend/services/publish_service.py`

关键理解：
- 如何启动 / 暂停发布
- 如何读取发布状态
- scheduler 如何循环工作
- 后台执行如何受授权状态约束

### 3. 任务组装
建议阅读：
- `backend/api/task.py`
- `backend/services/task_assembler.py`
- `backend/services/task_execution_semantics.py`

关键理解：
- 当前任务模型是 collection-based resource model
- 一个任务由账号与多种素材关联组成
- profile 默认配置会参与任务组装

### 4. 素材管理
建议阅读：
- `backend/api/video.py`
- `backend/api/copywriting.py`
- `backend/api/cover.py`
- `backend/api/audio.py`
- `backend/api/topic.py`
- `frontend/src/pages/material/*`

### 5. 认证与授权门禁
建议阅读：
- `frontend/src/features/auth/`
- `docs/domains/auth/README.md`
- `backend/services/scheduler.py` 中的 auth-aware runtime enforcement

关键理解：
- 认证不只是登录页
- 它已经进入后台执行约束
- 授权状态会影响发布任务的启动、暂停和停止

---

## 当前主业务链路

### 链路 A：日常使用
1. 打开桌面工具
2. 登录 / 校验授权
3. 管理账号
4. 管理或导入素材
5. 配置 profile
6. 创建任务
7. 配置调度
8. 启动发布
9. scheduler 周期性执行任务

### 链路 B：任务生成
1. 选择账号
2. 选择视频
3. 选择文案 / 封面 / 音频 / 话题
4. 合并 profile 默认设置
5. `TaskAssembler` 组装任务
6. 任务进入 `ready` 或 `draft`

### 链路 C：后台发布
1. scheduler 读取 `ScheduleConfig`
2. 获取下一个待执行任务
3. 检查当前 auth 状态是否允许执行
4. 调用 `PublishService`
5. 完成后等待下一轮

---

## 第一天下手建议

### 第 1 步：先跑起来
执行：

```powershell
.\dev.bat
```

确认：
- 前端能打开
- 后端 `/docs` 可访问
- 页面能够正常进入

### 第 2 步：建立系统地图
按顺序看：
1. `frontend/src/App.tsx`
2. `backend/main.py`
3. `frontend/electron/main.js`

目标是建立总体认知，而不是马上读细节。

### 第 3 步：只追一条主链路
优先建议：
1. 调度 / 发布
2. 任务组装
3. 认证与授权

不要一开始同时深入所有模块。

---

## 关于 remote 子系统的建议阅读顺序
在理解主线 A 之后，再阅读：

1. `remote/README.md`
2. `remote-docs/remote-auth-current-architecture.md`
3. `remote/remote-backend/app/main.py`
4. `remote/remote-admin/src/main.ts`

这样会更容易理解三者边界：
- 本地端：consumer / projection
- remote-backend：授权真相源
- remote-admin：管理与运维控制台

---

## 文档阅读的重要提醒
这个仓库对文档做了 current / archive 分层。

因此：
- 优先相信 `docs/current/architecture.md`
- 优先相信 `docs/current/runtime-truth.md`
- archive 文档更多用于历史背景参考

如果旧文档和当前代码不一致，应优先以 current 文档和代码为准。

---

## 建议收藏的关键文件

### 文档
- `README.md`
- `docs/README.md`
- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/guides/dev-guide.md`

### 前端
- `frontend/src/App.tsx`
- `frontend/src/features/auth/index.ts`
- `frontend/src/hooks/useScheduleConfig.ts`
- `frontend/src/hooks/usePublish.ts`

### 后端
- `backend/main.py`
- `backend/core/config.py`
- `backend/services/scheduler.py`
- `backend/services/task_assembler.py`
- `backend/models/__init__.py`

### Electron
- `frontend/electron/main.js`

### Remote
- `remote/README.md`
- `remote/remote-backend/app/main.py`
- `remote/remote-admin/src/main.ts`

---

## 一个需要注意的小点
当前文档中的环境要求有轻微不一致：

- `README.md` 写的是：Node 18+、Python 3.10+
- `docs/guides/dev-guide.md` 写的是：Node 22+、Python 3.11+

如果希望更稳妥，建议优先按 `docs/guides/dev-guide.md` 执行，也就是：

- Node 22+
- Python 3.11+

---

## 最后的建议
如果你准备接手这个项目，最有效的动作不是继续泛读，而是：

1. 先跑起来
2. 先看 App.tsx 和 backend/main.py 建立地图
3. 只追一条主链路：调度 / 发布

这样能最快进入有效状态。
