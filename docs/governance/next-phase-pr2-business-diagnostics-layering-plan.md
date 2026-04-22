# PR-2 业务层 / 诊断层分层规划（Focused Ralplan）

> Version: 1.0.0 | Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Approved PR-level planning artifact

> 本文件是对 `docs/governance/next-phase-execution-breakdown.md` 中 **PR-2：业务层 / 诊断层分层** 的聚焦规划。  
> 它回答：**PR-2 具体要把哪些信息留在默认业务层、哪些信息下沉到诊断层、如何切片、如何验证、为什么按这个方案推进。**

## 0. 在启动包中的角色

本文件不替代以下主线级文档，而是在它们已经成立的前提下，把 PR-2 收成可执行 plan：

- 总入口：`docs/current/next-phase-kickoff.md`
- 范围定义：`docs/governance/next-phase-prd.md`
- 验证规格：`docs/governance/next-phase-test-spec.md`
- 执行顺序：`docs/governance/next-phase-execution-breakdown.md`
- 现状问题来源：`docs/domains/creative/workbench-ui-issues.md`
- 已完成前置 PR：`docs/governance/inventory/pr1-workbench-manageability-closeout.md`

使用规则：

1. 主线变化，先改 kickoff / PRD，不先改本文件
2. PR-2 范围或验证口径变化时，先改本文件，再同步 test spec / breakdown
3. 本文件只规划 PR-2，不把 PR-3（文案与四态统一）或新的后端检索扩展混进来

对应的 OMX 工作工件：

- `.omx/plans/prd-pr2-business-diagnostics-layering.md`
- `.omx/plans/test-spec-pr2-business-diagnostics-layering.md`
- `.omx/plans/slice-plan-pr2-business-diagnostics-layering.md`

---

## 1. Grounded baseline / 当前基线

结合当前代码、现有 E2E 与已落盘文档，PR-2 的起点不是“完全没有分层意识”，而是“已经知道要分层，但默认工作面仍然混有太多诊断信号”。

### 已经成立的基础

- PR-1 已完成，`CreativeWorkbench` 的搜索 / 筛选 / 排序 / URL 恢复能力已经收口
- `CreativeDetail` 已经出现“高级诊断”区块，说明系统并不是没有诊断容器
- `task diagnostics` 已经是独立页面，说明执行排障能力已有外部承接面
- 现有 E2E 已覆盖：
  - workbench → detail 主链路
  - review / publish-pool 相关行为
  - cutover shadow diff
  - task diagnostics 跳转

### 当前仍未收口的缺口

- `CreativeWorkbench` 首屏仍直接暴露：
  - `scheduler mode`
  - `effective mode`
  - `runtime status`
  - `shadow read`
  - `kill switch`
  - 运行摘要 / 发布池摘要 warning
- `CreativeDetail` 默认业务页虽然已经加了“高级诊断”卡片，但默认视图仍混入：
  - 入口模式 + Shadow Compare 等运行语义
  - 执行记录入口
  - 发布与调度诊断 / 发布池历史 / Cutover 差异等重诊断区块
- 当前主路径仍带“验收台 / 排障台”气质，而不是稳定的业务工作面

### 明确不在 PR-2 解决的事

- 不扩 backend / server-side search contract
- 不做 PR-3 级别的全局文案统一与四态收口
- 不做大视觉重设计
- 不把 AIClip 深度产品化混入本轮

---

## 2. 一句话定义

> **PR-2 的任务，不是删除诊断能力，而是把诊断能力从默认业务面移到显式、按需打开的高级诊断层。**

---

## 3. RALPLAN-DR 摘要

### 3.1 Principles / 原则

1. **默认先服务业务操作**：用户进入 workbench / detail 时，先看到业务状态、主判断、主操作
2. **诊断只能下沉，不能消失**：scheduler / pool / shadow / kill-switch 仍要保留可达入口
3. **诊断入口必须显式且低摩擦**：不能把诊断信息藏到不可发现的位置；应做到“一次显式点击可达”
4. **优先前端分层，不引入新后端范围**：本轮只重组展示层与入口，不扩大 contract 面
5. **small diff / reversible**：workbench、detail、E2E 按 slice 顺序推进，每一片都可独立验证

