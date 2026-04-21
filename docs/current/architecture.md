# 当前架构基线（Current Architecture Baseline）

> Version: 0.3.0 | Updated: 2026-04-21
> Owner: Codex
> Status: Active

> 目的：给新读者和维护者提供一份**当前 authoritative 架构入口**。  
> 本文档回答“系统现在由哪些部分组成、业务主语义放在哪里、各子系统怎么协作、接下来该先读什么”。

## 1. 这份文档负责什么

本文件是 repo 级的**当前架构总入口**，负责：

- 描述当前系统的顶层拓扑
- 标出当前可信的 canonical / authoritative 文档
- 汇总本地桌面端、远程授权端、文档治理端的职责边界
- 给出推荐阅读路径

本文件**不**负责：

- 穷举全部运行时细节（见 `docs/current/runtime-truth.md`）
- 逐接口列出 API 契约（以 `/docs`、`/openapi.json`、remote shared 契约文档为准）
- 保存历史演进叙事（见 `docs/archive/`、`docs/domains/auth/`、`docs/domains/creative/*.md`）

## 2. 当前系统轮廓

当前系统已经不是“单一 Electron 应用”的心智模型，而是一个由**本地业务工作台**与**远程授权控制平面**组成的双系统：

```text
┌───────────────────────────────────────────────────────────────────┐
│ Local desktop workspace                                          │
│                                                                   │
│  Electron shell                                                   │
│    ├─ Main process: 窗口 / 托盘 / backend 生命周期 / IPC          │
│    ├─ Preload bridge: 最小 electronAPI 暴露                       │
│    └─ React renderer: HashRouter + Ant Design + React Query       │
│                                                                   │
│  FastAPI backend                                                  │
│    ├─ 业务 API: account / task / material / publish / system      │
│    ├─ Creative API: creative / review / workflow / publish-pool   │
│    ├─ Auth enforcement: machine-session / route policy            │
│    ├─ Scheduler + publish planner + task assembler                │
│    └─ SQLite + local files + FFmpeg + Patchright/Playwright       │
└───────────────────────────────────────────────────────────────────┘
                              │
                              │ remote auth / session / device trust
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│ Remote control plane                                              │
│                                                                   │
│  remote-backend (FastAPI)                                         │
│    ├─ auth API                                                    │
│    ├─ self-service API                                            │
│    └─ admin API                                                   │
│                                                                   │
│  remote-admin                                                     │
│    ├─ dashboard                                                   │
│    ├─ users / devices / sessions                                  │
│    └─ audit logs                                                  │
│                                                                   │
│  remote-shared                                                    │
│    ├─ release gate / runbook                                      │
│    ├─ compatibility harness                                       │
│    └─ contract / env / deployment docs                            │
└───────────────────────────────────────────────────────────────────┘
```

## 3. 顶层职责边界

### 3.1 本地桌面工作台（`frontend/` + `backend/`）

负责创意生产、素材组织、任务编排、调度发布、账号执行面与本地系统配置。

当前业务入口已经是 **Creative-first**：

- 默认业务入口由 `frontend/src/features/creative/creativeFlow.ts` 决定
- `frontend/src/App.tsx` 默认把 `/` 与 `/creative` 引导到 `CreativeWorkbench`
- Task 页面仍保留，但更偏向执行/兼容语义，而非唯一业务中心

### 3.2 远程授权控制平面（`remote/`）

负责独立的远程认证、管理员操作、设备与会话治理、审计与发布前治理资产。

这条线不是本地 backend 的一个“附属模块”，而是**独立 workspace**：

- `remote/remote-backend`：远程认证/控制 API
- `remote/remote-admin`：受保护的 admin 控制台
- `remote/remote-shared`：契约、兼容性、runbook、staging/release 文档

### 3.3 文档与治理平面（`docs/`）

负责把“当前真相”“历史资料”“运行时本地产物”分层。

