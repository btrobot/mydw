# PR-1 Workbench 可管理性收口规划（Focused Ralplan）

> Version: 1.0.0 | Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Active PR-level planning artifact

> 本文件是对 `docs/governance/next-phase-execution-breakdown.md` 中 **PR-1：Workbench 可管理性收口** 的聚焦规划。  
> 它回答：**PR-1 具体做什么、不做什么、怎么切片、如何验证、为什么按这个方案推进。**

## 0. 在启动包中的角色

本文件不替代以下主线级文档，而是在它们已经成立的前提下，把 PR-1 收成可执行 plan：

- 总入口：`docs/current/next-phase-kickoff.md`
- 范围定义：`docs/governance/next-phase-prd.md`
- 验证规格：`docs/governance/next-phase-test-spec.md`
- 执行顺序：`docs/governance/next-phase-execution-breakdown.md`
- 现状问题来源：`docs/domains/creative/workbench-ui-issues.md`

使用规则：

1. 主线变化，先改 kickoff / PRD，不先改本文件
2. PR-1 范围或验证口径变化时，先改本文件，再同步 test spec / breakdown
3. 本文件只规划 PR-1，不把 PR-2（业务层 / 诊断层分层）和 PR-3（文案与四态统一）混进来

对应的 OMX 工作工件：

- `.omx/plans/prd-pr1-workbench-manageability.md`
- `.omx/plans/test-spec-pr1-workbench-manageability.md`
- `.omx/plans/slice-plan-pr1-workbench-manageability.md`

---

## 1. Grounded baseline / 当前基线

结合当前代码、测试与文档，PR-1 的起点不是“完全没有工作台能力”，而是：

### 已经具备的基础

- `CreativeWorkbench` 已经是默认业务入口
- 当前页面已经是 **table-first** workbench，而不是 browse-only 卡片墙
- 当前已经有：
  - 关键词搜索
  - 作品状态筛选
  - 发布准备状态筛选
  - `updated_at` 排序
  - 基于当前窗口数据的分页
- 现有 E2E 已覆盖：
  - 搜索
  - 状态筛选
  - pool 筛选
  - workbench → detail 主链路

对应事实入口：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

### 当前仍未收口的缺口

- 当前筛选/分页/排序状态 **不具备 URL 持久化与可分享性**
- 当前排序只有 `updated_at` 一条轴线，缺少“待处理优先 / 最近失败 / 版本未对齐优先”这类工作台视角
- 当前缺少高频 **preset views**，仍偏“手工组合筛选”
- 当前“可管理性边界”还没被明确锁成正式 truth，后续容易继续漂移
- 当前窗口说明仍然隐含“先用本地窗口顶住，未来可能再接服务端检索”，但缺少明确的阈值和升级条件

### 明确不在 PR-1 解决的事

- 不做默认业务层 / 高级诊断层分层（留给 PR-2）
- 不做文案体系与四态统一（留给 PR-3）
- 不做大视觉重设计
- 不直接开启 remote / backend 新大功能线

---

## 2. 一句话定义

> **PR-1 的任务，不是发明一个全新的 Workbench，而是把现有 table-first workbench 收成“可定位、可恢复、可分享、可扩展”的日常工作台。**

---

## 3. RALPLAN-DR 摘要

### 3.1 Principles / 原则

1. **先稳工作面，不扩功能面**：优先收口管理能力，不借机扩新业务域
2. **先锁日常使用路径，再考虑更大规模架构**：先解决高频摩擦，再决定是否升级服务端检索
3. **small diff / reversible**：每个 slice 都要能独立验证和回滚
4. **不越过 PR 边界**：PR-1 不吞并 PR-2、PR-3 的问题
5. **现有 truth 优先**：复用当前 workbench 结构和现有 E2E 资产，不推倒重来

### 3.2 Decision drivers / 主要决策驱动

1. **日常可定位性**：用户能否快速找出待处理内容
2. **状态可恢复性**：刷新、分享链接、返回页面后，工作上下文能否保住
3. **执行风险可控性**：能否在不扩大主线的前提下完成验证闭环

---

## 4. Viable options / 备选方案

### 方案 A：一次做完整 server-side workbench 检索面

内容：

- 扩后端 creatives list contract
- 支持服务端搜索 / 筛选 / 排序 / 分页
- 前端同步引入完整 URL 状态与 preset 视图