### 3.2 Decision drivers / 主要决策驱动

1. **默认认知负担是否下降**：日常创作/审核用户进入页面时，是否先看到该做什么
2. **研发排障能力是否仍完整可达**：研发是否仍能拿到 pool / shadow / scheduler / task 事实
3. **回归成本是否可控**：能否在不重写信息架构的前提下完成真相收口

### 3.3 Viable options / 备选方案

#### 方案 A：保留当前混合视图，只做文案弱化

内容：

- 保留当前 workbench 顶部诊断标签与 warning
- 保留 detail 页现有混合布局
- 通过更轻的说明文案告诉用户“这些只是辅助信息”

优点：

- 改动最小
- E2E 改动可能较少

缺点：

- 结构问题仍在，认知噪音并不会真正下降
- 页面依旧带明显“诊断台”气质
- 后续 PR-3 很容易继续在过渡结构上打补丁

结论：

> **本轮不选。** 这会把“分层”退化成“解释型降噪”。

#### 方案 B：把诊断信息从默认页面直接删掉

内容：

- workbench / detail 默认页完全不显示运行诊断
- 依赖任务页或未来专门诊断页承接全部排障信息

优点：

- 默认业务面最干净
- 视觉上最像纯业务产品面

缺点：

- 研发排障链路会被切断
- 现有 publish-pool / cutover / task 相关事实缺少近场入口
- 一旦线上出现异常，定位成本会上升

结论：

> **本轮不选。** 这会把“分层”做成“丢能力”。

#### 方案 C：默认业务层 + 显式高级诊断层（推荐）

内容：

- workbench 默认页只保留业务状态、业务统计、主操作
- detail 默认页只保留业务概览、作品输入、当前版本、审核结论、主 CTA
- scheduler / pool / shadow / kill-switch / cutover / task diagnostics 统一下沉到显式“高级诊断”入口
- 诊断入口保留一跳可达、可测试、可深链的打开方式

优点：

- 同时降低默认噪音并保留排障能力
- 与现有 `CreativeDetail` 的“高级诊断”雏形连续
- 最符合 PRD 与 `workbench-ui-issues` 的问题定义

缺点：

- 需要迁移现有 E2E 断言位置
- 需要对“哪些字段算业务事实、哪些字段算诊断事实”做一次明确划线

结论：

> **推荐方案。**

### 3.4 Architect review / 架构复核

最强反方观点：

> 对内部系统来说，业务与诊断混在一起反而更高效；把诊断下沉会增加点击次数，削弱运营/研发联合作业速度。

真实张力：

- **默认干净** vs **近场排障效率**
- **减少首屏噪音** vs **避免把关键异常藏起来**

综合结论：

- 不做新页面拆分，不新开大 route
- 在原页面内保留 **显式 secondary entry**
- 诊断层应满足：
  - 默认关闭
  - 一次点击可达
  - 对异常态可保留轻量提醒，但提醒不直接展开完整诊断正文
  - 若实现成本可控，支持 URL 驱动的打开状态，便于 deep-link 与 E2E

### 3.5 Critic verdict / 批判性复核

批判要点：

1. 必须明确哪些内容留在业务层，不能只说“下沉诊断”
2. 必须锁定“显式入口”的最小标准，否则容易做成隐藏式信息
3. 必须把验证从“还能看到诊断”升级为“默认看不到、显式操作后可看到”
4. 必须防止把 PR-2 做成 PR-3 的文案大清洗

最终结论：

> **APPROVE**  
> 以“默认业务层 + 显式高级诊断层”为 PR-2 的执行方案；验收重点改为“默认隐藏 + 明确可达 + 主链路不回归”。

---

## 4. ADR / 决策记录

### Decision

