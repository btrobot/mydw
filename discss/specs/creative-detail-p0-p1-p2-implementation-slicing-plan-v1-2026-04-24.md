# 《CreativeDetail P0 / P1 / P2 实现切片计划 v1》

> 日期：2026-04-24  
> 适用范围：CreativeDetail / OMX 实施切片  
> 依据文档：  
> - `discss/specs/creative-detail-converged-prd-v1-2026-04-24.md`  
> - `discss/specs/creative-detail-p0-acceptance-test-draft-v1-2026-04-24.md`  
> - `discss/specs/creative-detail-implementation-strategy-v1-2026-04-24.md`  
> - `discss/specs/creative-detail-whole-page-lowfi-wireframe-copy-v1-2026-04-24.md`  
> 状态：Draft

---

## 0. 文档目的

这份文档回答的是：

> **CreativeDetail 真正开做时，应该按什么顺序拆成可交付、可验证、可回滚的实现切片。**

它不再讨论业务规则本身，
而是把已经收敛的规则翻译成：

- 先做什么
- 后做什么
- 哪些必须进 P0
- 哪些应该放到 P1 / P2

---

## 1. 总体切片原则

## 1.1 切片原则一：先补页面投影，再改页面结构

因为当前系统已经有：

- 现成 `/creative/:id` 路由
- 现成 `CreativeDetail.tsx`
- 现成 `CreativeItem / CandidateItem / InputItem / Version` 领域模型

所以最合理的顺序不是“先乱改前端再补 API”，而是：

> **先让后端把页面真正需要的结构投影出来，再让前端按新骨架消费。**

---

## 1.2 切片原则二：保留稳定入口，不重建外部页面

所有切片都默认：

- 保留 `/creative/:id`
- 保留 `CreativeDetail.tsx` 作为 route shell
- 在其内部逐步替换结构

---

## 1.3 切片原则三：P0 只解决主心智问题

P0 只锁四件事：

1. 页面结构正确
2. 当前入选语义正确
3. 默认值 / 控制权正确
4. 版本边界正确

任何“更强浏览器、更强筛选、更强视觉精修”都应后置。

---

## 1.4 切片原则四：每个切片都要能独立验证

每个切片都必须能回答：

- 改了哪些文件
- 解决了哪个问题
- 对应哪些 AC / TC
- 怎么验证通过

也就是：

> **切片不是按代码文件拆，而是按用户价值 + 验证口径拆。**

---

## 2. 切片总览

建议把实现拆成下面 3 个阶段、8 个主要切片：

### P0：做对主结构

- Slice P0-1：后端 CreativeDetail 页面投影重构
- Slice P0-2：前端页面壳重构与新骨架落位
- Slice P0-3：当前入选区 + 来源区联动落地
- Slice P0-4：状态 / CTA / 结果区后置重排
- Slice P0-5：回归与验收测试补齐

### P1：做强选择与查看

- Slice P1-1：商品选择器增强
- Slice P1-2：商品区 / 自由素材区查看与摘要增强

### P2：做强预览与发布衔接

- Slice P2-1：结果确认 / 发布衔接增强
- Slice P2-2：高阶筛选 / 预览 / 运营效率增强

---

## 3. P0 切片计划

## 3.1 Slice P0-1：后端 CreativeDetail 页面投影重构

### 目标

把当前偏“领域原料”的 detail response，
升级成更贴近页面结构的 projection。

---

### 解决的问题

当前前端需要自己从：

- `product_links`
- `candidate_items`
- `input_items`
- `current_*`
- `versions`

这些字段里重新拼页面结构。

这会导致：

- 前端页面逻辑过重
- “当前入选区”不是一等公民
- 商品区 / 自由素材区 / readiness 需要前端再推理

这个切片的目标是：

> **让后端直接返回更接近 A/B/C/D/E 的页面投影结构。**

---

### 建议产物

建议在 `CreativeDetailResponse` 基础上增加或演进以下 projection：

#### A. `current_selection`

至少包含：

- `product_name`
- `cover`
- `copywriting`
- `audio`
- `videos[]`

每项建议包含：

- current value
- source label
- state
- adopted_from

#### B. `product_zone`

至少包含：

- primary product summary
- product-derived candidates grouped by type

#### C. `free_material_zone`

至少包含：

- free-material candidates grouped by type

#### D. `readiness`

至少包含：

- state
- missing_fields
- can_compose
- next_action_hint

#### E. `page_mode`

至少包含：

- definition
- result_pending_confirm
- published_followup

---

### 是否需要改数据库

P0-1 原则上**优先不动大表结构**。

只建议评估一个小增强：

- `CreativeItem.current_audio_asset_id`
- `CreativeItem.audio_mode`

如果这一步不做，也可以先由 projection 从现有输入编排推导。

但视频集合不建议新建 JSON 字段，继续以：

> `CreativeInputItem(material_type='video')`

作为 authoritative source。

---

### 涉及范围

优先涉及：

- `backend/services/creative_service.py`
- `backend/schemas/__init__.py`
- `backend/api/creative.py`

