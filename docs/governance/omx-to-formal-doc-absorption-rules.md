# OMX → Formal Docs Absorption Rules / OMX 工作文档吸收到正式文档的规则

> Version: 1.0.0 | Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：回答一个长期会反复出现的问题：  
> **开发过程中，`.omx/` 下的 planning / slice / test-spec / closeout 等工作文档，应该在什么时机、以什么方式、吸收到正式 `docs/` 文档体系里。**

---

## 1. 一句话规则

> **OMX 工作文档先服务执行；一旦某部分已经稳定、可复用、并且经验证，就把它提炼吸收到正式 docs；等正式 docs 吸收完成，再把对应 `.omx` 工件降级为 archive。**

---

## 2. 先区分两类文档

## 2.1 `.omx/` 工作文档

它们主要服务：

- 讨论
- 规划
- 分歧收敛
- 切片执行
- 中间态记录
- closeout 前的 working artifacts

特点：

- 可以变化快
- 可以保留探索痕迹
- 可以只服务当前 PR / 当前阶段
- 不一定是最终 authoritative truth

典型例子：

- `.omx/plans/*.md`
- `.omx/context/*.md`
- 运行期状态、notepad、progress artifacts

## 2.2 `docs/` 正式文档

它们主要服务：

- 给后续开发提供稳定指导
- 成为 current truth / governance / guides 的正式入口
- 提供可长期复用的规则、边界、说明

特点：

- 应该稳定
- 应该少而准
- 应该有明确 authority
- 应该不依赖大量历史上下文也能理解

---

## 3. 吸收的判断门槛（Promotion Gate）

一个 `.omx` 文档或其中一部分，只有同时满足下面 3 个条件，才应该吸收到正式 `docs/`：

### 3.1 已稳定

不是“还在讨论”，而是“已经决定”。

判断信号：

- 关键方案已收敛
- 不再频繁变更方向
- 已经成为当前执行共识

### 3.2 会被复用

不是只服务这一次聊天或这一次 PR，而是后续的人还需要看它。

判断信号：

- 后续 PR 会继续依赖
- 下一位开发者 / agent 需要用它来理解当前系统
- 它定义了今后仍然生效的规则、边界或验证口径

### 3.3 已被验证

不是纸面设想，而是已经被代码、测试或执行规则证明。

判断信号：

- 已落代码
- 已有测试或验证命令
- 已成为当前治理/执行规则

---

## 4. 开发过程中的 5 个吸收时机

## 4.1 时机一：主线 / 阶段规划刚收敛后

这时吸收的是 **主线级 truth**。

适合吸收的内容：

- 下一阶段唯一主线
- 范围 / 非目标
- 成功标准
- PR sequence
- 主线级验证口径

典型落点：

- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`

一句话：

> 这是“开始执行前”的第一次吸收。

## 4.2 时机二：某个 PR 方案已收敛、准备执行时

这时吸收的是 **PR 级 execution truth**。

适合吸收的内容：

- 这个 PR 到底做什么
- 不做什么
- 如何切片
- 如何验证

建议先保存在：

- `.omx/plans/` 的工作工件

如果已经明确会长期引用，也可以直接落到正式 docs。

一句话：

> 这是“进入实现前”的第二次吸收。

## 4.3 时机三：某个 slice 做完并验证通过后

这时吸收的是 **实现后的 current truth**。

适合吸收的内容：

- 当前默认行为
- 当前边界
- 当前入口
- 当前验证要求

注意：

> **不要等整个大阶段做完才吸收。只要某个 slice 已经改变了 current truth，就应该及时回填正式 docs。**

## 4.4 时机四：PR 完成后

这时做的是 **PR closeout 吸收**。

适合吸收的内容：

- 最终决定
- 实际边界
- 验证结果
- 剩余风险

同时处理 `.omx/plans`：

- 已被正式 docs 吸收的 → archive
- 仍有参考价值但不是 current truth 的 → 保留 working/archive
- 明显一次性的 → 删除或归档

## 4.5 时机五：阶段完成后

这时做的是 **阶段收口吸收**。

适合吸收的内容：

- closeout
- current truth 总结
- baseline 更新
- backlog 压缩
- retention / ledger 更新

一句话：

> 阶段收口不是把 `.omx` 原文整包搬进 `docs/`，而是提炼其中仍然有效、仍然会复用、已经验证的部分。

---

## 5. 吸收时，不是“复制粘贴”

最佳实践不是：

> 把 `.omx/plans/*.md` 原样搬进 `docs/`

而是：

> **从 OMX 工件里提炼正式 truth。**

只吸收这三类信息：

### 5.1 已决定的内容

- scope
- non-goals
- 关键 ADR
- 成功标准

### 5.2 已验证的内容

- 测试命令
- pass/fail 标准
- 回归要求

### 5.3 已成为当前真相的内容

- 当前边界
- 当前默认行为
- 当前入口
- 当前流程

不要吸收：

- brainstorming 痕迹
- 已过时分歧
- 中间比较过程的全部细节
- 已失效候选方案

这些保留在 `.omx/` 或 archive 即可。

---

## 6. 吸收到哪类正式文档

把内容吸收到 `docs/` 时，不只要问“该不该吸收”，还要问“吸收到哪里”。

### 6.1 吸收到 `docs/current/`

如果它主要回答：

> 项目现在到底是什么样？

适合放：

- 当前入口
- 当前默认行为
- 当前架构/运行事实

### 6.2 吸收到 `docs/domains/`

如果它主要回答：

> 业务对象 / 流程 / 状态在业务上是什么意思？

适合放：

- 领域语义
- 业务边界
- 状态定义

### 6.3 吸收到 `docs/governance/`

如果它主要回答：

> 以后怎么维护、验证、收口、归档、切阶段？

适合放：

- verification rules
- retention rules
- closeout rules
- phase transition rules
- 文档吸收规则

### 6.4 吸收到 `docs/guides/`

如果它主要回答：

> 具体怎么做？

适合放：

- 操作步骤
- 实施手册
- 工具链 how-to

---

## 7. `.omx/plans` 与正式 docs 的推荐关系

推荐把它们看成两个层次：

### 7.1 `.omx/plans`

服务：

- 当前工作
- 当前分歧
- 当前执行

角色：

> **working execution artifacts**

### 7.2 `docs/`

服务：

- 当前真相
- 长期可复用规则
- 后续开发入口

角色：

> **formal authoritative artifacts**

所以理想生命周期是：

```text
OMX planning / slice / test-spec
        ↓
收敛并进入执行
        ↓
提炼成正式 docs
        ↓
对应 `.omx/plans` 工件降级为 archive
```

---

## 8. 一个实用的 4 问判断法

每次面对 `.omx` 文档时，先问这 4 个问题：

1. **这是不是已经定了？**
2. **这是不是后面的人还要看？**
3. **这是不是已经被代码/验证证明了？**
4. **它属于 current / domains / governance / guides 哪一类？**

如果前 3 个问题都回答“是”，就应该进入正式 docs。  
第 4 个问题决定它的落点。

---

## 9. 反模式

以下做法都不推荐：

### 9.1 把 `.omx` 原文整份复制进正式 docs

问题：

- 正式 docs 变得冗长
- 中间态和 current truth 混在一起

### 9.2 什么都不吸收，全部留在 `.omx`

问题：

- 后续开发者必须翻工作工件才能知道当前规则
- `.omx` 反过来变成隐性 authoritative source

### 9.3 等整个阶段结束后再一次性吸收

问题：

- current truth 长时间滞后
- 执行中大量口头共识没有被正式文档接住

### 9.4 吸收了正式 docs，却不降级 `.omx` 工件

问题：

- active / archive 边界持续混乱
- 旧 planning 继续与正式 docs 竞争 authority

---

## 10. 在当前项目中的应用方式

就本仓库当前节奏，推荐这样做：

### 主线级

- 用主线级启动包承接主线 ralplan 结果
- 即：
  - kickoff
  - PRD
  - test spec
  - execution breakdown

### PR 级

- 用 `.omx/plans` 或正式治理文档承接 PR 级 focused plan
- 当 PR 级范围、slice、验证已经稳定时，再吸收进正式 docs

### slice 级

- slice 做完并验证通过后，及时回填 current truth / verification truth

### 阶段级

- 阶段完成后更新：
  - closeout
  - backlog
  - retention
  - inventory ledger

---

## 11. 一句话收尾

> **OMX 文档先服务推进；正式 docs 只吸收已经稳定、会复用、且经验证的 truth；吸收完成后，再把对应 `.omx` 工件降级到 archive。**