优点：

- 理论上最完整
- 可以提前解决大规模列表问题

缺点：

- 需要扩 backend contract，扩大 PR 面
- 回归成本更高
- 当前成功标准只要求 50+ creative 可管理，并不需要一步到位做大规模检索平台

结论：

> **本轮不选。** 这会把 PR-1 从“稳定化”推成“新一轮功能扩张”。

### 方案 B：只做轻量 UI polish

内容：

- 小幅调整筛选 UI
- 微调默认排序说明
- 不引入 URL 状态、不引入 preset、不补强验证

优点：

- diff 小
- 实现快

缺点：

- 解决不了“刷新后丢上下文”“链接不可分享”“高频队列不显式”这些核心管理问题
- 容易做成“看起来更好一点，但仍然不够像真正工作台”

结论：

> **本轮不选。** 它不足以支撑 PRD 里的“日常可管理能力”目标。

### 方案 C：分阶段收口现有 table-first baseline（推荐）

内容：

- 以现有 `CreativeWorkbench` 为基础
- 不先扩 backend contract
- 先补：
  - URL query params 持久化
  - 明确排序模型
  - 高频 preset views
  - 当前窗口规模 guardrail
  - 对应 E2E / docs 真相

优点：

- 与当前代码和测试基线连续
- 最符合 PR-1 的稳定化性质
- 可以把“工作台可管理性”收实，而不会提前把主线扩大成搜索平台改造

缺点：

- 仍保留“未来可能升级到服务端检索”的后续空间
- 若实际列表很快超过当前窗口上限，需要后续补一轮 contract 设计

结论：

> **推荐方案。**

---

## 5. ADR / 决策记录

### Decision

选择 **方案 C：分阶段收口现有 table-first baseline** 作为 PR-1 的执行方案。

### Drivers

- 目标是收口 manageability，不是扩平台能力
- 当前代码已经具备搜索 / 筛选 / 排序 / 分页的基础形态
- 当前主线强调 small diff、reviewable、可验证

### Alternatives considered

- 方案 A：一次做完整 server-side workbench 检索面
- 方案 B：只做轻量 UI polish

### Why chosen

- 能把“日常工作台”真正收实
- 不需要提前打开更大的 backend / contract 变更面
- 与现有 kickoff / PRD / test spec / breakdown 完整对齐

### Consequences

- PR-1 将聚焦于前端 manageability baseline
- 服务端检索扩展不进入本轮默认范围
- 需要明确一个“何时升级到 server-side 检索”的阈值

### Follow-ups

- 若实际 creative 数量或使用反馈证明 200-item window 不够，再新开后续 planning
- PR-2 再收口业务层 / 诊断层边界
- PR-3 再统一文案与四态

---

## 6. In scope / Out of scope

### In scope

- `CreativeWorkbench` 的管理能力收口
- 当前筛选 / 排序 / 分页模型的显式化
- URL query params 与返回可恢复性
- 高频 preset views
- 当前窗口模式的阈值说明与 guardrail
- 对应 targeted E2E / docs 对齐

### Out of scope

- `CreativeDetail` 的默认业务层 / 诊断层重切
- 大规模视觉重做
- 后端 creatives list API 扩展为完整检索 contract
- AIClip 深度产品化
- 全局文案体系统一

---

## 7. 关键设计决策

### 7.1 Query params 应成为 PR-1 的一部分

原因：

- workbench 是“工作面”，不是一次性浏览页
- 用户刷新、复制链接、从 detail 返回时，应该尽量保住筛选上下文

建议保留的 URL 状态：

- `keyword`
- `status`
- `poolState`
- `sort`
- `page`
- `pageSize`
- `preset`（如启用）

### 7.2 PR-1 要显式支持“工作台排序”，不只保留时间排序

建议排序集：

- `updated_desc`：最近更新（默认）
- `updated_asc`：最早更新
- `attention_desc`：待处理优先
- `failed_desc`：最近失败优先

其中：

- `attention_desc` 只基于 **当前已存在字段** 计算，例如：
  - `WAITING_REVIEW`
  - `REWORK_REQUIRED`
  - `generation_error_msg`
  - `poolState === version_mismatch`

不要求引入新的后端字段。

### 7.3 PR-1 应增加 preset views，但只做高频最小集

