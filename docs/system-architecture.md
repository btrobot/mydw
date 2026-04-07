# 得物掘金工具 — 系统架构说明

> 版本: 0.1.0 | 更新日期: 2026-04-07

---

## 1. 系统概览

得物掘金工具是一个**得物平台自动化视频发布系统**，以 Electron 桌面应用为载体，集成账号管理、素材管理、AI 剪辑、定时发布等功能。

```
┌─────────────────────────────────────────────────────┐
│                   Electron Shell                     │
│  ┌───────────────┐         ┌──────────────────────┐ │
│  │  Main Process │◄─IPC──►│   Renderer Process    │ │
│  │  (Node.js)    │         │   (React SPA)         │ │
│  └───────┬───────┘         └──────────┬───────────┘ │
│          │ spawn                      │ HTTP/SSE     │
│          ▼                            ▼              │
│  ┌───────────────────────────────────────────────┐  │
│  │           FastAPI Backend (Python)             │  │
│  │  ┌─────┐ ┌────────┐ ┌───────┐ ┌───────────┐  │  │
│  │  │ API │ │Services│ │ Core  │ │   Utils   │  │  │
│  │  └──┬──┘ └───┬────┘ └───┬───┘ └─────┬─────┘  │  │
│  │     │        │          │            │        │  │
│  │     ▼        ▼          ▼            ▼        │  │
│  │  ┌──────┐ ┌────────┐ ┌──────────┐ ┌───────┐  │  │
│  │  │SQLite│ │Patchright│ │  FFmpeg  │ │AES-256│  │  │
│  │  └──────┘ └────────┘ └──────────┘ └───────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 2. 技术栈

| 层 | 技术 | 版本 | 用途 |
|---|---|---|---|
| 桌面框架 | Electron | 28.x | 窗口管理、托盘、后端进程生命周期 |
| 前端 UI | React + TypeScript | 18 / 5 | SPA 页面渲染 |
| 组件库 | Ant Design | 5.x | UI 组件 |
| 状态管理 | React Query (TanStack) | 5.x | 服务端状态缓存与同步 |
| 构建 | Vite | 5.x | 前端打包 |
| 后端框架 | FastAPI | — | REST API + SSE |
| ORM | SQLAlchemy (async) | 2.x | 数据库访问 |
| 数据库 | SQLite (aiosqlite) | — | 本地持久化 |
| 浏览器自动化 | Patchright (Playwright fork) | — | 反检测浏览器操作 |
| 视频处理 | FFmpeg (subprocess) | — | 剪辑、转码、封面提取 |
| 加密 | cryptography (AES-256-GCM) | — | Cookie/手机号加密存储 |
| 日志 | Loguru | — | 结构化日志 |

---

## 3. 前端架构

### 3.1 进程模型

```
Electron Main Process (electron/main.ts)
  ├── 创建 BrowserWindow (contextIsolation=true, nodeIntegration=false)
  ├── 系统托盘 (最小化到托盘)
  ├── spawn 后端 Python 进程
  └── IPC Handlers: get-version, get-platform, open-external, open-path, window-*

Preload (electron/preload.ts)
  └── contextBridge.exposeInMainWorld('electronAPI', { ... })
      仅暴露: getVersion, getPlatform, openExternal, openPath, window控制, onPublishAction

Renderer Process (React SPA)
  └── 通过 HTTP/SSE 与后端通信，不直接访问 Node.js API
```

### 3.2 页面结构

```
App.tsx
  └── ConfigProvider (Ant Design 中文 + 主题)
      └── QueryProvider (React Query)
          └── BrowserRouter
              └── Layout (Header + Sider + Content)
                  ├── /dashboard   → Dashboard    数据看板
                  ├── /account     → Account      账号管理
                  ├── /task        → Task          任务管理
                  ├── /material    → Material      素材管理
                  ├── /ai-clip     → AIClip        AI 剪辑
                  └── /settings    → Settings      系统设置
```

### 3.3 数据流

```
页面组件
  └── Custom Hook (useAccount, useTask, useMaterial, useAIClip, usePublish, useSystem)
      └── React Query (useQuery / useMutation)
          └── 生成式 API SDK (@/api/sdk.gen.ts) 或 Axios 实例 (@/services/api.ts)
              └── HTTP → FastAPI Backend