若做最小模型增强，再涉及：

- `backend/models/__init__.py`
- 新 migration

---

### 对应验收口径

主要对应：

- AC-04
- AC-05
- AC-06
- AC-07
- AC-08
- AC-09
- AC-13
- AC-15
- AC-20
- AC-21
- AC-22 ~ AC-26

---

### 完成定义

当以下成立时，P0-1 可视为完成：

1. 前端不需要再从散字段硬推完整页面结构
2. 当前入选区、商品区、自由素材区、readiness 有可直接消费的投影
3. 不引入新的双真相字段

---

## 3.2 Slice P0-2：前端页面壳重构与新骨架落位

### 目标

在不改路由的前提下，把 `CreativeDetail.tsx` 从“大杂糅页”改成：

> **route shell + page mode orchestration + section composition**

---

### 解决的问题

当前页面把很多内容堆在一起：

- authoring
- version review
- diagnostics
- workflow

导致：

- 首屏主角错位
- 当前入选区不突出
- 结果 / 诊断 / 版本信息抢页面主轴

这个切片的目标是：

> **先把整页骨架摆对。**

---

### 页面骨架要求

必须先落下这几个 section：

1. 页面头部
2. readiness 摘要
3. 当前入选区
4. 商品区
5. 自由素材区
6. 结果确认 / 当前版本区
7. 发布诊断 / 发布记录区

其中：

- A/B/C 为主工作区
- D/E 为后置承接区

---

### 建议新增组件

建议拆成：

- `CreativeDetailWorkspace`
- `CreativeDetailHeader`
- `CreativeReadinessSummary`
- `CreativeCurrentSelectionSection`
- `CreativeProductSourceSection`
- `CreativeFreeMaterialSection`
- `CreativeResultFollowupSection`

也可以继续拆更细，但不建议继续把所有结构留在 `CreativeDetail.tsx`。

---

### 涉及范围

