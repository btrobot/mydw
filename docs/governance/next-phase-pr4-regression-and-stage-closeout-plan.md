# PR-4 回归补强与阶段收口规划（Focused Ralplan）

> Version: 1.0.0 | Updated: 2026-04-22
> Owner: Tech Lead / Codex
> Status: Approved PR-level planning artifact

> 本文件是对 `docs/governance/next-phase-execution-breakdown.md` 中 **PR-4：回归补强与阶段收口** 的聚焦规划。  
> 它回答：**PR-4 到底要补强什么回归基线、阶段 closeout gate 应如何定义、哪些最小修复允许吸收、如何切片、如何验证、为什么按这个方案推进。**

## 0. 在启动包中的角色

本文件不替代以下主线级文档，而是在它们已经成立的前提下，把 PR-4 收成可执行 plan：

- 总入口：`docs/current/next-phase-kickoff.md`
- 范围定义：`docs/governance/next-phase-prd.md`
- 验证规格：`docs/governance/next-phase-test-spec.md`
- 执行顺序：`docs/governance/next-phase-execution-breakdown.md`
- backlog：`docs/governance/next-phase-backlog.md`
- 前置 closeout：
  - `docs/governance/inventory/pr1-workbench-manageability-closeout.md`
  - `docs/governance/inventory/pr2-business-diagnostics-layering-closeout.md`
  - `docs/governance/inventory/pr3-copy-and-state-unification-closeout.md`

使用规则：

1. 主线变化，先改 kickoff / PRD，不先改本文件
2. PR-4 的 closeout gate 或验证口径变化时，先改本文件，再同步 `next-phase-test-spec`
3. 本文件只规划 PR-4，不把 AIClip 产品化、remote 扩张、平台级 cleanup 混进来

对应的 OMX working artifacts（现已归档）：

- `.omx/plans/archive/prd-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/test-spec-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/slice-plan-pr4-regression-and-stage-closeout.md`

---

## 1. Grounded baseline / 当前基线

PR-4 的起点不是“系统还没稳定”，而是：

- PR-1 已把 Workbench 可管理性收口
- PR-2 已把业务层 / diagnostics 层边界收口
- PR-3 已把关键页面文案、CTA 与四态收口

因此，PR-4 的任务不再是继续发明新规则，而是把 **PR-1 → PR-3 已形成的 current truth** 变成一套足够支撑阶段退出与下一主线启动的 **stage closeout proof**。

### 已经成立的基础

- `docs/governance/next-phase-test-spec.md` 已定义：
  - backend / contract baseline
  - frontend baseline
  - PR-2 targeted suites
  - PR-3 targeted suites
- `docs/governance/phase-transition-checklist.md` 已定义阶段切换时 Part A / Part B 的检查口径
- `docs/governance/inventory/` 下已有 PR-1、PR-2、PR-3 closeout，可作为 PR-4 的直接输入

### 当前仍未收口的缺口

- 阶段级 closeout gate 仍未被锁成一条明确的“跑什么、看什么、产出什么”的路线
- 目前的 baseline 与 targeted suites 分散在多个文档里，尚未被 PR-4 汇总成一个阶段退出口径
- 还没有一份正式文档回答：
  - 这个阶段现在是否可以算“已被回归基线接住”
  - 如果要切到下一条主线，证据应该从哪里读

### 明确不在 PR-4 解决的事

- 不做 AIClip workflow 深度产品化
- 不做新 feature 扩张
- 不做 platform / backend 长尾 cleanup 大扫除
- 不做新的 IA / 页面结构改版
- 不做“为了更完整”而额外扩大战线的 full-matrix 验证工程

---

## 2. 一句话定义

> **PR-4 的任务，不是继续扩功能，而是把 PR-1 到 PR-3 已建立的主线收口成一套可重复验证、可解释退出、可支撑下一阶段启动的阶段级证明。**

---

## 3. RALPLAN-DR 摘要

### 3.1 Principles / 原则

1. **先锁门禁，再跑回归**：先定义 stage closeout gate，再执行验证，避免“跑完再解释”
2. **补强优先于扩张**：只吸收为通过 closeout gate 所必需的最小修复，不顺手开新问题
3. **文档证据与测试证据同权**：PR-4 不仅要跑绿，还要把结果落成正式 closeout 说明
4. **阶段退出必须可复述**：后续不翻聊天，也能知道本阶段如何被验证、为何可退出
5. **回归链路要可重复**：验证口径应能被后续阶段复用，而不是一次性表演

### 3.2 Decision drivers / 主要决策驱动

1. **阶段退出可信度是否足够**
2. **验证成本是否仍然可控**
3. **是否能为下一条主线提供清晰 handoff**

