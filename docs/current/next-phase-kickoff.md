# 下一阶段启动包（Next-Phase Kickoff）

> Version: 1.2.0 | Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把本轮收口结果变成一个新的开发起点，让后续开发者或 agent 不必重新做一遍盘点，就能知道现在从哪里开始。
>
> **本文件是“下一阶段启动包”的总入口。**  
> 阶段切换先看 `docs/governance/phase-transition-checklist.md`，确认能不能切；  
> 真正开始执行时，再从本文件进入 `next-phase PRD`、`next-phase test spec`、`next-phase execution breakdown`。

> 三句话记住阶段切换顺序：  
> 1. **先收尾到“能做决定”**，不是先把所有文档全补完。  
> 2. **再选线到“只剩一条主线”**，不是让 backlog 继续无限并列。  
> 3. **再补文档到“这条主线不再被误导”**，也就是只定向补齐这条主线依赖的 current truth。

## 0. 这份启动包怎么用

建议按下面顺序使用，而不是四份文档分散阅读：

1. 先用 `docs/governance/phase-transition-checklist.md` 确认 **Part A 当前阶段已收口**、**Part B 下一阶段可启动**
2. 再读本文件，确认当前基线、边界、主线和 backlog 入口
3. 进入 `docs/governance/next-phase-prd.md`，锁定“为什么做 / 做什么 / 什么不做 / 何为完成”
4. 进入 `docs/governance/next-phase-test-spec.md`，锁定“如何证明本阶段完成”
5. 最后进入 `docs/governance/next-phase-execution-breakdown.md`，按 PR sequence 执行

执行中的维护规则：

- **主线变化**：先改 kickoff + PRD，再决定是否调整 test spec / breakdown
- **验证变化**：先改 test spec，再同步 kickoff / breakdown
- **执行顺序变化**：先改 breakdown，再确认 PRD / test spec 是否仍成立
- **阶段完成**：回到 `phase-transition-checklist` 做下一轮 Part A 收口

## 1. 先说结论

下一阶段建议定义为：

> **Creative-first 稳定化 / UI-UX 收口主线**

它不是再开一条全新业务线，而是把已经跑通的 Creative-first 系统，从“可验证的过渡态”推进到“可持续开发、可持续使用的稳定基线”。

## 2. 当前完成度

进入下一阶段前，下面这些收口已经完成：

- **入口收口**：`README.md`、`docs/README.md`、`docs/current/architecture.md`
- **运行真相收口**：`docs/current/runtime-truth.md`
- **启动协议收口**：`docs/guides/dev-guide.md`、`docs/guides/startup-protocol.md`
- **验证基线收口**：`docs/governance/verification-baseline.md`
- **遗留问题压缩**：`docs/governance/inventory/root-doc-triage.md`、`docs/governance/next-phase-backlog.md`
- **Creative A~D 主线已完成**
- **auth Step 5 已完成**

这意味着下一阶段已经不需要重新确认：

- 系统是不是 Creative-first
- local / remote 的运行拓扑是什么
- 启动脚本按哪个协议跑
- 最小验证基线是什么

## 3. 当前边界

下一阶段的边界应明确为：

### 已完成，不作为第一主线重做

- Creative A~D 主业务迁移
- remote auth / admin 的已交付范围
- 启动协议与最小验证基线定义

### 仍然存在，但属于下一阶段 backlog

- Workbench 可管理性不够
- 业务层与诊断层混放
- 文案与页面状态不统一
- AIClip workflow 仍偏工程工具面板
- root docs 仍有待下沉 / 归档 / 删除的执行动作
- deprecation / env warning 仍未彻底清理

## 4. 当前验证基线

下一阶段开发默认按下面入口执行：

- `docs/governance/verification-baseline.md`

最小规则：

1. 日常开发先跑 daily baseline
2. 涉及 docs / startup protocol 时补跑 doc/startup baseline
3. 涉及 remote / auth 对接时补跑 remote gate
4. 阶段收口前跑 full frontend E2E + full remote Phase 4 release gate

## 5. 当前 backlog 入口

压缩后的 backlog 统一看：

- `docs/governance/next-phase-backlog.md`

根层 docs 的分类与后续 move/archive/delete 去向看：

- `docs/governance/inventory/root-doc-triage.md`

## 6. 下一阶段第一条主线

建议第一条主线是：

> **UI/UX 收口主线**

优先顺序：

1. `CreativeWorkbench` 可管理性收口
2. 业务层 / 诊断层彻底分层
3. 文案与四态统一

不建议一上来先做：

- AIClip 深度产品化
- 新业务域扩张
- 大规模 remote 新能力扩展

原因：

- 当前最直接阻碍“继续开发是否顺手”的，是工作台和信息架构没有收口
- 如果 UI/UX 仍保持过渡态，后续 AIClip 产品化与更多 feature 只会继续堆在不稳定地基上

## 7. 选择的执行方式

推荐执行方式：

> **单主线推进 + 多 PR sequence**

不建议：

- 同时多主线并行推进
- 按 domain 全面铺开再收口

原因：

- 当前问题高度集中在同一条前端产品化主线上
- 用一条主线拆成多个 PR，最利于控制 diff、验证、回归和交接

## 8. 对应启动包文档

下一阶段的配套文档为：

- Kickoff：`docs/current/next-phase-kickoff.md`
- PRD：`docs/governance/next-phase-prd.md`
- Test Spec：`docs/governance/next-phase-test-spec.md`
- Execution Breakdown：`docs/governance/next-phase-execution-breakdown.md`

四份文档的职责分工：

| 文档 | 作用 | 什么时候更新 |
| --- | --- | --- |
| `docs/current/next-phase-kickoff.md` | 启动总入口；回答“现在从哪里开始” | 主线、边界、启动方式变化时 |
| `docs/governance/next-phase-prd.md` | 范围与成功标准；回答“为什么做、做到哪里算完成” | 范围、目标、非目标变化时 |
| `docs/governance/next-phase-test-spec.md` | 验证规格；回答“怎么证明这阶段完成” | 验证面、测试命令、验收口径变化时 |
| `docs/governance/next-phase-execution-breakdown.md` | PR sequence；回答“下一步先做什么、按什么顺序做” | PR 切片、顺序、退出条件变化时 |

规则：

> **kickoff 是总入口，但不是单独真相；启动包必须四份一起使用。**

## 9. 推荐阅读顺序

如果你是下一位继续开发的人，建议直接按下面顺序进入：

1. `docs/current/architecture.md`
2. `docs/current/runtime-truth.md`
3. `docs/governance/phase-transition-checklist.md`
4. `docs/guides/dev-guide.md`
5. `docs/governance/verification-baseline.md`
6. `docs/governance/next-phase-backlog.md`
7. `docs/current/next-phase-kickoff.md`
8. `docs/governance/next-phase-prd.md`
9. `docs/governance/next-phase-test-spec.md`
10. `docs/governance/next-phase-execution-breakdown.md`

## 10. 一句话启动指令

如果只记一句话：

> **下一阶段先不要扩业务面，先把 Creative-first 的工作台、信息架构、文案和验证闭环收口到稳定状态，再继续扩展。**
