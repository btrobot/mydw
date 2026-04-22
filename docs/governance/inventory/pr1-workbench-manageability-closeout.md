# PR-1 Workbench 可管理性收口 Closeout

> Version: 1.0.0  
> Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Recorded closeout

> 目的：把 `PR-1 / Workbench 可管理性收口` 的实际交付、当前真相、验证结果与剩余风险落成一份正式收口件。  
> 这份文档回答的不是“PR-1 原本想做什么”，而是：**PR-1 最终实际做成了什么、没有做什么、现在系统应该如何理解、下一步该从哪里继续。**

---

## 1. 一句话总结

> PR-1 已把当前 `table-first CreativeWorkbench` 从“能用的列表页”收口成“可定位、可恢复、可排序、可分队列、边界显式”的日常工作台，同时明确保留 **window-based** 模型，不在本轮扩到 server-side search contract。

---

## 2. 本 PR 原始目标

- 让 Workbench 具备更明确的日常可管理能力
- 把 workbench 的工作上下文从隐式页面状态收口成可恢复、可分享的 URL 状态
- 补齐高频 work queue 视角，而不是只靠人工拼筛选
- 在 PR-1 内把 manageability baseline 收实，但不跨进 PR-2 / PR-3 / backend search 扩边界

关联文档：

- kickoff: `docs/current/next-phase-kickoff.md`
- PRD: `docs/governance/next-phase-prd.md`
- test spec: `docs/governance/next-phase-test-spec.md`
- execution breakdown: `docs/governance/next-phase-execution-breakdown.md`
- PR-level plan: `docs/governance/next-phase-pr1-workbench-manageability-plan.md`

对应 OMX working artifacts（现已吸收到正式 docs，并归档）：

- `.omx/plans/archive/prd-pr1-workbench-manageability.md`
- `.omx/plans/archive/test-spec-pr1-workbench-manageability.md`
- `.omx/plans/archive/slice-plan-pr1-workbench-manageability.md`

---

## 3. 实际交付结果

### 3.1 已完成

- **Slice A：URL 状态与返回链路收口**
  - Workbench 关键工作状态进入 URL：`keyword` / `status` / `poolState` / `preset` / `sort` / `page` / `pageSize`
  - Workbench → Detail → Back 通过 `returnTo` 保持工作上下文
  - 刷新、复制链接、返回后，工作台视图可恢复
- **Slice B：排序与 preset views 收口**
  - 增加工作台排序：`updated_desc` / `updated_asc` / `attention_desc` / `failed_desc`
  - 增加高频 preset：`all` / `waiting_review` / `needs_rework` / `recent_failures` / `version_mismatch`
  - 高频待处理内容可直接定位，不再只能手工拼筛选
- **Slice C：window-based guardrail / docs / regression 收口**
  - Workbench UI 中显式提示当前是 **window-based model**
  - 明确“最多加载最近 200 条”“搜索/筛选/排序/preset 只对当前窗口生效”
  - 明确何时才需要升级到 `server-side search planning`
  - formal docs 与 targeted regression 已对齐这条 current truth

### 3.2 未完成 / 明确不做

- **不做 PR-2**：默认业务层 / 诊断层进一步分层
- **不做 PR-3**：文案坏点修复与 loading / empty / error / success 四态统一
- **不做 backend contract 扩展**：不引入完整 server-side search / sort / pagination 协议
- **不做大改版视觉重设计**

### 3.3 与原计划相比的偏差

- 偏差 1：PR-1 没有升级为服务端检索方案  
  - 原因：本轮目标是收口 manageability baseline，而不是扩一轮新的搜索平台能力
- 偏差 2：window-based 边界最终采用“显式 guardrail”而不是“隐含在实现里”  
  - 原因：PR-1 的关键不是把问题藏住，而是把当前上限和升级条件讲清楚

---

## 4. 当前系统真相发生了什么变化

### 4.1 架构 / 运行事实变化

- `CreativeWorkbench` 仍然是 **Creative-first** 主入口中的默认工作台入口
- Workbench 当前仍是 **window-based** 工作台，而不是全量检索台
- 当前窗口上限为 `200`
- 当前 manageability baseline 已明确覆盖：
  - URL 状态恢复
  - 返回链路恢复
  - 高频 preset 队列
  - 工作台排序视角
  - window-based 边界提示

### 4.2 Page / contract / workflow 变化

- Workbench URL 参数协议已稳定为：
  - `keyword`
  - `status`
  - `poolState`
  - `preset`
  - `sort`
  - `page`
  - `pageSize`
- `returnTo` 现在是 Workbench ↔ Detail ↔ 下游返回链路的一部分 current truth
- preset 与 sort 不再是临时 UI 行为，而是 PR-1 明确交付的一部分
- “找不到但其实存在” 已被正式定义为未来升级 `server-side search planning` 的触发信号，而不是当前 PR-1 内继续补功能

### 4.3 哪些旧材料不再应被当成 active planning

