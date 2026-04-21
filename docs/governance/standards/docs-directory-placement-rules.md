# docs/ 目录放置规则（四分法）

> Updated: 2026-04-21
> Status: Active

> 目的：给团队一个 5 秒可用的放置规则，避免新文档一律堆到 `docs/` 根目录，或者把 `current / domains / governance / guides` 混用。

---

## 1. 一句话版

- `docs/current/` = **当前真相 / 当前默认入口**
- `docs/domains/` = **业务领域真相**
- `docs/governance/` = **治理规则 / 收口规则 / 阶段推进规则**
- `docs/guides/` = **操作指南 / 实施手册 / how-to**

一句话速记：

> **当前事实进 `current/`，业务语义进 `domains/`，治理机制进 `governance/`，操作步骤进 `guides/`。**

---

## 2. 四分法决策表

| 如果这份文档主要回答…… | 放这里 | 典型例子 |
| --- | --- | --- |
| “项目现在到底是什么样？” | `docs/current/` | `architecture.md`、`runtime-truth.md`、`next-phase-kickoff.md` |
| “这个业务对象/流程/状态在业务上是什么意思？” | `docs/domains/` | domain model、workflow、semantics |
| “这些真相以后怎么维护、验证、收口、归档、切换阶段？” | `docs/governance/` | authority matrix、verification baseline、retention policy、phase checklist |
| “具体要怎么做、怎么操作、怎么执行？” | `docs/guides/` | dev guide、build guide、OpenAPI workflow、startup protocol |

---

## 3. 四个目录分别解决什么问题

## 3.1 `docs/current/`

这里放的是团队默认信任的**当前事实入口**。

它回答：

- 当前系统结构是什么？
- 当前 runtime truth 是什么？
- 当前阶段启动入口是什么？

适合放：

- 当前 architecture 总入口
- 当前 runtime truth
- 当前阶段 kickoff 入口
- 其他需要被高频直接打开的 current truth 文档

不适合放：

- 历史设计稿
- 业务术语细节全集
- 过程治理规则
- 具体执行步骤

判断口诀：

> **如果团队默认“先看这份就能知道现在系统是什么样”，放 `current/`。**

---

## 3.2 `docs/domains/`

这里放的是**业务领域真相**。

它回答：

- 业务对象是什么？
- 业务流程是什么？
- 业务状态、事件、约束是什么？
- 某个领域边界如何定义？

适合放：

- 领域模型
- 业务流程说明
- 任务语义
- 状态机
- 边界定义

不适合放：

- 页面实现分层
- 模块技术拆分
- 验证基线
- 阶段推进规则
- 操作手册

判断口诀：

> **如果重点在“业务上这到底算什么”，放 `domains/`。**

---

## 3.3 `docs/governance/`

这里放的是**治理机制**。

它回答：

- 哪份文档 authoritative？
- 哪些文档是 stale / archive / active？
- 阶段结束前需要做哪些收口？
- 下一阶段启动前需要满足什么条件？
- 文档、代码、测试如何保持一致？

适合放：

- authority matrix
- verification baseline
- post-MVP development model
- retention / artifact policy
- phase transition checklist
- inventory / triage / stale-doc 清单

不适合放：

- 具体业务规则本身
- 某个模块的结构设计细节
- 开发环境启动步骤
- 某个工具怎么使用

判断口诀：

> **如果重点在“以后怎么维持有序”，放 `governance/`。**

---

## 3.4 `docs/guides/`

这里放的是**操作指南和实施手册**。

它回答：

- 本地怎么启动？
- 某个流程具体怎么执行？
- 某个工具链怎么跑？
- 团队成员按什么步骤完成一件事？

适合放：

- 开发环境指南
- build / release 指南
- OpenAPI 生成流程
- 启动协议
- 用户操作指南

不适合放：

- 当前 truth 入口
- 业务领域定义
- 文档 authority / retention 规则

判断口诀：

> **如果读者的目标是“照着做”，放 `guides/`。**

---

## 4. 最容易混淆的边界

### 4.1 `current/` vs `guides/`

- `current/` 讲 **现在是什么**
- `guides/` 讲 **具体怎么做**

例子：

- “当前架构总览” → `current/`
- “本地怎么启动前后端” → `guides/`

### 4.2 `domains/` vs `architecture`

如果重点是业务含义，放 `domains/`。  
如果重点是系统结构，通常应进入当前架构入口或架构相关 current truth，而不是写成领域文档。

### 4.3 `governance/` vs `guides/`

- `governance/` 讲 **规则和约束**
- `guides/` 讲 **执行步骤**

例子：

- “什么文档该归档” → `governance/`
- “怎么跑 OpenAPI 生成命令” → `guides/`

---

## 5. 放置顺序：拿不准时按这个问

新增一份文档时，按下面顺序判断：

1. 它是不是团队默认要先看的 current truth？  
   - 是：优先放 `docs/current/`
2. 它是不是主要解释业务对象、流程、状态、边界？  
   - 是：优先放 `docs/domains/`
3. 它是不是主要定义规则、收口、验证、保留、阶段切换？  
   - 是：优先放 `docs/governance/`
4. 它是不是主要给人照着执行？  
   - 是：优先放 `docs/guides/`

如果四个都不完全符合，再考虑：

- 是否应该归档到 `docs/archive/`
- 是否只是 runtime / local artifact，不应该进入正式文档体系

---

## 6. 最终统一口径

如果团队只保留一个简短规则，就用这段：

> `docs/current/` 放当前默认真相；`docs/domains/` 放业务领域真相；`docs/governance/` 放治理和阶段推进规则；`docs/guides/` 放具体执行指南。

