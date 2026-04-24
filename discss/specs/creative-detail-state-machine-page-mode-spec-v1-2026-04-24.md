# 《CreativeDetail 状态机与页面模式规范 v1》

> 适用对象：`/creative/:id` / CreativeDetail  
> 目标：解决“同一路由下，不同阶段是否还能编辑、如何编辑、主任务是什么”的混乱问题  
> 设计原则：**状态分层、页面分模、编辑受控、版本可追溯**

---

## 1. 一句话结论

**CreativeDetail 可以继续作为统一路由，但不能继续作为“永远可编辑的创建页”。**  
必须引入：

1. **生命周期状态机**
2. **页面模式（Page Mode）**
3. **编辑策略（Mutability Policy）**
4. **就绪度（Readiness）**

---

## 2. 设计目标

本规范要解决 4 个问题：

1. 列表页点作品后，为什么都进同一页但体验不能一样  
2. 作品进入生成/审核/发布阶段后，哪些内容必须锁定  
3. 用户想修改时，是“直接改当前对象”还是“派生新草稿/新版本”  
4. 如何避免“页面显示的定义”和“后台正在跑的版本”不一致

---

## 3. 状态模型：不要只用一个 status

最佳实践：**拆成 3 层**

### 3.1 生命周期状态（Lifecycle Status）

回答：

> 这个作品当前处于业务哪一阶段？

建议沿用当前后端语义：

- `PENDING_INPUT`
- `READY_TO_COMPOSE`
- `COMPOSING`
- `WAITING_REVIEW`
- `APPROVED`
- `REWORK_REQUIRED`
- `REJECTED`
- `IN_PUBLISH_POOL`
- `PUBLISHING`
- `PUBLISHED`
- `FAILED`

---

### 3.2 页面模式（Page Mode）

回答：

> 当前进入 CreativeDetail 后，这一页应该以什么心智工作？

建议定义：

- `authoring`：编辑定义模式
- `submitting`：提交后锁定观察模式
- `reviewing`：审核查看模式
- `reworking`：返工编辑模式
- `publishing`：发布观察模式
- `published_readonly`：已发布只读模式
- `failed_recovery`：失败恢复模式

---

### 3.3 就绪度（Readiness）

回答：

> 离“可提交生成”还差什么？

建议独立保留：

- `not_ready`
- `partially_ready`
- `ready`

并附带：

- `missing_items`
- `invalid_reasons`

---

## 4. 核心原则

### 4.1 路由可以统一，模式必须切换

- 可以都进 `/creative/:id`
- 但不能都按“create detail 可编辑表单”处理

### 4.2 生成后必须锁版本

一旦进入 `COMPOSING` 及之后的结果流转阶段：

- 当前提交版本应视为**冻结快照**
- 不允许继续无约束修改当前定义

### 4.3 修改要么回到返工态，要么派生新版本

- `REWORK_REQUIRED`：允许回到当前对象继续改
- `APPROVED / PUBLISHED / PUBLISHING / WAITING_REVIEW`：优先走“创建新版本/新草稿”

### 4.4 readiness 不能替代 lifecycle

- “可生成”不是完整生命周期
- 它只是“是否满足提交条件”

---

## 5. 推荐状态机

```text
PENDING_INPUT
  -> READY_TO_COMPOSE
  -> FAILED

READY_TO_COMPOSE
  -> COMPOSING
  -> FAILED

COMPOSING
  -> WAITING_REVIEW
  -> FAILED

WAITING_REVIEW
  -> APPROVED
  -> REWORK_REQUIRED
  -> REJECTED

REWORK_REQUIRED
  -> PENDING_INPUT
  -> READY_TO_COMPOSE
  -> COMPOSING

APPROVED
  -> IN_PUBLISH_POOL
  -> PUBLISHING

IN_PUBLISH_POOL
  -> PUBLISHING
  -> FAILED

PUBLISHING
  -> PUBLISHED
  -> FAILED

FAILED
  -> PENDING_INPUT
  -> READY_TO_COMPOSE
  -> COMPOSING
```