### 3.3 Viable options / 备选方案

#### 方案 A：轻量收口，只跑现有 baseline，快速出总结

内容：

- 只重跑当前最小 baseline
- 输出一份总结文档
- 不进一步明确 PR-2 / PR-3 的 suites 如何并入阶段 gate

优点：

- 速度最快
- 文档工作量最小

缺点：

- 阶段 closeout gate 仍然模糊
- 后续很难回答“哪些回归现在是必须守住的”
- 容易把 PR-4 退化成一次性的收尾报告

结论：

> **本轮不选。** 这会留下“总结有了，但门禁没锁”的问题。

#### 方案 B：先锁阶段 closeout gate，再做回归执行 / 最小修复 / 正式收口（推荐）

内容：

- 先定义 PR-4 的 stage closeout gate
- 再运行 backend / frontend / targeted suites 与手工链路
- 若出现回归，只吸收通过 gate 所必需的最小修复
- 最后产出正式 closeout 文档并回填治理入口

优点：

- 兼顾可信度与范围控制
- 最适合“当前阶段结束、下一阶段即将启动”的任务形态
- 能把已有 PR closeout 串成阶段级 authority

缺点：

- 前期需要先统一口径
- docs、tests、验证记录会一起动

结论：

> **推荐方案。**

#### 方案 C：直接扩成更大的全量回归 / 观测性补强工程

内容：

- 在 PR-4 内继续扩充 suite、观测性、脚本化 closeout
- 试图把后续长期验证体系一次补齐

优点：

- 理论上的信心最高
- 未来复用空间更大

缺点：

- 极易 scope creep
- 会把 PR-4 从“阶段收口”膨胀成“新一轮验证平台建设”
- 与当前“先关账，再启下一主线”的目标不匹配

结论：

> **本轮不选。** 这会让 PR-4 偏离 closeout 本意。

### 3.4 Architect review / 架构复核

最强反方观点：

> PR-4 看起来像“阶段收口”，但如果把 baseline、targeted suites、closeout docs、checklist 映射都放进一个 PR，很容易演变成“无上限的稳定化工程”；一旦回归失败，还可能借机把旧问题一并清理，导致 PR-4 失去边界。

真实张力：

- **验证充分** vs **范围可控**
- **做成阶段 authority** vs **避免再开一个治理工程**
- **允许修复回归** vs **防止顺手扩张**

综合结论：

- 保留 **方案 B**
- 必须把“允许吸收的修复”限制为：
  - 直接导致 closeout gate 失败的问题
  - 文档 / 测试 / 代码之间的事实不一致
- 任何需要重开设计讨论、变更边界、增加新功能的事项，转入新的 planning，不混进 PR-4

### 3.5 Critic verdict / 批判性复核

批判要点：

1. 必须明确 PR-4 的 **阶段 closeout gate**，不能只写“跑 baseline”
2. 必须明确 **最小修复政策**，否则执行时会失控
3. 必须明确 **closeout 产物 contract**，否则后续仍然需要翻聊天补证据
4. 必须给出清晰 slice，不允许把 PR-4 变成模糊的大杂烩

最终结论：

> **APPROVE**  
> 以“先锁阶段 gate → 执行回归 / 吸收最小修复 → 形成正式 closeout authority”作为 PR-4 的执行方案。

---

## 4. ADR / 决策记录

### Decision

选择 **方案 B：先锁阶段 closeout gate，再做回归执行 / 最小修复 / 正式收口** 作为 PR-4 的执行方案。

### Drivers

- 当前问题不是“还缺一个功能 PR”，而是“还缺阶段级退出证明”
- PR-1 ～ PR-3 已有足够多 current truth，需要被串成可复用的阶段 authority
- 下一阶段若要继续推进，必须先把当前阶段的验证门禁与 closeout 证据补齐

### Alternatives considered

- 方案 A：轻量收口，只跑 baseline，快速出总结
- 方案 C：扩成更大的全量回归 / 观测性工程

### Why chosen

- 在可信度、成本、边界三者之间最平衡
- 最适合“当前阶段准备退出”的时机
- 能直接为后续主线提供 handoff，而不是再留一个含糊的尾巴

### Consequences

- PR-4 会同时触及 docs、tests、closeout evidence
- 执行期间允许吸收最小必要修复，但不允许功能扩张
- PR-4 完成后，应把“本阶段是否已被 regression baseline 接住”回答清楚

### Follow-ups

- PR-4 完成后，再决定下一条主线是否进入 AIClip 产品化或其它新方向
- 若后续需要长期化 regression orchestration，再单独规划，而不是挤进 PR-4

