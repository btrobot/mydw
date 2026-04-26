# CreativeDetail 精简重构实现计划

> 日期：2026-04-25
> 基于：`creative-detail-redesign-proposal.md`
> 决策：删除视频时序编辑功能（trim_in、trim_out、slot_duration_seconds、role）

---

## 一、现状分析

### 1.1 当前组件结构

```
CreativeDetail.tsx (2,228 行)
├── useCreativeAuthoringModel (状态管理 + API 调用)
├── useCreativePublishDiagnosticsModel (发布诊断)
├── useCreativeVersionReviewModel (版本审核)
├── projection.ts (投影模型构建)
│
├── CreativeDetailHeroCard (Hero 卡片)
├── CreativeCurrentSelectionSection (A 区)
├── CreativeSourceZoneSection (B/C 区复用)
│
├── legacy editor (800 行，Form + Form.List)
│   ├── product_links 编辑
│   ├── candidate_items 编辑
│   └── input_items 编辑（含视频时序）
│
└── D/E 区 (版本结果、发布诊断)
```

### 1.2 关键依赖

| 模块 | 职责 | 改动影响 |
|------|------|---------|
| `useCreativeAuthoringModel` | Form 状态 + API 调用 | 核心改动：改为实时 API 调用 |
| `projection.ts` | 数据投影模型 | 保留，改为基于 creative query 数据 |
| `useCreatives` hooks | API 层（useUpdateCreative） | 保留，无需改动 |

### 1.3 API 层

当前 API：
- `PATCH /api/creatives/{id}` — 更新作品定义
- `POST /api/creatives/{id}/submit` — 提交合成

后端 API 设计已经是细粒度的（单一字段更新），前端可以做到每个操作直接调用 API。

---

## 二、实现阶段

### Phase 0：准备（先于一切）

**目标**：验证 API 能力 + 锁定现有测试

#### Step 0.1：验证 PATCH API 字段支持

读取并验证 `backend/` 中 `PATCH /api/creatives/{id}` 接口支持的字段：
- `current_cover_asset_id`
- `current_copywriting_id`
- `current_product_name`
- `input_items`（视频入选列表）

确认每个操作的 API payload 结构。

#### Step 0.2：锁定现有 E2E 测试

标记当前测试为 baseline snapshot：
- 不在改动期间修改现有测试断言
- 改动完成后统一更新测试

---

### Phase 1：核心闭环（最关键）

**目标**：实现"区内操作 → 实时 API 调用 → A 区刷新"闭环

**视频操作简化决策**：
- 视频只做入选/移出，不做时序编辑（trim_in、trim_out、slot_duration_seconds、role 全部删除）
- 视频集合卡片只显示已入选视频列表和添加/移除按钮

#### Step 1.1：重构 useCreativeAuthoringModel

**改动**：将 Form 状态管理改为直接 API 调用

```
原：handleSetCurrentCover() → form.setFieldValue() → handleSaveInput() → PATCH API
改：handleSetCurrentCover() → PATCH API → refetch → A 区刷新
```

具体改动：

```typescript
// 改为每个操作直接调用 API（使用乐观更新）
const handleSetCurrentCover = useCallback(async (assetId?: number) => {
  // 1. 乐观更新（立即更新 UI）
  // 2. 调用 API
  await updateCreative.mutateAsync({ current_cover_asset_id: assetId })
  // 3. 刷新数据
  await refreshCreative()
}, [updateCreative, refreshCreative])

const handleToggleSelectedVideo = useCallback(async (assetId: number) => {
  // 获取当前选中列表，添加或移除 assetId
  // 调用 API
  await updateCreative.mutateAsync({ input_items: newInputItems })
  await refreshCreative()
}, [updateCreative, refreshCreative])
```

**文件**：`frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`

**工作量**：中

#### Step 1.2：改造 projection.ts

**改动**：去掉 `draft` 参数依赖，改为基于 `creative` query 数据直接计算

```
原：projection 依赖 Form 数据 + creative 数据合并
改：projection 只依赖 creative 数据
```

- 删除 `DraftProjectionState` 和相关逻辑
- `projection.ts` 简化为纯数据转换函数
- A/B/C 区直接消费 projection 输出

**文件**：`frontend/src/features/creative/components/detail/projection.ts`

**工作量**：小

#### Step 1.3：实现 A 区卡片

**改动**：新建 A 区组件，替代 `CreativeCurrentSelectionSection`

```
新建文件：
  frontend/src/features/creative/components/detail/CurrentSelectionPanel.tsx
    ├── ProductNameCard（商品名唯一位）
    ├── CoverCard（封面唯一位）
    ├── CopywritingCard（文案唯一位）
    ├── AudioCard（音频唯一位）
    └── VideoCollectionCard（视频集合位，仅入选/移除）
```

