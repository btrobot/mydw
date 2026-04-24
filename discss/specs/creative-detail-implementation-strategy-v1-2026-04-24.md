# 《CreativeDetail 实施策略建议 v1》

> 日期：2026-04-24  
> 适用范围：CreativeDetail / OMX 实施 / 既有系统渐进演进  
> 目的：回答以下三个问题：  
> 1. 如何按照 OMX 最佳实践实施  
> 2. 现有系统已有框架时，应重构现有页面还是新建页面替换  
> 3. 后台数据模型如何考虑  
> 状态：Draft

---

## 0. 先给结论

### 结论 1：实施方式

> **按照 OMX 最佳实践，这件事不应该直接跳代码，而应该走“当前真相 -> 收敛 PRD -> 验收标准 -> 实现切片 -> P0 渐进落地 -> 验证收口”的链路。**

### 结论 2：页面策略

> **不建议新建一个新的外部业务页面再替换；建议保留 `/creative/:id` 这个既有页面入口，采用“同路由下的渐进式重构”。**

### 结论 3：后台模型策略

> **不建议推倒重做后台数据模型；建议沿用现有 `CreativeItem + ProductLink + CandidateItem + InputItem + CreativeVersion` 主干模型，在 P0 先补“页面投影层”，必要时只做小幅模型增强。**

一句话总收口：

> **这是一次“渐进式重构 + API 投影升级 + 小步模型增强”，不是“另起炉灶重做一套”。**

---

## 1. 这次应该遵循哪些 authoritative 文档

根据 `docs/` 当前目录结构，这次讨论不应再把所有历史文档混为一谈。

应优先信任：

### 1.1 当前真相入口

- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `backend/models/__init__.py`

这三处是“当前系统长什么样”的 authoritative 入口。

---

### 1.2 Creative 领域历史与现状衔接

- `docs/domains/creative/progressive-rebuild-final-summary.md`
- `docs/domains/creative/progressive-rebuild-completion-audit.md`

这两份文档清楚说明：

- 系统已经从 task-first 转向 creative-first
- `CreativeWorkbench` / `CreativeDetail` 已经是主工作流的一部分
- 现有系统本来就是“渐进式重建”，不是一次性爆炸式重写

---

### 1.3 OMX / 治理实施方法

- `docs/governance/post-mvp-development-model.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`

这些文档明确了：

- MVP 之后要先锁当前真相与主线
- 先锁 PRD，再锁 test spec，再拆执行顺序
- 不能跳过验证口径直接开做

---

### 1.4 明确是历史参考、不是当前真相的文档

- `docs/archive/reference/data-model.md`

这份文档自己已经标了：

> **Status: Stale / archival reference**

所以它可以作为历史字典参考，
但不能作为这次 CreativeDetail 数据模型设计的主依据。

---

## 2. 按照 OMX 最佳实践，CreativeDetail 应该怎么实施

## 2.1 正确实施链路

结合当前 repo 的治理规则，这次应走下面这条链：

### Phase 0：锁当前真相

输入来源：

- `docs/current/*`
- `backend/models/__init__.py`
- 现有 `frontend/src/features/creative/*`

目的：

- 明确现在系统已经有什么
- 明确哪些是可以复用的
- 明确哪些是旧页面负担

---

### Phase 1：锁页面合同

这一层我们已经基本完成：

- 收敛 PRD
- 低保真整页线框
- P0 验收标准 / 测试草案

这就是 OMX 里的：

> **先锁规则，再锁验收。**

---

### Phase 2：锁执行切片

在 OMX 最佳实践里，下一步不是“大家一起乱改”，而是：

> **把 P0 拆成几个可独立验证的 slice。**

建议至少拆成：

1. **后端投影层 slice**
2. **前端页面骨架 slice**
3. **来源区联动 slice**
4. **结果区降权 / 后置 slice**
5. **E2E 与回归验证 slice**

---

### Phase 3：只做 P0

P0 只实现：

- 三分区骨架
- 当前入选区
- 商品选择入口升级
- 默认值 / 脱钩规则
- 唯一位 / 集合位语义
- 版本创建边界表达

不在 P0 做：

- 完整高保真商品浏览器
- 复杂筛选
- 完整发布控制台
- 所有视觉精修

---

