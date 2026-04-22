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
| `README.md` + `docs/current/architecture.md` + `docs/current/runtime-truth.md` + `docs/governance/authority-matrix.md` + `docs/guides/dev-guide.md` | 当前项目入口、当前架构、当前运行事实、文档权威边界、开发指南 | `current` | `keep` | 当前主阅读路径 |
| `docs/current/next-phase-kickoff.md` + `docs/governance/next-phase-prd.md` + `docs/governance/next-phase-test-spec.md` + `docs/governance/next-phase-execution-breakdown.md` | 下一阶段启动入口、范围定义、验证计划、执行分解 | `working` with high entry value | `keep` | 下一阶段开发起跑线，不属于历史归档 |
| `docs/` 其余专题文档（如 generation/settings/topic/task/phase docs） | 迁移说明、治理文档、专题设计、阶段性工程说明 | `working` | `keep` then reclassify/move selectively | 需要后续拆到 `guides/` / `operations/` / `archive/` |
| `docs/archive/history/refactor-roadmap.md`, `docs/archive/history/refactor-issue-breakdown.md`, `docs/archive/history/refactor-gap-list.md` | 历史重构计划与 gap-tracking 文档，仍被部分 `.omx` 历史 planning context 引用 | `historical` | `archive` | 已迁入 `docs/archive/history/`，按历史规划参考理解 |
| `docs/archive/reference/system-architecture.md`, `docs/archive/reference/api-reference.md`, `docs/archive/reference/data-model.md`, `docs/archive/planning/` 下的旧 sprint / breakdown 文档，以及 `docs/archive/analysis/` 下的旧分析/设计文档 | 高可见度旧文档与历史计划/分析资料 | `historical` | `archive` | 已迁入 archive 子目录，避免与 current docs 竞争 |
| `docs/archive/README.md` + 各二级目录 `README.md` | archive 总入口与二级分类索引 | `historical` with navigation value | `keep` | 负责说明 archive 怎么读、不同历史材料怎么分层，不承担 current truth 角色 |
| `design/` | 设计草图、栈说明、历史设计材料 | `historical` with a shrinking active subset | `move` / `archive` later | 已把明显的技能说明、旧栈说明、旧登录架构和历史探索材料移到 `design/archive/`，剩余文件再逐个判断 |
| `docs/archive/dev-docs/` | 历史开发探索 / 登录自动化笔记 | `historical` | `archive` | 原 `dev-docs/` 已完全并入 `docs/archive/dev-docs/` |
| `private-docs/` | 私有/内部分析与评审材料 | `historical` | `archive` | 已移入 `docs/archive/private/`，不再占据根层主路径 |
| `docs/archive/backend-docs/` | backend 局部设计/状态文档 | `historical` | `archive` | 原 `backend/docs/` 已完全并入 `docs/archive/backend-docs/` |
| `plans/` | 根层零散计划文档 | `historical` | `archive` | 首个根层计划文档已移入 `docs/archive/planning/`，其余同类文件应继续离开根目录 |
| `docs/archive/exports/` | 导出型项目说明/快照/分析报告 | `historical` or `reference-export` | `archive` | 原 `.codex-export/` 已迁入 docs archive，更符合其参考快照属性 |
| `.codex/` | Codex prompts, skills, sessions, logs, local state | `runtime` | `keep` or revisit policy later | agent/runtime 资产，不是产品文档 |
| `.omx/` | OMX state, active plans, archived plans, logs, context snapshots, notepad | `runtime` | keep active planning assets; archive absorbed plans under `.omx/plans/archive/` | orchestration/runtime 资产；分流规则见 `docs/governance/policies/omx-plan-retention.md` |
| `.omc/` | OMC / Claude runtime state, sessions, mission memory | `runtime` | `ignore local state, clear tracked exceptions` | 会话/调度状态，不属于项目主文档入口 |
| local runtime output directories | 本地会话/日志/状态输出目录（仓库不保留 `production/`） | `runtime` | `ignore` | 本地运行输出，不属于 repo surface |

Runtime/local boundary policy:

- `docs/governance/policies/runtime-local-artifact-policy.md`
- `docs/governance/policies/omx-plan-retention.md`
- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/next-phase-backlog.md`

## Immediate decisions from this ledger

### Keep as current entrypoints
- `README.md`
- `docs/README.md`
- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/governance/authority-matrix.md`
- `docs/guides/dev-guide.md`
- `docs/current/next-phase-kickoff.md`

### Keep, but do not treat as default truth
- active governance and engineering docs under `docs/`
- `docs/adr/`
- `docs/archive/dev-docs/`
- `docs/archive/backend-docs/`
- `private-docs/`

### Archive candidates
- old architecture/reference docs already marked stale
- old sprint / refactor / breakdown / roadmap style documents once references are updated
- clearly superseded design notes

### Archive index baseline
- `docs/archive/README.md`
- `docs/archive/reference/README.md`
- `docs/archive/planning/README.md`
- `docs/archive/analysis/README.md`
- `docs/archive/history/README.md`
- `docs/archive/dev-docs/README.md`
- `docs/archive/backend-docs/README.md`
- `docs/archive/examples/README.md`
- `docs/archive/exports/README.md`
- `docs/archive/private/README.md`

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
- `.omc/`
- local runtime output directories (the repo no longer keeps `production/`)

### Third archive batch completed in PR-6
- `design/Claude Code Hooks.md`
- `design/sprint-intro.md`
- `design/task-breakdown-intro.md`
- `docs/archive/dev-docs/dewu-login-automation.md`
- `docs/archive/dev-docs/login-dewu.md`
- `docs/archive/dev-docs/thinking-x.md`
- `docs/archive/dev-docs/req-04-02.md`

