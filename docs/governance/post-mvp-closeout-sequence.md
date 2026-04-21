# Post-MVP Closeout Sequence / MVP 后收尾—选线—定向收口流程

> Version: 1.0.0  
> Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把 “MVP 结束后到底先做什么、后做什么” 这件事落成标准流程，避免陷入两个误区：
>
> 1. 先试图把所有历史文档全部补全  
> 2. 还没收尾清楚，就直接拍脑袋进入下一阶段开发

---

## 1. 一句话结论

MVP 后的正确顺序不是：

> 先把所有文档都补全，再决定下一步做什么。

也不是：

> 什么都没收尾清楚，就直接确定下一阶段路线。

而是：

> **先做当前阶段收尾总结 → 再选下一阶段唯一主线 → 再围绕主线定向补齐 current truth → 再启动下一阶段执行。**

---

## 2. 什么时候使用这份流程

以下场景都适用：

- MVP 刚完成，准备进入下一轮开发
- 一个大阶段刚结束，感觉文档很多、方向很多、难以前进
- 你发现“当前真相”和“历史规划”开始混在一起
- 团队开始争论：到底应该先补文档，还是先继续做功能

---

## 3. 标准流程图

```text
Step 0 识别触发条件
  ↓
Step 1 当前阶段收尾总结
  ↓
Step 2 下一阶段选主线
  ↓
Step 3 围绕主线定向收口 current truth
  ↓
Step 4 形成下一阶段启动包
  ↓
Step 5 按 PR sequence 执行
  ↓
Step 6 阶段完成后再次收口，进入下一轮
```

也可以压缩记成一句话：

> **收尾 → 选线 → 定向收口 → 启动 → 执行 → 再收口**

---

## 4. Step 1：当前阶段收尾总结

### 4.1 这一步回答什么

这一步不是回答“下一步做什么”，而是先回答：

- 我们现在到底做到哪了
- 已完成什么
- 没完成什么
- 当前系统边界大致是什么
- 剩余风险是什么
- 哪些旧文档已经不适合继续指导开发

### 4.2 产物应该至少包括

- current architecture / runtime truth
- verification baseline
- backlog 压缩结果
- closeout / summary / audit / report 至少一种

### 4.3 这一步的边界

**这一步不是全局补文档。**

它只要求你能回答：

> **“我们现在站在哪儿？”**

### 4.4 通过标准

当你不需要重新翻大量聊天记录，也能讲清当前状态时，这一步才算完成。

配套文档：

- `docs/governance/post-mvp-development-model.md`
- `docs/governance/phase-transition-checklist.md`
- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`

---

## 5. Step 2：下一阶段选主线

### 5.1 这一步回答什么

在收尾总结基础上，回答：

- 下一阶段唯一主线是什么
- 为什么现在做这条，而不是别的
- 这条主线做完后会带来什么系统杠杆
- 哪些问题先明确不做，压缩进 backlog

### 5.2 核心规则

> **下一阶段有且只有一条主线。**

如果答案还是“这些都重要，都想一起推进”，说明这一步还没完成。

### 5.3 这一步为什么不能跳过

因为没有主线，就无法判断：

- 哪些文档必须优先补
- 哪些边界需要先固定
- 哪些接口 / 数据 / 页面事实最值得更新

### 5.4 通过标准

当你能用一句话回答：

> **“接下来 4~8 周，我们最重要的一条主线是什么？”**

这一步才算完成。

配套文档：

- `docs/governance/post-mvp-development-model.md`
- `docs/governance/next-phase-backlog.md`
- `docs/current/next-phase-kickoff.md`

---

## 6. Step 3：围绕主线定向收口 current truth

### 6.1 这一步回答什么

路线定下来之后，不是全面补所有文档，而是回答：

> **为了让这条主线顺利推进，哪些 current truth 必须先准？**

### 6.2 必补内容的判断规则

问每份文档一句话：

> **如果这份文档不准，后面的人会不会因为它做错事？**

如果答案是“会”，就应该更新、替换或建立 authoritative 入口。  
如果答案是“不会，只是历史参考”，就应该降级、redirect 或 archive。

### 6.3 全局最小基线 vs 路线绑定文档

这里要明确区分两类：

#### A. 全局最小基线

这些通常在任何下一阶段之前都应该可用：

- `docs/README.md`
- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/governance/authority-matrix.md`
- `docs/governance/verification-baseline.md`
- `docs/governance/next-phase-backlog.md`