---

## 6. 生命周期到页面模式映射

| Lifecycle | Page Mode | 是否可编辑 | 页面主任务 |
|---|---|---:|---|
| PENDING_INPUT | authoring | 是 | 补齐作品定义 |
| READY_TO_COMPOSE | authoring | 是 | 确认定义并提交生成 |
| COMPOSING | submitting | 否 | 查看提交版本与生成进度 |
| WAITING_REVIEW | reviewing | 否 | 查看结果、等待审核 |
| REWORK_REQUIRED | reworking | 是 | 按审核意见返工 |
| APPROVED | reviewing | 否 | 查看通过版本 |
| IN_PUBLISH_POOL | reviewing / publishing | 否 | 查看入池与待发布状态 |
| PUBLISHING | publishing | 否 | 查看发布进度 |
| PUBLISHED | published_readonly | 否（建议） | 查看已发布版本 |
| FAILED | failed_recovery | 条件式 | 恢复、修复、重提 |

---

## 7. 编辑策略规范

### 7.1 可编辑态

适用于：

- `PENDING_INPUT`
- `READY_TO_COMPOSE`
- `REWORK_REQUIRED`

允许编辑：

- A 当前定义区
- B 当前入选区
- C 候选池区

---

### 7.2 锁定态

适用于：

- `COMPOSING`
- `WAITING_REVIEW`
- `APPROVED`
- `IN_PUBLISH_POOL`
- `PUBLISHING`
- `PUBLISHED`

规则：

- 表单只读
- 不允许直接改“当前提交版本”
- 顶部明确说明：**当前版本已冻结**
- 如需变更，走：
  - `创建新版本`
  - 或 `基于当前版本创建新草稿`

---

### 7.3 失败恢复态

适用于：

- `FAILED`

规则按失败类型分流：

#### a) 提交前失败

如保存失败、校验失败  
=> 保持可编辑

#### b) 生成任务失败

=> 当前生成版本保留证据  
=> 页面给出两种动作：

- 修复定义后重新提交
- 基于当前定义新建草稿再提交

---

## 8. 各页面模式规范

### 8.1 authoring 模式

适用状态：

- `PENDING_INPUT`
- `READY_TO_COMPOSE`

目标：

- 定义作品
- 补齐缺项
- 提交生成

首屏重点：

1. 当前作品是谁
2. 当前定义是什么
3. 距离可生成还差什么

主 CTA：

- 保存作品定义
- 提交生成

---

### 8.2 submitting 模式

适用状态：

- `COMPOSING`

目标：

- 看“正在跑的版本”
- 看生成进度
- 避免误改当前版本

首屏重点：

1. 当前提交版本摘要
2. 生成进度/任务状态
3. 锁定说明

主 CTA：

- 查看任务进度
- 刷新状态

次 CTA：

- 基于当前定义创建新草稿（可选）

---

### 8.3 reviewing 模式

适用状态：

- `WAITING_REVIEW`
- `APPROVED`
- `IN_PUBLISH_POOL`

目标：

- 看审核结果/待审核状态
- 看当前版本是否通过
- 看是否已进入发布准备

首屏重点：

1. 当前版本结果
2. 审核状态
3. 下一步动作

主 CTA：

- 查看版本详情
- 查看审核结论

次 CTA：

- 创建新版本
- 去发布侧查看

---

### 8.4 reworking 模式

适用状态：

- `REWORK_REQUIRED`

目标：

- 按审核意见返工，而不是重新从零创建

首屏重点：

1. 返工原因
2. 受影响区域
3. 修改完成后如何重新提交

主 CTA：

- 保存返工修改
- 重新提交生成

特殊要求：

- 审核意见必须前置显示
- 缺陷点要回指 A/B/C 具体区域

---

### 8.5 publishing 模式

适用状态：

- `PUBLISHING`

目标：

- 看发布执行
- 看发布诊断
- 不再修改内容定义

首屏重点：

1. 当前发布对象
2. 发布状态
3. 风险/错误

主 CTA：