---

## 5. In scope / Out of scope

### In scope

- 阶段 closeout gate 的定义与落盘
- backend / contract baseline
- frontend typecheck / build / stage closeout E2E suite
- 手工主链路复核
- 通过 closeout gate 所必需的最小修复
- PR-4 正式 closeout 文档
- 对 `next-phase-test-spec` / `next-phase-execution-breakdown` / `README` 等入口文档的必要同步

### Out of scope

- AIClip workflow 深度产品化
- 新功能、新页面、新交互方向
- 大规模 cleanup / refactor
- 超出 closeout gate 所需的全量验证体系建设
- 新一轮 domain / architecture 边界重画

---

## 6. Stage closeout gate / 阶段收口门禁

PR-4 必须把“跑什么 / 看什么 / 产出什么”锁成下面这套 gate。

## 6.1 自动化 gate

### Backend / contract baseline

- `backend/tests/test_creative_workflow_contract.py`
- `backend/tests/test_openapi_contract_parity.py`

### Frontend build gate

- `frontend` `npm run typecheck`
- `frontend` `npm run build`

### Frontend stage closeout E2E suite（去重后的阶段级最小集合）

- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-error-ux/auth-status-live-state.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/publish-pool/publish-pool.spec.ts`
- `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`
- `frontend/e2e/dashboard/dashboard-state.spec.ts`

## 6.2 手工 gate

至少确认：

1. 从 `/` 进入 `CreativeWorkbench` 的主链路仍顺畅
2. Workbench 的筛选 / 管理语义、window-based guardrail 没回退
3. 默认业务面仍未把 diagnostics 混回主视图
4. diagnostics secondary entry 仍显式可达，且 URL / refresh 语义不丢
5. auth/login shell、creative 主链路、Dashboard 的四态与文案 current truth 不回退

## 6.3 文档 / authority gate

PR-4 完成时至少应有：

- 一份正式 PR-4 closeout 文档，说明：
  - 实际交付了什么
  - 没做什么
  - closeout gate 如何通过
  - 还剩哪些 residual risks
- `docs/governance/next-phase-test-spec.md` 与 `docs/governance/next-phase-execution-breakdown.md` 已同步 PR-4 当前 truth
- 若新增高频入口文档，`docs/governance/README.md` 与 `inventory-ledger.md` 已补导航

## 6.4 最小修复政策

PR-4 执行过程中允许吸收的修复，仅限：

1. 导致 closeout gate 失败的真实回归
2. 文档 / 测试 / 当前实现之间的事实不一致
3. 为让验证稳定可重复所需的最小测试修正

不允许：

- 顺手加入新功能
- 借回归修复之名做大重构
- 把“可延后问题”一并清理

---

## 7. Slice 划分（推荐 3 片）

## Slice A：收口门禁锁定与验证范围冻结

目标：

- 把 PR-4 的 stage closeout gate、最小修复政策、closeout 产物 contract 落到正式文档和 OMX 工件

主要改动面：

- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`（如导航需同步）
- `.omx/plans/archive/prd-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/test-spec-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/slice-plan-pr4-regression-and-stage-closeout.md`

完成标准：

- “跑什么、看什么、产出什么”已经写清
- PR-4 不再只是一个占位标题
- 后续可无歧义交给 `$ralph` / `$team`

最小验证：

- 文档 UTF-8 回读无损
- `git diff --check`

## Slice B：回归执行、最小修复与证据沉淀

目标：

- 运行 stage closeout gate
- 对失败项只做必要修复
- 把结果转成可引用的验证证据

主要改动面：

- `backend/tests/*`（仅当 contract baseline 失败且需最小修正）
- `frontend/e2e/*`
- 受回归影响的最小代码面
- 临时验证记录 / closeout 草稿

完成标准：

- backend / frontend / 手工 gate 通过
- 修复范围未越界
- 每类验证结果都有明确证据

最小验证：

- stage closeout gate 全部通过

## Slice C：正式 closeout 与阶段 handoff

目标：

- 形成 PR-4 正式收口件
- 把本阶段“为什么现在可以退出”写成当前 authority

主要改动面：

- `docs/governance/inventory/` 下的 PR-4 closeout 文档
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/inventory/inventory-ledger.md`
- 如需要，`docs/governance/README.md`

完成标准：

- 不翻聊天，也能理解本阶段如何被验证并为何可退出
- PR-4 成为当前阶段的正式 closing PR，而不是继续开放的模糊尾项

最小验证：

- closeout 文档 UTF-8 回读无损
- 引用路径与导航可用

---

## 8. 验证计划

PR-4 完成时至少应满足：

### Automated verification

```powershell
pytest `
  backend/tests/test_creative_workflow_contract.py `
  backend/tests/test_openapi_contract_parity.py `
  -q
```

