# PR-3 文案与四态统一规划（Focused Ralplan）

> Version: 1.0.0 | Updated: 2026-04-22
> Owner: Tech Lead / Codex
> Status: Approved PR-level planning artifact

> 本文件是对 `docs/governance/next-phase-execution-breakdown.md` 中 **PR-3：文案与四态统一** 的聚焦规划。  
> 它回答：**PR-3 具体要统一哪些文案与 CTA、哪些页面必须进入 loading / empty / error / success 四态收口、如何切片、如何验证、为什么按这个方案推进。**

## 0. 在启动包中的角色

本文件不替代以下主线级文档，而是在它们已经成立的前提下，把 PR-3 收成可执行 plan：

- 总入口：`docs/current/next-phase-kickoff.md`
- 范围定义：`docs/governance/next-phase-prd.md`
- 验证规格：`docs/governance/next-phase-test-spec.md`
- 执行顺序：`docs/governance/next-phase-execution-breakdown.md`
- 现状问题来源：`docs/domains/creative/workbench-ui-issues.md`
- 已完成前置 PR：
  - `docs/governance/inventory/pr1-workbench-manageability-closeout.md`
  - `docs/governance/inventory/pr2-business-diagnostics-layering-closeout.md`

使用规则：

1. 主线变化，先改 kickoff / PRD，不先改本文件
2. PR-3 范围或验证口径变化时，先改本文件，再同步 test spec / breakdown
3. 本文件只规划 PR-3，不把 PR-4（回归补强与阶段收口）或 AIClip 深度产品化混进来

对应的 OMX 工作工件（现已归档）：

- `.omx/plans/archive/prd-pr3-copy-and-state-unification.md`
- `.omx/plans/archive/test-spec-pr3-copy-and-state-unification.md`
- `.omx/plans/archive/slice-plan-pr3-copy-and-state-unification.md`

---

## 1. Grounded baseline / 当前基线

结合当前代码、现有 E2E 与已落盘文档，PR-3 的起点不是“完全没有文案与状态治理”，而是“已经做过多轮局部修正，但仍缺一个跨 auth / creative / dashboard 的统一 contract”。

### 已经成立的基础

