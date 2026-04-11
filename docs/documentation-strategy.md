# 文档体系策略

> 日期: 2026-04-07
> 作者: Tech Lead
> 状态: Proposed

---

## 一、现状评估

### 1.1 现有文档清单

| 类别 | 文件 | 质量 | 问题 |
|------|------|------|------|
| **项目入口** | `CLAUDE.md` | 好 | 面向 Agent 协作，不是面向开发者的 README |
| **后端入口** | `backend/CLAUDE.md` | 好 | 虚拟环境、项目结构、依赖管理，实用 |
| **系统架构（历史长文）** | `docs/system-architecture.md` | 中 | 当前保留为 stale / archival reference，不再是默认入口 |
| **旧架构文档** | `docs/architecture.md` | 过时 | 与 `system-architecture.md` 内容重叠，版本 0.2.0 |
| **需求说明** | `docs/requirements-spec.md` | 好 | 整合三份需求来源，标注冲突 |
| **用户手册** | `docs/user-guide.md` | 好 | 面向终端用户的操作指南 |
| **领域分析** | `docs/domain-model-analysis.md` | 好 | DDD 视角的素材域重建分析 |
| **差距分析** | `docs/material-gap-analysis.md` | 好 | 手册 vs 实现的偏差清单 |
| **Sprint 计划** | `docs/sprint-plan-phase{1,3,4}.md`, `sprint5.md` | 中 | 有计划但缺 phase2，编号不连续 |
| **任务分解** | `docs/task-breakdown-*.md` | 中 | 有分解但缺 phase2 |
| **ADR** | `docs/adr/ADR-007,008,015` | 中 | 只有 3 条，编号跳跃（7→8→15），缺少早期决策记录 |
| **原始需求** | `docs/init-req.md`, `docs/chat-req.md` | 参考 | 原始输入，已被 requirements-spec 整合 |
| **Agent 框架** | `.claude/docs/*.md` | 好 | DSL 规范、使用指南，面向 Agent 开发 |
| **编码规范** | `.claude/rules/*.md` | 好 | 9 个规则文件，覆盖全面 |

### 1.2 覆盖度评分

| 文档维度 | 覆盖度 | 说明 |
|----------|--------|------|
| 需求文档 | 90% | 有统一需求说明 + 差距分析，做得好 |
| 系统架构 | 85% | 当前 authoritative 入口已切到 baseline + runtime truth，旧长文仍需谨慎引用 |
| API 参考 | 20% | 架构文档有端点总览表，但无参数/响应/示例详情 |
| 数据模型 | 40% | 架构文档有 ER 概览，但字段说明不够，缺少迁移历史 |
| 开发指南 | 30% | `backend/CLAUDE.md` 有后端启动，前端完全没有 |
| ADR | 15% | 只有 3 条，大量早期决策未记录 |
| 变更日志 | 0% | 不存在 |
| 测试文档 | 0% | 无测试策略、无测试覆盖率报告 |
| 部署文档 | 0% | 无打包、分发、环境配置说明 |

### 1.3 "每次要遍历代码"的根因分析

核心问题不是文档数量不够，而是缺少**查找型文档**（reference docs）。现有文档偏向**叙事型**（架构说明、需求分析、Sprint 计划），适合从头读，不适合快速查找。

具体痛点：

| 场景 | 当前做法 | 根因 |
|------|----------|------|
| "这个 API 接受什么参数？" | 读 `backend/api/*.py` 源码 | 无 API 参考文档 |
| "Account 表有哪些字段？" | 读 `backend/models/__init__.py` | 数据模型文档只有 ER 概览 |
| "前端怎么启动？" | 猜测或问人 | 无前端开发指南 |
| "为什么用 Patchright 不用 Playwright？" | 不知道，没记录 | ADR 缺失 |
| "上个版本改了什么？" | 翻 git log | 无 CHANGELOG |
| "怎么打包发布？" | 不知道 | 无部署文档 |
| "这个模块的边界在哪？" | 读代码推断 | 架构文档有但不够细 |

---

## 二、文档体系建议

### 2.1 文档分层模型

```
                    ┌─────────────────┐
                    │   README.md     │  ← 项目入口（新增）
                    │   30 秒了解项目  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  开发指南   │  │  架构文档   │  │  参考文档   │
     │ (How-to)   │  │ (Why)      │  │ (What)     │
     └────────────┘  └────────────┘  └────────────┘
     快速启动         当前架构基线     API 参考
     添加新功能       ADR 决策记录     数据模型字典
     常见问题         领域模型分析     配置项说明
```

### 2.2 需要的文档及优先级

#### P0 — 立即需要（解决日常查找痛点）