### Phase 4：验证后再吸收

P0 做完不是结束。

要走 OMX 标准闭环：

1. typecheck
2. build
3. targeted E2E / regression
4. 把真正落地后的稳定结论吸收到正式文档

也就是：

> **实现不是终点，验证与文档吸收才是闭环。**

---

## 2.2 如果用 OMX 角色/skill 来组织，推荐怎么配

如果按 OMX 的角色分工来执行，这个任务最合理的是：

### A. `ralplan` / 计划阶段

职责：

- 锁最终 P0 切片
- 锁先后顺序
- 锁哪些是 P0、哪些是 P1

适合输出：

- P0/P1/P2 切片计划
- 执行顺序

---

### B. `executor` / 实施阶段

职责：

- 具体改后端投影
- 具体改前端页面骨架
- 具体落地交互联动

建议拆两个执行面：

1. backend/API projection
2. frontend/page shell

---

### C. `test-engineer` / 验证阶段

职责：

- 把 P0 验收草案映射到自动化测试
- 补 targeted E2E
- 保证旧链路不回归

---

### D. `verifier` / 收口阶段

职责：

- 检查是否真的满足 AC / TC
- 检查是否有漏掉的结构性问题
- 给出 completion evidence

---

## 2.3 对这次任务的实际建议

如果你要我按 OMX 最佳实践继续推进，最合理的下一串动作是：

1. 产出 `P0 / P1 / P2 实现切片计划`
2. 锁 `后端投影优先、前端页面其后`
3. 再进入实现

而不是现在直接开一个大 PR 把所有东西一起改乱。

---

## 3. 现有系统下，应该重构当前页面，还是新建页面替换

## 3.1 当前代码真相

从现有实现看：

- 路由已经是 `/creative/:id`
- `CreativeDetail.tsx` 已经是当前创作详情页
- 页面里已经同时挂了：
  - authoring model
  - version review
  - diagnostics
  - AIClip workflow

也就是说，当前页面不是“没有”，而是：

> **已经存在，但职责过重、结构过旧、信息层级混杂。**

---

## 3.2 不建议的做法：新建一个全新外部页面

不建议直接新建一个新的公开路由页面，例如：

- `/creative-v2/:id`
- `/creative/detail-v2/:id`

原因有四个：

### 原因 A：当前主入口已经稳定

系统已经完成 creative-first 迁移，
`/creative/:id` 是现有心智入口。

如果新建外部页面，会造成：

- 新旧页面并存
- 测试口径分裂
- 文档口径分裂

---

### 原因 B：当前页面里已经有可复用资产

例如：

- `useCreative`
- `useCreativeAuthoringModel`
- `useCreativeVersionReviewModel`
- `VersionPanel`
- `CheckDrawer`
- AIClip workflow 入口

这些都不是废物，
而是可以被“重新编排”的资产。

---

### 原因 C：路由切换成本高于页面重排成本

真正要改的核心不是：

> “这个页面地址对不对”

而是：

> “这个页面首屏主角错了、结构顺序错了、来源区与定稿区关系错了”

这是页面架构问题，
不是 URL 问题。

---

### 原因 D：更符合当前 repo 的渐进式重建历史

`docs/domains/creative/progressive-rebuild-final-summary.md` 明确说明，
这个项目本身已经是在采用：

> **新建上层业务真相 + 渐进替换入口 + 复用既有执行底座**

所以再继续沿用“渐进式重构”才与 repo 历史一致。

---

## 3.3 推荐做法：同路由下的渐进式重构

推荐策略是：

> **保留 `/creative/:id` 路由，不新建外部业务页；但在这个页面内部，逐步把旧结构替换成新的页面骨架。**

这可以再分成两个层面：

### 层面 A：外部不变

- 路由不变
- 入口不变
- 列表跳转不变
- 现有 E2E 主链路入口不变

### 层面 B：内部重构

逐步引入新的：

- 页面头部
- 当前入选区
- 商品区
- 自由素材区
- 下段结果 / 发布区

把旧的混杂布局拆掉。

---

## 3.4 最佳工程落法

最推荐的工程落法不是“在原文件里一点点硬 patch 到看不懂”，
而是：

### 方案：保留页面壳，但换内部结构

例如：