Current locations:

- `design/archive/`
- `docs/archive/dev-docs/`

### Fourth archive batch completed in PR-7
- `docs/archive/backend-docs/account-management-design.md`
- `docs/archive/backend-docs/api-contract-connect.md`
- `docs/archive/backend-docs/batch-health-check-design.md`
- `docs/archive/backend-docs/state-machine.md`

Current location:

- `docs/archive/backend-docs/`

### Fifth archive batch completed in PR-8
- `design/backend-stack.md`
- `design/frontend-stack.md`
- `design/login-arch.md`
- `x-01.md`（已统一收口到 `design/archive/`）

Current location:

- `design/archive/`

### Sixth archive batch completed in current cleanup execution
- `plans/cosmic-baking-micali.md`
- `docs/archive/examples/task-management-impl.md`
- `docs/archive/examples/task-orchestration.md`

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

## Ninth archive batch completed in current cleanup execution

- `.omx/plans/archive/prd-login-bs-alignment-pr-plan.md`
- `.omx/plans/archive/test-spec-login-bs-alignment-pr-plan.md`
- `.omx/plans/archive/prd-task-management-page-closeout.md`
- `.omx/plans/archive/test-spec-task-management-page-closeout.md`
- `.omx/plans/archive/prd-work-driven-creative-flow-refactor.md`
- `.omx/plans/archive/test-spec-work-driven-creative-flow-refactor.md`

Current location:

- `.omx/plans/archive/`

## Follow-up actions supported by this ledger

1. Maintain `docs/archive/README.md` plus second-level archive indexes whenever archive categories change.
2. Decide whether `design/`, `docs/archive/dev-docs/`, `private-docs/`, and `docs/archive/backend-docs/` become:
   - `docs/` subtrees,
   - `internal/`,
   - or archive-only areas.
3. Write one explicit runtime/local artifact policy so `.codex/`, `.omx/`, and remaining session paths stop competing with human-authored docs.
4. Only delete documents after they are:
   - classified,
   - confirmed unreferenced or fully superseded,
   - and safe to remove.

## Phase E compression artifacts

- `docs/governance/inventory/root-doc-triage.md` — 根层未分类 docs 的四分法去向表
- `docs/governance/next-phase-backlog.md` — 从 closeout / audit / issue docs 压缩出的下一阶段 backlog

## Phase F launch artifacts

- `docs/current/next-phase-kickoff.md` — 下一阶段单入口启动包
- `docs/governance/next-phase-prd.md` — 下一阶段范围定义
- `docs/governance/next-phase-test-spec.md` — 下一阶段验证规格
- `docs/governance/next-phase-execution-breakdown.md` — 下一阶段 PR sequence 分解
- `docs/governance/next-phase-pr1-workbench-manageability-plan.md` — PR-1「Workbench 可管理性收口」的聚焦规划与 slice 建议
- `docs/governance/next-phase-pr2-business-diagnostics-layering-plan.md` — PR-2「业务层 / 诊断层分层」的聚焦规划与 slice 建议
- `docs/governance/next-phase-pr3-copy-and-state-unification-plan.md` — PR-3「文案与四态统一」的聚焦规划与 slice 建议
- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md` — PR-4「回归补强与阶段收口」的聚焦规划与 stage closeout gate 定义

## Formal closeout artifact

- `docs/governance/inventory/post-mvp-doc-governance-closeout.md` — 本轮文档治理收口正式件，汇总入口收口、archive 分类、post-MVP 治理链与后续维护规则

## Current-project closeout execution artifacts

- `docs/governance/inventory/current-project-mvp-closeout-checklist.md` — 当前项目 MVP 收口逐项检查清单
- `docs/governance/inventory/current-project-mvp-closeout-execution.md` — 按清单执行后的项目级收口记录与残留项说明
- `docs/governance/inventory/current-project-phase-transition-decision.md` — 按阶段切换清单做出的项目级放行决议，确认可以进入下一阶段主线
- `docs/governance/inventory/pr1-workbench-manageability-closeout.md` — PR-1「Workbench 可管理性收口」的正式收口件，汇总最终交付、当前 current truth、验证结果与后续交接
- `docs/governance/inventory/pr2-business-diagnostics-layering-closeout.md` — PR-2「业务层 / 诊断层分层」的正式收口件，汇总默认业务面与 diagnostics surface 分层后的 current truth
- `docs/governance/inventory/pr3-copy-and-state-unification-closeout.md` — PR-3「文案与四态统一」的正式收口件，汇总 auth/login、creative 与 Dashboard 的 CTA / 文案 / 四态 current truth
- `docs/governance/inventory/pr3-slice-b-state-feedback-closeout.md` — PR-3 / Slice B 的正式收口件，汇总四态统一、失败语义显式化与 targeted verification 证据

## Tenth archive batch completed in PR-1 closeout

- `.omx/plans/archive/prd-pr1-workbench-manageability.md`
- `.omx/plans/archive/test-spec-pr1-workbench-manageability.md`
- `.omx/plans/archive/slice-plan-pr1-workbench-manageability.md`

Current location:

- `.omx/plans/archive/`

## Eleventh archive batch completed in PR-3 closeout

- `.omx/plans/archive/prd-pr3-copy-and-state-unification.md`
- `.omx/plans/archive/test-spec-pr3-copy-and-state-unification.md`
- `.omx/plans/archive/slice-plan-pr3-copy-and-state-unification.md`

Current location:

- `.omx/plans/archive/`
