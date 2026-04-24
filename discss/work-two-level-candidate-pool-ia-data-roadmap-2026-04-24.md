# 作品二级候选池：页面信息架构图 / 数据表草案 / workbench-detail 迁移 roadmap

## 0. 目标一句话

把当前 creative workbench / detail 从“围绕输入项拼装”升级为：

> **全局大池提供资源，作品小池收敛候选，当前入选表达作品真值。**

其中：

- **全局大池** = 商品池 + 素材池
- **作品小池** = 当前作品候选范围
- **当前入选** = 当前作品真正采用的内容

---

# 1. 页面信息架构图

## 1.1 全局导航关系

```text
Creative Workbench
├─ 作品列表
├─ 新建作品
│  ├─ 从商品开始
│  ├─ 从素材开始
│  └─ 从得物链接导入并初始化
└─ 进入作品详情页
   ├─ 当前定义
   ├─ 当前入选
   ├─ 候选列表
   ├─ 版本与诊断
   └─ 发布包
```

---

## 1.2 Workbench 页面信息架构

Workbench 不再只是“作品状态表”，而是要明确回答两件事：

1. 这件作品当前定义得怎么样
2. 这件作品当前入选内容是否完整、是否可生成/可审核

```text
Creative Workbench
├─ Header / Breadcrumb / Global Actions
│  ├─ 新建作品
│  ├─ 导入商品并建草稿
│  └─ 批量操作（后续）
├─ Summary 区
│  ├─ 全部作品
│  ├─ 待补素材
│  ├─ 待生成
│  ├─ 待审核
│  └─ 可发布
├─ Query & Preset 区
│  ├─ 搜索
│  ├─ 状态筛选
│  ├─ 诊断筛选
│  ├─ 高频视角 preset
│  └─ 排序 / 分页
├─ 作品列表区
│  └─ 每行作品卡/表格行
│     ├─ 基础信息（编号 / 标题 / 状态）
│     ├─ 当前真值摘要
│     │  ├─ 商品名称
│     │  ├─ 当前封面缩略图
│     │  └─ 文案摘要
│     ├─ 当前入选摘要
│     │  ├─ 商品数
│     │  ├─ 视频入选数
│     │  ├─ 音频入选数
│     │  └─ 候选池规模
│     ├─ 版本/审核/发布摘要
│     └─ 行操作
│        ├─ 继续编辑
│        ├─ 查看诊断
│        ├─ 生成版本
│        └─ 进入审核/发布
└─ Diagnostics Drawer
   ├─ 缺失真值
   ├─ 缺失入选
   ├─ 候选与当前冲突
   └─ 快捷跳转动作
```

### Workbench 列表字段建议

- 基础：`creative_no` / `title` / `status`
- 真值摘要：`current_product_name` / `current_cover_thumb` / `current_copy_excerpt`
- 入选摘要：`linked_product_count` / `selected_video_count` / `selected_audio_count`
- 候选摘要：`candidate_cover_count` / `candidate_video_count` / `candidate_audio_count`
- 诊断摘要：`missing_required_fields` / `composition_ready` / `review_ready`

### Workbench 的核心变化

当前 workbench 更偏“流程状态视角”；新模型下建议多加一层“定义完成度视角”。

也就是说一行作品不仅要看：

- 它是什么状态

还要看：

- 它当前到底选好了没有

---

## 1.3 Creative Detail 页面信息架构

Detail 页应该成为“定义作品”的主阵地。

我建议采用：

- 上方：当前定义 / 当前真值
- 中部：当前入选
- 下方或右侧：候选列表
- 底部：版本 / 诊断 / 发布