当前文档治理原则是：

- `README.md` + `docs/README.md` 负责入口导航
- `docs/current/architecture.md` 负责架构入口
- `docs/current/runtime-truth.md` 负责事实清单
- `docs/guides/dev-guide.md` + `docs/guides/startup-protocol.md` 负责开发 / 启动协议
- `docs/archive/` 保留历史参考，不再默认视为当前真相

## 4. 本地桌面端架构

### 4.1 Electron shell

`frontend/electron/main.ts` 当前负责：

- 创建主窗口
- 创建系统托盘
- 在 app ready 后启动并健康检查本地 FastAPI backend
- 提供 `get-version`、`get-platform`、`open-external`、`open-path`、窗口控制等 IPC
- 托盘侧提供发布动作入口（start / pause）

`frontend/electron/preload.ts` 通过 `contextBridge` 暴露最小 `electronAPI`，保持：

- `contextIsolation = true`
- `nodeIntegration = false`
- renderer 不直接获得 Node.js 完整能力

### 4.2 React renderer

当前 renderer 的核心分层：

```text
src/
├─ api/            OpenAPI 生成客户端与基础序列化逻辑
├─ components/     通用页面/选择/布局组件
├─ features/
│  ├─ auth/        登录、授权门禁、状态页、session admin
│  └─ creative/    Creative workbench / detail / workflow panels
├─ hooks/          account/task/material/publish/system 等业务 hooks
├─ pages/          Dashboard、Account、Task、Material、AIClip、Settings...
├─ providers/      QueryProvider
└─ services/       API 适配层
```

当前前端有两条明显主线：

1. **Auth shell**
   - `features/auth/*`
   - 登录页、门禁、错误边界、状态页、session 管理
   - 路由层区分 public login 与 protected app shell

2. **Creative workbench**
   - `features/creative/pages/CreativeWorkbench.tsx`
   - `features/creative/pages/CreativeDetail.tsx`
   - `VersionPanel`、`CheckDrawer`、`AIClipWorkflowPanel`
   - 已成为默认业务入口

### 4.3 前端路由结构

从 `frontend/src/App.tsx` 看，当前主路由包括：

- `login`
- `auth/revoked` / `auth/device-mismatch` / `auth/expired` / `auth/grace`
- `dashboard`
- `account`
- `creative/workbench`
- `creative/:id`
- `task/list` / `task/create` / `task/:id`
- `material/*`
- `ai-clip`
- `settings`
- `settings/auth-admin`
- `schedule-config`
- `profile-management`

这意味着当前前端已经不是单纯的“任务管理后台”，而是：

- 先经过授权门禁
- 再进入 Creative-first 工作台
- 同时保留 Task / Material / Schedule / Settings 等执行与配置面

## 5. 本地 FastAPI backend 架构

### 5.1 API surface

`backend/api/` 目前已经形成三类 API 面：

#### A. 业务资源面

- `account.py`
- `task.py`
- `product.py`
- `video.py`
- `copywriting.py`
- `cover.py`
- `audio.py`
- `topic.py`
- `profile.py`
- `system.py`
- `schedule_config.py`
- `publish.py`

#### B. Creative 面

- `creative.py`
- `creative_review.py`
- `creative_publish_pool.py`
- `creative_workflows.py`

#### C. 本地 auth / admin 面

- `auth.py`
- 路由中同时存在 end-user auth 与本地 admin/session 管理能力

### 5.2 服务层

`backend/services/` 当前已经体现出“组合式业务核心”，而不是早期的少量 service：

- 发布与调度：`publish_service.py`、`publish_planner_service.py`、`scheduler.py`
- 任务与素材语义：`task_service.py`、`task_assembler.py`、`task_distributor.py`
- Creative：`creative_service.py`、`creative_version_service.py`、`creative_review_service.py`
- AI / 合成：`ai_clip_service.py`、`ai_clip_workflow_service.py`、`composition_service.py`、`local_ffmpeg_composition_service.py`
- 配置与系统：`schedule_config_service.py`、`system_config_service.py`、`system_backup_service.py`
- 兼容与领域收口：`task_compat_service.py`、`topic_relation_service.py`、`topic_semantics.py`

