# PR-3 Slice B 四态统一与关键页面状态反馈收口件

> Version: 1.0.0  
> Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Recorded slice closeout

> 目的：把 `PR-3 / Slice B：四态统一与关键页面状态反馈收口` 的实际交付、当前真相、验证结果与剩余风险落成一份正式收口件。  
> 这份文档回答的不是“Slice B 原本想做什么”，而是：*Slice B 最终实际做成了什么、没有做什么、现在系统应该如何理解、下一步应该从哪里继续。*

---

## 1. 一句话总结

> Slice B 已把 `Dashboard / AuthStatusPage / CreativeWorkbench / CreativeDetail` 的关键状态反馈，从“局部显式、局部回退、局部靠默认值兜底”的过渡态，收口成“loading / empty / error / success 四态明确、失败不伪装、诊断面不误导”的当前真相。

---

## 2. 本 Slice 原始目标

- 统一 auth / creative / dashboard 关键页面的四态表达
- 避免把 error 伪装成 empty / default / placeholder
- 保持 `Dashboard` 继续是 diagnostics surface，而不是重新退回主业务入口
- 在不引入新 IA / 新后端 contract / 新依赖的前提下，补齐状态语义与测试证据

关联规划：

- `docs/governance/next-phase-pr3-copy-and-state-unification-plan.md`
- `.omx/plans/prd-pr3-copy-and-state-unification.md`
- `.omx/plans/test-spec-pr3-copy-and-state-unification.md`
- `.omx/plans/slice-plan-pr3-copy-and-state-unification.md`

---

## 3. 实际交付结果

### 3.1 已完成

- **Dashboard 四态显式化**
  - 任务统计区显式区分：
    - loading：`dashboard-task-stats-loading`
    - empty：`dashboard-task-stats-empty`
    - error：`dashboard-task-stats-error`
    - success：`dashboard-task-stats-success`
  - 发布器状态区显式区分：
    - loading：`dashboard-publish-status-loading`
    - error：`dashboard-publish-status-error`
    - success：`dashboard-publish-status-success`
  - 系统资源区不再用 `--` 这类占位回退掩盖失败，而是显式区分：
    - loading：`dashboard-system-stats-loading`
    - error：`dashboard-system-stats-error`
    - success：`dashboard-system-stats-success`
  - 系统日志区显式区分：
    - loading：`dashboard-logs-loading`
    - empty：`dashboard-logs-empty`
    - error：`dashboard-logs-error`
    - success：`dashboard-logs-success`

- **系统 hooks 事实语义收紧**
  - `frontend/src/hooks/useSystem.ts`
    - `useSystemStats` / `useSystemLogs` / `useSystemConfig` 改为 `throwOnError: true`
    - `retry: false`
  - `useSystemLogs` 不再把请求失败静默吞掉并回落成空日志，而是让 UI 显式进入 error state
  - 非法日志响应格式不再默认当成 empty，而是直接视为错误

- **Auth shell live state 可验证化**
  - `AuthStatusPage` 增加：
    - `auth-status-live-loading`
    - `auth-status-live-error`
  - 现在 auth shell 的 live refresh loading / error 是显式可断言的，而不只是“主告警 + 隐含刷新过程”

- **Creative 页面 loading state 可验证化**
  - `CreativeWorkbench` 增加 `creative-workbench-loading`
  - `CreativeDetail` 增加 `creative-detail-loading`
  - 保持既有 error / empty 分支不变，同时补齐首屏 loading 态的自动化可见性

- **新增 targeted regression**
  - `frontend/e2e/dashboard/dashboard-state.spec.ts`
    - 锁住 Dashboard 在 success/empty 情况下仍是 diagnostics surface
    - 锁住 Dashboard 在多路请求失败时进入显式 error，而不是 fallback default
  - `frontend/e2e/auth-error-ux/auth-status-live-state.spec.ts`
    - 锁住 auth status live refresh 失败时出现显式 live error

### 3.2 明确没做

- **没做 Slice A 的文案统一收口**
  - 本轮不是主文案统一盘，不负责把 PR-3 全量中文文案策略收完

- **没做 Slice C 的全量 docs 同步**
  - 本文只记录 Slice B 收口事实
  - `next-phase-test-spec / execution-breakdown / README` 的全面同步，属于 PR-3 文档对齐层继续工作

- **没做新 shared state abstraction**
  - 规划里提过“如必要可补轻量 helper / shared state descriptor”
  - 本轮判断没有必要为四态再引入新抽象，直接在现有页面上收口更小、更稳

- **没做新的 route / IA / diagnostics page**
  - Dashboard 仍是原有 diagnostics surface
  - 没新增 diagnostics 独立页，也没把 PR-2 边界重新打开

### 3.3 与原规划相比的偏差

- 偏差 1：**Slice B 主要聚焦状态 contract 与 testability，而不是视觉层重构**
  - 原因：当前问题的关键不是“缺一个新组件体系”，而是失败态被吞、空态与错误态混淆、自动化无法断言