每个卡片：
- 显示当前值 + 来源标签
- 操作按钮（编辑 / 更换 / 移除）
- 缺失时显示占位 + 快速入口

**视频卡片简化**：只显示已入选视频列表 + [移除] 按钮，无时序编辑。

**不调用 Form**，直接使用 `useCreativeAuthoringModel` 提供的操作函数。

**工作量**：中

#### Step 1.4：实现 B/C Tab 来源区

**改动**：新建来源 Tab 组件

```
新建文件：
  frontend/src/features/creative/components/detail/SourcePanel.tsx
    ├── SourceTabs（Tab 切换）
    ├── ProductSourceTab（B 区）
    │   ├── ProductSummary（商品摘要）
    │   └── CandidateList（候选素材列表）
    └── FreeMaterialSourceTab（C 区）
        ├── UploadActions（上传入口）
        └── CandidateList（候选素材列表）
```

候选操作：
- 封面 / 音频 / 文案（唯一位）：[采用] → 调用 `handleSetCurrentCover` 等
- 视频（集合位）：[入选] / [移出] → 调用 `handleToggleSelectedVideo`

**工作量**：中

#### Step 1.5：精简 Header

**改动**：新建 Header 组件

```
新建文件：
  frontend/src/features/creative/components/detail/CreativeDetailHeader.tsx
```

包含：
- 返回入口
- 作品名称（可点击编辑）
- 状态标签（草稿 / 部分就绪 / 可生成）
- 主 CTA（提交合成）
- 辅助信息（最近更新时间、缺失项）

**不包含**：Alert 提示、次 CTA 按钮组

**工作量**：小

---

### Phase 2：移除旧代码

**目标**：删除 legacy editor 和 D/E 区

#### Step 2.1：删除 legacy editor

**删除**：`CreativeDetail.tsx` 中的 legacy editor 代码（约 600 行）

删除区域：
- `id="creative-detail-legacy-editor"` 整个 Card
- Form.List 的 product_links / candidate_items / input_items
- 相关的保存 / 提交按钮

#### Step 2.2：删除 D/E 区

**删除**：
- 版本结果卡片（`currentVersionResult`）
- 审核结论卡片（`effectiveCheck`）
- VersionPanel
- 高级诊断 Drawer
- AIClip Drawer
- 所有相关的 useCreativePublishDiagnosticsModel / useCreativeVersionReviewModel 调用

#### Step 2.3：删除无用组件和目录

| 文件/目录 | 说明 |
|----------|------|
| `components/detail/CreativeDetailHeroCard` | 删除 |
| `components/detail/CreativeCurrentSelectionSection` | 删除 |
| `components/detail/CreativeSourceZoneSection` | 删除 |
| `components/diagnostics/` 目录 | 删除 |
| `components/VersionPanel.tsx` | 删除 |
| `components/AIClipWorkflowPanel.tsx` | 删除（如确定移除） |

#### Step 2.4：清理 hooks 和 imports

删除不再使用的：
- `useCreativePublishDiagnosticsModel`
- `useCreativeVersionReviewModel`
- 相关 Alert 组件

---

## 三、重构后的页面结构

### 3.1 组件树

```
CreativeDetail.tsx (精简后约 500 行)
├── CreativeDetailHeader (新建)
├── CurrentSelectionPanel (A 区，新建)
│   ├── ProductNameCard
│   ├── CoverCard
│   ├── CopywritingCard
│   ├── AudioCard
│   └── VideoCollectionCard（仅入选/移除，无时序）
├── SourcePanel (B/C 区，新建)
│   ├── SourceTabs
│   ├── ProductSourceTab
│   └── FreeMaterialSourceTab
└── [无 D/E 区，无 legacy editor]
```

### 3.2 状态流

```
用户操作（B/C 区 [采用] 按钮）
    ↓
handleSetCurrentCover() / handleToggleSelectedVideo()
    ↓
updateCreative.mutateAsync({ ... })
    ↓
refreshCreative()
    ↓
creative 数据更新
    ↓
projection.ts 重新计算
    ↓
CurrentSelectionPanel 重新渲染
```

---

## 四、文件变更清单

### 4.1 新建文件

| 文件 | 用途 |
|------|------|
| `components/detail/CreativeDetailHeader.tsx` | 精简 Header |
| `components/detail/CurrentSelectionPanel.tsx` | A 区面板 |
| `components/detail/SourcePanel.tsx` | B/C Tab 来源区 |

### 4.2 修改文件