### 5.3 核心基础设施

`backend/core/` 当前关键基础设施包括：

- `config.py`：运行配置
- `browser.py` / `dewu_client.py`：本地自动化执行面
- `remote_auth_client.py`：连接远程授权控制平面
- `auth_dependencies.py`：路由级授权策略收口
- `device_identity.py`：设备身份
- `secret_store.py` / `auth_crypto.py`：本地 secret 存储与 auth secret 加密
- `auth_events.py` / `auth_metrics.py` / `observability.py`：auth 与观测

### 5.4 当前 backend 的关键判断

当前 backend 不是“只有 CRUD 的本地 API”，而是同时承担：

- 本地业务真相汇聚层
- 执行面调度与发布 orchestrator
- Creative / Version / Review 语义中心
- 本地 machine-session 授权 enforcement
- 与远程授权系统的桥接适配层

## 6. 当前业务主语义

### 6.1 Creative-first

当前主业务语义已经从“Task-first”迁移到“Creative-first”：

- Creative workbench 成为默认业务入口
- Creative detail / version / review / publish-pool 已形成专门 API 与前端面
- Task 仍存在，但更多承接执行、兼容、映射与调度语义

相关 supporting docs：

- `docs/domains/creative/progressive-rebuild-final-summary.md`
- `docs/domains/creative/progressive-rebuild-completion-audit.md`

### 6.2 调度配置真相

当前 canonical source 为 `ScheduleConfig`，而不是旧的 `publish_config`。

详见：

- `docs/current/runtime-truth.md`
- `docs/domains/system/settings-truth-matrix.md`

### 6.3 Topic / relation-first

Topic 语义已收口到 relation-first canonical source，旧 JSON/FK 字段只承担兼容与回退角色。

详见：

- `docs/domains/publishing/phase-6-topic-compat-matrix.md`
- `docs/domains/publishing/phase-6-topic-relation-cutover.md`
- `docs/adr/ADR-016-topic-canonical-semantics-phase-6.md`

## 7. 当前 auth 架构位置

当前 auth 不是单点功能，而是贯穿本地与远程两层：

### 7.1 本地

- 前端通过 `features/auth/*` 管理登录态、门禁、错误 UX、状态页
- backend 通过 `core/auth_dependencies.py` 将路由区分为：
  - `ACTIVE_REQUIRED`
  - `GRACE_READONLY_ALLOWED`
- 许多只读路由已经明确允许 grace 模式访问

### 7.2 远程

- `remote/remote-backend/app/api/auth.py`
- `remote/remote-backend/app/api/self_service.py`
- `remote/remote-backend/app/api/admin.py`

共同提供：

- 远程认证
- 自助视角
- 管理员控制平面

### 7.3 控制台

`remote/remote-admin` 当前已具备：

- `dashboard`
- `users`
- `devices`
- `sessions`
- `audit-logs`

所以当前 auth 架构应理解为：

> **远程授权决定信任，本地 machine-session 决定执行面能否继续工作。**

## 8. 远程 workspace 架构

`remote/README.md` 明确了 remote workspace 的当前边界：

```text
remote/
├─ remote-backend/   FastAPI remote auth/admin backend
├─ remote-admin/     protected admin console
├─ remote-shared/    OpenAPI / compatibility / release docs / runbooks
└─ .env.example      shared env template
```

当前 remote 线已经包含 MVP + Phase 4 hardening 资产，覆盖：

- admin RBAC
- actor-level audit
- dashboard / audit operational UX
- users / devices / sessions 运维能力
- release gate / checklist / rollback / restore runbook