```text
Creative Detail
├─ Header
│  ├─ 返回 Workbench
│  ├─ 状态标签
│  ├─ 保存
│  ├─ 生成
│  └─ 更多操作
├─ A. 当前定义（唯一真值区）
│  ├─ 商品名称卡
│  │  ├─ 当前值
│  │  ├─ 来源（跟随主题商品 / 候选 / 手工）
│  │  └─ 操作（恢复默认 / 手工编辑）
│  ├─ 封面卡
│  │  ├─ 当前封面
│  │  ├─ 来源
│  │  └─ 操作（更换）
│  ├─ 文案卡
│  │  ├─ 当前文案
│  │  ├─ 来源
│  │  └─ 操作（采用候选 / 重新生成 / 手工编辑）
│  └─ 目标时长 / 主题商品摘要
├─ B. 当前入选区
│  ├─ 当前入选商品表
│  │  ├─ 主题商品
│  │  ├─ 关联商品顺序
│  │  └─ 操作（上移/下移/设为主题/移除）
│  ├─ 当前入选视频表
│  │  ├─ 缩略图
│  │  ├─ 来源
│  │  ├─ 顺序
│  │  ├─ 启用状态
│  │  └─ 操作（移除/排序）
│  └─ 当前入选音频表
│     ├─ 名称
│     ├─ 来源
│     ├─ 顺序/主音轨
│     └─ 操作
├─ C. 候选列表区
│  ├─ 商品候选
│  ├─ 封面候选
│  ├─ 文案候选
│  ├─ 视频候选
│  └─ 音频候选
│     每个候选项显示：
│     ├─ 来源（商品 / 素材库 / 手工上传）
│     ├─ 预览
│     ├─ 当前状态（已入选 / 未入选 / 已手工覆盖）
│     └─ 快捷动作（采用 / 加入 / 取消 / 设为当前）
├─ D. 版本与诊断区
│  ├─ 版本列表
│  ├─ 合成诊断
│  ├─ 审核诊断
│  └─ 发布诊断
└─ E. 发布包区
   ├─ 冻结后的四件套预览
   └─ 发布记录
```

---

## 1.4 新建作品页 / 初始化向导信息架构

这个页其实是 Detail 的“轻量前置版”。

```text
Create Work Wizard
├─ Step 1: 选择初始化来源
│  ├─ 从商品选择
│  ├─ 从得物链接导入
│  └─ 从素材开始
├─ Step 2: 生成作品小池
│  ├─ 关联商品
│  ├─ 自动带入商品素材
│  ├─ 选择是否带入额外素材
│  └─ 预生成文案候选
├─ Step 3: 确认当前定义
│  ├─ 商品名称
│  ├─ 封面
│  ├─ 文案
│  ├─ 默认入选视频
│  └─ 默认入选音频
└─ Step 4: 创建草稿并进入 Detail
```

---

# 2. 数据表草案

## 2.1 总体原则

建议保留当前主干对象：

- `creative_items`
- `creative_versions`
- `package_records`
- `products`
- `videos`
- `covers`
- `copywritings`

在此基础上新增“作品小池”相关表，并把 `creative_items` 从“输入项容器”提升为“当前真值载体”。

---

## 2.2 推荐表结构（目标态）

## A. creative_items（作品主表，继续保留）

### 职责

- 作品主对象
- 保存当前真值
- 保存自动/手工模式

### 建议字段

现有字段保留：

- `id`
- `creative_no`
- `title`
- `status`
- `current_version_id`
- `latest_version_no`
- `target_duration_seconds`

建议新增 / 重命名语义字段：

- `primary_product_id`
- `current_product_name`
- `product_name_mode`  
  (`follow_primary_product` / `adopted_candidate` / `manual`)
- `current_cover_asset_type`  
  (`cover`)
- `current_cover_asset_id`
- `cover_mode`  
  (`default_from_primary_product` / `adopted_candidate` / `manual`)
- `current_copywriting_id`（可空）
- `current_copywriting_text`
- `copywriting_mode`  
  (`generated` / `adopted_candidate` / `manual`)
- `selected_video_count`
- `selected_audio_count`
- `candidate_video_count`
- `candidate_audio_count`
- `candidate_cover_count`

### 说明

- `subject_product_id` 可逐步迁移为 `primary_product_id`
- `subject_product_name_snapshot` / `main_copywriting_text` 最终可并入新的 current-* 字段体系

---

## B. creative_product_links（新增：作品-商品关联表）

### 职责

- 表达作品关联了哪些商品
- 表达顺序和主题商品

### 字段建议

- `id`
- `creative_item_id`
- `product_id`
- `sort_order`
- `is_primary`
- `enabled`
- `source_mode`  
  (`manual_add` / `import_bootstrap`)
- `created_at`
- `updated_at`

### 约束建议

- `creative_item_id + product_id` 唯一
- 同一作品最多一个 `is_primary = true`

---

## C. creative_candidate_items（新增：作品候选池表）

### 职责

- 表达某个候选项已进入该作品小池
- 统一承接封面 / 文案 / 视频 / 音频候选

### 字段建议

- `id`
- `creative_item_id`
- `candidate_type`  
  (`product_name` / `cover` / `copywriting` / `video` / `audio`)