| 文件 | 改动 |
|------|------|
| `view-models/useCreativeAuthoringModel.ts` | 改为实时 API 调用 + 乐观更新 |
| `components/detail/projection.ts` | 去掉 draft 依赖，简化 |
| `pages/CreativeDetail.tsx` | 重写（约 500 行） |

### 4.3 删除文件/代码

| 文件/区域 | 改动 |
|----------|------|
| legacy editor（~600 行） | 删除 |
| D/E 区（~300 行） | 删除 |
| `useCreativePublishDiagnosticsModel` 调用 | 删除 |
| `useCreativeVersionReviewModel` 调用 | 删除 |
| `CreativeDetailHeroCard` | 删除 |
| `CreativeCurrentSelectionSection` | 删除 |
| `CreativeSourceZoneSection` | 删除 |
| `components/diagnostics/` 目录 | 删除 |
| `components/VersionPanel.tsx` | 删除 |
| `components/AIClipWorkflowPanel.tsx` | 删除（确认后） |

---

## 五、测试策略

### 5.1 锁定现有测试

现有测试位置：`frontend/e2e/creative-workbench/creative-workbench.spec.ts`

**改动期间策略**：
- 不修改现有测试断言
- Phase 1-2 完成后统一更新测试

### 5.2 新增测试

```
e2e/creative-detail/
├── current-selection-panel.spec.ts
│   ├── renders all selection cards
│   ├── updates product name in real-time
│   ├── updates cover in real-time
│   ├── adds video to selection
│   └── removes video from selection
├── source-panel.spec.ts
│   ├── switches between product and free tabs
│   ├── adopts cover from product zone
│   ├── adopts video from free zone
│   └── video toggle updates current selection
└── header.spec.ts
    ├── shows status tag
    ├── shows missing items
    └── submit button enabled when ready
```

### 5.3 测试覆盖目标

- 区内操作（采用 / 移出）：100% 覆盖
- 实时刷新：验证 A 区响应时间 < 500ms
- 状态标签：正确显示草稿 / 部分就绪 / 可生成

---

## 六、风险与缓解

### 6.1 API 调用频率增加

**风险**：每个操作都调用 API，可能导致频繁网络请求。

**缓解**：
- 使用乐观更新（先更新 UI，后调 API）
- 减少用户感知延迟

### 6.2 视频操作并发

**风险**：用户快速点击多个视频时，并发 API 调用可能产生竞态。

**缓解**：
- 使用 React Query mutation 的 `onMutate` 实现乐观更新
- 避免竞态条件

### 6.3 后端 API 兼容性

**风险**：后端 API 可能不支持单字段更新。

**缓解**：
- Phase 0 验证每个操作的 API payload
- 当前后端 `PATCH /api/creatives/{id}` 支持部分字段更新

---

## 七、验收标准

### 7.1 功能验收

- [ ] 用户从商品 Tab 选封面，A 区封面 1 秒内更新
- [ ] 用户从自由素材 Tab 入选视频，A 区视频列表实时更新
- [ ] 页面不显示"保存"按钮
- [ ] Header 精简：标题 + 状态 + 主 CTA
- [ ] 无 legacy editor 代码
- [ ] 无 D/E 区代码
- [ ] 视频集合无时序编辑功能

### 7.2 性能验收

- [ ] A 区刷新时间 < 500ms（API 响应 + React 渲染）
- [ ] 无内存泄漏

### 7.3 测试验收

- [ ] 区内操作 E2E 测试覆盖
- [ ] 所有现有测试通过

---

## 八、工作量估算

| Phase | 任务 | 工作量 |
|-------|------|--------|
| Phase 0 | API 验证 + 测试准备 | 小 |
| Phase 1.1 | 重构 useCreativeAuthoringModel + 乐观更新 | 中 |
| Phase 1.2 | 改造 projection.ts | 小 |
| Phase 1.3 | 实现 A 区卡片（简化版，无时序） | 中 |
| Phase 1.4 | 实现 B/C Tab 来源区 | 中 |
| Phase 1.5 | 精简 Header | 小 |
| Phase 2 | 删除旧代码 + 清理 | 小 |

**总计**：约 1.5-2 周工作量（比原计划减少，因删除视频时序功能）

---

## 九、第一步建议

从 `Phase 0` 开始：

1. 读取 `backend/` 中 `PATCH /api/creatives/{id}` 的 schema 定义
2. 读取 `useCreatives.ts` 了解 `useUpdateCreative` 的 mutation 方式
3. 验证每个字段的 API payload 结构
4. 从 `Phase 1.2` 开始：改造 `projection.ts`，去掉 draft 依赖
5. 从 `Phase 1.1` 开始：实现最小闭环——`creativeQuery.data` → A 区封面卡片 → 调 API → `refetch` → 卡片刷新