选择 **方案 C：默认业务层 + 显式高级诊断层** 作为 PR-2 的执行方案。

### Drivers

- 当前默认页面的主要问题是信息混层，而不是缺少诊断能力
- 现有代码已经具备诊断事实与任务排障链路，不需要另起后端工程
- PR-2 的目标是“产品面收口”，不是“排障能力扩张”

### Alternatives considered

- 方案 A：保留混合视图，只做文案弱化
- 方案 B：直接删掉默认页上的诊断信息

### Why chosen

- 能同时满足“默认好用”和“排障可达”
- 能延续现有 detail 页的高级诊断雏形，不引入大改版
- 与下一阶段主线、PRD、现有 domain 分析保持一致

### Consequences

- 默认业务页上不再展示运行模式、shadow、kill-switch、raw diff、pool item id 等诊断事实
- 诊断内容会集中到显式入口内，E2E 需要迁移相应断言
- PR-2 完成后，PR-3 才有更稳定的业务页面结构可继续统一文案与四态

### Follow-ups

- 若后续 diagnostics 体量继续扩大，再考虑独立 diagnostics page / tab 信息架构
- PR-3 再统一主 CTA、提示文案与四态语义

---

## 5. In scope / Out of scope

### In scope

- `CreativeWorkbench` 默认业务层与诊断入口重组
- `CreativeDetail` 默认业务层与高级诊断层重组
- task diagnostics / publish diagnostics / publish pool / cutover diff 的入口整理
- 对应 targeted E2E、test spec、execution breakdown 对齐

### Out of scope

- 新建后端 API 或扩展诊断 contract
- 新建完整 diagnostics 子系统
- 全局 CTA / 文案 / 四态统一
- 大范围导航或视觉系统改版

---

## 6. 目标分层模型

## 6.1 Workbench：默认业务层

默认页保留：

- workbench 标题与当前窗口 guardrail
- 业务统计（总量、待处理、需返工、可发布等）
- 搜索 / 筛选 / 排序 / preset
- 表格列表
- 进入 detail 的主操作

默认页不再直接展开：

- scheduler mode
- effective mode
- runtime status
- shadow read
- kill switch
- 完整运行 warning 正文

允许保留的最小异常提示：

- 当运行诊断加载失败时，可保留一条 **不展开正文的轻量提醒**
- 提醒必须把用户导向“查看运行诊断”，而不是在首屏直接承载完整诊断叙事

## 6.2 Workbench：高级诊断层

高级诊断层承接：

- 发布运行摘要
- 调度模式 / 生效模式 / runtime status
- shadow read / kill switch
- 需要时的重试动作

入口要求：

- 默认关闭
- 一次显式点击可达
- 推荐支持 URL 可恢复的打开状态，但不要求新 route

## 6.3 Detail：默认业务层

默认页保留：

- 业务概览
- 作品输入
- 合成准备判断
- 当前版本
- 当前有效审核结论
- 主要 CTA：保存输入 / 提交合成 / 审核当前版本 / 打开 AIClip

默认页可保留但应降为业务语义的内容：

- 当前生成失败记录
- 是否满足合成前置条件
- 与当前作品直接相关的执行入口

默认页不再承担：

- 调度模式 / 生效模式 / shadow read / kill switch
- pool item id / 最近失效记录
- cutover diff 正文
- 发布池历史详情

## 6.4 Detail：高级诊断层

高级诊断层承接：

- 发布与调度诊断
- 发布池历史
- Cutover 差异
- 执行记录 / 跳转任务管理

要求：

- 与业务层物理分区明确
- 默认不抢占业务首屏
- 用户知道“当我要排障时去哪看”

---

## 7. Slice 划分（推荐 3 片）

## Slice A：Workbench 默认业务层收束

目标：

- 把 workbench 首屏从“业务 + 运行摘要混排”收成“业务主面 + 显式诊断入口”

主要改动面：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

验收：