- 保留 `CreativeDetail.tsx` 作为 route shell
- 新增内部组件：
  - `CreativeDetailWorkspace`
  - `CreativeCurrentSelectionSection`
  - `CreativeProductSourceSection`
  - `CreativeFreeMaterialSection`
  - `CreativeResultFollowupSection`

然后让 `CreativeDetail.tsx` 逐步改为：

> 查询数据 + 组织 mode + 拼装新组件

而不是继续把所有 UI 都堆在一个大文件里。

这本质上是：

> **重构当前页面，但通过“新组件替换旧结构”的方式完成。**

---

## 3.5 最终判断

所以第二个问题的明确答案是：

> **重构当前页面，不新建新的外部业务页面。**

更精确一点：

> **保留 `/creative/:id` 作为稳定入口，在同路由下用新的内部工作台结构逐步替换旧页面内容。**

---

## 4. 后台数据模型应该怎么考虑

## 4.1 当前模型已经具备的主骨架

从 `backend/models/__init__.py` 看，当前 Creative 领域已经有了比较完整的主骨架：

### 聚合主对象

- `CreativeItem`
- `CreativeVersion`
- `PackageRecord`
- `CheckRecord`
- `PublishPoolItem`

### 页面定义相关

- `CreativeProductLink`
- `CreativeCandidateItem`
- `CreativeInputItem`

这说明：

> **后台不是没有模型，而是已经有模型，但当前 API 投影与页面表达还没有完全对齐我们刚刚收敛出来的 PRD。**

---

## 4.2 当前模型和新页面规范的对齐情况

### 已经比较对齐的部分

#### A. 作品主对象

`CreativeItem`

适合继续作为：

- 当前作品草稿定义
- 当前页面主聚合根

#### B. 主题商品关联

`CreativeProductLink`

已经具备：

- 多商品关联
- primary product
- sort order
- enabled

这和“商品区 / 主题商品”的方向是兼容的。

#### C. 候选池来源

`CreativeCandidateItem`

已经具备：

- candidate_type
- source_kind
- source_product_id
- adopted/candidate/dismissed

这非常适合继续承载：

- 商品派生候选
- 自由素材候选

#### D. 生成输入编排

`CreativeInputItem`

已经具备：

- material_type
- material_id
- sequence
- enabled

它很适合继续承载：

- 当前视频集合
- 执行级输入编排

---

## 4.3 当前模型的主要缺口

### 缺口 1：页面“当前入选区”投影不够一等公民

当前 `CreativeItem` 里已经有：

- `current_product_name`
- `current_cover_asset_id`
- `current_copywriting_id`

但音频和视频的“当前入选”表达不够对称：

- 音频没有显式的一等公民字段
- 视频更多藏在 `CreativeInputItem`

这会带来一个问题：

> 前端很难直接拿到“当前入选区”的完整投影，只能自己拼。

---

### 缺口 2：API 返回的是通用结构，不是页面结构

当前 `CreativeDetailResponse` 里主要还是：

- `product_links`
- `candidate_items`
- `input_items`
- `input_orchestration`

这更像“领域原料”，
而不是我们要的页面结构：

- 当前入选区
- 商品区
- 自由素材区
- readiness
- 页面模式

也就是说：

> **现在更缺的是“页面投影层”，而不一定是“先改数据库表”。**

---

## 4.4 后台模型的最佳实践：分三层考虑

我建议这次后台不要直接从“表设计”想起，
而要从三层想：

### 第一层：领域真相层

继续以这些对象为真相：

- `CreativeItem`
- `CreativeProductLink`
- `CreativeCandidateItem`
- `CreativeInputItem`
- `CreativeVersion`

这层解决：

- 数据如何存
- 生成如何用
- 版本如何演进

---

### 第二层：页面投影层

为 `CreativeDetail` 单独提供更贴页面的 response projection。

建议至少提供：

- `current_selection`
  - product_name
  - cover
  - copywriting
  - audio
  - videos[]
- `product_zone`
  - primary_product
  - product_derived_candidates
- `free_material_zone`
  - free_material_candidates
- `readiness`
  - state
  - missing_fields
  - can_compose
- `page_mode`
  - definition
  - result_pending_confirm
  - published_followup

这层解决：

- 页面怎么读
- 页面怎么展示

而不是让前端自己从几十个字段里重新推理。

