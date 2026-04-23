# ADP UI System Adoption Slice 2：PageContainer / ListPageLayout 评估收口

日期：2026-04-23

## 1. Slice 目标

本 Slice 只处理 PageContainer 使用约定与 `ListPageLayout` 是否仍有价值的评估，不迁移 CreativeDetail、CheckDrawer、Dashboard、TaskCreate，也不改变 Workbench 的 URL canonical state。

目标：

1. 统一项目后续使用 PageContainer / ProTable 的边界。
2. 输出页面清单：哪些页面保留现状，哪些页面可删除/简化 `ListPageLayout`。
3. 若发现无消费者的自研 wrapper，优先删除。

## 2. 结论

`frontend/src/components/ListPageLayout.tsx` 已无任何前端代码 / 运行时消费者；当前列表页已经直接使用 `ProTable` 的 `headerTitle`、`toolBarRender`、search、pagination 等能力承载列表布局。

因此本 Slice 采用 **删除 unused wrapper** 的低风险路径：

- 删除 `frontend/src/components/ListPageLayout.tsx`。
- 不批量给现有 ProTable 列表页外包 PageContainer。
- 不迁移 Detail / Drawer / Dashboard / TaskCreate。

## 3. PageContainer / ProTable 使用约定

### 3.1 列表页

列表页优先使用 ProTable 自带能力：

- 页面主标题：`ProTable.headerTitle`
- 主操作：`ProTable.toolBarRender`
- 搜索筛选：`ProTable.search` / columns search schema
- 分页与排序：ProTable pagination / request 或受控数据模式

除非页面存在 ProTable 之外的强页面级信息架构需求，否则不再额外套一层自研 `Card + Row + Col` wrapper。

### 3.2 详情页 / 工作流页

详情页、工作流页使用 `PageContainer`：

- 标题：`PageContainer.title`
- 返回：`PageContainer.onBack`
- 状态标签：`PageContainer.tags`
- 页面级操作：`PageContainer.extra`

### 3.3 Workbench 特例

Workbench 保持既有设计：

- URL 仍是 canonical query state。
- `WorkbenchTable` 的 `ProTable` 仍是受控展示，不引入 `request` 接管。
- 页面级信息架构仍由 `CreativeWorkbench` 负责。

## 4. 页面清单

### 4.1 保留 PageContainer 的页面

这些页面已使用 PageContainer，且符合“详情页 / 工作流页 / 页面级信息架构”的使用边界：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/pages/AIClip.tsx`
- `frontend/src/pages/product/ProductDetail.tsx`
- `frontend/src/pages/material/VideoDetail.tsx`
- `frontend/src/pages/material/TopicGroupDetail.tsx`

### 4.2 保留 ProTable 直出、不额外套 PageContainer 的列表页

这些页面主要由 ProTable 承载搜索、工具栏、表格与分页；本 Slice 不做额外容器迁移：

- `frontend/src/pages/TaskList.tsx`
- `frontend/src/pages/product/ProductList.tsx`
- `frontend/src/pages/material/VideoList.tsx`
- `frontend/src/pages/material/CopywritingList.tsx`
- `frontend/src/pages/material/CoverList.tsx`
- `frontend/src/pages/material/AudioList.tsx`
- `frontend/src/pages/material/TopicList.tsx`
- `frontend/src/pages/material/TopicGroupList.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchTable.tsx`

### 4.3 可删除 / 已删除

- `frontend/src/components/ListPageLayout.tsx`

理由：

- 无前端代码 / 运行时消费者。
- 与 ProTable toolbar/search/pagination 能力重叠。
- 保留会增加后续 UI 约定歧义。

## 5. 验收标准

- `ListPageLayout` 无前端代码 / 运行时消费者。
- TypeScript typecheck 通过。
- Production build 通过。
- Workbench 回归通过，确认未触碰 canonical query state。
- diff 不混入 Detail / Drawer / Dashboard / TaskCreate 迁移。