```

- API 客户端由 OpenAPI 规范自动生成 (`@/api/sdk.gen.ts`, `types.gen.ts`)
- 部分新增端点（tag/search 过滤、preview、health-check）通过手动 Axios 调用补充
- SSE 用于连接流程的实时状态推送 (`EventSource`)

### 3.4 共享组件

| 组件 | 用途 |
|---|---|
| `Layout` | 全局布局：Header + 侧边导航 + 内容区 |
| `ConnectionModal` | 手机验证码连接弹窗，含 SSE 状态订阅 |
| `StatusBadge` | 账号状态标签渲染 |

---

## 4. 后端架构

### 4.1 分层结构

```
backend/
├── main.py              # FastAPI 入口、CORS、路由注册、startup/shutdown
├── api/                 # 路由层 (thin controllers)
│   ├── account.py       # 账号管理 (含连接流程、健康检查、预览)
│   ├── task.py          # 任务 CRUD + 发布 + 批量操作
│   ├── material.py      # 素材 CRUD + 上传 + 扫描导入
│   ├── publish.py       # 发布控制 (start/pause/stop) + 配置
│   ├── ai.py            # AI 剪辑 (视频信息/高光检测/剪辑/配音/封面)
│   └── system.py        # 系统统计、日志、配置、备份、商品管理
├── services/            # 业务逻辑层
│   ├── publish_service.py   # 发布执行逻辑
│   ├── scheduler.py         # 任务调度器 (后台循环)
│   ├── task_service.py      # 任务业务逻辑
│   ├── material_service.py  # 素材业务逻辑
│   └── ai_clip_service.py   # FFmpeg 剪辑引擎
├── core/                # 核心基础设施
│   ├── config.py        # pydantic-settings 配置 (.env)
│   ├── browser.py       # BrowserManager + PreviewBrowserManager
│   └── dewu_client.py   # 得物平台自动化客户端
├── models/              # SQLAlchemy ORM 模型 + DB 初始化
├── schemas/             # Pydantic 请求/响应 Schema
├── utils/
│   ├── crypto.py        # AES-256-GCM 加密/解密 + 手机号脱敏
│   └── logger.py        # 日志配置
└── migrations/          # 数据库迁移脚本 (幂等)
```

### 4.2 数据模型 (ER)

```
Account ──1:N──► Task ──1:N──► PublishLog
                  │
Product ──1:N────┤
                  │
Video ──1:N──────┤
                  │
Copywriting ─────┤
                  │
Audio ───────────┘

Topic (全局话题池)
Cover (封面资源)
PublishConfig (单例配置)
SystemLog (系统日志)
```

| 模型 | 关键字段 |
|---|---|
| `Account` | account_id, account_name, cookie(加密), storage_state(加密), status, phone_encrypted, dewu_nickname, tags(JSON), session_expires_at, last_health_check |
| `Task` | account_id(FK), product_id(FK), video_id(FK), copywriting_id(FK), audio_id(FK), status, publish_time, priority |
| `Video` | name, file_path, product_id(FK), file_size, duration |
| `Copywriting` | content, product_id(FK), source_type, source_ref |
| `Cover` | file_path, video_id(FK), file_size |
| `Audio` | name, file_path, file_size, duration |
| `Topic` | name, heat, source |
| `Product` | name, link, description |
| `PublishLog` | task_id(FK), account_id(FK), status, message |
| `PublishConfig` | interval_minutes, start_hour, end_hour, max_per_account_per_day, shuffle, auto_start |

### 4.3 API 端点总览

| 模块 | 前缀 | 核心端点 |
|---|---|---|
| 账号管理 | `/api/accounts` | CRUD, connect/send-code/verify (手机验证码登录), SSE stream, health-check, batch-health-check, preview, disconnect, export/import session |
| 任务管理 | `/api/tasks` | CRUD, publish, batch-create, assemble, shuffle |
| 视频 | `/api/videos` | CRUD, product filter |
| 文案 | `/api/copywritings` | CRUD, product/source filter |
| 封面 | `/api/covers` | upload, list, delete |
| 音频 | `/api/audios` | upload, list, delete |
| 话题 | `/api/topics` | CRUD, search, global topics |
| 商品 | `/api/products` | CRUD, name search |
| 发布控制 | `/api/publish` | config (GET/PUT), status, control (start/pause/stop), refresh, shuffle, logs |
| AI 剪辑 | `/api/ai` | video-info, detect-highlights, smart-clip, add-audio, add-cover, trim, full-pipeline |
| 系统 | `/api/system` | stats, logs, config, backup |

### 4.4 核心流程

#### 账号连接流程 (手机验证码)

```
前端 ConnectionModal
  │
  ├─ EventSource(/connect/{id}/stream) ──► SSE 实时状态推送
  │
  ├─ POST /connect/{id}/send-code ──► 后端启动 Patchright 浏览器
  │     └─ DewuClient: 打开登录页 → 输入手机号 → 点击发送验证码
  │     └─ ConnectionStatusManager: 更新状态 → SSE 推送
  │
  └─ POST /connect/{id}/verify ──► 后端输入验证码 → 等待跳转
        └─ 成功: 保存 storage_state(加密) → 更新 Account 状态
        └─ SSE 推送 done 事件 → 前端关闭弹窗
```

#### 健康检查

```
POST /accounts/{id}/health-check
  └─ 创建浏览器上下文 (加载加密的 storage_state)
  └─ 访问 creator.dewu.com → 检测是否跳转到登录页
  └─ 有效: 更新 last_health_check + session_expires_at
  └─ 过期: 更新 status → session_expired
```

#### 发布流程

```
POST /publish/control {action: "start"}
  └─ TaskScheduler._publish_loop()
      └─ 循环: PublishService.get_next_task() → 按优先级+时间取 pending 任务
          └─ DewuClient: 打开上传页 → 上传视频 → 填写文案/话题 → 发布
          └─ 记录 PublishLog
          └─ 遵守: 时间窗口(start_hour~end_hour), 间隔, 每日上限