---

### 第三层：执行快照层

继续由：

- `CreativeVersion`
- `PackageRecord`

承接：

- 提交生成后版本冻结
- 发布前 package 冻结

这层不应被页面编辑态污染。

---

## 4.5 P0 数据模型建议：先投影，后少量增强

### 建议 A：P0 先不推倒表结构

P0 的主目标是页面结构与交互语义正确，
所以第一优先级应该是：

> **先补 API 投影层，让前端能按新页面结构读数据。**

这一步通常只需要：

- 改 schema
- 改 service projection
- 不一定立刻大改数据库表

---

### 建议 B：P0 可以做一个小幅模型增强——补音频当前真值

如果要做数据库增强，
我认为 P0 最值得做、也最克制的一步是：

- 在 `CreativeItem` 上补显式音频当前真值字段
  - 例如：`current_audio_asset_id`
  - 以及对应 `audio_mode`

原因：

- 商品名称、封面、文案已经是一等公民
- 音频在新 PRD 里也是唯一位
- 唯独音频还不够一等公民

补这一对字段后，
“四个唯一位 + 一个视频集合”的结构会更对称。

---

### 建议 C：视频不要新开一套 JSON 字段

我**不建议**为了页面方便，再给 `CreativeItem` 加一个：

- `selected_video_ids`

原因：

- `CreativeInputItem` 已经能表达多选、顺序、启用态
- 它天然更适合“视频集合”
- 再加一个 JSON 列，会制造双真相

所以视频这块的建议是：

> **继续以 `CreativeInputItem(material_type='video')` 作为 authoritative source。**

页面只需要一个更友好的 projection。

---

### 建议 D：不要为商品区 / 自由素材区再拆两张新表

当前 `CreativeCandidateItem` 已经有：

- `source_kind`
- `source_product_id`

这足以区分：

- 商品派生来源
- 自由素材来源

所以不建议再为了页面分区而引入：

- `creative_product_candidates`
- `creative_free_material_candidates`

这样的新表。

更合理的是：

> **一张候选表，两个页面分区投影。**

---

## 4.6 最终的后台策略建议

后台建议采用下面这个顺序：

### P0

1. 保持现有主表主关系不推倒
2. 优先补 `CreativeDetail` 页面投影 response
3. 视需要补 `current_audio_asset_id + audio_mode`
4. 继续复用 `CreativeInputItem` 承载视频集合

### P1

1. 进一步增强商品区 / 自由素材区摘要字段
2. 丰富候选素材展示信息
3. 丰富选择器支持能力

### P2

1. 再考虑是否需要更强的素材域抽象
2. 再考虑更复杂的浏览、筛选、审核记录表达

---

## 5. 对这三个问题的组合回答

如果把这三个问题合起来，其实答案是一套完整策略：

### 5.1 OMX 实施方法

> 先锁 PRD / 验收 / 切片，再做 P0，小步验证收口。

### 5.2 页面策略

> 保留 `/creative/:id`，在同路由下渐进式重构，不新建新的公开业务页面。

### 5.3 数据策略

> 保留现有 Creative 主模型，优先补页面投影层，只做必要的小幅模型增强，不推倒重做。

---

## 6. 我给你的明确建议

如果现在要真正开始干，我建议顺序就是：

### Step 1

先落盘：

> 《CreativeDetail P0 / P1 / P2 实现切片计划 v1》

把实施顺序锁定。

### Step 2

P0 第一个实现 slice 先做：

> **后端 `CreativeDetail` 页面投影重构**

也就是先把 API 变成更适合 A/B/C/D/E 页面结构读取的形状。

### Step 3

P0 第二个实现 slice 再做：

> **前端 `CreativeDetail` 页面骨架重构**

但仍保留 `/creative/:id`。

### Step 4

最后补：

- targeted E2E
- typecheck / build
- 文档吸收

---

## 7. 收口结论

一句话收口：

> **按 OMX 最佳实践，CreativeDetail 应该作为一次“渐进式重构项目”来做：先锁 P0 合同，再在既有 `/creative/:id` 页面上重构结构，同时以现有 Creative 数据模型为主干，只补页面投影层和必要的小幅模型增强。**

再压缩一句：

> **不新开页面，不推倒模型，先补投影，再做重构。**