- 偏差 2：**通过收紧 hooks 错误语义来保证 UI 真相**
  - 原因：只在页面层加判断还不够；如果 query hook 继续把失败吞成空数据，Dashboard 仍然会被误导

---

## 4. 当前系统真相发生了什么变化

### 4.1 Dashboard 当前真相

- `Dashboard` 仍然是运行态 / 发布态 / 日志态的 **diagnostics surface**
- 但现在不再允许以下误导：
  - 请求失败却显示成 `--`
  - 请求失败却显示成“暂无日志”
  - 请求失败却看起来像普通空闲 / 默认态
- 当前可接受的状态语义是：
  - loading：正在获取事实
  - empty：请求成功，但当前没有数据
  - error：请求失败，事实不可判断
  - success：请求成功，数据可读、动作可继续

### 4.2 Auth shell 当前真相

- auth status shell 的主告警仍然负责描述当前授权状态
- live refresh 现在是显式状态，而不是隐式背景过程
- 因此“主状态告警”和“状态刷新失败”被区分成两个层次：
  - 主状态：当前账号/设备/授权是否可继续
  - live state：实时刷新是否成功

### 4.3 Creative 页面当前真相

- `CreativeWorkbench` / `CreativeDetail` 原本已有 explicit error / empty 分支
- 本次收口补齐了 loading state testability
- 当前这两页已具备：
  - loading 可见
  - error 可见
  - empty 可见
  - success 可见

### 4.4 哪些旧理解不再成立

- “系统日志接口失败也可以先按暂无日志显示” —— **不再成立**
- “Dashboard 的系统统计失败可以先回退成 `--` 占位” —— **不再成立**
- “auth status live refresh 失败不必单独表达” —— **不再成立**

---

## 5. 验证总结

### 5.1 自动化验证

- `frontend` `npm run typecheck` —— **PASS**
- `frontend` `npm run build` —— **PASS**
- `frontend` targeted Playwright suite —— **PASS（39 passed）**
  - `e2e/auth-error-ux/auth-error-ux.spec.ts`
  - `e2e/auth-error-ux/auth-status-live-state.spec.ts`
  - `e2e/auth-shell/auth-shell.spec.ts`
  - `e2e/auth-routing/auth-routing.spec.ts`
  - `e2e/creative-main-entry/creative-main-entry.spec.ts`
  - `e2e/creative-workbench/creative-workbench.spec.ts`
  - `e2e/creative-review/creative-review.spec.ts`
  - `e2e/dashboard/dashboard-state.spec.ts`

### 5.2 结构/架构复核

- 结论：**通过**
- 复核口径：
  - Dashboard 仍是 diagnostics surface
  - PR-2 的业务层 / 诊断层边界未回退
  - 没把 Slice B 扩成新的 IA / 视觉改版

### 5.3 Slice B 对应提交

- `559cec6` — `Make runtime state failures explicit before they mislead operators`

---

## 6. 影响文件

代码：

- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/hooks/useSystem.ts`
- `frontend/src/features/auth/AuthStatusPage.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`

测试：

- `frontend/e2e/dashboard/dashboard-state.spec.ts`
- `frontend/e2e/auth-error-ux/auth-status-live-state.spec.ts`

---

## 7. Remaining risks / Residual risks

1. **PR-3 仍未完成整体验收**
   - 影响：Slice B 已把状态 contract 收住，但 PR-3 的文案统一与 docs 全面对齐还未全部结束
   - 当前处理：后续继续进入 Slice C / PR-3 收口

2. **四态统一仍主要是页面内收口，不是共享设计系统级 contract**
   - 影响：未来若更多页面加入，仍可能出现新的表达偏移
   - 当前处理：本轮优先选择小而稳的页面内收口；是否抽公共状态组件，留待后续再评估

3. **未跑全量前端 E2E 矩阵**
   - 影响：本轮证据以 PR-3 相关 targeted suites 为主
   - 当前处理：保留到更大阶段性 baseline / PR-4 收口再看是否扩大验证范围

---

## 8. Backlog handoff

建议后续继续回答的问题：

- 哪些 PR-3 文案事实还未同步进正式 docs？
- 是否需要把“四态 contract”进一步提升成共享页面规范？
- PR-3 在完成 Slice C 后，是否形成整 PR closeout，而不仅是 Slice-level closeout？

推荐下一入口：

> **PR-3 Slice C：验证与文档事实对齐**

原因：

- Slice B 的实现与回归证据已经形成
- 下一步最自然的工作不是继续扩状态逻辑，而是把当前真相同步到正式 docs 和阶段执行视图

---

## 9. Exit decision / Slice B 退出结论

> **PR-3 Slice B 可以视为已正式收口。**  
> 它已经把 Dashboard / auth live state / creative loading state 的四态契约、失败语义、自动化验证与当前真相都接住了；后续不应再把 Slice B 当成“顺手补几个状态判断”的开放工作，而应基于这份收口件继续推进 PR-3 的文档对齐与整 PR 收口。
