# Next-Phase Mainline Selection Template / 下一阶段选线模板

> Version: 1.0.0  
> Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active template

> 用途：在阶段收尾之后，从多个 open issues / backlog / 机会点中，**明确选出下一阶段唯一主线**。

---

## 1. 使用说明

前置条件：

- 已有当前阶段 closeout / summary / audit / report
- 当前 `docs/current/architecture.md` / `runtime-truth.md` / `verification-baseline.md` 可读
- 已经能区分 current truth 与历史 planning

使用规则：

1. 这份模板只用于 **选主线**，不是写 next-phase PRD
2. 这里选出的应该是“唯一主线”，不是“所有重要事项列表”
3. 选完线之后，再进入 kickoff / PRD / test spec / execution breakdown

相关治理文档：

- `docs/governance/post-mvp-closeout-sequence.md`
- `docs/governance/post-mvp-development-model.md`
- `docs/governance/phase-transition-checklist.md`
- `docs/governance/next-phase-backlog.md`

---

## 2. 模板正文

将下面内容复制到你的选线文档中再填写：

```md
# Next-Phase Mainline Selection / 下一阶段主线选择

> Version: <版本>
> Updated: <YYYY-MM-DD>
> Owner: <负责人>
> Status: Active selection

## 1. 当前起点

本轮选线基于以下输入：

- closeout / summary: <路径>
- current architecture: `docs/current/architecture.md`
- runtime truth: `docs/current/runtime-truth.md`
- verification baseline: `docs/governance/verification-baseline.md`
- backlog: `docs/governance/next-phase-backlog.md`

## 2. 当前阶段已知约束

- <约束 1>
- <约束 2>
- <约束 3>

## 3. 候选主线

### 候选 A：<候选名称>

- 解决的问题：<问题>
- 主要收益：<收益>
- 主要风险：<风险>
- 不做的代价：<代价>

### 候选 B：<候选名称>

- 解决的问题：<问题>
- 主要收益：<收益>
- 主要风险：<风险>
- 不做的代价：<代价>

### 候选 C：<候选名称>

- 解决的问题：<问题>
- 主要收益：<收益>
- 主要风险：<风险>
- 不做的代价：<代价>

## 4. 候选对比

| 候选 | 业务价值 | 系统杠杆 | 风险压降 | 实施复杂度 | 结论 |
| --- | --- | --- | --- | --- | --- |
| A / <名称> | <高/中/低> | <高/中/低> | <高/中/低> | <高/中/低> | <保留/淘汰> |
| B / <名称> | <高/中/低> | <高/中/低> | <高/中/低> | <高/中/低> | <保留/淘汰> |
| C / <名称> | <高/中/低> | <高/中/低> | <高/中/低> | <高/中/低> | <保留/淘汰> |

## 5. 最终选择

> **下一阶段唯一主线：<主线名称>**

## 6. 为什么现在做这条

### 6.1 业务价值

- <价值 1>
- <价值 2>

### 6.2 系统杠杆

- <杠杆 1>
- <杠杆 2>

### 6.3 风险压降

- <风险压降点 1>
- <风险压降点 2>

## 7. 为什么不是其他候选

- 不选 <候选 A>，因为：<原因>
- 不选 <候选 B>，因为：<原因>

## 8. 主线范围草稿

### In scope

- <范围 1>
- <范围 2>

### Out of scope

- <不做内容 1>
- <不做内容 2>

## 9. 为这条主线必须先补准的 current truth

### 9.1 全局最小基线（若仍有缺口）

- <docs/README / architecture / runtime truth / verification baseline 的缺口>

### 9.2 路线绑定文档

- <domain doc>
- <page spec>
- <API contract truth>
- <data model truth>
- <test spec 需要补的验证口径>

## 10. 启动条件

- [ ] 当前阶段已收口
- [ ] backlog 已压缩
- [ ] 下一阶段有且只有一条主线
- [ ] 这条主线的 current truth 缺口已识别
- [ ] 可以开始写 kickoff / PRD / test spec / execution breakdown

## 11. 进入下一步的输出件

选线完成后，下一步应产出：

- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`

## 12. 一句话决策

> <一句话说清为什么这条主线是下一阶段唯一主线>
```

---

## 3. 最小填写要求

如果先做轻量版，至少补齐：

1. 当前起点
2. 候选主线
3. 候选对比
4. 最终选择
5. 为什么现在做这条
6. 为这条主线必须先补准的 current truth

---

## 4. 通过标准

一份合格的选线文档，至少应满足：

- 能清楚解释为什么选这条，不是那条
- 能清楚说明“现在不做什么”
- 能直接推动 kickoff / PRD / test spec / execution breakdown 生成

一句话：

> **选线模板不是 backlog 汇总表，而是“下一阶段唯一主线”的决策单。**
