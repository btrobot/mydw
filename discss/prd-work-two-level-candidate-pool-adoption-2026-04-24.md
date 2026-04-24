# PRD — 作品二级候选池模型落地（Workbench / Detail）

## 1. 文档目标

本 PRD 覆盖将当前 creative workbench / detail 从“输入项编排中心”升级为“作品真值 + 候选池 + 当前入选”模型。

目标：

- 建立 **全局大池 → 作品小池 → 当前入选** 的稳定模型
- 让 `CreativeDetail` 成为“定义作品”的主阵地
- 让 `CreativeWorkbench` 能汇总作品当前定义完成度与入选状态
- 在不推翻现有 creative/version/package 主干的前提下渐进迁移

明确排除：

- 新后端服务或外部依赖
- 新状态管理库
- 重新设计发布/审核业务流程
- 索引优化、性能专项优化
- 视觉风格大改版

---

## 2. 背景与问题

当前系统已经具备：

- 商品管理（`products` + `videos` + `covers` + `copywritings` + `topics`）
- 作品管理（`creative_items` + `creative_versions` + `package_records`）
- detail/workbench 基础页面

但当前模型仍然更偏向：

- 用输入项来表达作品
- 用编排结构来间接表达当前作品状态

这会带来几个问题：

1. 用户难以一眼确认“当前作品最终采用了什么”
2. 商品名称 / 封面 / 文案这类唯一真值没有被提升为作品一级概念
3. 候选项和已采用项容易混淆
4. workbench 更偏流程状态视角，较少表达“定义是否完整”

因此需要把模型升级为：

> **全局大池提供资源，作品小池收敛候选，当前入选表达作品真值。**

---

## 3. 核心原则

1. **作品是输出责任主体**
2. **商品和素材是资源来源，不是作品真值**
3. **商品名称 / 封面 / 文案是唯一真值，必须显式**
4. **视频 / 音频是集合型当前入选，必须与候选区分**
5. **先让 detail 正确表达模型，再让 workbench 汇总模型**
6. **先加结构，不急着删旧结构**

---

## 4. 目标模型

## 4.1 三层模型

### 全局大池

由：

- 商品池
- 素材池

组成。

职责：

- 统一沉淀资源
- 为作品提供候选来源

### 作品小池

由作品自己持有，包含：

- 候选商品
- 候选封面
- 候选文案
- 候选视频
- 候选音频

职责：

- 收敛当前作品可选范围

### 当前入选

由作品当前状态直接表达，包含：

- 当前商品名称
- 当前封面
- 当前文案
- 当前视频集合
- 当前音频集合

职责：

- 表达作品当前采用结果
- 作为合成 / 审核 / 发布的直接输入

---

## 4.2 作品页面的核心拆分

`CreativeDetail` 目标结构：

1. **当前定义**
   - 商品名称
   - 封面
   - 文案
   - 目标时长
2. **当前入选**
   - 关联商品表
   - 当前入选视频
   - 当前入选音频
3. **候选列表**
   - 商品候选
   - 封面候选
   - 文案候选
   - 视频候选
   - 音频候选
4. **版本 / 诊断 / 发布**

`CreativeWorkbench` 目标结构：

1. summary
2. query / preset
3. 作品列表
4. diagnostics drawer

但列表摘要从“流程状态视角”为主，升级为：

- 流程状态 + 定义完成度 + 当前入选摘要

---

## 5. 范围定义

## In Scope

- 将作品唯一真值显式化
- 引入作品-商品关联表
- 引入作品候选池
- 将视频 / 音频的当前入选与候选分开
- 升级 detail 页面结构
- 升级 workbench 列表摘要与 diagnostics 视角
- 让 version/package 对齐新真值模型

## Out of Scope

- 新增 tab/subroute 信息架构
- 后端搜索/索引优化
- 上传服务重构
- 引入复杂时间线编辑器
- 真正的多轨音频工程能力

---

## 6. 用户价值

对用户的直接价值：

1. **一眼看到当前作品是什么**
2. **明确知道当前采用了哪些商品/视频/音频**
3. **候选很多时不再混淆“导入了”和“正在用”**
4. **能在 workbench 快速定位“缺真值”还是“缺入选内容”**
5. **多商品场景下有稳定心智：主题商品 + 关联商品 + 候选池**

---

## 7. Slice 划分

## Slice 1：作品真值显式化

目标：

- 把商品名称 / 封面 / 文案提升为作品一级显式状态

结果：

- detail 顶部能直接显示和编辑当前真值

## Slice 2：作品-商品关联表

目标：

- 支持一件作品关联多个商品、维护顺序、指定主题商品

结果：

- 作品不再只有一个隐含 subject product

## Slice 3：作品候选池

目标：

- 正式引入候选列表，而不是靠运行时拼装

结果：

- 可独立管理候选封面 / 文案 / 视频 / 音频

## Slice 4：当前入选媒体集合

目标：

- 让视频 / 音频从“泛输入项”中收敛成清晰的当前入选集合

结果：

- detail 页面形成“候选 ↔ 当前入选”联动

## Slice 5：Workbench 汇总升级

目标：

- 让 workbench 看懂这套新模型

结果：

- 列表和 summary 可以显示定义完成度与当前入选摘要

