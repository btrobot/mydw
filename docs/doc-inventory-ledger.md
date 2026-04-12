# Document Inventory Ledger

> 目的：把当前仓库里的主要文档/资料簇做一次显式分类，供后续目录迁移、归档和删除决策使用。  
> 这是一份 **整理台账**，不是新的 authoritative architecture 文档。

## 分类规则

| Category | Meaning |
|---|---|
| `current` | 当前默认阅读入口或 current/canonical truth 文档 |
| `working` | 仍有工程参考价值，但不是唯一真相 |
| `historical` | 历史/归档/考古参考资料 |
| `runtime` | 本地运行时、agent、session、导出或生成产物，不属于项目主文档入口 |

## Cluster ledger

| Cluster | What it contains today | Category | Default disposition | Notes |
|---|---|---|---|---|
| `README.md` + `docs/current-architecture-baseline.md` + `docs/current-runtime-truth.md` + `docs/epic-7-doc-authority-matrix.md` + `docs/dev-guide.md` | 当前项目入口、当前架构、当前运行事实、文档权威边界、开发指南 | `current` | `keep` | 当前主阅读路径 |
| `docs/` 其余专题文档（如 generation/settings/topic/task/phase docs） | 迁移说明、治理文档、专题设计、阶段性工程说明 | `working` | `keep` then reclassify/move selectively | 需要后续拆到 `guides/` / `operations/` / `archive/` |
| `docs/refactor-roadmap.md`, `docs/refactor-issue-breakdown.md`, `docs/refactor-gap-list.md` | 历史重构计划与 gap-tracking 文档，仍被部分 `.omx` 历史 planning context 引用 | `historical` | `keep in place for now` | 先加 boundary banner，后续在 runtime-context 政策明确后再决定是否迁移 |
| `docs/system-architecture.md`, `docs/api-reference.md`, `docs/data-model.md`, `docs/archive/planning/` 下的旧 sprint / breakdown 文档，以及 `docs/archive/analysis/` 下的旧分析/设计文档 | 高可见度旧文档与历史计划/分析资料 | `historical` | `archive` | 已开始把旧计划文档与一批无当前引用的旧分析文档移入 archive 子目录 |
| `design/` | 设计草图、栈说明、历史设计材料 | `historical` with a shrinking active subset | `move` / `archive` later | 已把明显的技能说明、旧栈说明、旧登录架构和历史探索材料移到 `design/archive/`，剩余文件再逐个判断 |
| `dev-docs/` | 开发探索/登录自动化相关笔记 | `working` → mixed with `historical` | `move` / `archive` later | 已把明显历史探索材料移到 `dev-docs/archive/`，其余文件待继续分层 |
| `private-docs/` | 私有/内部分析与评审材料 | `historical` | `archive` | 已移入 `docs/archive/private/`，不再占据根层主路径 |
| `backend/docs/` | backend 局部设计/状态文档 | `historical` | `archive` | 首批旧 backend 设计/审批稿已移入 `backend/docs/archive/`；若后续新增 docs，应明确其是否仍属于 active engineering docs |
| `plans/` | 根层零散计划文档 | `historical` | `archive` | 首个根层计划文档已移入 `docs/archive/planning/`，其余同类文件应继续离开根目录 |
| `docs/archive/exports/` | 导出型项目说明/快照/分析报告 | `historical` or `reference-export` | `archive` | 原 `.codex-export/` 已迁入 docs archive，更符合其参考快照属性 |
| `production/session-*` | 生产/会话状态与拆解产物 | `runtime` | `keep` with explicit boundary | 不属于项目主文档入口 |
| `production/task-breakdown/` | task breakdown 示例/历史产物 | `historical` or `example` | `archive` | 已开始移到 `docs/archive/examples/`，避免继续停留在 runtime-like 根路径下 |
| `.codex/` | Codex prompts, skills, sessions, logs, local state | `runtime` | `keep` or revisit policy later | agent/runtime 资产，不是产品文档 |
| `.omx/` | OMX state, plans, logs, context snapshots, notepad | `runtime` | `keep` or revisit policy later | orchestration/runtime 资产 |

