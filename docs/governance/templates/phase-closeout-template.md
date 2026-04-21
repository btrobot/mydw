# Phase Closeout Template / 阶段收尾模板

> Version: 1.0.0  
> Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active template

> 用途：在一个阶段、主线或大 PR 序列完成后，快速形成一份**可读、可交接、可进入下一轮决策**的收尾文档。

---

## 1. 使用说明

适用场景：

- MVP 完成后的第一轮总收尾
- 某个 next-phase 主线执行完成后的阶段收尾
- 一个较大的 PR sequence 做完后，需要形成 closeout / summary / audit

使用规则：

1. 先基于事实填写，不要先写结论再反推
2. 优先写“当前阶段真的交付了什么”，不要把未完成内容写得像已完成
3. 写完后，应能支持下一步的 **选主线**，而不是只是一份回顾感想
4. 配套检查建议参考：`docs/governance/phase-transition-checklist.md`

相关治理文档：

- `docs/governance/post-mvp-closeout-sequence.md`
- `docs/governance/post-mvp-development-model.md`
- `docs/governance/phase-transition-checklist.md`

---

## 2. 模板正文

将下面内容复制到你的阶段收尾文档中再填写：

```md
# <阶段名称> Closeout / <阶段名称> 收尾总结

> Version: <版本>
> Updated: <YYYY-MM-DD>
> Owner: <负责人>
> Status: Active closeout

## 1. 一句话总结

> <一句话说清本阶段做完了什么，以及系统进入了什么新状态>

## 2. 本阶段原始目标

- <目标 1>
- <目标 2>
- <目标 3>

关联文档：

- kickoff: <路径>
- PRD: <路径>
- test spec: <路径>
- execution breakdown: <路径>

## 3. 实际交付结果

### 3.1 已完成

- <已完成内容 1>
- <已完成内容 2>
- <已完成内容 3>

### 3.2 未完成 / 明确不做

- <未完成或明确下放 backlog 的内容 1>
- <内容 2>

### 3.3 与原计划相比的偏差

- <偏差点 1>：<原因>
- <偏差点 2>：<原因>

## 4. 当前系统真相发生了什么变化

### 4.1 架构 / 运行事实变化

- <architecture / runtime truth 的变化>

### 4.2 domain / page / contract / data 变化

- <业务边界变化>
- <页面职责变化>
- <接口契约变化>
- <数据模型变化>

### 4.3 哪些旧文档已经不再可信

- <旧文档路径> → <stale / historical / archive / redirect>
- <旧文档路径> → <处理方式>

## 5. 验证总结

### 5.1 自动化验证

- <命令 1> — <结果>
- <命令 2> — <结果>
- <命令 3> — <结果>

### 5.2 手工验证

- <链路 1> — <结果>
- <链路 2> — <结果>

### 5.3 未覆盖或未完全验证项

- <缺口 1>
- <缺口 2>

## 6. 文档吸收情况

- [ ] current architecture 已更新（如适用）
- [ ] runtime truth 已更新（如适用）
- [ ] 相关 domain docs 已更新
- [ ] 相关 page specs 已更新
- [ ] verification baseline 已更新（如适用）
- [ ] 高可见度旧文档已标 stale / redirect / archive

如果没有更新，请说明原因：

- <未更新项>：<原因>

## 7. Planning / Archive 收口

- [ ] 已被正式文档吸收的 planning 已移出 active 区
- [ ] `.omx/plans/archive/` 已收纳本阶段完成后的 planning
- [ ] `docs/governance/policies/omx-plan-retention.md` 已更新（如适用）

相关 planning / archive：

- <planning 路径 1>
- <archive 路径 1>

## 8. Remaining risks / Residual risks

- <风险 1>：<影响> / <当前处理方式>
- <风险 2>：<影响> / <当前处理方式>

## 9. Backlog handoff

明确进入 backlog 的事项：

- <P0/P1/P2 项 1>
- <P0/P1/P2 项 2>

对应文档：

- `docs/governance/next-phase-backlog.md`

## 10. 对下一阶段的输入

### 建议继续回答的问题

- <问题 1>
- <问题 2>

### 推荐主线候选（可选）

- <候选主线 A>
- <候选主线 B>

## 11. Exit decision / 阶段退出结论

> <当前阶段是否可以视为已收口；若可以，进入“下一阶段选主线”；若不可以，缺口是什么>
```

---

## 3. 最小填写要求

如果你不想一次写太长，至少先补齐下面 6 块：

1. 一句话总结
2. 已完成 / 未完成
3. 当前系统真相变化
4. 验证总结
5. Remaining risks / Residual risks
6. Exit decision / 阶段退出结论

---

## 4. 通过标准

一份合格的阶段收尾文档，至少应满足：

- 不翻聊天记录，也能知道这一阶段做了什么
- 不需要重读全部 planning，也能知道留下了什么风险
- 能直接给下一步“选主线”提供输入

一句话：

> **收尾模板不是回忆录，而是下一阶段决策的输入件。**