#### B. 路线绑定的 current truth

这些要在主线确定后定向补齐：

- 相关 domain docs
- 相关 page specs
- 相关 API contract truth
- 相关 data model truth
- 相关 test spec / execution breakdown

### 6.4 通过标准

当你能明确说出：

> **“不是所有文档都要补，只是这条主线依赖的 current truth 要补准。”**

这一步才算完成。

配套文档：

- `docs/governance/authority-matrix.md`
- `docs/governance/verification-baseline.md`
- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`

---

## 7. Step 4：形成下一阶段启动包

当主线和定向收口范围都明确后，再形成启动包：

- Kickoff：`docs/current/next-phase-kickoff.md`
- PRD：`docs/governance/next-phase-prd.md`
- Test Spec：`docs/governance/next-phase-test-spec.md`
- Execution Breakdown：`docs/governance/next-phase-execution-breakdown.md`

启动包的作用不是回顾历史，而是把“下一步怎么开始”讲清楚。

---

## 8. Step 5：按 PR sequence 执行

执行时延续已经验证有效的方法：

- `ralplan`
- 切 PR
- `ralph`
- 验证
- closeout

重点不是“同时多开几条线”，而是：

> **单主线推进 + 多 PR sequence**

---

## 9. Step 6：阶段完成后再次收口

每一轮主线完成后，都要回到收口动作，而不是直接开始下一个大方向。

固定动作：

1. 更新正式 docs
2. 归档或降级 planning
3. 更新 verification baseline / backlog / retention
4. 记录 closeout / summary / audit / report
5. 再进入下一轮 Step 1

---

## 10. 标准检查清单

### 10.1 收尾阶段检查

```text
[ ] 已有当前阶段 closeout / summary / audit / report
[ ] 当前架构与 runtime truth 已可读
[ ] 当前 verification baseline 已可运行
[ ] backlog 已压缩，不再是无限散点列表
[ ] 高可见度旧文档已被标 stale / redirect / archive
```

### 10.2 选线阶段检查

```text
[ ] 下一阶段只有一条主线
[ ] 已说明为什么现在做它
[ ] 已说明这条主线的系统杠杆
[ ] 已说明其他问题先不做，进入 backlog
```

### 10.3 定向收口检查

```text
[ ] 已区分全局最小基线 与 路线绑定文档
[ ] 已识别本主线最容易误导开发的文档/边界
[ ] 已明确哪些 current truth 必须先更新
[ ] 不再要求把所有历史文档一次性补平
```

### 10.4 启动阶段检查

```text
[ ] next-phase kickoff 已存在
[ ] next-phase PRD 已存在
[ ] next-phase test spec 已存在
[ ] next-phase execution breakdown 已存在
[ ] 启动包能直接指导下一步开发
```

---

## 11. 反模式

以下做法都说明流程跑偏了：

### 11.1 先全量补文档，再谈路线

问题：

- 成本失控
- 没有主线就不知道优先级

### 11.2 还没收尾清楚，就直接进入下一阶段

问题：

- 当前真相不稳
- 新阶段建立在模糊基线上

### 11.3 用 backlog 代替主线

问题：

- 什么都重要
- 最终什么都推进不深

### 11.4 把历史规划继续当 current truth

问题：

- 旧边界反复复活
- 新实现持续被旧文档误导

---

## 12. 与现有治理文档的关系

- `docs/governance/post-mvp-development-model.md`：解释为什么 MVP 后必须进入治理节奏
- `docs/governance/phase-transition-checklist.md`：解释阶段切换前后要检查什么
- `docs/current/next-phase-kickoff.md`：解释下一阶段从哪里正式启动

这份文档补的是：

> **“收尾 → 选线 → 定向收口” 这条执行顺序本身。**

---

## 13. 一句话规则

> **MVP 后不要先试图补全文档；先收尾，再选线，再围绕主线定向补齐 current truth。**