- 查看发布状态
- 查看诊断

---

### 8.6 published_readonly 模式

适用状态：

- `PUBLISHED`

目标：

- 查看已发布结果
- 提供后续派生入口

首屏重点：

1. 已发布版本摘要
2. 发布时间/发布记录
3. 后续动作

主 CTA：

- 基于当前版本创建新版本
- 查看发布记录

不建议：

- 直接开放原定义编辑

---

### 8.7 failed_recovery 模式

适用状态：

- `FAILED`

目标：

- 先解释失败，再给恢复路径

首屏重点：

1. 失败发生在哪一环
2. 失败原因
3. 恢复动作

主 CTA：

- 修复并重试
- 基于当前内容新建版本

---

## 9. A/B/C/D/E 在不同模式下的表现

| 区域 | authoring | submitting | reviewing | reworking | publishing | published_readonly |
|---|---|---|---|---|---|---|
| A 当前定义 | 可编辑 | 只读 | 只读 | 可编辑 | 只读 | 只读 |
| B 当前入选 | 可编辑 | 只读 | 只读 | 可编辑 | 只读 | 只读 |
| C 候选池 | 可操作 | 只读/弱化 | 弱化 | 可操作 | 隐藏/折叠 | 隐藏/折叠 |
| D 版本审核 | 次级 | 前移 | 前移 | 前移 | 次级 | 前移 |
| E 发布诊断 | 折叠 | 次级 | 次级 | 折叠 | 前移 | 次级 |

---

## 10. 主 CTA / 次 CTA 规范

| Mode | 主 CTA | 次 CTA | 禁止 CTA |
|---|---|---|---|
| authoring | 保存定义 / 提交生成 | 查看候选 / 查看历史版本 | 发布 |
| submitting | 刷新进度 | 查看任务 / 新建草稿 | 直接改定义 |
| reviewing | 查看审核 / 查看版本 | 创建新版本 | 直接改当前版本 |
| reworking | 保存返工 / 重新提交 | 查看返工意见 | 发布 |
| publishing | 查看发布进度 | 查看诊断 | 编辑定义 |
| published_readonly | 基于当前版本创建新版本 | 查看发布记录 | 直接编辑已发布版本 |

---

## 11. 首屏提示语规范

### 可编辑态

- 草稿
- 部分就绪
- 可生成

### 锁定态

- 当前版本已提交生成，定义已锁定
- 当前版本待审核，暂不可直接修改
- 当前版本已发布，如需调整请创建新版本

### 返工态

- 当前版本被要求返工，请按下列问题修正后重新提交

### 失败态

- 本次流程执行失败，请先确认失败原因后再决定修复或重提

---

## 12. 推荐实现方式

### 12.1 后端

保留当前 `status`，新增或明确以下派生字段：

- `page_mode`
- `is_editable`
- `can_submit`
- `can_fork_new_version`
- `lock_reason`

如果后端暂不返回，前端可先做映射，但最终建议后端收口。

---

### 12.2 前端

在 CreativeDetail 中建立统一派生：

```ts
const pageMode = deriveCreativePageMode(status)
const editPolicy = deriveEditPolicy(status)
const primaryActions = derivePrimaryActions(status, eligibilityStatus)
```

不要在各个按钮上零散写条件。

---

## 13. 对当前项目的直接建议

基于当前实现，建议先做这 3 件事：

1. **定义状态到页面模式映射表**
2. **把 `COMPOSING / WAITING_REVIEW / APPROVED / PUBLISHING / PUBLISHED` 默认改为只读模式**
3. **为锁定态补一个“创建新版本/新草稿”入口**

这是最小闭环。

---

## 14. 最终结论

> **CreativeDetail 不是不能承载全生命周期，而是必须从“单一编辑页”升级为“状态驱动的多模式页面”。**

核心不是多加几个状态标签，  
而是把下面三件事彻底分开：

- **作品走到哪一步**（Lifecycle）
- **页面现在该怎么用**（Page Mode）
- **用户还能不能改**（Edit Policy）