这意味着 remote 线已进入**可运维、可发布治理**阶段，而不再只是合同占位。

## 9. 测试与验证结构

当前工程的验证面已经分成多层：

### 9.1 本地 backend

`backend/tests/` 中包含：

- auth 系列测试
- creative 系列测试
- composition / FFmpeg / contract 系列测试
- doc truth / generated artifact / openapi parity 系列测试

### 9.2 本地 frontend

`frontend/e2e/` 中包含 Playwright E2E：

- auth bootstrap / shell / routing / admin / transport
- creative workbench / review / version panel
- ai-clip workflow
- publish pool / publish cutover
- task management / diagnostics

### 9.3 remote

`remote/README.md` 与 `remote/remote-shared/docs/*release-gate*.md` 已定义 remote release gate，覆盖：

- pytest
- compatibility harness
- remote-admin typecheck / build / test

### 9.4 最小可信回归基线入口

“至少跑什么”不再分散在 README、remote runbook、个人记忆里，而是统一收口到：

- `docs/governance/verification-baseline.md`

它把当前验证面拆成：

- 日常开发必跑
- 文档 / 启动协议补充基线
- remote 最小 gate
- 阶段发布必跑

## 10. 当前 authoritative 文档入口

建议把下面几份文档当作当前阅读主路径：

| 文档 | 作用 |
|---|---|
| `README.md` | 项目入口与启动方式 |
| `docs/README.md` | 文档导航首页 |
| `docs/current/architecture.md` | 当前架构入口 |
| `docs/current/runtime-truth.md` | 当前 runtime facts / canonical truth |
| `docs/governance/authority-matrix.md` | current / working / archival / runtime 边界 |
| `docs/guides/dev-guide.md` | 开发与启动协议 |
| `docs/governance/verification-baseline.md` | 最小可信回归基线与分层验证清单 |
| `docs/current/next-phase-kickoff.md` | 下一阶段启动入口与推荐主线 |
| `docs/guides/startup-protocol.md` | 启动模式、服务矩阵与 launcher 协议 |
| `docs/domains/auth/README.md` | auth 相关冻结规范与实现总结入口 |
| `remote/README.md` | remote workspace 总入口 |

## 11. 推荐阅读路径

### 11.1 想快速了解系统

1. `README.md`
2. `docs/README.md`
3. `docs/current/architecture.md`

### 11.2 想知道“当前真实行为”

1. `docs/current/runtime-truth.md`
2. 对应专题真相文档（settings / topic / auth / creative）
3. 必要时再回到代码

### 11.3 想知道“远程授权线怎么组织”

1. `remote/README.md`
2. `docs/domains/auth/README.md`
3. `remote/remote-shared/docs/remote-full-system-operating-model-v1.md`

### 11.4 想知道“为什么当前是 Creative-first”

1. `docs/domains/creative/progressive-rebuild-final-summary.md`
2. `docs/domains/creative/progressive-rebuild-completion-audit.md`

### 11.5 想直接开始下一阶段开发

1. `docs/current/next-phase-kickoff.md`
2. `docs/governance/next-phase-backlog.md`
3. `docs/governance/next-phase-prd.md`
4. `docs/governance/next-phase-test-spec.md`
5. `docs/governance/next-phase-execution-breakdown.md`

## 12. 与历史文档的关系

`docs/archive/reference/system-architecture.md` 仍保留，但它是**历史长文参考**，不是默认 authoritative source。

当它与当前代码或本文档不一致时，优先级应为：

1. 代码
2. `docs/current/runtime-truth.md`
3. 本文档
4. archival / historical 文档

---

如果只允许记住一句话，可以记住：

> 当前系统是一个 **Creative-first 的本地桌面工作台**，由 **Electron + React + FastAPI + SQLite** 承载执行面，并通过 **remote auth/control plane** 提供远程授权、设备/会话治理与运营控制能力。
