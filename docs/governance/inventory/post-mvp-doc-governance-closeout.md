# Post-MVP Doc Governance Closeout / MVP 后文档治理正式收口件

> Version: 1.0.0  
> Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Recorded closeout

> 目的：把本轮 **文档盘点、治理收口、入口重连、archive 分类、下一阶段启动包** 的结果，收口成一份正式记录。  
> 这份文档不是新的长期规范，而是本轮治理工作的 **formal closeout artifact / 正式收口件**，用于回答两个问题：
>
> 1. 这一轮到底已经收口了什么？  
> 2. 下一阶段应该基于哪一套 current truth 继续推进？

---

## 1. 本次收口覆盖范围

本次正式收口覆盖的是 **MVP 后第一轮文档治理工作**，重点不是新增产品能力，而是把“已经做出来的东西”收成一套能支撑下一阶段开发的 current truth 文档体系。

覆盖范围包括：

- `docs/` 根层入口收口
- `docs/governance/` 分类与索引重组
- `docs/archive/` 二级分类与 README 索引补齐
- post-MVP 治理链路显式化
- Phase E / Phase F 产物吸收
- 文档真相测试补强

不在本次收口范围内的事项：

- 全量重写所有历史文档
- 把每一份 working / archive 文档都同步成 current truth
- 直接扩展新的产品主线

---

## 2. 一句话结论

> 本轮收口已经把仓库从“文档很多但入口分散”推进到“入口明确、层次清楚、治理链路连通、下一阶段可直接启动”的状态。

---

## 3. 已完成的正式收口内容

### 3.1 入口收口：根层与高频入口已经稳定

已完成的关键变化：

- `docs/` 根层现在只保留默认入口文档：`docs/README.md` 与 `docs/runtime-truth.md`
- `docs/current/architecture.md`、`docs/current/runtime-truth.md`、`docs/governance/authority-matrix.md` 已形成 current truth 主入口组
- `docs/governance/README.md` 已成为治理目录的稳定分类入口

这意味着：

- 后续开发者不需要先在根层翻大量历史文档
- “先看哪里”这件事已经被显式定义
- 高可见度入口与 historical material 已基本脱钩

相关文档：

- `docs/README.md`
- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/governance/README.md`
- `docs/governance/authority-matrix.md`

### 3.2 分类收口：治理目录不再杂乱堆叠

`docs/governance/` 已完成明确分类：

- Core：高频治理入口
- Policies：规则与边界
- Inventory：盘点、分诊、收口台账
- Standards：长期方法与规范
- Templates：可复用模板

对应入口见：

- `docs/governance/README.md`

本轮收口之后，governance 不再承担“把所有治理文档都堆在同一层”的角色，而是回到：

> **Core 负责入口，Policies 负责规则，Inventory 负责盘点，Standards 负责方法，Templates 负责复用。**

### 3.3 Archive 收口：历史材料已具备二级导航

`docs/archive/` 已完成总入口与二级目录索引补齐，至少包括：

- `docs/archive/README.md`
- `docs/archive/reference/README.md`
- `docs/archive/planning/README.md`
- `docs/archive/analysis/README.md`
- `docs/archive/history/README.md`
- `docs/archive/dev-docs/README.md`
- `docs/archive/backend-docs/README.md`
- `docs/archive/examples/README.md`
- `docs/archive/exports/README.md`
- `docs/archive/private/README.md`

这一步的意义不是“让 archive 变成 current truth”，而是：

- 让历史材料可查
- 让 archive 有层次
- 让历史文档不再和 current docs 抢入口

### 3.4 Post-MVP 治理链已经显式连通

本轮最重要的治理成果之一，是把 MVP 后“先做什么、后做什么、用什么文档驱动”这条链路固定下来：

1. `docs/governance/post-mvp-development-model.md`
2. `docs/governance/post-mvp-closeout-sequence.md`
3. `docs/governance/phase-transition-checklist.md`
4. `docs/current/next-phase-kickoff.md`

统一记忆方式已经明确：

> **model 讲为什么，sequence 讲顺序，checklist 讲门槛，kickoff 讲起点。**

这条链路解决的是：

- 为什么 MVP 后不能直接继续散着做
- 为什么不是先全量补文档
- 为什么必须先收口到“能做决定”
- 为什么下一阶段必须以 kickoff + PRD + test spec + execution breakdown 启动

### 3.5 Phase E / Phase F 产物已经吸收进正式文档体系

本轮收口不是停在讨论层，而是已经把产物落进正式文档：

Phase E：

- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/next-phase-backlog.md`