```powershell
cd E:\ais\mydw\frontend
$env:E2E_BASE_URL='http://127.0.0.1:4174'
npm run typecheck
npm run build
npm run test:e2e -- `
  e2e/auth-bootstrap/auth-bootstrap.spec.ts `
  e2e/auth-error-ux/auth-error-ux.spec.ts `
  e2e/auth-error-ux/auth-status-live-state.spec.ts `
  e2e/auth-routing/auth-routing.spec.ts `
  e2e/auth-shell/auth-shell.spec.ts `
  e2e/login/login.spec.ts `
  e2e/creative-main-entry/creative-main-entry.spec.ts `
  e2e/creative-workbench/creative-workbench.spec.ts `
  e2e/creative-review/creative-review.spec.ts `
  e2e/creative-version-panel/creative-version-panel.spec.ts `
  e2e/publish-pool/publish-pool.spec.ts `
  e2e/publish-cutover/publish-cutover.spec.ts `
  e2e/task-diagnostics/task-diagnostics.spec.ts `
  e2e/dashboard/dashboard-state.spec.ts
```

### Documentation integrity

- `git diff --check`
- 本轮新增/修改中文文档 UTF-8 回读

### 手工验证

1. `/` → `CreativeWorkbench` 主链路正常
2. Workbench 可管理性、业务 / diagnostics 边界、URL 恢复语义未回退
3. auth/login shell、creative 主链路、Dashboard 的四态与文案仍符合 PR-3 current truth
4. publish-pool / publish-cutover / task-diagnostics 仍符合 PR-2 边界口径

### 通过标准

- stage closeout gate 全绿
- 没有通过“扩大范围”来换取通过
- closeout authority 已写入正式 docs

---

## 9. docs / tests 同步更新清单

PR-4 执行时，至少同步检查：

- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`
- `docs/governance/inventory/inventory-ledger.md`
- `.omx/plans/archive/prd-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/test-spec-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/slice-plan-pr4-regression-and-stage-closeout.md`

---

## 10. 执行建议

推荐执行方式：

> **按本文件先锁 PR-4，再按 Slice A → Slice B → Slice C 顺序推进。**

不建议：

- 先跑测试，失败后再反向定义 closeout gate
- 借 PR-4 顺手做新功能或大重构
- 把 PR-4 做成“所有遗留问题的一次性总清理”

更具体地：

1. 先做 Slice A，锁 closeout gate 与最小修复政策
2. 再做 Slice B，执行回归与必要修复
3. 最后做 Slice C，形成正式 closeout authority 与 handoff

---

## 11. OMX 执行交接建议

推荐执行车道：

- **`$ralph`**：适合按 Slice A → B → C 顺序做验证、修复、收口闭环
- **`$team`**：适合把“验证执行 / 最小修复 / docs closeout”拆成并行 lane

推荐可用角色：

- `executor`：最小修复与实现
- `debugger`：失败回归定位
- `verifier`：基线运行与证据整理
- `writer`：closeout 文档与治理入口同步
- `test-engineer`：E2E / baseline 命令与断言维护
- `architect`：最终边界复核
- `critic`：收口质量挑战

### Available-agent-types roster

- `planner`
- `architect`
- `critic`
- `executor`
- `debugger`
- `verifier`
- `writer`
- `test-engineer`
- `code-reviewer`

### Ralph staffing guidance

- Slice A：`writer` + `test-engineer`
- Slice B：`verifier` + `debugger` + `executor`
- Slice C：`writer` + `verifier`
- 终验：`architect` / `critic`

### Team staffing guidance

- lane 1：backend / contract baseline + frontend build gate
- lane 2：frontend E2E regression + 最小修复
- lane 3：docs / closeout / checklist mapping
- final verification lane：整体验证复跑 + evidence 汇总

### Suggested reasoning levels by lane

- gate 定义 / closeout 结构：high
- 回归定位 / 最小修复：high
- docs 对齐 / evidence 汇总：medium
- 大批量验证执行：medium

### Launch hints

- 顺序执行：
  - `$ralph 执行 PR-4 Slice A`
  - `$ralph 执行 PR-4 Slice B`
  - `$ralph 执行 PR-4 Slice C`
- 并行执行：
  - `$team PR-4：回归补强与阶段收口`

一句话：

> **PR-4 适合“focused ralplan → gate-first ralph execution”；只有在验证执行、最小修复、文档收口可清晰拆 lane 时，再考虑 `$team`。**
