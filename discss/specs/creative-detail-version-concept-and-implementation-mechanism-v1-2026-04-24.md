# 《CreativeDetail 里的“版本”概念与实现机制说明 v1》

> 日期：2026-04-24  
> 适用范围：CreativeDetail / CreativeVersion / Review / PublishPackage / PublishPool  
> 目的：解释当前项目里“版本”到底是什么、为什么需要它、它与作品/审核/发布之间的关系是什么  
> 状态：Draft

---

## 1. 一句话结论

在当前项目里：

> **Creative 是“作品定义”，CreativeVersion 是“某一次生成出来并被记录下来的结果快照”。**

也就是说：

- `Creative` 回答：**我要做什么**
- `CreativeVersion` 回答：**这一次实际做出了什么**

版本不是草稿本身，  
版本也不是发布包本身，  
版本是处在两者之间的：

> **“从作品定义到最终发布之间的结果冻结层”**

---

## 2. 为什么一定要有“版本”

如果没有版本，系统会出现一个根本问题：

> 用户不断改同一个作品定义，但系统又要保留每次生成出来的结果、审核结论、发布对应关系。

这三件事天然冲突：

1. 作品定义是会继续改的
2. 某次生成结果必须固定下来
3. 审核和发布必须指向某个确定结果

所以必须插入一个中间层：

> **Version = 一次结果的稳定引用点**

它的作用是：

- 冻结一次生成结果
- 让审核有明确对象
- 让发布有明确来源
- 让历史可追溯

---

## 3. 版本与几个核心对象的关系

## 3.1 Creative

`Creative` 是作品主对象。

它保存的是：

- 作品标题
- 当前商品定义
- 当前文案定义
- 当前封面定义
- 当前输入编排
- 目标时长
- 当前整体状态

它更像：

> **作品工作台上的“当前草稿定义”**

---

## 3.2 CreativeVersion

`CreativeVersion` 是某次结果快照。

从当前 API 类型可以看到，版本里有这些关键字段：

- `id`
- `version_no`
- `parent_version_id`
- `version_type`
- `title`
- `actual_duration_seconds`
- `final_video_path`
- `final_product_name`
- `final_copywriting_text`
- `package_record_id`
- `latest_check`
- `is_current`

这说明版本记录的不是“输入候选池”，而是**结果侧真值**，比如：

- 最终视频路径
- 最终商品名
- 最终文案
- 实际时长

所以版本更像：

> **一次生成后被系统认领的结果对象**

---

## 3.3 Review（审核）

审核不是挂在 `Creative` 草稿上的，  
而是挂在 **某个 version** 上的。

从类型里可以看到：

- `CheckRecord.creative_version_id`
- `CreativeReviewSummary.current_version_id`

这意味着：

> **审核的对象是版本，不是抽象的作品定义。**

这样做是对的，因为审核必须针对一个确定结果。

---

## 3.4 PackageRecord（发布包）

发布包也不是直接挂在作品草稿上，  
而是挂在 **某个 version** 上。

关键字段：

- `package_record_id`
- `package_record.creative_version_id`
- `frozen_video_path`
- `frozen_cover_path`
- `frozen_duration_seconds`
- `frozen_product_name`
- `frozen_copywriting_text`

这说明发布包表达的是：

> **准备发布时，对某个版本结果再次冻结后的发布载荷**

所以：

- `Version` 是结果冻结层
- `PackageRecord` 是发布冻结层

---

## 3.5 PublishPool

PublishPool 里放的不是抽象作品，而是：

- `creative_item_id`
- `creative_version_id`
- `creative_current_version_id`

这套字段很关键，它说明发布池关注的是：

> **当前池里的候选版本，是否仍然等于该作品当前有效版本**

这就是为什么工作台会有：

- `version_mismatch`

因为如果作品当前版本变了，而池里还是旧版本，就出现：

> **发布候选和当前结果未对齐**

---

## 4. 当前项目里，“版本”在业务上到底代表什么

从领域语义上看，当前项目的版本不是 Git 那种源码版本，也不是表单保存历史。

它更准确地说是：

> **“作品的一次结果产出版本”**

它有 4 个核心特征：

### 4.1 它来自某次生成/产出

不是每次保存都会生成版本。  
版本通常是在“提交生成”之后出现。

---

### 4.2 它有自己的编号