- 首屏不再直接展示 scheduler / effective mode / runtime / shadow / kill-switch 标签
- 运行相关信息通过显式 diagnostics entry 打开
- 业务列表、筛选、guardrail、进入 detail 主链路不回归

## Slice B：Detail 默认业务层 / 高级诊断层分层

目标：

- 把 detail 页的业务输入、审核、版本信息和运行诊断彻底分区

主要改动面：

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/publish-pool/publish-pool.spec.ts`
- `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`

验收：

- 默认 detail 先展示业务概览 / 输入 / 当前版本 / 当前审核结论
- 发布池 / cutover / scheduler / task diagnostics 收束到高级诊断层
- 执行记录仍可一跳进入任务页，不丢 returnTo / taskId 主链路

## Slice C：验证与文档事实对齐

目标：

- 把 PR-2 的分层边界锁进正式 planning / test-spec / execution docs
- 补齐“默认隐藏 + 显式可达”的验证口径

主要改动面：

- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`
- 必要的 targeted E2E

验收：

- planning artifacts、test spec、execution breakdown 对齐
- E2E 证明默认业务层不再承担过量诊断信息
- 研发 diagnostics 入口仍然存在且稳定

---

## 8. 验证计划

PR-2 完成时至少应满足：

### Targeted E2E

```powershell
cd E:\ais\mydw\frontend
$env:E2E_BASE_URL='http://127.0.0.1:4174'
npm run test:e2e -- `
  e2e/creative-workbench/creative-workbench.spec.ts `
  e2e/creative-review/creative-review.spec.ts `
  e2e/publish-pool/publish-pool.spec.ts `
  e2e/publish-cutover/publish-cutover.spec.ts `
  e2e/task-diagnostics/task-diagnostics.spec.ts
```

### Merge gate baseline

继续满足当前主线 baseline：

- `backend/tests/test_creative_workflow_contract.py`
- `backend/tests/test_openapi_contract_parity.py`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`

### 手工验证

1. 从 `/` 进入 `CreativeWorkbench`
2. 首屏先看到业务统计、筛选、列表，而不是运行模式/诊断标签
3. 进入 detail 后，先看到业务概览 / 输入 / 当前版本 / 当前审核结论
4. 当需要排障时，用户能通过显式入口打开高级诊断并拿到 pool / cutover / task facts
5. 从 diagnostics 跳到任务页再返回，主链路上下文仍正确

### 通过标准

- 默认业务层不再承担过量诊断信息
- diagnostics 入口显式存在，且一次操作可达
- 关键返回链路与 task diagnostics 链路不回归
- 没有把 PR-2 做成 PR-3 级别的全局文案大修

---

## 9. docs / tests 同步更新清单

PR-2 执行时，至少同步检查：

- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/publish-pool/publish-pool.spec.ts`
- `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`

---

## 10. 执行建议

推荐执行方式：

> **按本文件先锁 PR-2，再按 Slice A → Slice B → Slice C 顺序推进。**

不建议：

- 直接把 workbench 和 detail 一次性大改完再统一验证
- 在 PR-2 内同时展开 PR-3 级别的文案/四态全局清洗

更具体地：

1. 先做 Slice A，确认 workbench diagnostics entry 模型
2. 再做 Slice B，把 detail 的默认业务层和高级诊断层真正拉开
3. 最后做 Slice C，把 test spec / breakdown / E2E 收口

---

## 11. OMX 执行交接建议

推荐执行车道：

- **`$ralph`**：适合按 slice 顺序做实现 + 验证闭环
- **`$team`**：只有在明确拆成独立写入面时再考虑，例如
  - lane 1：`CreativeWorkbench`
  - lane 2：`CreativeDetail`
  - lane 3：E2E / docs 对齐

推荐可用角色：

- `executor`：主实现
- `debugger`：链路回归 / returnTo / query-param 问题排查
- `verifier`：E2E 与验收证明
- `writer`：docs / test-spec / closeout 对齐

一句话：

> **PR-2 适合“focused ralplan → slice-by-slice ralph execution”，而不是跳过分层决策直接大改页面。**
