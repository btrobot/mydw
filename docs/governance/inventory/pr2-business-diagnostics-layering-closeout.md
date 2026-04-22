# PR-2 业务层 / 诊断层分层 Closeout

> Version: 1.0.0
> Updated: 2026-04-22
> Owner: Tech Lead / Codex
> Status: Recorded closeout

> 目的：把 `PR-2 / 业务层 / 诊断层分层` 的实际交付、当前真相、验证结果与剩余风险落成一份正式收口件。  
> 这份文档回答的不是“PR-2 原本想做什么”，而是：**PR-2 最终实际做成了什么、没有做什么、现在系统应该如何理解、下一步该从哪里继续。**

---

## 1. 一句话总结

> PR-2 已把 `CreativeWorkbench` 与 `CreativeDetail` 从“默认业务面混排诊断信息”的过渡态，收口成“默认业务层 + 显式高级诊断入口”的当前真相：**默认隐藏 diagnostics、显式入口一跳可达、打开状态可通过 URL 恢复。**

---

## 2. 本 PR 原始目标

- 让默认业务面先服务作品定位、输入、审核、版本与主操作
- 把 scheduler / runtime / pool / shadow / kill-switch / cutover / task diagnostics 等诊断事实下沉到显式入口
- 保住 workbench → detail → task diagnostics 的排障链路
- 在 PR-2 内完成前端分层收口，不扩 backend / diagnostics contract，不混入 PR-3 文案与四态统一

关联文档：

- kickoff: `docs/current/next-phase-kickoff.md`
- PRD: `docs/governance/next-phase-prd.md`
- test spec: `docs/governance/next-phase-test-spec.md`
- execution breakdown: `docs/governance/next-phase-execution-breakdown.md`
- PR-level plan: `docs/governance/next-phase-pr2-business-diagnostics-layering-plan.md`

对应 OMX working artifacts（现已吸收到正式 docs，并归档）：

- `.omx/plans/archive/prd-pr2-business-diagnostics-layering.md`
- `.omx/plans/archive/test-spec-pr2-business-diagnostics-layering.md`
- `.omx/plans/archive/slice-plan-pr2-business-diagnostics-layering.md`

---

## 3. 实际交付结果

### 3.1 已完成

- **Slice A：Workbench 默认业务层收束**
  - `CreativeWorkbench` 首屏不再直接展开 scheduler / runtime / shadow / kill-switch 诊断正文
  - 默认页保留业务统计、窗口 guardrail、搜索 / 筛选 / 排序 / preset、表格列表与进入 detail 主操作
  - 运行诊断通过“查看运行诊断”显式入口进入 drawer
- **Slice B：Detail 默认业务层 / 高级诊断层分层**
  - `CreativeDetail` 默认页先展示业务概览、作品输入、当前版本、当前有效审核结论与主 CTA
  - 发布与调度诊断、发布池历史、Cutover 差异、任务诊断入口统一收束到“查看高级诊断”drawer
  - task diagnostics 仍保留一跳入口，returnTo / taskId 主链路不回归
- **Slice C：验证与文档事实对齐**
  - `docs/governance/next-phase-test-spec.md` 已明确 PR-2 的口径是“默认隐藏 + 显式可达 + URL 可恢复”
  - `docs/governance/next-phase-execution-breakdown.md` 已同步 PR-2 的实际验收、切片完成情况与正式 closeout
  - `docs/governance/README.md` 已补齐 next-phase / PR-2 的正式阅读路径

### 3.2 未完成 / 明确不做

- **不做 PR-3**：全局 CTA、坏文案修复、loading / empty / error / success 四态统一
- **不做新 diagnostics 子系统**：没有拆新 route、tab 或新后端 contract
- **不做 backend 扩边界**：没有新增 publish / diagnostics 相关接口协议
- **不做 AIClip 深度产品化**

### 3.3 与原计划相比的偏差

- 偏差 1：诊断层没有拆成新页面，而是在原页面内采用显式 drawer  
  - 原因：本轮目标是先完成“默认业务面收口”，不是再开一轮新的 IA / 路由重构
- 偏差 2：PR-2 最终把 **URL 可恢复** 提升为 current truth 的一部分  
  - 原因：这能稳定承接 deep-link、refresh 与 E2E，而不需要引入额外 route 复杂度

---

## 4. 当前系统真相发生了什么变化

### 4.1 Workbench 当前真相

- `CreativeWorkbench` 默认入口现在首先承接：
  - 业务统计
  - 搜索 / 筛选 / 排序 / preset
  - 列表定位与进入 detail 主动作
  - window-based guardrail
- 默认首屏不再直接承担：
  - scheduler mode
  - effective mode
  - runtime status
  - shadow read
  - kill switch
  - 完整运行 warning 正文
- 当 diagnostics 请求失败时，可保留轻量提醒，但提醒只负责导向“查看运行诊断”，不再在首屏展开完整排障叙事

### 4.2 Detail 当前真相

- `CreativeDetail` 默认页现在首先承接：
  - 业务概览
  - 作品输入
  - 合成准备判断
  - 当前版本
  - 当前有效审核结论
  - 主 CTA（保存输入 / 提交合成 / 审核当前版本 / 打开 AIClip）
- 默认详情页不再直接混排：
  - 调度模式 / 生效模式 / shadow read / kill switch
  - 发布池历史细节
  - Cutover diff 正文
  - 任务排障正文
- 排障相关事实现在通过“查看高级诊断”统一进入 diagnostics drawer

### 4.3 URL / workflow 当前真相

- diagnostics 打开状态已成为当前前端状态模型的一部分：
  - workbench：`diagnostics=runtime`
  - detail：`diagnostics=advanced`
