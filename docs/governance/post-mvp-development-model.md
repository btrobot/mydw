# Post-MVP Development Model / MVP 后开发治理模型

> Version: 1.0.0  
> Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：回答一个典型问题——**项目已经从 0 做到 MVP 之后，接下来如何继续推进，而不是重新掉回“文档越来越多、规范越来越旧、方向越来越散”的混乱状态。**

## 1. 这个模型解决什么问题

项目从 0 到 MVP 时，通常依赖下面这条链路推进：

1. 初始 PRD
2. 核心业务流程 / 边界分析
3. 数据库与接口草稿
4. 系统规划设计
5. 每个阶段 `ralplan`
6. 切 PR
7. `ralph` 执行 PR

这条链路非常适合“把东西做出来”。  
但到了 MVP 之后，问题会变成：

- 文档越来越多，但不知道谁说了算
- 早期边界设计不断被修正，旧规范显得过时
- backlog 很长，但不知道下一阶段真正的主线是什么
- 系统已经“能跑”，却还没有变成“可持续开发的稳定基线”

所以，**MVP 后的核心问题，不再是单点功能实现，而是项目治理。**

---

## 2. 核心判断：MVP 后进入的是“治理阶段”

MVP 后的工作重点要从：

- 做功能
- 补页面
- 快速打通链路

切换到：

- 建立当前真相
- 控制规范漂移
- 选择下一阶段主线
- 让后续开发可持续

一句话总结：

> **前期解决“怎么做出来”，后期解决“怎么持续往前做”。**

---

## 3. 文档分层模型

MVP 后必须先把文档分层，否则文档会持续互相竞争。

## 3.1 Current / Canonical

用途：回答“现在系统到底是什么样”。

特点：

- 数量少
- 可直接指导实现
- 是当前开发默认信任的入口

典型内容：

- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- 各域 current truth 文档
- 当前 page specs
- `docs/governance/verification-baseline.md`

## 3.2 Working / Planning

用途：回答“下一步准备怎么做”。

特点：

- 生命周期短
- 服务当前阶段执行
- 一旦被正式文档吸收，就应该归档

典型内容：

- `.omx/plans/` 中仍活跃的 PRD / test spec / PR sequence
- 阶段内执行计划

## 3.3 Reports / Closeout

用途：回答“这个阶段做完了什么、剩下什么风险”。

特点：

- 不是当前真相入口
- 但提供阶段收口证据

典型内容：

- completion audit
- closeout summary
- release gate

## 3.4 Archive / Historical

用途：回答“以前是怎么想的、为什么后来改了”。

特点：

- 保留追溯价值
- 不参与当前默认开发决策

---

## 4. 旧规范过时之后怎么办

MVP 后，早期设计被修正是正常现象，不是失败。

真正要处理的不是“为什么变了”，而是：

> **如何让过时规范失去当前指导权，而不是继续污染后续开发。**

## 4.1 每份高价值文档都要有状态

推荐状态：

- `Proposed`
- `Active`
- `Historical`
- `Stale`
- `Archived`

## 4.2 一个主题只能有一个当前权威入口

例如：

- 商品域只能有一个 current truth 入口
- 任务域只能有一个 current truth 入口
- 某个页面只能有一个当前 page spec

其他文档可以存在，但必须：

- 明确说明自己不是 authoritative
- 或跳转到当前入口

## 4.3 优先修“入口文档”，不是试图同步所有旧文档

治理顺序应该是：

1. 先保证入口文档正确
2. 再处理高可见度、会误导人的旧文档
3. 最后逐步归档低价值历史稿

也就是：

> **先保入口，再控误导，最后清历史。**

## 4.4 阶段完成后必须做“文档吸收”

每个阶段的 planning 文档，不应永久停留在 active 状态。  
阶段完成后应执行：

1. 实现完成
2. 验证通过
3. 吸收到正式文档
4. planning 下沉到 archive
5. 更新 retention / checklist / authority

## 4.5 用文档真相测试保护高价值事实

对容易漂移、又高频被误读的事实，应该用自动化测试兜底，例如：

- 当前 API 创建字段
- 当前页面规格是否仍在描述旧流程
- `docs/README.md` 是否指向正确入口
- `omx-plan-retention` 是否反映最新 active/archive 划分

---

## 5. MVP 后如何选方向

MVP 后不要把问题理解成“还有很多事可以做”。  
要把问题改写成：

> **下一阶段的唯一主线是什么？**

## 5.1 主线选择的三个维度

### A. 业务价值