优先涉及：

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/components/*` 新 section 组件

---

### 对应验收口径

主要对应：

- AC-01
- AC-02
- AC-03
- AC-04
- AC-07
- AC-10
- AC-27
- AC-28

---

### 完成定义

当以下成立时，P0-2 可视为完成：

1. 首屏第一主区已经是当前入选区
2. 商品区 / 自由素材区被明确后置到中段
3. 结果 / 发布区被压到下段，不再抢首屏
4. `CreativeDetail.tsx` 不再承担整页细节渲染职责

---

## 3.3 Slice P0-3：当前入选区 + 来源区联动落地

### 目标

把页面最核心的业务交互做正确：

- 当前入选如何显示
- 来源区如何采用
- 默认值如何补位
- 手改后如何脱钩

---

### 解决的问题

如果只摆出骨架，但 A/B/C 之间没有联动，
页面仍然只是“看起来对了”，实际上没法用。

这个切片要真正落实：

#### 当前入选区

- 商品名称唯一位
- 封面唯一位
- 文案唯一位
- 音频唯一位
- 视频集合位

#### 商品区

- 主题商品选择入口
- 商品派生候选采用状态
- 默认回填和脱钩

#### 自由素材区

- 按类型分组
- 采用状态可见
- 能把素材采用到当前字段

---

### 特别优先规则

这个切片必须优先锁住：

1. 商品名称空值时默认回填
2. 手改后不再静默覆盖
3. 封面默认采用与后续脱钩
4. 视频集合默认勾选与后续用户控制
5. 唯一位只能有一个当前值
6. 视频集合维持多选语义

---

### 涉及范围

优先涉及：

- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- 新的 section 组件
- 必要的 API payload / projection 对接

必要时同步涉及：

- `backend/services/creative_service.py`

---

### 对应验收口径

主要对应：

- AC-08 ~ AC-21
- TC-01
- TC-02
- TC-03
- TC-04

---

### 完成定义

当以下成立时，P0-3 可视为完成：

1. 用户可以在 A/B/C 三个区之间完成真实的采用与替换
2. 默认值与脱钩规则正确
3. 唯一位 / 集合位语义正确

---

## 3.4 Slice P0-4：状态 / CTA / 结果区后置重排

### 目标

把页面主任务表达彻底拉直：

- 头部状态
- readiness
- 主 CTA
- 结果待确认态
- 发布态

---

### 解决的问题

当前页面的一个大问题不是“没功能”，
而是：

> **同一页上有太多并列主任务。**

这个切片要解决：

1. 同屏只保留一个最强主 CTA
2. 结果确认与发布信息不再压过编辑定义态
3. 页面模式切换后，区块主次随之切换

---

### 重点内容

#### 页面头部

必须清晰承载：

- 当前状态
- 缺失项
- 最近更新时间
- 主 CTA / 次 CTA / 更多操作

#### 结果待确认模式

要强化：

- D 区
- 结果状态提示

同时保留：

- A 区用于对照

#### 已发布跟进模式

要强化：

- E 区
- 发布状态提示

---

### 涉及范围

优先涉及：

- `CreativeDetail.tsx`
- 新 header / readiness / followup 组件
- `useCreativeVersionReviewModel.ts`

必要时涉及：

- `useCreativePublishDiagnosticsModel.ts`

但原则是：

> **诊断能力保留，不再默认压主页面。**

---

### 对应验收口径

主要对应：

- AC-03
- AC-04
- AC-05
- AC-06
- AC-22 ~ AC-28
- TC-05
- TC-06
- TC-07
- TC-08

---

### 完成定义

当以下成立时，P0-4 可视为完成：

1. 页面主 CTA 体系清晰
2. readiness 与状态表达一致
3. 结果 / 发布区后置
4. 页面模式切换后区块主次正确

---

## 3.5 Slice P0-5：回归与验收测试补齐

### 目标

把前面四个实现切片锁进验证体系，
避免“页面看起来对，但没有证明”。

---

### 解决的问题

如果不专门留一个验证切片，
实现最后很容易变成：

- 手工看过了
- 大概能用
- 但回归链路没补上

这不符合 OMX 的闭环要求。

---

### 必做内容

#### A. 静态验证

- `npm run typecheck`
- `npm run build`

#### B. 定向前端验证

优先补或更新：

- `frontend/e2e/creative-main-entry/*`
- `frontend/e2e/creative-workbench/*`
- `frontend/e2e/creative-review/*`
- `frontend/e2e/creative-version-panel/*`

必要时补新的 detail-focused spec。

#### C. 主链路人工核验

至少手动核：

1. 从列表进入 detail
2. 选择主题商品
3. 修改商品名称
4. 替换封面
5. 调整视频集合
6. 保存草稿
7. 提交生成
8. 回到编辑

---

### 对应验收口径

覆盖全部：

- AC-01 ~ AC-28
- TC-01 ~ TC-08

---

### 完成定义

当以下成立时，P0-5 可视为完成：

1. 类型检查与构建通过
2. targeted E2E 通过
3. P0 阻塞缺陷为 0
4. 文档吸收条件具备

---

## 4. P0 切片顺序建议

推荐严格按下面顺序做：

### 顺序 1：P0-1 后端投影层

先把页面读的数据形状理顺。

### 顺序 2：P0-2 页面骨架

先让页面摆对。

### 顺序 3：P0-3 区域联动

再让页面真正可用。

### 顺序 4：P0-4 状态与 CTA

最后把主任务表达收口。

### 顺序 5：P0-5 验证

收口验证，禁止跳过。

---

## 5. P1 切片计划

P1 的主题是：

> **让“选”和“看”更强。**

---

## 5.1 Slice P1-1：商品选择器增强

### 目标

把当前商品选择入口升级为更成熟的商品选择器。

### 包含内容

- 抽屉 / 弹层式选择器
- 商品卡摘要更丰富
- 封面 / 标题 / 视频 / 基础信息更完整
- 更好的切换与回填体验

### 不在 P0 做的原因

这是增强体验，不是 P0 主心智阻塞项。

---

## 5.2 Slice P1-2：商品区 / 自由素材区查看增强

### 目标

让用户更容易回看已选商品和自由素材细节。

### 包含内容

- 展开查看更多商品素材
- 更强的素材摘要
- 更清楚的来源标签与采用状态
- 更顺手的预览动作

---

## 6. P2 切片计划

P2 的主题是：

> **让结果、发布、效率增强真正成熟。**

---

## 6.1 Slice P2-1：结果确认 / 发布衔接增强

### 目标

让 D/E 区从“后置承接”升级成“成熟后链路”。

### 包含内容

- 更强结果预览
- 更清楚的版本差异信息
- 更完整的发布前检查
- 更完整的发布记录查看

---

## 6.2 Slice P2-2：高阶筛选 / 预览 / 运营效率增强

### 目标

进一步提升复杂使用场景效率。

### 包含内容

- 更强素材筛选
- 更强批量预览
- 更强排序与组织能力
- 更强运营效率工具

---

## 7. 推荐的 PR / 提交边界

如果按工程实施来切，建议最小 PR 边界如下：

### PR-A

P0-1 后端投影层

### PR-B

P0-2 页面骨架

### PR-C

P0-3 A/B/C 联动

### PR-D

P0-4 状态 / CTA / 结果后置

### PR-E

P0-5 验证与回归收口

这样每个 PR 都有明确目的，也更容易回滚。

---

## 8. 当前最推荐的下一步

基于这份切片计划，
现在最推荐的下一步不是同时开做前后端，
而是：

> **先从 Slice P0-1：后端 CreativeDetail 页面投影重构 开始。**

原因：

1. 它能把页面结构从“前端推理”改成“后端投影”
2. 它能降低前端重构复杂度
3. 它最符合“先真相、后表达”的 OMX 原则

---

## 9. 收口结论

一句话收口：

> **CreativeDetail 应按“P0 先做对主结构，P1 做强选择与查看，P2 做强结果与效率”的节奏推进；而 P0 内部又必须按“后端投影 -> 页面骨架 -> 区域联动 -> 状态 CTA -> 回归验证”的顺序实施。**

再压缩一句：

> **先让数据适合页面，再让页面适合用户。**