| 文档 | 路径 | 目的 | 维护策略 |
|------|------|------|----------|
| API 参考 | `docs/api-reference.md` | 历史性参考；当前真相以 `/docs` / `/openapi.json` 为准 | **自动生成/导出** |
| 数据模型字典 | `docs/data-model.md` | 历史性参考；当前真相以 `backend/models/__init__.py` 为准 | **半自动** — 从 SQLAlchemy 模型提取，手动补充业务说明 |
| 开发快速启动 | `docs/dev-guide.md` | 环境搭建、前后端启动、常用命令 | **手写** — 变更少，偶尔更新 |

#### P1 — 短期补充（提升协作效率）

| 文档 | 路径 | 目的 | 维护策略 |
|------|------|------|----------|
| README.md | `README.md`（项目根） | 项目简介、技术栈、快速启动链接 | **手写** — 项目入口，保持简洁 |
| ADR 补录 | `docs/adr/ADR-001~006.md` 等 | 补录早期关键决策 | **手写** — 回忆补录，之后每次决策时写 |
| CHANGELOG | `CHANGELOG.md` | 版本变更记录 | **半自动** — 基于 commit 生成草稿，手动整理 |
| 架构文档清理 | 处理旧架构文档与 stale 标记 | 消除旧文档伪装成当前事实的问题 | 一次性/按需操作 |

#### P2 — 中期完善（支撑规模化）

| 文档 | 路径 | 目的 | 维护策略 |
|------|------|------|----------|
| 测试策略 | `docs/testing-strategy.md` | 测试分层、覆盖率目标、如何运行测试 | **手写** — QA Lead 负责 |
| 部署指南 | `docs/deployment-guide.md` | Electron 打包、分发、环境配置 | **手写** — DevOps 负责 |
| 前端架构补充 | `docs/frontend-architecture.md` | 组件树、状态管理、路由、hooks 设计 | **手写** — 当前 baseline 文档只做总入口，前端细节仍可后续展开 |

---

## 三、各文档详细说明

### 3.1 API 参考 (`docs/api-reference.md`)

**为什么最优先**：这是被查找频率最高的文档。每次前后端对接、调试、写测试都需要。

**生成方式**：

FastAPI 已经内置 OpenAPI schema（`/openapi.json`），且项目已配置 hey-api 自动生成前端 SDK（`frontend/openapi.config.ts`）。API 参考文档可以：

1. 直接使用 FastAPI 内置的 `/docs`（Swagger UI）和 `/redoc` 作为在线参考
2. 用脚本从 `/openapi.json` 生成 Markdown 版本，方便离线查阅和 Agent 读取

```python
# 建议：添加一个生成脚本
# scripts/gen-api-docs.py
# 从 openapi.json 提取端点信息，输出 Markdown
```

**内容结构**：

```markdown
## 账号管理 /api/accounts

### POST /api/accounts
创建得物账号
- 请求体: AccountCreate { account_id, account_name, tags?, notes? }
- 响应: AccountResponse
- 错误: 409 账号已存在

### GET /api/accounts/{id}/health-check
...
```

**维护成本**：低。OpenAPI schema 随代码自动更新，文档生成是一次性脚本。

### 3.2 数据模型字典 (`docs/data-model.md`)

**为什么优先**：当前 `system-architecture.md` 的 ER 部分只有表名和关键字段，缺少完整字段列表、约束、索引、加密标记。

**内容结构**：

```markdown
## Account 表

得物平台账号，核心实体。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 内部 ID |
| account_id | String | unique, not null | 得物账号 ID |
| account_name | String | not null | 账号名称 |
| cookie | Text | nullable | 加密存储 (AES-256-GCM) |
| storage_state | Text | nullable | 加密存储 |
| phone_encrypted | String | nullable | 加密存储，脱敏显示 138****8000 |
| status | String | default="disconnected" | disconnected/connected/session_expired |
| ...

### 关系
- Account 1:N Task
- Account 1:N PublishLog

### 加密字段
cookie, storage_state, phone_encrypted 使用 utils/crypto.py 的 AES-256-GCM 加密。
```

**生成方式**：可写脚本从 SQLAlchemy 模型提取字段定义，手动补充业务说明。

### 3.3 开发快速启动 (`docs/dev-guide.md`)

**为什么优先**：`backend/CLAUDE.md` 只覆盖后端，前端启动完全没有文档。新人（或 Agent）无法快速上手。

**内容结构**：

```markdown
# 开发指南

## 环境要求
- Node.js 18+, Python 3.11+, Git

## 快速启动

### 后端
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

### 前端
cd frontend
npm install
npm run dev

### Electron（完整桌面应用）
cd frontend
npm run electron:dev

## 常用命令
- 生成前端 API SDK: cd frontend && npx openapi-ts
- 数据库位置: backend/data/dewugojin.db
- 日志位置: backend/logs/

## 添加新功能的流程
1. 后端：models → schemas → services → api
2. 前端：重新生成 SDK → hooks → pages
3. 参考 .claude/docs/usage-guide.md 的 Agent 协作流程
```