- 这意味着：
  - refresh 后可恢复 diagnostics 打开状态
  - deep-link 与 E2E 可稳定复现
  - 无需新增 route 也能维持显式入口模型
- `task diagnostics` 继续作为独立排障面存在，但它现在被明确界定为 **diagnostics surface**，不再与默认业务面职责混淆

### 4.4 哪些旧材料不再应被当成 active planning

- `.omx/plans/archive/prd-pr2-business-diagnostics-layering.md` → 已吸收，留作 archive
- `.omx/plans/archive/test-spec-pr2-business-diagnostics-layering.md` → 已吸收，留作 archive
- `.omx/plans/archive/slice-plan-pr2-business-diagnostics-layering.md` → 已吸收，留作 archive

这些材料仍有追溯价值，但不再是当前 authoritative input；当前 authoritative truth 以正式 docs 与本收口件为准。

---

## 5. 验证总结

### 5.1 自动化验证

- `frontend` `npm run typecheck` — **PASS**
- `frontend` `npm run build` — **PASS**
- `frontend` targeted Playwright suite（设置 `E2E_BASE_URL=http://127.0.0.1:4174`）— **PASS（31 passed）**
  - `e2e/creative-workbench/creative-workbench.spec.ts`
  - `e2e/creative-review/creative-review.spec.ts`
  - `e2e/publish-pool/publish-pool.spec.ts`
  - `e2e/publish-cutover/publish-cutover.spec.ts`
  - `e2e/task-diagnostics/task-diagnostics.spec.ts`
  - `e2e/creative-version-panel/creative-version-panel.spec.ts`
  - `e2e/creative-main-entry/creative-main-entry.spec.ts`
  - `e2e/auth-routing/auth-routing.spec.ts`

PR-2 对应提交链：

- planning lock：`0e6ec0a`
- Slice A：`4991012`
- Slice B：`6ff390d`
- Slice C：`f5cc875`

### 5.2 手工验证

- 未单独补一轮新的人工 closeout 演练记录
- 当前主要依赖 targeted Playwright 覆盖以下关键链路：
  - workbench 默认业务入口
  - diagnostics secondary entry
  - detail 默认业务视图
  - publish-pool / cutover / task diagnostics 可达性
  - creative main entry / auth-routing 主入口

### 5.3 未覆盖或未完全验证项

- 未重跑 backend contract baseline
- 未单独形成一份人工验收记录
- 未对 diagnostics query-key 作为外部公开协议做兼容性承诺

---

## 6. 文档吸收情况

- [x] `docs/governance/next-phase-test-spec.md` 已更新
- [x] `docs/governance/next-phase-execution-breakdown.md` 已更新
- [x] `docs/governance/README.md` 已更新
- [x] PR-2 closeout 已形成正式文档
- [x] PR-2 对应 OMX planning 已移出 `.omx/plans` active 区
- [x] 本文档已作为 inventory / closeout 正式记录

本轮没有更新的文档与原因：

- `docs/current/next-phase-kickoff.md`：主线没有变化
- `docs/governance/next-phase-prd.md`：PR-2 没有改写主线范围定义，只是把该 PR 实际收口

---

## 7. Planning / Archive 收口

- [x] 已吸收到正式 docs 的 PR-2 planning 已移出 `.omx/plans` active 区
- [x] `.omx/plans/archive/` 已收纳本 PR 对应 working artifacts

归档后的路径：

- `.omx/plans/archive/prd-pr2-business-diagnostics-layering.md`
- `.omx/plans/archive/test-spec-pr2-business-diagnostics-layering.md`
- `.omx/plans/archive/slice-plan-pr2-business-diagnostics-layering.md`

---

## 8. Remaining risks / Residual risks

1. **PR-3 仍未收口**  
   - 影响：虽然页面职责边界已清晰，但跨页面 CTA、文案一致性与四态表达仍可能不稳  
   - 当前处理：留给 PR-3

2. **diagnostics 体量继续增长时，现有 drawer 模型可能再次吃力**  
   - 影响：未来若排障内容显著扩张，drawer 内信息架构可能不够  
   - 当前处理：后续如有必要，再考虑独立 diagnostics page / tab

3. **backend contract baseline 未在本 closeout 重跑**  
   - 影响：本轮 closeout 不能把 backend 契约验证也算作 fresh evidence  
   - 当前处理：当前 closeout 以 frontend 分层与主链路回归为主

---

## 9. Backlog handoff

明确进入后续 backlog / 下一 PR 的事项：

- PR-3：文案与四态统一
- PR-4：回归补强与阶段收口
- 如 diagnostics 继续膨胀，再评估独立 diagnostics IA

对应文档：

- `docs/governance/next-phase-backlog.md`
- `docs/governance/next-phase-execution-breakdown.md`

---

## 10. 对下一阶段的输入

### 建议继续回答的问题

- 哪些 CTA / 状态文案仍然带有过渡态解释口吻，需要在 PR-3 收口？
- 哪些页面的 loading / empty / error / success 四态仍不一致？
- 哪些提示文案还在借用 diagnostics 语言，而不是业务语言？

### 推荐下一入口

> **PR-3：文案与四态统一**

原因：

- PR-2 已把默认业务面和 diagnostics 面拉开
- 下一步最自然的工作，不是继续改 diagnostics 容器，而是统一业务页面语言、CTA 与四态反馈

---

## 11. Exit decision / PR-2 退出结论

> **PR-2 可以视为已正式收口。**  
> 它已经把“默认业务面”和“诊断面”的边界、显式入口、URL 恢复、验证口径与正式文档都接住了；后续不应再把 PR-2 当成“还可以顺手继续调一点 diagnostics 布局”的开放 PR，而应把下一步工作切换到 PR-3 / PR-4 或新的独立 planning。
