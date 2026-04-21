# OMX Planning Artifact Retention / `.omx/plans` 归档规则

> Version: 1.0.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把 `.omx/plans` 做一次显式分类，区分哪些仍然是**活跃规划资产**，哪些已经被 `docs/` 正式文档吸收，应下沉到 `.omx/plans/archive/`。

## 1. 这份文档解决什么问题

`.omx/plans` 属于 **runtime / working planning artifacts**，不是项目主文档入口。  
但随着 closeout、阶段总结和下一阶段启动包逐步补齐，这个目录里已经混入了三类不同角色的文件：

1. **仍在驱动开发的活跃计划**
2. **已经被正式文档吸收的历史计划**
3. **尚未确认是否还能删除/归档的中间 planning artifacts**

如果不分类，目录会越来越像“什么都往里堆”的缓冲区，后续开发会继续读不清主次。

## 2. 归档原则

### 2.1 保留在 `.omx/plans/` 的条件

满足任一条件就继续保留在 `.omx/plans/`：

- 仍被 README、handoff pack、remote 运行文档或自动化测试当作当前 planning baseline 引用
- 仍在为下一阶段或当前主线提供执行边界
- 还没有被 `docs/current/*`、`docs/governance/*`、`docs/domains/*` 的正式文档吸收

### 2.2 移到 `.omx/plans/archive/` 的条件

满足以下条件即可进入 `.omx/plans/archive/`：

- 规划内容已经被 `docs/` 中的正式文档总结/吸收
- 当前不再作为 active planning baseline 被 README / tests / handoff docs 依赖
- 保留它的主要原因只剩“历史追溯”或“审计证据”

### 2.3 当前不直接删除的原因

本轮优先做 **分类 + 归档**，不激进删除：

- `.omx/` 是 runtime/local artifact 区，不是主文档树
- 计划文件仍可能对历史审计、提交回溯、阶段总结有价值
- 先把“活跃 vs 历史”分开，比立即删除更稳妥

## 3. 当前分类结果

## 3.1 Keep active in `.omx/plans/`

| 文件组 | 处理 | 原因 |
| --- | --- | --- |
| `prd-remote-full-system.md` / `test-spec-remote-full-system.md` / `prd-remote-full-system-a0-pr-plan.md` / `prd-remote-full-system-b0-pr-plan.md` | 保留 | `remote/README.md` 仍把它们定义为 next upgrade stage 的 authoritative planning assets；相关 backend tests 也直接读取 |
| `prd-remote-auth.md` / `test-spec-remote-auth.md` / `prd-remote-auth-step0~5-pr-plan.md` / `test-spec-remote-auth-step0~5-pr-plan.md` | 保留 | `docs/domains/auth/*` 和 Step 0 handoff docs 仍把这组文件当作当前 auth/domain 规划基线 |

## 3.2 Archive now to `.omx/plans/archive/`