- PR-1 已完成，Workbench 的可管理性、URL 状态与 window-based guardrail 已收口
- PR-2 已完成，Workbench / Detail 的默认业务面与 diagnostics 面已经拉开
- auth shell / auth error UX 已有较稳定的测试基线：
  - `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
  - `frontend/e2e/auth-shell/auth-shell.spec.ts`
  - `frontend/e2e/auth-routing/auth-routing.spec.ts`
- creative 主路径已有 targeted E2E：
  - `creative-main-entry`
  - `creative-workbench`
  - `creative-review`
  - `creative-version-panel`

### 当前仍未收口的缺口

- 页面文案仍存在：
  - 中英混搭与术语口径不稳
  - 过渡期解释口吻残留
  - 局部坏文案 / 占位字符问题
- CTA 层级仍不够统一：
  - 主 CTA 与次动作命名方式不稳定
  - 不同页面对“主动作”的表达方式不一致
- 四态表达仍不够统一：
  - 有些页面已显式区分 error / empty
  - 有些页面仍依赖默认值、说明型 Alert 或 diagnostics 语言补偿
- `Dashboard` 仍是最容易回到“解释型页面”的位置，但它又不能在 PR-3 内变成新一轮 IA 改版

### 明确不在 PR-3 解决的事

- 不做 AIClip workflow 深度产品化
- 不做 task 页面 IA 或 diagnostics route 重构
- 不做新的共享 UI framework 基建工程
- 不扩 backend contract / API 状态模型
- 不做大视觉系统重设计

---

## 2. 一句话定义

> **PR-3 的任务，不是重新设计页面，而是把核心页面的业务文案、CTA 层级与 loading / empty / error / success 四态收口成一套稳定 current truth。**

---

## 3. RALPLAN-DR 摘要

### 3.1 Principles / 原则

1. **业务语言优先**：默认业务面优先使用中文业务语言，不借 diagnostics 语言解释页面职责
2. **结构胜过解释**：优先用标题、分区、主 CTA 与状态组件表达页面角色，而不是依赖说明型 Alert
3. **四态必须显式**：loading / success / empty / error 要可区分，不能把 error 伪装成 empty 或默认值
4. **小步收口，不做基建漂移**：以页面为单位收口，只引入必要的轻量共享规则
5. **不回退 PR-2**：文案与状态统一不能重新把 diagnostics 混回默认业务层

### 3.2 Decision drivers / 主要决策驱动

1. **理解成本是否下降**：用户与开发者是否更容易判断页面职责与主动作
2. **状态语义是否稳定**：核心页面在 loading / empty / error / success 间是否不再误导判断
3. **回归成本是否可控**：能否在有限 diff 内完成并维持主链路稳定

### 3.3 Viable options / 备选方案

#### 方案 A：逐页文案清洗，不抽统一 contract

内容：

- 页面看到哪里改哪里
- 以页面局部体验为主，不先锁一套 CTA / 四态规则

优点：

- 启动最快
- 每片 diff 看起来更直观

缺点：

- 容易再次漂移
- 文案统一会退化成“页面单点修补”
- 后续 PR-4 很难判断什么才算“统一完成”

结论：

> **本轮不选。** 这会把 PR-3 退化成零散 polishing。

#### 方案 B：轻量文案 / 四态 contract + 关键页面分片落地（推荐）

内容：

- 先锁定中文主文案策略、CTA 层级和四态定义
- 再按 auth / creative / dashboard 关键页面分 slice 落地
- 共享规则保持轻量，不另起大框架

优点：

- 既能形成统一 current truth，又不会演变成 UI 基建工程
- 最适合 PR-3 这种“收口而非扩张”的任务形态
- 与 PR-1 / PR-2 的小步收口方式保持一致

缺点：

- 前期需要先做一次边界定义
- docs、页面、E2E 会一起动

结论：

> **推荐方案。**

#### 方案 C：先抽完整共享 UI state framework，再批量接入页面

内容：

- 先做统一 state container / shared components / copy registry
- 再让页面全部迁移接入

优点：

- 长期一致性最强
- 理论上复用最好

缺点：

- 极易过度设计
- 容易膨胀成 PR-4 甚至新一轮前端基建项目
- 对当前“先收口再继续开发”的目标不够友好

结论：

> **本轮不选。** 这会让 PR-3 偏离“低风险稳定化”。

### 3.4 Architect review / 架构复核

最强反方观点：

> PR-3 看起来像“文案与四态统一”，但实际把 auth、creative、dashboard 都拉进来，很容易变成范围过宽的体验清洗；如果没有进一步缩边界，最终会一边修文案、一边改状态组件、一边补测试，导致成本超过 PR-2。

真实张力：

- **广覆盖一致性** vs **可控范围**
- **抽统一规则** vs **避免抽象过度**
- **把 Dashboard 一起收口** vs **不重新打开 diagnostics IA**

综合结论：

- 保留 **轻量 contract + 分 slice 落地** 路线
- 把范围明确分成：
  - **核心主路径页面**：auth / workbench / detail / version panel
  - **有界 secondary surface**：Dashboard 仅做文案与状态反馈，不做 IA 重构
- 若 Dashboard 收口需要新测试，允许加一条 targeted suite；但不因此扩大到 task 页面大扫除

### 3.5 Critic verdict / 批判性复核

批判要点：

1. 必须明确“主路径页面”和“secondary surface”的范围边界
2. 必须把四态 contract 写成可验证规则，而不是抽象口号
3. 必须给出清晰的 slice 验收口径，不允许把 PR-3 变成长尾 polishing
4. 必须约束 docs 更新面，避免为了 PR-3 过度改动无关治理文档

最终结论：

> **APPROVE**  
> 以“轻量文案 / 四态 contract + 关键页面分片落地”作为 PR-3 的执行方案；验收重点改为“业务语言稳定、CTA 层级稳定、四态显式且不误导”。

---

## 4. ADR / 决策记录

### Decision

选择 **方案 B：轻量文案 / 四态 contract + 关键页面分片落地** 作为 PR-3 的执行方案。

### Drivers

- 当前问题是“规则还不够统一”，不是“完全没有组件”
- PR-3 需要的是稳定 current truth，而不是新的 UI framework
- PR-2 刚完成边界分层，PR-3 应该在这个边界上统一语言和状态，而不是重新打开结构层改动

### Alternatives considered

- 方案 A：逐页文案清洗，不抽统一 contract
- 方案 C：先抽完整共享 UI state framework，再批量接入页面

### Why chosen

- 能在不扩大范围的前提下统一核心页面体验
- 与现有 E2E 和前置 PR 收口方式兼容
- 最利于后续 PR-4 做回归补强与阶段收口

### Consequences

- PR-3 会同时碰页面文案、CTA 命名、局部状态组件和 targeted E2E
- Dashboard 会被纳入“有界 secondary surface”，但不会重开 IA 改版
- 若需要共享规则，只允许轻量 helper / 文案 contract，不允许演化成新框架

### Follow-ups

- PR-4 再收阶段级 baseline / closeout
- AIClip workflow 产品化继续留在后续 P1

---

## 5. In scope / Out of scope

### In scope

- `CreativeWorkbench`
- `CreativeDetail`
- `VersionPanel`
- `LoginPage`
- `AuthStatusPage`
- `AuthProvider`
- `AuthSessionHeader`
- `authErrorHandler`
- `Dashboard`（仅限文案与状态反馈）
- 对应 targeted E2E、test spec、execution breakdown 对齐

### Out of scope

- AIClip workflow 深度产品化
- Task 页面 IA / diagnostics surface 重构
- 新 diagnostics route / drawer 模型
- backend contract 扩展
- 全局 i18n 系统建设
- 大视觉改版

---

## 6. 目标 contract

## 6.1 文案与 CTA contract

### 语言策略

- 默认业务面以中文主文案为主
- 仅在必要技术语境下保留英文术语，例如：
  - AIClip
  - Shadow Compare（限 diagnostics surface）
- 页面标题、按钮、空态、错误提示应使用同一套业务语言，不混用“平台验收语气”和“产品语气”

### CTA 层级策略

- 每个核心页面 / 主卡片优先有 **一个清晰主 CTA**
- 次级动作应通过：
  - 次按钮
  - link button
  - drawer / diagnostics trigger
  表达，而不是与主 CTA 并列竞争
- 不再使用说明型 Alert 来代替 CTA 层级表达

### 说明文案下限

- 允许保留：
  - 异常态提醒
  - guardrail 提醒
  - diagnostics 可达性提醒
- 不允许保留：
  - 纯为解释“这个页面其实是干什么”的过渡态说明文案

## 6.2 四态 contract

对于核心页面 / 核心卡片，统一采用：

### Loading

- 数据仍在获取中
- 允许使用 `Spin` / loading prop / skeleton
- 不应提前渲染为 success 或 empty

### Success

- 数据成功获取，且页面可继续执行主动作
- 可以是正常数据，也可以是“有数据但为空字段”的业务成功态

### Empty

- 请求成功，但当前没有可展示业务数据
- Empty 文案应解释“当前没有什么”，而不是解释“请求为什么失败”

### Error

- 请求失败、关键数据不可用、或当前状态不能继续判断
- 必须明确提示失败，不得回退成默认值或空白态
- 若需要允许继续动作，必须说明“还能做什么”

---

## 7. Slice 划分（推荐 3 片）

## Slice A：文案基线与 CTA 层级统一

目标：

- 冻结核心页面语言策略、主 CTA 命名与说明文案下限

主要改动面：

- `frontend/src/features/auth/authErrorHandler.ts`
- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/features/auth/AuthStatusPage.tsx`
- `frontend/src/features/auth/AuthSessionHeader.tsx`
- `frontend/src/features/creative/components/VersionPanel.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`