- `version_no`

这说明它是作品内部的顺序版本，而不是全局随机快照。

---

### 4.3 它可以有父版本

- `parent_version_id`

这说明版本之间是允许形成链路的，比如：

- V1 是首版
- V2 基于 V1 调整
- V3 基于 V2 再生成

所以版本不是平铺列表，而是带演进关系的。

---

### 4.4 它承接审核与发布

版本是审核对象，也是发布包的来源对象。

这意味着版本处于链路中间：

```text
Creative 定义
  -> 生成
  -> CreativeVersion
  -> 审核
  -> PackageRecord
  -> PublishPool / 发布
```

---

## 5. 当前实现机制：版本是怎么进系统的

## 5.1 创建作品时，不一定有版本

当前代码里：

- 列表页点“创建作品”
- 先创建 `Creative`
- 然后跳到 `/creative/{id}`

此时通常只是有一个作品对象，  
不代表已经有结果版本。

所以：

> **Creative 创建 = 建立作品壳；不等于生成版本。**

---

## 5.2 提交生成时，系统进入“版本产生”的关键节点

当前前端通过：

- `POST /api/creatives/{creative_id}/submit-composition`

发起生成。

这一步的业务含义不是“普通保存”，而是：

> **拿当前 Creative 定义去生成一个结果版本。**

从 e2e mock 的行为可以看到，提交后会把作品推进到：

- `WAITING_REVIEW`
- 并设置 `current_version_id`

这意味着在当前实现心智里：

> **一旦生成成功，系统会把某个 version 认定为当前版本。**

---

## 5.3 CreativeDetail 同时返回“当前版本投影”和“版本列表”

在 `CreativeDetailResponse` 里，当前接口同时返回：

- `current_version_id`
- `current_version`
- `versions`
- `review_summary`

这代表后端在 detail 接口里做了两层读模型：

### A. 当前版本投影

- `current_version`

给当前页首屏快速展示用。

### B. 历史版本列表

- `versions`

给版本面板、历史回看、审核记录用。

这是一种很合理的 detail 聚合方式。

---

## 5.4 current_version 是“当前生效结果”的便捷投影

当前类型里：

- `current_version` 是 `CreativeCurrentVersionResponse`
- `versions` 是 `CreativeVersionSummaryResponse[]`

这说明：

> `current_version` 不是另一个独立对象，  
> 而是“当前版本”的轻量投影 / 当前读模型。

它的作用是：

- 让主页面不用每次自己从 `versions` 里找一遍
- 让首屏直接读到“当前结果”

---

## 5.5 versions 是完整版本时间线

`versions` 列表里包含：

- `is_current`
- `version_no`
- `parent_version_id`
- `latest_check`
- `package_record`

这说明版本列表承担的是：

- 历史查看
- 当前版本标记
- 审核记录承接
- 发布包对齐查看

所以它不是单纯“历史记录”，而是：

> **作品结果时间线**

---

## 6. 审核机制为什么必须围绕版本转

当前审核抽屉 `CheckDrawer` 提交时，传的是：

- `version_id`

而不是只传 `creative_id`。

例如：

- approve
- rework
- reject

这些操作都明确绑定当前 version。

这很重要，因为如果审核只挂在作品上，会出现歧义：

> 你审核的是哪一版结果？

而有了 `version_id`，这个问题就消失了。

所以机制上：

> **审核记录是 version-scoped，不是 creative-scoped。**

`Creative.review_summary` 只是把“当前有效审核结论”投影回作品页。

---

## 7. 发布机制为什么也必须围绕版本转

当前发布相关结构里，发布池和发布包都引用版本：

- `PackageRecord.creative_version_id`
- `PublishPoolItem.creative_version_id`

原因同样很直接：

> 发布必须针对一个确定的结果，而不能针对会继续变化的草稿定义。

如果没有 version 这一层，发布会遇到两个大问题：

1. 用户后来改了作品定义，已发布内容对应不上
2. 无法确认发布的是哪次生成结果

所以机制上必须是：

> **先有 version，再从 version 冻结 package，再从 package / pool 走发布。**

---

## 8. “当前版本”是什么意思

在当前项目里，`current_version_id` 不是“最新创建的版本”这么简单。

它更准确的意思是：

> **当前作品被系统视为正在生效/正在承接后续流程的那个结果版本**

