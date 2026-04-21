# 文档导航 / Docs Index

> 目的：给维护者和新读者一个稳定的文档入口，先回答“先读什么”，再回答“历史资料和运行时产物放在哪里理解”。

## 先看哪些文档

推荐阅读顺序：

1. `README.md` — 项目入口、快速开始、当前推荐阅读路径
2. `docs/README.md` — 文档导航首页（本文件）
3. `docs/current/architecture.md` — 当前架构总入口
4. `docs/current/runtime-truth.md` — 当前运行事实 / canonical fact inventory
5. `docs/governance/authority-matrix.md` — 文档职责边界
6. `docs/guides/dev-guide.md` — 开发环境与启动流程
7. `docs/governance/verification-baseline.md` — 最小可信回归基线
8. `docs/current/next-phase-kickoff.md` — 下一阶段启动入口 / 启动包总入口
9. `docs/governance/inventory-ledger.md` — 当前文档/资料簇分类台账
10. `docs/governance/runtime-local-artifact-policy.md` — 运行时 / 本地 agent 资产边界说明
11. `docs/governance/omx-plan-retention.md` — `.omx/plans` 活跃/归档分类规则
12. `docs/governance/post-mvp-development-model.md` — MVP 完成后如何做收口、选主线、再启动下一阶段
13. `docs/governance/phase-transition-checklist.md` — 每次阶段切换前后要检查什么，避免未收口就启动下一阶段

## Current / canonical docs

这些文档回答“现在这个项目到底是什么样”：

- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/governance/authority-matrix.md`
- `docs/governance/verification-baseline.md`
- `docs/current/next-phase-kickoff.md`
- `docs/guides/dev-guide.md`
- `docs/governance/generated-artifact-policy.md`
- `docs/guides/openapi-generation-workflow.md`
- `docs/governance/post-mvp-development-model.md`
- `docs/governance/phase-transition-checklist.md`

## Working engineering docs

这些文档仍然有工程参考价值，但不应自动被当作唯一真相：

- sprint / phase / migration / refactor 相关文档
- `docs/domains/creative/progressive-rebuild-final-summary.md`（Creative 渐进式重建 A~D 阶段收口总结）
- `docs/frontend-ui-issues-and-improvements.md`（当前前端界面问题分析与改进方向）
- `docs/governance/root-doc-triage.md`（根层未分类文档去向收口）
- `docs/governance/post-mvp-development-model.md`（MVP 后开发治理模型）
- `docs/governance/phase-transition-checklist.md`（阶段切换执行清单）
- `docs/governance/next-phase-backlog.md`（压缩后的 open issues / next-phase backlog）
- `docs/governance/next-phase-prd.md` / `docs/governance/next-phase-test-spec.md` / `docs/governance/next-phase-execution-breakdown.md`（下一阶段启动包的范围/验证/执行分解，需与 kickoff 一起使用）
- `docs/governance/omx-plan-retention.md`（`.omx/plans` 活跃计划与 archive 的分流规则）
- 专题设计说明（如 settings、topic、task semantics、generation governance）
- `docs/adr/` 中的决策记录
- `docs/domains/auth/README.md`（远程认证 / 本地授权门禁冻结文档入口；Step 0 artifacts）

## Historical / archival references

以下高可见度文档已经被降级为 historical / stale / archival reference，应在 current 文档之后阅读：

- `docs/archive/reference/system-architecture.md`
- `docs/archive/reference/api-reference.md`
- `docs/archive/reference/data-model.md`
- `docs/archive/planning/` 下的早期 task-breakdown / sprint-plan 类文档
- `docs/archive/history/refactor-roadmap.md` / `docs/archive/history/refactor-issue-breakdown.md` / `docs/archive/history/refactor-gap-list.md`（历史规划参考）
- 其他仍在 `docs/` 根目录中的旧 roadmap / planning / breakdown 文档

更完整的 authority 说明见：

- `docs/governance/authority-matrix.md`
- `docs/epic-7-stale-doc-inventory.md`
- `docs/governance/inventory-ledger.md`
- `docs/governance/runtime-local-artifact-policy.md`

当前第一批已归档的旧计划文档位于：

- `docs/archive/planning/`

当前第二批已归档的旧分析/设计文档位于：

- `docs/archive/analysis/`

当前第三批已归档的 design / dev-docs 历史探索材料位于：

- `design/archive/`
- `docs/archive/dev-docs/`

当前第四批已归档的 backend 局部历史设计文档位于：

- `docs/archive/backend-docs/`

当前第五批已归档的 design 栈说明 / 登录架构旧稿位于：

- `design/archive/`

当前第六批已归档的根层计划与 task-breakdown 示例位于：

- `docs/archive/planning/`
- `docs/archive/examples/`

当前第七批已归档的 private-docs 材料位于：

- `docs/archive/private/`

当前第八批已归档的导出型参考快照位于：

- `docs/archive/exports/`

## Runtime / local artifact boundary

下面这些路径**不是项目主文档入口**，不要把它们当作“先读什么”的答案：

- `.codex/` — Codex 本地 prompts / skills / sessions / state
- `.omx/` — OMX runtime state、plans、archive、logs、notepad、session artifacts
- `.omc/` — OMC/Claude runtime state、sessions、mission memory
- 本地 session / runtime 输出目录（仓库中已不再保留 `production/`）

它们可能对 agent/runtime 运维有用，但不属于产品/架构主阅读路径。

更完整的边界规则见：

- `docs/governance/runtime-local-artifact-policy.md`
- `docs/governance/omx-plan-retention.md`

## 当前整理策略

当前阶段优先做：

1. 统一入口与阅读路径
2. 区分 current / working / historical / runtime
3. 之后再逐步迁移目录或归档文档

所以在正式归档目录落地前，读者应先以本页和 authority matrix 为导航，而不是直接从 `docs/` 文件列表中盲读。