Runtime/local boundary policy:

- `docs/runtime-local-artifact-policy.md`

## Immediate decisions from this ledger

### Keep as current entrypoints
- `README.md`
- `docs/README.md`
- `docs/current-architecture-baseline.md`
- `docs/current-runtime-truth.md`
- `docs/epic-7-doc-authority-matrix.md`
- `docs/dev-guide.md`

### Keep, but do not treat as default truth
- active governance and engineering docs under `docs/`
- `docs/adr/`
- selected material in `design/`, `dev-docs/`, `backend/docs/`, `private-docs/`

### Archive candidates
- old architecture/reference docs already marked stale
- old sprint / refactor / breakdown / roadmap style documents once references are updated
- clearly superseded design notes

### First archive batch completed in PR-3
- `task-breakdown-phase1.md`
- `task-breakdown-phase3.md`
- `task-breakdown-phase4.md`
- `sprint-plan-phase1.md`
- `sprint-plan-phase3.md`
- `sprint-plan-phase4.md`
- `sprint-plan-sprint5.md`
- `sprint-6-plan.md`
- `sprint-7-plan.md`
- `sprint-8-plan.md`

Current location:

- `docs/archive/planning/`

### Second archive batch completed in PR-4
- `refactor-list.md`
- `task-management-analysis.md`
- `task-management-er-design.md`
- `task-management-operations.md`

Current location:

- `docs/archive/analysis/`

### Runtime-boundary candidates
- `.codex/`
- `.omx/`
- `production/session-*`

### Third archive batch completed in PR-6
- `design/Claude Code Hooks.md`
- `design/sprint-intro.md`
- `design/task-breakdown-intro.md`
- `dev-docs/dewu-login-automation.md`
- `dev-docs/login-dewu.md`
- `dev-docs/thinking-x.md`
- `dev-docs/req/04-02.md`

Current locations:

- `design/archive/`
- `dev-docs/archive/`

### Fourth archive batch completed in PR-7
- `backend/docs/account-management-design.md`
- `backend/docs/api-contract-connect.md`
- `backend/docs/batch-health-check-design.md`
- `backend/docs/state-machine.md`

Current location:

- `backend/docs/archive/`

### Fifth archive batch completed in PR-8
- `design/backend-stack.md`
- `design/frontend-stack.md`
- `design/login-arch.md`

Current location:

- `design/archive/`

### Sixth archive batch completed in current cleanup execution
- `plans/cosmic-baking-micali.md`
- `production/task-breakdown/task-management-impl.md`
- `production/task-breakdown/task-orchestration.md`

Current locations:

- `docs/archive/planning/`
- `docs/archive/examples/`

### Seventh archive batch completed in current cleanup execution
- `private-docs/arch.md`
- `private-docs/multi-agents-review.md`

Current location:

- `docs/archive/private/`

### Eighth archive batch completed in current cleanup execution
- `.codex-export/dewu-architecture-and-dataflow.md`
- `.codex-export/dewu-architecture-risks-and-refactor-recommendations.md`
- `.codex-export/dewu-database-models-and-field-responsibilities.md`
- `.codex-export/dewu-frontend-backend-interface-mapping.md`
- `.codex-export/dewu-frontend-backend-page-api-mapping.md`
- `.codex-export/dewu-page-api-mapping.md`
- `.codex-export/dewu-project-overview.md`
- `.codex-export/dewu-task-end-to-end-sequence.md`
- `.codex-export/dewu-task-lifecycle-sequence.md`

Current location:

- `docs/archive/exports/`

## Follow-up actions supported by this ledger

1. Create a future `docs/archive/` destination and migrate high-noise historical docs there.
2. Decide whether `design/`, `dev-docs/`, `private-docs/`, and `backend/docs/` become:
   - `docs/` subtrees,
   - `internal/`,
   - or archive-only areas.
3. Write one explicit runtime/local artifact policy so `.codex/`, `.omx/`, and remaining session paths stop competing with human-authored docs.
4. Only delete documents after they are:
   - classified,
   - confirmed unreferenced or fully superseded,
   - and safe to remove.
