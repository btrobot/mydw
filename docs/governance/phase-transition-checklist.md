# Phase Transition Checklist / 阶段切换检查清单

> Version: 1.1.0  
> Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把 `docs/governance/post-mvp-development-model.md` 落成可执行清单，避免“当前阶段未收口，就仓促启动下一阶段”。

---

## 1. 使用原则

每次阶段切换都按两部分执行：

1. **Part A：确认当前阶段已经收口**
2. **Part B：确认下一阶段已经准备好启动**

只有 A、B 都通过，才允许正式切换阶段。

---

## 2. Part A：当前阶段收口检查

### 2.0 什么叫“已经收尾到能做决定”？

如果你想快速判断当前阶段是不是已经收尾到足以决定下一阶段，可以先看这 5 条：

```text
[ ] 不翻聊天记录，也能讲清“现在做到哪了”
[ ] 已完成 / 未完成 / 剩余风险 能明确说清
[ ] 当前边界已经稳定到足以支持选主线
[ ] 高可见度误导性旧文档已处理
[ ] backlog 已压缩到可以支持“只选一条主线”
```

这 5 条的作用不是替代 Part A 全量检查，而是先回答一个更高层的问题：

> **当前阶段是否已经收尾到“能做下一阶段决策”，而不是还停留在“状态还说不清”的阶段。**

### 2.1 实现完成度

```text
[ ] 当前阶段主线范围已经实现完成
[ ] 当前阶段没有仍在等待补救的关键 PR
[ ] 当前阶段遗留项已被明确写成 residual risk 或 backlog
```

### 2.2 验证完成度

```text
[ ] 当前阶段承诺的关键验收项已实际验证
[ ] 当前最小回归基线可以通过
[ ] 若本阶段引入了新的验证面，verification baseline 已更新
[ ] 已知失败项已明确归类：修复 / 延后 / 接受风险
```

### 2.3 文档吸收

```text
[ ] 实现事实已吸收到正式 docs，而不只停留在 planning / chat / handoff
[ ] 对应 domain doc 已更新
[ ] 对应 page spec 已更新（如适用）
[ ] 对应 governance / baseline 文档已更新（如适用）
[ ] 高可见度旧文档已标 stale、redirect 或 archive
```

### 2.4 Planning 收口

```text
[ ] 已被正式文档吸收的 planning 文件已移出 active 区
[ ] `.omx/plans` 已明确区分 active / archive
[ ] `docs/governance/policies/omx-plan-retention.md` 已反映最新划分
[ ] 不再把旧 planning 当成当前 authoritative 输入
```

### 2.5 收口产物

```text
[ ] 已有 closeout / summary / audit / report 至少一种收口产物
[ ] 收口产物说明了：做了什么、没做什么、剩余风险是什么
[ ] 不需要重新翻大量聊天记录，才能理解当前边界
```

**Part A 规则：**

> 只要当前阶段还没收干净，就不要启动下一阶段。

---

## 3. Part B：下一阶段启动检查

### 3.1 主线唯一性

```text
[ ] 下一阶段有且只有一条主线
[ ] 主线不是“什么都做一点”的混合目标
[ ] 其他问题已被压缩进 backlog，而不是混进主线
```

### 3.2 主线合理性

```text
[ ] 已回答为什么现在做，而不是以后做
[ ] 已回答做完后会带来什么系统杠杆
[ ] 已回答如果现在不做，会带来什么风险
```

### 3.3 启动包完整性

```text
[ ] next-phase PRD 已存在
[ ] next-phase test spec 已存在
[ ] execution breakdown / PR sequence 已存在
[ ] kickoff 入口文档已存在并可读
```

### 3.4 边界清晰度

```text
[ ] in-scope / out-of-scope 已明确
[ ] 成功标准已明确，不是抽象口号
[ ] 当前不做的内容已写清楚，避免执行中回流
```

### 3.5 执行可行性

```text
[ ] 当前代码基线足够稳定，可以承接下一阶段
[ ] 当前 docs 基线足够清晰，不需要从多份冲突文档里猜
[ ] 当前验证能力足够支撑下一阶段增量开发
[ ] 当前 backlog 已经压缩，不会在执行时持续抢主线
```

**Part B 规则：**

> 主线不唯一、启动包不完整、边界不清晰时，不要宣布进入下一阶段。

---

## 4. 通过标准

阶段切换通过，必须同时满足：

```text
[ ] Part A：当前阶段已收口
[ ] Part B：下一阶段已准备好启动
```

也就是说：

> **阶段切换 = 前一阶段结束得足够干净 + 下一阶段开始得足够清楚。**

---

## 5. 建议配套阅读

1. `docs/governance/post-mvp-development-model.md`
2. `docs/current/architecture.md`
3. `docs/current/runtime-truth.md`
4. `docs/governance/verification-baseline.md`
5. `docs/governance/inventory/current-project-mvp-closeout-checklist.md`
6. `docs/current/next-phase-kickoff.md`
7. `docs/governance/next-phase-backlog.md`
8. `docs/governance/policies/omx-plan-retention.md`

---

## 6. 反模式提醒

若出现以下任一情况，通常说明不该切阶段：

```text
[ ] 还在用聊天记录代替正式文档
[ ] 还在用旧 planning 代替 current truth
[ ] closeout 还没完成，就先写下一阶段 PRD
[ ] 同时存在两条以上“其实都很重要”的主线
[ ] 还没定义成功标准，就已经开始拆 PR
```

---

## 7. 一句话规则

> **不要在“当前阶段还没收干净”的时候启动下一阶段。**