| 文件组 | 归档原因 | 已被哪些正式文档吸收 |
| --- | --- | --- |
| `docs-information-architecture-plan-2026-04-21.md` / `open-questions.md` / `prd-closeout-next-phase-foundation-2026-04-21.md` | Closeout 盘点与入口收口已经转入正式治理/启动文档 | `docs/governance/verification-baseline.md`、`docs/governance/inventory/root-doc-triage.md`、`docs/governance/next-phase-backlog.md`、`docs/current/next-phase-kickoff.md`、`docs/governance/next-phase-prd.md`、`docs/governance/next-phase-test-spec.md`、`docs/governance/next-phase-execution-breakdown.md` |
| `prd-creative-progressive-rebuild-roadmap.md` / `prd-creative-progressive-rebuild-phase-a-pr-plan.md` / `prd-creative-progressive-rebuild-phase-b-pr-plan.md` / `prd-creative-progressive-rebuild-phase-c-pr-plan.md` / `prd-creative-progressive-rebuild-phase-d-pr-plan.md` / `test-spec-creative-progressive-rebuild-roadmap.md` / `test-spec-creative-progressive-rebuild-phase-b-pr-plan.md` / `test-spec-creative-progressive-rebuild-phase-c-pr-plan.md` / `test-spec-creative-progressive-rebuild-phase-d-pr-plan.md` / `ralplan-phase-b-pr-plan-creative-progressive-rebuild.md` | Creative A~D 主线已经完成，保留价值以历史回溯为主 | `docs/domains/creative/progressive-rebuild-final-summary.md`、`docs/domains/creative/progressive-rebuild-completion-audit.md`、`docs/domains/creative/phase-a-acceptance-checklist.md` |
| `prd-frontend-ui-ux-closeout-phase-e-pr-plan.md` / `test-spec-frontend-ui-ux-closeout-phase-e-pr-plan.md` | Frontend Phase E 已完成，当前只需要 closeout summary，不再需要它们占据 active plans 区 | `docs/archive/history/frontend-ui-ux-closeout-final-summary.md` |
| `prd-local-ffmpeg-composition-pr-plan.md` / `test-spec-local-ffmpeg-composition-pr-plan.md` | `local_ffmpeg V1` 已经完成 contract / 执行链 / 文档 / 回归收口 | `docs/domains/publishing/local-ffmpeg-composition.md`、`docs/domains/tasks/task-management-domain-model.md`、`docs/domains/tasks/task-semantics.md`、`reports/local-ffmpeg-plan-closeout-2026-04-20.md` |
| `prd-login-ux-closeout-pr-plan.md` / `test-spec-login-ux-closeout-pr-plan.md` | 登录 UX 收口阶段已完成，当前保留价值以阶段总结与回归证据为主 | `reports/login-ux-closeout-stage-summary-2026-04-19.md` |
| `prd-release-hardening-runtime-acceptance-closeout.md` / `test-spec-release-hardening-runtime-acceptance-closeout.md` | release hardening / runtime acceptance 已转为基线治理与验收留痕 | `docs/governance/verification-baseline.md`、`reports/release-hardening-tail-triage-2026-04-20.md`、`reports/runtime-acceptance-local-ffmpeg-and-random-account-2026-04-20.md`、`reports/flaky-e2e-convergence-2026-04-20.md` |
| `prd-remote-system-mvp.md` / `test-spec-remote-system-mvp.md` / `prd-remote-system-phase0-pr-plan.md` ~ `prd-remote-system-phase3-pr-plan.md` | 已被新一轮 `remote-full-system` 规划基线取代 | `remote/README.md`、`remote/remote-shared/docs/remote-full-system-operating-model-v1.md`、`remote/remote-shared/docs/phase1-release-gate.md` ~ `phase4-release-gate.md` |
| `remote-admin-platform-ui-pr-sequence-2026-04-16.md` / `remote-admin-platform-ui-ralplan-2026-04-16.md` | `remote-admin` UI 规划已被正式 spec 接管 | `remote/remote-shared/docs/remote-admin-platform-ui-spec-v1.md` |
| `prd-product-create-name-share-text.md` / `test-spec-product-create-name-share-text.md` | product-create 双字段规划已经被正式商品域文档、页面规格和文档真相测试吸收 | `docs/domains/products/redesign.md`、`docs/domains/products/requirements.md`、`docs/specs/page-specs/product-list.md`、`docs/specs/page-specs/product-detail.md`、`backend/tests/test_doc_truth_fixes.py` |
| `product-create-dual-field-ralplan-2026-04-16.md` / `ralplan-login-bs-alignment-2026-04-20.md` / `ralplan-task-management-filters-2026-04-19.md` / `ralplan-task-management-page-closeout-2026-04-19.md` / `ralplan-work-driven-creative-flow-2026-04-20.md` | 这批属于中间共识/分歧收敛 artifacts，已被后续 PRD / test-spec / report 接管 | `prd-product-create-name-share-text.md`、`test-spec-product-create-name-share-text.md`、`prd-login-bs-alignment-pr-plan.md`、`test-spec-login-bs-alignment-pr-plan.md`、`prd-task-management-page-closeout.md`、`reports/task-management-filter-simplification-plan.md`、`prd-work-driven-creative-flow-refactor.md`、`test-spec-work-driven-creative-flow-refactor.md` |

## 3.3 Keep in `.omx/plans/` pending manual review

以下文件暂不移动，等相关主线是否继续推进更明确后再做下一批：

- `prd-login-bs-alignment-pr-plan.md`
- `test-spec-login-bs-alignment-pr-plan.md`
- `prd-task-management-page-closeout.md`
- `test-spec-task-management-page-closeout.md`
- `prd-work-driven-creative-flow-refactor.md`
- `test-spec-work-driven-creative-flow-refactor.md`

这批文件的共同特点是：**可能仍有工程参考价值，但还没有足够证据证明它们已经完全被 `docs/` 正式文档吸收。**

## 4. 当前执行约定

本轮开始采用以下约定：

1. `.omx/plans/` 只保留仍会被当前开发直接读取的 planning baseline
2. 已被正式文档吸收的计划文件，优先移到 `.omx/plans/archive/`
3. 如果 `docs/` 仍需要引用这些历史计划，应改为引用 `.omx/plans/archive/...`
4. 不把 `.omx/plans/archive/` 误当作 `docs/archive/` 的替代；它仍属于 runtime/local artifact 范畴

## 5. 结论

如果只记一条规则：

> **`.omx/plans` 留给“还在驱动开发的计划”；已经被 `docs/` 正式吸收的计划，统一下沉到 `.omx/plans/archive/`。**