它是否显著提升：

- 用户可用性
- 交付效率
- 核心流程打通程度

### B. 系统杠杆

它做完之后，是否会让后面很多事情更顺？

例如：

- 文档真相收口
- 验证基线稳定
- 核心工作流稳定化
- 工作台可管理性提升

### C. 风险压降

如果现在不做，会不会导致：

- 后续持续返工
- 方向选择越来越模糊
- 文档和实现继续漂移

## 5.2 MVP 后四类典型主线

### 方向 1：真相收口 / 基线治理

适用于：

- 文档多、口径乱
- 系统边界在 MVP 阶段被改动较多
- 继续开发前需要先盘点

### 方向 2：核心工作流稳定化

适用于：

- 功能基本打通
- 但成功率、可靠性、验证性不够稳

### 方向 3：体验与效率收口

适用于：

- 系统已经能用
- 但还不够好用、不够顺手、不够可管理

### 方向 4：下一阶段产品能力扩展

适用于：

- 当前真相稳定
- 当前 baseline 可信
- 团队已能基于已有系统放心扩展

---

## 6. 推荐的推进节奏

MVP 后，建议固定用下面的阶段循环，而不是继续松散推进。

## 6.1 Phase A：收口

目标：

- 当前真相清楚
- 当前边界清楚
- 当前验证基线清楚

产物：

- current architecture
- runtime truth
- verification baseline
- authority matrix
- next-phase kickoff

## 6.2 Phase B：选主线

只回答一个问题：

> 接下来 4~8 周最重要的一条主线是什么？

要求：

- 只选一条主线
- 其他问题进入 backlog
- 不同时推进多条重主线

## 6.3 Phase C：做启动包

围绕主线准备：

- next-phase PRD
- next-phase test spec
- execution breakdown / PR sequence

目标是让执行前就回答清楚：

- 为什么做
- 先做什么
- 何为完成

## 6.4 Phase D：按 PR 序列执行

每个 PR 延续已验证有效的方法：

- `ralplan`
- 切 PR
- `ralph`
- 验证
- closeout

## 6.5 Phase E：阶段收口

每完成一个阶段，固定执行：

1. 吸收正式文档
2. 归档 planning
3. 更新 backlog / baseline
4. 写 closeout report

然后再进入下一轮。

---

## 7. 阶段启动前的检查表

在真正开始下一阶段之前，至少要确认：

- 当前 canonical docs 已经可读、可依赖
- 高可见度过时文档已标 stale 或归档
- 当前验证基线可以跑通
- 当前 backlog 已经压缩，不再是无限散点问题列表
- 下一阶段只有一条主线
- 主线对应的 PRD / test spec / execution breakdown 已存在

如果这些条件不满足，就不要急着“继续写功能”。

---

## 8. 阶段收口后的检查表

每个阶段结束时，应确认：

- 代码行为已验证
- 实现事实已吸收到正式文档
- page spec / domain doc / governance doc 已同步
- planning 文档已从 active 区迁出或标明状态
- closeout / report 已记录剩余风险
- next backlog 已更新

---

## 9. 反模式

下面这些都是 MVP 后的高风险反模式：

### 9.1 继续让所有文档处于同一层级

后果：

- 没人知道谁说了算
- 老文档不断复活

### 9.2 每个阶段只做实现，不做吸收

后果：

- planning 越堆越多
- 当前真相越来越模糊

### 9.3 同时开多个重主线

后果：

- backlog 越来越大
- 每条线都推进不深

### 9.4 过度执着于修平所有旧文档

后果：

- 维护成本爆炸
- 治理动作本身失控

正确做法是先修入口，再清误导。

---

## 10. 与本仓库现有治理文档的关系

本模型不是替代现有 current truth 文档，而是解释：

- 为什么要有这些 current truth
- 为什么 `.omx/plans` 需要 active/archive 分流
- 为什么 next-phase kickoff 之前必须先收口

配套阅读建议：

1. `docs/README.md`
2. `docs/current/architecture.md`
3. `docs/current/runtime-truth.md`
4. `docs/governance/authority-matrix.md`
5. `docs/governance/verification-baseline.md`
6. `docs/current/next-phase-kickoff.md`
7. `docs/governance/next-phase-backlog.md`
8. `docs/governance/omx-plan-retention.md`

---

## 11. 一句话结论

如果只记住一条规则，请记住：

> **MVP 之后，不要再靠“继续做更多”往前走，而要靠“先建立当前基线，再启动下一阶段主线”往前走。**