完成标准：

- 中文主文案统一
- 修复坏文案与异常占位字符
- 主 CTA 唯一且命名稳定
- 纯解释页面职责的过渡型 Alert 明显减少

最小验证：

- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`

## Slice B：四态统一与关键页面状态反馈收口

目标：

- 把 auth / creative / dashboard 关键页面统一到明确四态语义

主要改动面：

- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/features/auth/AuthProvider.tsx`
- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/features/auth/AuthStatusPage.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- 如必要，补轻量 helper / 共享 state descriptor

完成标准：

- error 不伪装成 empty / default
- loading / empty / error / success 表达一致
- Dashboard 继续作为 diagnostics surface，但状态文案不再误导成主业务入口

最小验证：

- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- 如 Dashboard 状态断言发生变化，新增 `frontend/e2e/dashboard/dashboard-state.spec.ts`

## Slice C：验证与文档事实对齐

目标：

- 把 PR-3 的文案 / 四态 contract、验证口径、执行顺序同步到正式 docs

主要改动面：

- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`（如导航需要）
- `docs/governance/next-phase-pr3-copy-and-state-unification-plan.md`
- 受影响 E2E

完成标准：

- `docs/` 与 `.omx/plans/` 指向一致
- test spec 对 PR-3 明确要求 CTA / 四态一致
- PR-3 可以无歧义交给 `$ralph` 或 `$team` 执行

最小验证：

- 文档 UTF-8 回读无损
- `git diff --check`
- targeted E2E 全绿

---

## 8. 验证计划

PR-3 完成时至少应满足：

### Targeted verification

```powershell
cd E:\ais\mydw\frontend
$env:E2E_BASE_URL='http://127.0.0.1:4174'
npm run typecheck
npm run build
npm run test:e2e -- `
  e2e/auth-bootstrap/auth-bootstrap.spec.ts `
  e2e/auth-error-ux/auth-error-ux.spec.ts `
  e2e/auth-error-ux/auth-status-live-state.spec.ts `
  e2e/auth-shell/auth-shell.spec.ts `
  e2e/auth-routing/auth-routing.spec.ts `
  e2e/login/login.spec.ts `
  e2e/creative-main-entry/creative-main-entry.spec.ts `
  e2e/creative-workbench/creative-workbench.spec.ts `
  e2e/creative-review/creative-review.spec.ts `
  e2e/creative-version-panel/creative-version-panel.spec.ts `
  e2e/dashboard/dashboard-state.spec.ts
```