### 3.4 ADR 补录建议

当前只有 ADR-007、008、015，编号跳跃说明中间的决策没有记录。建议补录以下关键决策：

| ADR | 主题 | 重要性 |
|-----|------|--------|
| ADR-001 | 选择 Electron + FastAPI 架构（为什么不用纯 Web） | 高 — 最基础的架构决策 |
| ADR-002 | 选择 Patchright 替代 Playwright（反检测需求） | 高 — 经常被问到 |
| ADR-003 | 选择 SQLite 而非 PostgreSQL（本地桌面应用） | 中 |
| ADR-004 | Cookie 加密方案（AES-256-GCM + PBKDF2HMAC） | 高 — 安全核心 |
| ADR-005 | 选择 React Query 替代 Zustand 做服务端状态 | 中 — 前端状态管理 |
| ADR-006 | SSE 替代 WebSocket 做实时推送 | 中 |

格式沿用现有 ADR 模板。不需要完美回忆，记录"当时的选项和选择理由"即可。

### 3.5 CHANGELOG

**格式**：采用 [Keep a Changelog](https://keepachangelog.com/) 格式。

```markdown
# Changelog

## [Unreleased]

### Added
- 批量健康检查 + 实时日志面板
- 产品用户手册

### Fixed
- 登录/预览状态管理问题
- 浏览器 storage_state 传递方式
```

**维护方式**：每次提交有用户可感知的变更时更新。可以用 `git log --oneline` 辅助回顾，但不要直接复制 commit message — CHANGELOG 面向用户，commit 面向开发者。

---

## 四、自动化 vs 手写矩阵

| 文档 | 方式 | 工具/方法 | 频率 |
|------|------|-----------|------|
| API 参考 | 自动生成 | FastAPI `/openapi.json` → Markdown 脚本 | 每次 API 变更后 |
| 数据模型字典 | 半自动 | SQLAlchemy 模型提取 + 手动业务说明 | 模型变更后 |
| CHANGELOG | 半自动 | git log 辅助 + 手动整理 | 每次发布前 |
| 前端 SDK 类型 | 自动生成 | hey-api（已配置） | 每次 API 变更后 |
| 开发指南 | 手写 | — | 环境/流程变更时 |
| ADR | 手写 | — | 每次架构决策时 |
| 测试策略 | 手写 | — | 测试框架确定后 |
| 部署指南 | 手写 | — | 打包流程确定后 |

---

## 五、实施路线

### 第一周（P0）

1. 编写 `docs/dev-guide.md` — 开发快速启动（手写，约 1 小时）
2. 编写 API 参考生成脚本 + 首次生成 `docs/api-reference.md`
3. 编写 `docs/data-model.md` — 从现有模型提取

### 第二周（P1）

4. 创建 `README.md` — 项目入口
5. 补录 ADR-001 ~ ADR-006
6. 创建 `CHANGELOG.md` — 从 git history 回溯
7. 删除 `docs/architecture.md`（旧版本，内容已被 `system-architecture.md` 覆盖）

### 第三周+（P2）

8. `docs/testing-strategy.md` — 等测试框架确定后
9. `docs/deployment-guide.md` — 等打包流程确定后
10. `docs/frontend-architecture.md` — 前端架构细化

---

## 六、维护原则

1. **文档跟代码走**：API 变了就更新 API 参考，模型变了就更新数据模型字典。不要攒着。
2. **单一事实来源**：每个信息只在一个地方维护。Epic 7 后当前架构总入口应为 `docs/current-architecture-baseline.md`，当前运行事实清单应为 `docs/current-runtime-truth.md`，`system-architecture.md` 只保留为历史长文参考。
3. **删除过时文档**：过时文档比没有文档更危险。`docs/architecture.md` 应该删除。
4. **自动化优先**：能从代码生成的就不手写。FastAPI 的 OpenAPI schema 是天然的 API 文档源。
5. **实用主义**：不追求文档完美，追求"能在 30 秒内找到答案"。

---

## 七、与 Agent 框架的关系

当前 `.claude/` 下的文档体系（agents、rules、skills、docs）服务于 Agent 协作，做得很好。本策略补充的是**项目本身的技术文档**，两者互补：

| 文档体系 | 服务对象 | 位置 |
|----------|----------|------|
| Agent 框架文档 | Agent 协作流程 | `.claude/docs/`, `.claude/rules/` |
| 项目技术文档 | 开发者（人和 Agent 都用） | `docs/`, `README.md`, `CHANGELOG.md` |

Agent 在执行任务时，会同时参考两套文档：框架文档告诉它"怎么协作"，技术文档告诉它"系统长什么样"。