Phase F：

- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`

这意味着当前仓库已经具备：

- 收口结果
- backlog 压缩结果
- 下一阶段主线启动包

三者之间不再断裂。

### 3.6 Inventory / retention 规则已经能支撑持续维护

与本轮正式收口直接相关的 inventory / retention 文档已经落位：

- `docs/governance/inventory/inventory-ledger.md`
- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/policies/omx-plan-retention.md`

它们分别承担：

- 文档/资料簇总台账
- 根层文档四分法去向表
- `.omx/plans` active / archive / 删除边界

这保证了后续不是再回到“产物越堆越多、没有去向规则”的状态。

### 3.7 文档真相测试已经成为收口保护层

本轮治理不是只靠人工记忆维持，已经有测试把高价值文档入口和关键说法锁住，包括：

- `backend/tests/test_doc_truth_fixes.py`
- `backend/tests/test_epic7_docs_baseline.py`

当前被测试保护的内容包括：

- docs / governance / archive 入口是否存在
- post-MVP 四件套是否连通
- inventory / root triage / archive index 是否仍可导航
- 当前高频文档中的关键判断语句是否被保留

---

## 4. 当前形成的“可继续开发”状态

### 4.1 当前 truth 体系已经够用，不需要先全局补文档

当前已经形成的不是“全局唯一大全文档”，而是：

> **一套能指导下一阶段开发的 current truth 文档体系。**

它至少覆盖：

- 当前入口：`docs/README.md`
- 当前架构与运行事实：`docs/current/architecture.md`、`docs/current/runtime-truth.md`
- 权威边界：`docs/governance/authority-matrix.md`
- 验证基线：`docs/governance/verification-baseline.md`
- 阶段推进模型：`docs/governance/post-mvp-development-model.md`
- 阶段切换顺序与门槛：`docs/governance/post-mvp-closeout-sequence.md`、`docs/governance/phase-transition-checklist.md`
- 下一阶段启动入口：`docs/current/next-phase-kickoff.md`

### 4.2 这轮收口回答了“鸡蛋问题”

本轮治理采用的不是：

- 先确定完整未来路线，再决定怎么收口  
也不是：
- 先把所有文档都补完，再谈下一阶段

而是：

1. 先把当前阶段收口到“能做决定”
2. 再确定下一阶段唯一主线
3. 再围绕主线定向补齐 current truth

对应文档：

- `docs/governance/post-mvp-closeout-sequence.md`

因此，本轮正式收口的目标已经达成：  
**不是把一切写完，而是把下一阶段继续往前走所需的最小 current truth 收实。**

---

## 5. 本轮之后的维护规则

后续继续推进时，默认遵循下面几条维护规则：

1. **一个主题只保留一个当前权威入口**  
   不让多个高可见度文档并列竞争 current truth。

2. **优先修入口文档，而不是同步所有旧文档**  
   先保当前使用路径不误导，再逐步处理历史材料。

3. **新收口件优先放 Inventory，不要重新堆到 governance 根层**  
   尤其是 ledger、triage、closeout、audit、parity、version inventory 这类文档。

4. **已被正式文档吸收的 planning，要继续从 active 区退出**  
   规则见 `docs/governance/policies/omx-plan-retention.md`。

5. **Archive 负责保留历史，不负责承担当前真相**  
   除非 current docs 明确引用，否则不应把 archive 当默认起点。

---

## 6. 仍然保留的风险 / 未在本轮解决的事项

以下事项仍然存在，但已被显式降级为后续工作，而不是本轮收口阻塞项：

- 部分 working docs 仍有吸收空间，但不影响当前主入口判断
- archive 中的历史材料仍可能继续细分，但二级导航已足够可用
- `.omx/plans` 仍会继续增长，需要按 retention 规则持续归档
- 仓库内仍有少量未进入正式治理链的草稿/分析材料，需要后续再判断是否吸收、归档或删除

---

## 7. Exit decision / 退出结论

> 本轮 **MVP 后文档治理收口** 可以视为已正式完成。  
> 当前仓库已经具备清晰入口、分层治理、archive 导航、post-MVP 推进链路和下一阶段启动包，足以在不重新盘点全仓的前提下继续进入下一阶段开发。

一句话总结：

> **这次收口完成的不是“把所有文档写完”，而是“把下一阶段继续开发所需的 current truth 和治理链条收实”。**