- `.omx/plans/archive/prd-pr1-workbench-manageability.md` → 已吸收，留作 archive
- `.omx/plans/archive/test-spec-pr1-workbench-manageability.md` → 已吸收，留作 archive
- `.omx/plans/archive/slice-plan-pr1-workbench-manageability.md` → 已吸收，留作 archive

这些材料仍有追溯价值，但不再是当前 authoritative input；当前 authoritative truth 以正式 docs 与本收口件为准。

---

## 5. 验证总结

### 5.1 自动化验证

- `frontend` `npm run typecheck` — **PASS**
- `frontend` `npm run build` — **PASS**
- `frontend` `npm exec playwright test e2e/creative-workbench/creative-workbench.spec.ts --project=chromium --config=e2e/playwright.config.ts` — **PASS（9 passed）**
- `frontend` `npm exec playwright test e2e/creative-main-entry/creative-main-entry.spec.ts e2e/creative-review/creative-review.spec.ts --project=chromium --config=e2e/playwright.config.ts`（设置 `E2E_BASE_URL=http://127.0.0.1:4174`）— **PASS（4 passed）**

PR-1 对应提交链：

- Slice A：`0081d46`
- Slice B：`a6966f7`
- Slice C：`2712b3f`

### 5.2 手工验证

- 未单独补一轮人工点点点 closeout 演练
- 当前主要依赖 targeted Playwright 覆盖以下关键链路：
  - workbench 搜索 / 筛选 / 排序 / preset
  - refresh 恢复
  - detail → back 恢复
  - creative main entry → workbench
  - review drawer 主链路

### 5.3 未覆盖或未完全验证项

- 未重跑 full frontend E2E baseline
- 未重跑 backend contract baseline
- 未做独立人工验收记录

---

## 6. 文档吸收情况

- [x] `docs/architecture/workbench-url-state-model.md` 已更新
- [x] `docs/governance/next-phase-test-spec.md` 已更新
- [x] `docs/governance/next-phase-execution-breakdown.md` 已更新
- [x] PR-1 closeout 已形成正式文档
- [x] PR-1 对应 OMX planning 已从 active 区移出
- [x] 本文档已作为 inventory / closeout 正式记录

本轮没有更新的文档与原因：

- `docs/current/runtime-truth.md`：PR-1 没有改变系统运行拓扑或运行阶段真相
- `docs/current/next-phase-kickoff.md`：主线没有变化，仍然是 Creative-first 稳定化 / UI-UX 收口主线

---

## 7. Planning / Archive 收口

- [x] 已吸收到正式 docs 的 PR-1 planning 已移出 `.omx/plans` active 区
- [x] `.omx/plans/archive/` 已收纳本 PR 对应 working artifacts

归档后的路径：

- `.omx/plans/archive/prd-pr1-workbench-manageability.md`
- `.omx/plans/archive/test-spec-pr1-workbench-manageability.md`
- `.omx/plans/archive/slice-plan-pr1-workbench-manageability.md`

---

## 8. Remaining risks / Residual risks

1. **window-based 模型仍有规模上限**  
   - 影响：当日常处理稳定超出 `200` 条时，当前本地窗口模型会开始吃力  
   - 当前处理：已把升级信号与触发条件写清楚，但尚未进入 backend search planning

2. **业务层 / 诊断层分层尚未收口**  
   - 影响：默认页面的信息密度与职责边界仍可能不够干净  
   - 当前处理：留给 PR-2

3. **文案与四态统一尚未收口**  
   - 影响：跨页面 CTA、状态反馈、错误态的一致性仍可能不足  
   - 当前处理：留给 PR-3

---

## 9. Backlog handoff

明确进入后续 backlog / 下一 PR 的事项：

- PR-2：业务层 / 诊断层分层
- PR-3：文案与四态统一
- 仅在触发条件出现后，再开启 server-side search planning

对应文档：

- `docs/governance/next-phase-backlog.md`
- `docs/governance/next-phase-execution-breakdown.md`

---

## 10. 对下一阶段的输入

### 建议继续回答的问题

- 默认业务层与高级诊断层的边界，哪些信息应留在默认视图，哪些必须下沉？
- 在不扩 backend contract 的前提下，还有哪些 UI/UX 坏点会持续阻塞日常开发与使用？

### 推荐下一入口

> **PR-2：业务层 / 诊断层分层**

原因：

- PR-1 已把“工作台可管理性”这条线收住
- 下一步最自然的收口点，不是继续给 Workbench 叠功能，而是把默认业务视图与诊断视图彻底拉开

---

## 11. Exit decision / PR-1 退出结论

> **PR-1 可以视为已正式收口。**  
> 它已经把 Workbench 的 manageability baseline、当前边界、验证口径和正式文档都接住了；后续不应再把 PR-1 当成“还没收实、可以继续顺手扩一点”的开放 PR，而应把下一步工作切换到 PR-2 / PR-3 或新的独立 planning。