它可能同时承担：

- 当前结果展示
- 当前审核摘要关联
- 当前发布候选对齐判断

所以“当前版本”是一个业务位，不只是排序位。

---

## 9. parent_version_id 的意义

`parent_version_id` 说明当前版本是从哪个版本演化来的。

这意味着版本机制并不是“每次都从零独立生成”，  
而是支持：

- 基于上一个结果继续修
- 基于某个版本再派生

它给后续这些能力预留了空间：

- 新版本派生
- 返工链路追溯
- AIClip 基于某个 source version 再生成

从 `CreativeAiClipWorkflowSubmitRequest.source_version_id` 也能看出来：

> 有些后续工作流本质上就是“从一个已有 version 再派生新 version”。

---

## 10. 当前版本机制的实现特点

结合当前代码和 mock，可以总结出 5 个实现特点。

## 10.1 版本是结果真值层，不是输入真值层

当前输入真值仍主要在：

- `Creative`
- `input_items`
- `product_links`
- `candidate_items`

版本里保存的是：

- `final_video_path`
- `final_product_name`
- `final_copywriting_text`
- `actual_duration_seconds`

所以版本是：

> **输出真值层**

---

## 10.2 版本是审核和发布的枢纽层

审核挂版本，发布包挂版本，发布池也对版本。

所以版本是整个链路的中枢：

```text
定义层（Creative）
  -> 结果层（Version）
  -> 审核层（Check）
  -> 发布冻结层（Package）
  -> 发布执行层（Pool / Publish）
```

---

## 10.3 当前 detail 页已经把“版本”当成一级对象了

从 `VersionPanel` 和 `CreativeDetail` 可以看到：

- 首屏显示当前版本结果
- 单独显示版本列表
- 单独显示审核摘要
- 单独显示 package freeze

这说明当前产品语义里：

> **Version 已经不是附属字段，而是一级业务对象。**

---

## 10.4 current_version 与 versions 是“快读 + 全量”的双读模型

这是当前实现的一个好点：

- `current_version` 负责主界面快读
- `versions` 负责完整时间线

这能减少前端页面自行拼装复杂度。

---

## 10.5 publish 侧还有“版本是否对齐”的额外约束

当前 workbench 和 diagnostics 会看：

- `creative_version_id`
- `creative_current_version_id`

如果不一致，就会出现：

- `version_mismatch`

这说明版本机制不只是历史记录，  
它还是当前发布一致性的关键检查点。

---

## 11. 用一句更业务的话解释“版本”

如果不用技术术语，对业务方可以这样说：

> **作品是“要做什么”，版本是“这一次做出来了什么”。**

再细一点：

- 作品可以一直改
- 版本是一轮结果快照
- 审核是对版本做判断
- 发布是拿版本去冻结和发出

---

## 12. 如果从单用户心智重新解释版本

在你们现在更偏单用户的使用场景里，版本最好不要讲成“复杂审批对象”，而要讲成：

> **每次生成出来的一版结果**

这样用户更容易理解：

- 我编辑作品
- 我生成一版结果
- 我确认这版结果
- 我决定是否继续发布

所以对单用户来说，“版本”最自然的理解就是：

> **结果版**

而不是：

> 审批版 / 流程节点

---

## 13. 最终结论

### 13.1 概念上

`CreativeVersion` 是：

> **作品的一次结果快照**

不是作品草稿本身，也不是发布包本身。

---

### 13.2 机制上

当前实现大致是：

```text
创建 Creative
  -> 编辑 Creative 定义
  -> submit-composition
  -> 生成 current_version / versions 中的新版本
  -> review 绑定 version_id
  -> package_record 绑定 creative_version_id
  -> publish_pool 继续绑定 creative_version_id
```

---

### 13.3 业务价值上

版本机制解决了 4 件事：

1. 结果冻结
2. 历史追溯
3. 审核可定位
4. 发布可对齐

---

### 13.4 对页面设计的直接启发

CreativeDetail 不应该只看成“编辑页”，  
它本质上还承载着：

- 当前作品定义
- 当前结果版本
- 当前结果审核
- 当前版本发布对齐

所以页面真正的结构应该是：

> **定义层 + 结果版本层 + 发布承接层**

而不能把所有东西都混在一个“草稿表单”里看。