建议最小集：

- `all`：全部
- `waiting_review`：待审核
- `needs_rework`：需返工
- `recent_failures`：最近失败
- `version_mismatch`：版本未对齐

不建议在 PR-1 直接引入：

- 过多业务口径 preset
- 需要额外领域判断的“可发布”“待我处理”等复杂队列

### 7.4 保留当前 window-based 模式，但加清晰 guardrail

PR-1 默认继续使用当前 window-based 数据模式：

- creative list：当前窗口
- 本地筛选 / 本地排序 / 本地分页

但必须补一条清晰规则：

> **当 workbench 日常使用已稳定超过当前窗口，或“找不到但其实存在”的问题开始频繁出现时，再进入后续 server-side 检索 planning。**

---

## 8. Slice 划分（推荐 3 个）

## Slice A：管理模型定稿与 URL 状态收口

目标：

- 锁定 query params 模型
- 锁定支持的筛选项 / 排序项 / 默认值
- 保证页面刷新、复制链接、返回页面时状态可恢复

主要改动面：

- `CreativeWorkbench.tsx`
- workbench 相关 query params / state

验收：

- 指定筛选和排序后，刷新页面仍保留当前视图
- 从 detail 返回 workbench 时，当前视图不丢
- 至少一条 E2E 覆盖状态恢复链路

最小验证：

- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- 手工验证：筛选后进入详情再返回

## Slice B：排序与 preset views 收口

目标：

- 增加工作台视角排序
- 增加高频 preset views
- 让“待处理内容可快速定位”成为显式能力

主要改动面：

- workbench toolbar / search form / table request
- attention / failure / mismatch 的前端计算逻辑

验收：

- 用户无需手工组合多个条件，也能直接进入高频工作队列
- `attention_desc` / `failed_desc` 的行为可解释、可测试

最小验证：

- targeted E2E：preset 视图 + 排序结果
- 必要手工链路：切换 preset 后进入详情再返回

## Slice C：规模 guardrail、文档与回归收口

目标：

- 明确当前 window-based 模式的适用边界
- 补齐 docs / tests 对 manageability baseline 的保护
- 确认 PR-1 完成后不需要立刻再开一次 search architecture cleanup

主要改动面：

- `docs/governance/next-phase-test-spec.md`（若验证面扩大）
- `docs/governance/next-phase-execution-breakdown.md`（若 PR-1 验收表述需要收紧）
- workbench E2E

验收：

- PR-1 的 manageability 范围、限制、验证都变得显式
- 后续不会再把“列表可管理性”当成隐性口头共识

最小验证：

- workbench targeted E2E
- 相关 doc truth tests

---

## 9. 验证计划

PR-1 完成时至少应满足：

### 自动化

- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- 受影响时补跑：
  - `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`
  - `frontend/e2e/creative-review/creative-review.spec.ts`

### 手工

1. 从 `/` 进入 `CreativeWorkbench`
2. 切换 preset 或筛选条件
3. 修改排序
4. 进入 detail
5. 返回 workbench
6. 确认当前工作上下文仍可恢复

### 通过标准

- workbench 不再只是“能筛一下”的列表，而是具备明确工作台视角
- 刷新 / 返回 / 分享链接不再轻易打断工作上下文
- 不引入 PR-2 / PR-3 级别的范围扩张

---

## 10. docs / tests 同步更新清单

PR-1 执行时，至少同步检查：

- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- 如新增高可见度行为说明，再更新：
  - `docs/current/next-phase-kickoff.md`
  - `docs/domains/creative/workbench-ui-issues.md`

---

## 11. 执行建议

推荐执行方式：

> **先按本文件把 PR-1 再切成 3 个 slices，再逐 slice 执行。**

更具体地：

- 不建议直接开一个“大而全的 PR-1 实现”
- 也不建议重新回到主线级大规划

推荐节奏：

1. 先确认 Slice A
2. 执行 + 验证 Slice A
3. 再做 Slice B
4. 最后做 Slice C 收口

如果使用 OMX：

- **ralplan**：用于本文件这种 PR 级聚焦规划
- **ralph**：更适合每个已锁定 slice 的实现 + 验证闭环

一句话：

> **PR-1 适合“focused ralplan → slice-by-slice execution”，而不是“整条主线重规划”或“跳过规划直接大干”。**