- `asset_type`  
  (`product` / `cover` / `copywriting` / `video` / `audio`)
- `asset_id`
- `source_kind`  
  (`product_derived` / `material_library` / `manual_upload` / `llm_generated`)
- `source_product_id`（可空）
- `source_ref`（可空，记录生成任务、导入批次等）
- `sort_order`
- `enabled`
- `is_default`
- `status`  
  (`candidate` / `selected` / `dismissed`)
- `created_at`
- `updated_at`

### 说明

- 这是“作品小池”的核心表
- 它不直接表达最终真值，只表达“该候选是否进入作品上下文，以及当前状态”

---

## D. creative_selected_media_items（推荐新增；兼容期也可先复用 creative_input_items）

### 职责

- 保存真正参与合成的媒体集合
- 只关注视频 / 音频

### 字段建议

- `id`
- `creative_item_id`
- `media_type`  
  (`video` / `audio`)
- `asset_id`
- `candidate_item_id`（可空，指向来自哪个候选）
- `sort_order`
- `enabled`
- `trim_in`
- `trim_out`
- `slot_duration_seconds`
- `created_at`
- `updated_at`

### 说明

- 这是“当前入选集合”的媒体部分
- 比把所有唯一真值都塞在 `creative_input_items` 更清楚

### 与现有 creative_input_items 的关系

迁移期建议：

- **短期**：继续复用 `creative_input_items`
- **中期**：约束其只表达 `video/audio` 当前入选
- **长期**：视是否值得，再 rename / replace

---

## E. creative_versions（保留）

### 建议补充字段

- `final_cover_asset_id`（可空）
- `final_cover_path`
- `final_product_name`
- `final_copywriting_text`
- `selected_video_manifest_json`
- `selected_audio_manifest_json`
- `generation_params_snapshot`

### 职责

- 保存“某次生成结果”

---

## F. package_records（保留）

### 建议补充字段

- `frozen_cover_asset_id`
- `frozen_selected_video_manifest_json`
- `frozen_selected_audio_manifest_json`
- `frozen_primary_product_id`

### 职责

- 保存“某次发布时冻结的四件套和输入快照”

---

## 2.3 一个更务实的“兼容态”方案

如果不想一次加太多表，可以先走兼容态：

### 兼容态最小改动

1. `creative_items`
   - 增加 current-* 真值字段
   - 增加 mode 字段
2. 新增 `creative_product_links`
3. 新增 `creative_candidate_items`
4. 暂时保留 `creative_input_items` 作为“当前入选媒体集合”

这样能以最小代价完成模型升级。

---

# 3. 从现有 workbench/detail 迁移到这个模型的 roadmap

## 3.1 当前基线（你现在已有的东西）