## Slice 6：版本 / 发布快照对齐

目标：

- 让 version/package 冻结的内容与新模型一致

结果：

- 可回看某次版本/发布到底冻结了哪套真值与入选

---

## 8. 数据模型方向

建议保留主干表：

- `creative_items`
- `creative_versions`
- `package_records`
- `products`
- `videos`
- `covers`
- `copywritings`

建议新增：

- `creative_product_links`
- `creative_candidate_items`

媒体当前入选：

- 短期兼容复用 `creative_input_items`
- 中期收敛为仅表达 `video/audio` 当前入选
- 长期视情况抽成 `creative_selected_media_items`

---

## 9. 关键产品规则

## 9.1 唯一真值

唯一真值包括：

- 商品名称
- 封面
- 文案

它们必须在作品层显式保存，并支持来源模式：

- 默认跟随
- 采用候选
- 手工覆盖

## 9.2 集合型当前入选

集合型内容包括：

- 视频
- 音频

它们必须区分：

- 候选列表
- 当前入选

## 9.3 手工覆盖优先

一旦用户手工修改：

- 该字段切换到 manual 模式
- 候选变动不再自动覆盖它

## 9.4 主题商品唯一

一件作品可关联多个商品，但：

- 主题商品只能一个

---

## 10. 页面触点

## 前端主触点

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/creativeAuthoring.ts`
- `frontend/src/features/creative/components/workbench/*`

## 后端主触点

- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- creative detail/list API
- version/package 相关 service

---

## 11. 风险

1. **模型并存期的语义混乱**
   - 新旧字段可能短期并存
2. **detail 页面改动过大导致行为回归**
   - 需要 slice 化推进
3. **workbench 摘要字段与 detail 真值不同步**
   - 需要后端统一聚合口径
4. **把候选池做成资源管理页**
   - 必须坚持“作品页优先展示当前入选”

---

## 12. 验收标准

### AC1：Detail 能正确表达作品当前定义

- 商品名称 / 封面 / 文案置顶显式
- 支持来源模式回显

### AC2：Detail 能清晰区分候选与当前入选

- 视频 / 音频当前入选集合可见
- 候选操作能联动当前入选

### AC3：多商品关系清晰

- 作品可关联多个商品
- 主题商品唯一
- 顺序可编辑

### AC4：Workbench 能汇总新模型

- 可显示当前真值摘要
- 可显示当前入选摘要
- 可识别定义完成度

### AC5：Version / Package 对齐

- 版本与发布记录能冻结真值与入选快照

---

## 13. 推荐执行模式

建议执行顺序：

1. Slice 1
2. Slice 2
3. Slice 3
4. Slice 4
5. Slice 5
6. Slice 6

推荐模式：

- 规划：`$ralplan`
- 执行：`$ralph`
- 每个 Slice 独立推进与验证

---

## 14. 最终结论

本 PRD 的本质不是“再加几张表”，而是：

> **把 creative 从输入项编排模型升级成作品真值模型。**

后续所有实现都应围绕下面这条主线保持一致：

> **先让作品定义模型成立，再让 workbench 看懂它，最后让 version/package 冻结它。**

---

## 15. 2026-04-24 总收口更新（Master Closeout Update）

本 PRD 对应的整条执行主线已经完成总收口；不再处于“待执行中”状态。

对应收口材料：

- 总收口：`discss/creative-two-level-candidate-pool-adoption-closeout-2026-04-24.md`
- 计划侧 closeout：`.omx/plans/closeout-creative-two-level-candidate-pool-adoption-2026-04-24.md`
- 计划 PRD：`.omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md`
- 计划 test spec：`.omx/plans/test-spec-creative-two-level-candidate-pool-adoption-2026-04-24.md`

### 15.1 完成矩阵

| Phase / Slice | 状态 | 代表提交 |
| --- | --- | --- |
| Phase 0 | completed | `454eac9` |
| Slice 1 | completed | `2fb9561` |
| Slice 2 | completed | `38b8a29` |
| Slice 3 | completed | `6333d13` |
| Slice 4 | completed | `a426abd`、`867c80d` |
| Slice 5 | completed | `b81fcad` |
| Slice 6 | completed | `9a49bb9` |

### 15.2 现状改写

本 PRD 中原本以 future tense 描述的关键目标，现已成为已落地约束：

1. `creative_items.current-*` 已成为作品当前真值面
2. `creative_product_links.is_primary` 已成为 primary product 的唯一主入口
3. `creative_candidate_items` 已成为作品候选池持久化表达
4. selected-media projection 已成为 video/audio 当前入选的权威读口径
5. Workbench 已切换为后端 summary aggregator
6. Version / Package / Publish 已切换为统一 freeze/manifest 口径

### 15.3 关闭边界

从 2026-04-24 起，这份 PRD 不再作为“继续往后追加 Slice”的执行文档，而是作为：

- 已实现主线的设计归档
- 后续独立 follow-up 的边界基线

以下事项如果后续继续推进，应单独立项，不再并入本 PRD：

- legacy compat write fields 的 hard-removal
- `creative_input_items` 是否迁移为独立 selected-media 物理表
- publish/runtime live verification 与 observability 增强