### 手工验证

1. 登录页、bootstrap、auth status shell 的 CTA 层级清晰，不靠解释性文案补偿
2. Workbench / Detail / VersionPanel 的主动作命名一致
3. 核心页面能明确区分 loading / success / empty / error
4. Dashboard 虽仍是 diagnostics surface，但不会被读成主业务入口
5. PR-2 的 diagnostics 二级入口边界未回退

### 通过标准

- 核心页面中文主文案稳定
- 主 CTA 与次动作层级清晰
- 四态显式、不误导
- 现有 Creative-first 主链路与 auth 主链路不回归
- 没有把 PR-3 做成新的 IA / 视觉改版

---

## 9. docs / tests 同步更新清单

PR-3 执行时，至少同步检查：

- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`
- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-error-ux/auth-status-live-state.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/dashboard/dashboard-state.spec.ts`

---

## 10. 执行建议

推荐执行方式：

> **按本文件先锁 PR-3，再按 Slice A → Slice B → Slice C 顺序推进。**

不建议：

- 把所有页面文案一次性大扫除后再回头补测试
- 先抽完整共享 UI framework，再等待页面迁移
- 在 PR-3 内重新打开 Dashboard / Task / diagnostics IA 改版

更具体地：

1. 先做 Slice A，锁语言策略与 CTA 层级
2. 再做 Slice B，统一四态 contract
3. 最后做 Slice C，把 test spec / breakdown / docs 收口

---

## 11. OMX 执行交接建议

推荐执行车道：

- **`$ralph`**：适合按 slice 顺序做实现 + 验证闭环
- **`$team`**：适合把 auth / creative / docs+E2E 分成并行 lane

推荐可用角色：

- `executor`：主实现
- `debugger`：状态回归 / query / conditional rendering 问题排查
- `verifier`：E2E 与验收证明
- `writer`：docs / test-spec / closeout 对齐
- `test-engineer`：新增/调整 targeted E2E
- `architect`：最终边界审查
- `critic`：计划/验收一致性挑战

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

- Slice A：`executor` + `test-engineer`
- Slice B：`executor` + `debugger` + `test-engineer`
- Slice C：`writer` + `verifier`
- 终验：`architect` / `verifier`

### Team staffing guidance

- lane 1：auth copy + state surfaces
- lane 2：creative copy + state surfaces
- lane 3：docs + E2E alignment
- final verification lane：typecheck / build / targeted E2E / closeout

一句话：

> **PR-3 适合“focused ralplan → slice-by-slice ralph execution”；只有在 auth / creative / docs+E2E 写面清晰拆开时，再考虑 `$team`。**
