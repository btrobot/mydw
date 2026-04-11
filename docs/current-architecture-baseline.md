# 当前架构基线（Epic 7 / PR1）

> 目的：给新人和维护者提供一份**当前系统入口文档**。  
> 它回答“系统现在长什么样、哪些文档可信、应该从哪里开始读”，而不是替代更细粒度的事实清单。

## 1. 这份文档负责什么

这份文档是当前 repo 的**架构总入口**，负责：

- 给出当前系统的高层结构
- 指向当前 authoritative 文档
- 汇总 Phase 1-6 已收口的核心真相
- 提供推荐阅读路径

它**不**负责逐条记录所有运行时事实；那是 `docs/current-runtime-truth.md` 的职责。

## 2. 当前系统轮廓

当前系统仍是一个 **Electron + React + FastAPI + SQLite** 的桌面应用：

- **Electron Main**：窗口、托盘、后端进程启动、IPC
- **Renderer (React)**：前端页面、hooks、OpenAPI client/服务调用
- **FastAPI Backend**：API、services、models、migrations
- **SQLite**：本地持久化

高层职责边界：

1. **调度配置真相**：`ScheduleConfig`
2. **发布运行状态真相**：`TaskScheduler` runtime state
3. **任务 authoritative 语义**：collection-based task resource model
4. **系统设置真相**：startup-env / runtime-config / read-only 已在 Phase 5 收口
5. **topic relation 真相**：Phase 6 后已切到 relation-first canonical source

## 3. 当前 authoritative 文档入口

- **当前架构总入口**：`docs/current-architecture-baseline.md`
- **当前运行事实清单**：`docs/current-runtime-truth.md`
- **轻量入口 / alias**：`docs/runtime-truth.md`
- **Architecture decisions**：`docs/adr/`

## 4. Phase 1-6 已沉淀的关键真相

### 调度配置
- canonical source：`ScheduleConfig`
- 兼容入口：`/api/publish/config`
- 当前事实细节：见 `docs/current-runtime-truth.md`

### 发布状态
- canonical source：scheduler runtime state
- `/api/publish/status` 已不再自创平行状态真相

### 任务语义
- authoritative model：`video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids`
- legacy 单资源 FK 不再是主语义来源
- 详见：`docs/task-semantics.md`

### 系统设置
- 已收口 startup-env / runtime-config / read-only / unsupported setting policy
- 详见：
  - `docs/settings-truth-matrix.md`
  - `docs/system-settings-operational-notes.md`

### Topic relation
- canonical source 已收口到 relation tables
- profile-level default topics 仍是 task assembly 唯一 auto-merged default source
- 详见：
  - `docs/phase-6-topic-compat-matrix.md`
  - `docs/phase-6-topic-relation-cutover.md`
  - `docs/adr/ADR-016-topic-canonical-semantics-phase-6.md`

### 剩余 JSON 字段结论
- 已有 `keep-json / normalize-later / delete-ready-later / compat-readonly` 的最终决策
- 详见：
  - `docs/phase-6-field-classification.md`
  - `docs/phase-6-migration-ledger.md`

## 5. 推荐阅读路径

### 30 秒了解项目
1. `README.md`
2. `docs/current-architecture-baseline.md`

### 想知道“当前真实行为”
1. `docs/current-runtime-truth.md`
2. 对应专题文档：
   - `docs/task-semantics.md`
   - `docs/settings-truth-matrix.md`
   - `docs/phase-6-*.md`

### 想知道“为什么这样设计”
1. `docs/adr/README.md`
2. 相关 ADR

## 6. 与旧文档的关系

`docs/system-architecture.md` 当前仍存在，但在 Epic 7 / PR1 后：

- **不是默认阅读入口**
- 后续会在 Epic 7 / PR2 中被明确处理：
  - rewrite 成当前事实
  - 或标记为 stale / archival

在 PR2 完成前，阅读该文件时应以本基线文档和 `current-runtime-truth` 为准。

PR2 完成后，以下文档也被明确降级为 archival / stale reference：

- `docs/api-reference.md`
- `docs/data-model.md`

它们仍可提供历史性上下文，但当前 authoritative source 已切换到：

- API：`/docs` / `/openapi.json`
- 数据模型：`backend/models/__init__.py`

## 7. 配套文档

- `docs/epic-7-doc-authority-matrix.md`
- `docs/epic-7-docs-parity-checklist.md`