```

#### AI 剪辑流程

```
POST /ai/full-pipeline
  └─ AIClipService
      ├─ ffprobe: 获取视频信息
      ├─ detect_highlights: 高光片段检测
      ├─ smart_clip: FFmpeg 剪辑 + 转场
      ├─ add_audio: 混音/替换音轨
      └─ add_cover: 提取/生成封面
```

---

## 5. 安全架构

| 层面 | 措施 |
|---|---|
| 敏感数据存储 | AES-256-GCM 加密 (cookie, storage_state, phone)，PBKDF2HMAC 密钥派生 |
| 密钥管理 | 环境变量 `COOKIE_ENCRYPT_KEY`，启动时检测默认值并警告 |
| Electron 安全 | contextIsolation=true, nodeIntegration=false, preload 最小化 API 暴露 |
| API 安全 | Pydantic 输入验证, ORM 防 SQL 注入, 响应模型排除敏感字段 |
| 日志安全 | Loguru 结构化日志，禁止记录 cookie/密码/token |
| 手机号脱敏 | `mask_phone()`: 138****8000 |
| 浏览器反检测 | Patchright (Playwright fork) 规避自动化检测 |

---

## 6. 浏览器管理

系统维护两个独立的浏览器管理器：

| 管理器 | 模式 | 用途 |
|---|---|---|
| `BrowserManager` | headless (可配置) | 自动化操作：登录、发布、健康检查 |
| `PreviewBrowserManager` | headed (始终可见) | 用户手动预览账号状态，支持保存 session |

两者都通过 `storage_state` 实现会话持久化，加密存储在数据库中。

---

## 7. 配置管理

通过 `pydantic-settings` 统一管理，支持 `.env` 文件覆盖：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | sqlite+aiosqlite:///./data/dewugojin.db | 本地 SQLite |
| `PLAYWRIGHT_HEADLESS` | true | 自动化浏览器是否无头 |
| `MATERIAL_BASE_PATH` | D:/系统/桌面/得物剪辑/待上传数据 | 素材根目录 |
| `SESSION_TTL_HOURS` | 24 | 会话有效期 |
| `PUBLISH_INTERVAL_MINUTES` | 30 | 发布间隔 |
| `PUBLISH_START_HOUR` / `END_HOUR` | 9 / 22 | 发布时间窗口 |
| `MAX_PUBLISH_PER_ACCOUNT_PER_DAY` | 5 | 每账号每日上限 |

---

## 8. 多 Agent 协作框架

项目使用 Claude Code 的 Agent 定义文件实现多角色协作开发：

```
用户 (Product Owner)
  └── Tech Lead (opus, maxTurns=40)
        ├── Frontend Lead (sonnet, maxTurns=25)
        ├── Backend Lead (sonnet, maxTurns=25)
        │     └── Automation Developer (sonnet, maxTurns=25)
        ├── QA Lead (sonnet, maxTurns=25)
        ├── Security Expert (sonnet, maxTurns=25)
        └── DevOps Engineer (sonnet, maxTurns=25)
```

- Agent 定义: `.claude/agents/*.md` (frontmatter 指定 model/tools/maxTurns)
- 协作规则: `.claude/rules/coordination-rules.md` (垂直委托、水平协商、冲突升级)
- 生命周期 Hooks: `.claude/hooks/*.ts` (会话状态恢复、Agent 审计日志、Skill 记录)
- 会话状态: `production/session-state/active.md` (跨会话持久化)

---

## 9. 目录结构总览

```
dewugojin/
├── frontend/
│   ├── electron/          # Electron 主进程 + preload
│   ├── src/
│   │   ├── api/           # OpenAPI 生成的 SDK + 类型
│   │   ├── components/    # Layout, ConnectionModal, StatusBadge
│   │   ├── hooks/         # useAccount, useTask, useMaterial, useAIClip, usePublish, useSystem
│   │   ├── pages/         # Dashboard, Account, Task, Material, AIClip, Settings
│   │   ├── providers/     # QueryProvider (React Query)
│   │   └── services/      # Axios 实例
│   └── vite.config.ts
├── backend/
│   ├── api/               # 6 个路由模块
│   ├── services/          # 5 个业务服务
│   ├── core/              # config, browser, dewu_client
│   ├── models/            # 7 个 ORM 模型
│   ├── schemas/           # Pydantic schemas
│   ├── utils/             # crypto, logger
│   └── migrations/
├── production/
│   ├── session-state/     # 会话状态文件
│   └── session-logs/      # 归档日志 + Agent 审计 JSONL
├── .claude/
│   ├── agents/            # 7 个 Agent 定义
│   ├── skills/            # 7 个 Skill 工作流
│   ├── hooks/             # 6 个生命周期 Hook
│   └── rules/             # 编码规范 + 协作规则
└── docs/
    └── system-architecture.md  ← 本文件
```