前端当前主要触点：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/components/workbench/*`
- `frontend/src/features/creative/view-models/*`
- `frontend/src/features/creative/creativeAuthoring.ts`

后端当前主要触点：

- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- creative 相关 API / service

当前模型特点：

- `creative_items` 已有：
  - `subject_product_id`
  - `subject_product_name_snapshot`
  - `main_copywriting_text`
- `creative_input_items` 还承担较泛的“输入编排”语义
- product / video / cover / copywriting 已有全局池基础

所以这次迁移不是推倒重来，而是：

> **把现有 creative 体系从“输入编排中心”慢慢迁移到“当前真值 + 候选池 + 当前入选”中心。**

---

## 3.2 迁移原则

1. **先加结构，不先删结构**
2. **先让 detail 页能表达新模型**
3. **再让 workbench 汇总新摘要**
4. **最后再收敛旧字段 / 旧语义**

---

## 3.3 推荐迁移切片

## Slice 1：作品真值显式化（最先做）

### 目标

先把商品名称 / 封面 / 文案从“隐含状态”提升成 detail 页显式真值。

### 后端改动

- `creative_items` 增加：
  - `primary_product_id`
  - `current_product_name`
  - `product_name_mode`
  - `current_cover_asset_id`
  - `cover_mode`
  - `current_copywriting_text`
  - `copywriting_mode`
- `CreativeDetailResponse` 返回这些字段

### 前端改动

- `CreativeDetail.tsx`
  - 增加“当前定义”区块
- `useCreativeAuthoringModel.ts`
  - 管理 unique truth state
- `creativeAuthoring.ts`
  - 收敛 parse/build 逻辑

### 验收

- Detail 页顶部能直接看到：
  - 当前商品名称
  - 当前封面
  - 当前文案
- 用户修改后能正确保存、回显

---

## Slice 2：作品-商品关联表落地

### 目标

让作品可以明确关联多个商品，并有主题商品 / 顺序语义。

### 后端改动

- 新增 `creative_product_links`
- `CreativeDetailResponse` 增加 `linked_products`

### 前端改动

- `CreativeDetail.tsx`
  - 增加“当前入选商品表”
- 增加：
  - 设为主题商品
  - 调整顺序
  - 移除商品

### 验收

- 一件作品可关联多个商品
- 主题商品唯一
- 主题商品变化能联动默认商品名/封面来源

---

## Slice 3：作品候选池落地

### 目标

把“候选列表”正式建模，而不是靠运行时拼凑。

### 后端改动

- 新增 `creative_candidate_items`
- 增加接口：
  - 获取作品候选池
  - 增加候选
  - 移除候选
  - 采用候选

### 前端改动

- `CreativeDetail.tsx`
  - 新增候选区
- 组件拆分建议：
  - `WorkCurrentDefinitionCard`
  - `WorkSelectedMediaPanel`
  - `WorkCandidatePanel`
  - `WorkProductLinkTable`

### 验收

- 候选封面 / 文案 / 视频 / 音频可以独立查看
- 来源可见
- 候选操作能联动当前入选

---

## Slice 4：当前入选媒体集合收敛

### 目标

把视频 / 音频的“当前入选”从泛化 input 编排语义里剥离清楚。

### 后端改动

二选一：

#### 方案 A（推荐更稳）

- 先继续使用 `creative_input_items`
- 但约束其只承担 video/audio 当前入选

#### 方案 B（更干净）

- 新增 `creative_selected_media_items`
- 再把旧 `creative_input_items` 逐步兼容淘汰

### 前端改动

- `CreativeDetail.tsx`
  - 形成“候选表 ↔ 当前入选表”双区
- `useCreativeVersionReviewModel.ts`
  - 读取当前入选结果

### 验收

- 视频 / 音频有明确当前入选集合
- 支持排序 / 启停 / 移除
- 合成仅读当前入选集合

---

## Slice 5：Workbench 汇总升级

### 目标

让 workbench 真正能看见“当前定义完成度”和“当前入选状态”。

### 后端改动

- 列表接口增加摘要字段：
  - `current_product_name`
  - `selected_video_count`
  - `selected_audio_count`
  - `candidate_video_count`
  - `candidate_audio_count`
  - `definition_ready`
  - `composition_ready`

### 前端改动

- `CreativeWorkbench.tsx`
- `WorkbenchSummaryCard.tsx`
- `WorkbenchTable.tsx`
- `WorkbenchPresetBar.tsx`
- `WorkbenchDiagnosticsDrawer.tsx`

### 验收

- Workbench 能直接看到每件作品当前采用了什么、缺什么
- 高频视角/preset 能基于新摘要筛选

---

## Slice 6：版本 / 发布快照对齐

### 目标

把版本与发布也对齐到新模型，保证可追溯。

### 后端改动

- `creative_versions`
  - 存 final 四件套 + 当前入选快照
- `package_records`
  - 冻结发布时四件套 + 入选快照

### 前端改动

- `VersionPanel.tsx`
- `CheckDrawer.tsx`
- diagnostics / publish 相关 view-model

### 验收

- 每次版本都能回看当时采用的封面 / 名称 / 文案 / 入选媒体
- 发布包可稳定回溯

---

## 3.4 推荐执行顺序（最务实版）

如果要尽量降低风险，我建议按下面顺序做：

### Phase A：先让 Detail 正确表达新模型

1. Slice 1：作品真值显式化
2. Slice 2：作品-商品关联表
3. Slice 3：候选池
4. Slice 4：当前入选媒体集合

### Phase B：再让 Workbench 汇总新模型

5. Slice 5：Workbench 汇总升级

### Phase C：最后对齐版本 / 发布

6. Slice 6：版本 / 发布快照对齐

这个顺序的好处是：

- Detail 先稳定，用户能真正编辑新模型
- Workbench 再基于 detail 已稳定的数据做汇总
- 版本 / 发布最后补齐，不会反复返工

---

## 3.5 与当前代码文件的建议对应关系

## 前端

### 优先改动

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/creativeAuthoring.ts`

### 第二批改动

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchTable.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchSummaryCard.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchDiagnosticsDrawer.tsx`

### 可能新增组件

- `components/detail/CurrentDefinitionCard.tsx`
- `components/detail/SelectedMediaTable.tsx`
- `components/detail/CandidateListPanel.tsx`
- `components/detail/ProductLinkTable.tsx`

## 后端

### 优先改动

- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- creative detail / list API

### 第二批改动

- composition / version / package service

---

## 3.6 测试建议

## 前端

- Detail：
  - 当前真值回显
  - 候选切换联动当前入选
  - 手工编辑后不再被自动覆盖
- Workbench：
  - 新摘要字段展示
  - preset / filter 基于新状态工作

## 后端

- 多商品关联
- 主题商品唯一性
- 候选池增删改查
- 当前入选媒体排序
- 版本 / 发布快照冻结正确

---

## 3.7 最终收口建议

如果只用一句话描述这次迁移的本质，它不是“多加几张表”，而是：

> **把 creative 从“输入项编排模型”升级成“作品真值模型”。**

再展开一点就是：

- 当前 `creative_input_items` 更像“系统怎么拼”
- 你现在要的模型更像“作品当前到底是什么”

这次 roadmap 的目标，就是把两者拆开：

- **作品真值**
- **候选池**
- **当前入选**
- **版本 / 发布快照**

让它们各自职责清楚。

---

## 4. 最终结论

我建议你后续真正执行时，按下面这条主线推进：

1. **先把 Detail 做成“当前定义 + 当前入选 + 候选列表”的页面**
2. **再把 Workbench 做成“定义完成度 + 入选状态”的汇总页**
3. **最后把版本和发布包对齐到这套真值模型**

一句话总结：

> **先让作品定义模型成立，再让工作台看懂它，最后让版本/发布冻结它。**

---

## 5. 2026-04-24 执行收口状态

这份 roadmap 对应的执行主线现已完成，不再是待实施路线图，而是**已落地路线图回放**。

### 5.1 完成矩阵

| 项目 | 状态 | 代表提交 |
|---|---|---|
| Phase 0 合同冻结 | 已完成 | `454eac9` |
| Slice 1 作品真值显式化 | 已完成 | `2fb9561` |
| Slice 2 作品-商品关联表 | 已完成 | `38b8a29` |
| Slice 3 作品候选池 | 已完成 | `6333d13` |
| Slice 4 当前入选媒体集合 | 已完成 | `a426abd`、`867c80d` |
| Slice 5 Workbench 汇总升级 | 已完成 | `b81fcad` |
| Slice 6 Version / Package 对齐 | 已完成 | `9a49bb9` |

### 5.2 roadmap 与实际落地的对应关系

本 roadmap 的三段式执行顺序已经按原建议完成：

1. **Phase A：先让 Detail 正确表达新模型**  
   - 已完成 Slice 1 / 2 / 3 / 4
2. **Phase B：再让 Workbench 汇总新模型**  
   - 已完成 Slice 5
3. **Phase C：最后对齐版本 / 发布**  
   - 已完成 Slice 6

也就是说，这份 roadmap 当初主张的执行顺序最终被证明是可执行且可收口的，没有出现需要改写主线路径的重大偏差。

### 5.3 当前可视为已稳定的系统结构

当前 creative 页面与数据模型可以概括为：

- **当前定义**：由 `creative_items.current-*` 承接
- **商品关联**：由 `creative_product_links` 承接
- **作品候选池**：由 `creative_candidate_items` 承接
- **当前入选媒体**：由 selected-media projection 承接（迁移期仍物理复用 `creative_input_items`）
- **Workbench 汇总**：由后端聚合摘要承接
- **Version / Package / Publish freeze**：由统一的 freeze/manifest contract 承接

### 5.4 这份 roadmap 现在的角色

从 2026-04-24 起，这份文档不再主要用于“指导下一步先做什么”，而更适合作为：

1. 本轮迁移的 IA / data / rollout 回放文档
2. 新成员理解这条主线是怎么收口的入口文档
3. 后续 follow-up 的边界说明

### 5.5 后续不再属于本 roadmap 主线的事项

以下事项如果继续推进，应单列 follow-up：

- legacy compat write fields 的 hard-removal
- `creative_input_items` 是否迁出为独立 selected-media 表
- publish/runtime live verification 与观测增强

因此，roadmap 主线的结论可以更新为：

> **这条路线已经走完；后续不是继续追加 Slice，而是围绕兼容收紧、物理清理与生产验证做独立 follow-up。**
