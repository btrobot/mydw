# 商品管理

> Layout Template: T1 Standard List
> Route: `/product`
> API: `GET /api/products`, `POST /api/products`, `PUT /api/products/{id}`, `DELETE /api/products/{id}`
> Permissions: 无（当前未实现权限控制）

## 1. Toolbar

### 1.1 FilterBar（左侧）

| Element | Type | Behavior |
|---------|------|----------|
| 搜索商品名称 | `Input`（allowClear, width: 200） | 输入文本后按 `name` 前端过滤商品列表；清空则显示全部 |

### 1.2 ActionBar（右侧）

> 排列原则：添加为主操作的页面，添加按钮排首位。

| # | Element | Type | Icon | Behavior |
|---|---------|------|------|----------|
| 1 | 添加商品 | `Button`（type=primary） | `PlusOutlined` | 重置 `editingProduct` 为 null，重置表单，打开"添加商品"Modal |

## 2. Search Bar（1 条件）

| # | Label | Field | Control | Search Mode |
|---|-------|-------|---------|-------------|
| 1 | 搜索商品名称 | `name`（前端过滤） | `Input`（文本输入） | 即时筛选（onChange 更新 `searchText`，前端 `filter()` 过滤） |

> **Issue [S1]**: 搜索为纯前端 `Array.filter()`，当商品数量增长后应改为后端 `GET /api/products?name=` 查询（后端已支持 `name` query 参数）。

## 3. Table Columns（6 列）

| # | Label | Field | Render | Sortable | Width |
|---|-------|-------|--------|----------|-------|
| 1 | 商品名称 | `name` | `Typography.Link`（ellipsis），点击跳转 `/product/{id}` | 否 | auto |
| 2 | 商品链接 | `link` | 有值 → `Text`（type=secondary, fontSize=12），无值 → `Text`（"—"） | 否 | auto |
| 3 | 视频数 | — | `ProductCountCell`（type=videos），调用 `useVideos(productId)` 获取计数 | 否 | 80 |
| 4 | 文案数 | — | `ProductCountCell`（type=copywritings），调用 `useCopywritings(productId)` 获取计数 | 否 | 80 |
| 5 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 否 | 160 |
| 6 | 操作 | — | 操作按钮列 | 否 | 120 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `rowSelection`: 无

> **Issue [P1]**: `ProductCountCell` 为每行发起独立的 `useVideos` / `useCopywritings` 请求（N+1 问题）。商品列表 100 条时将产生 200 个额外请求。应由后端在 `GET /api/products` 响应中返回 `video_count` / `copywriting_count` 聚合字段。

## 4. Action Column

| # | Button | Type | Icon | Behavior |
|---|--------|------|------|----------|
| 1 | 编辑 | `Button`（type=link, size=small） | `EditOutlined` | 设置 `editingProduct`，回填表单字段，打开 Modal |
| 2 | 删除 | `Button`（type=link, danger, size=small） | `DeleteOutlined` | `Popconfirm`（"确定删除此商品？"）确认后调用 `DELETE /api/products/{id}`；后端 409 阻止有关联素材的删除 |

## 5. Modal：添加 / 编辑商品

| 触发 | 添加商品按钮 / 行内编辑按钮 |
|------|---------------------------|
| 标题 | `editingProduct ? '编辑商品' : '添加商品'` |
| 确认 | 编辑模式 → `PUT /api/products/{id}`；添加模式 → `POST /api/products`；成功后关闭并重置表单 |
| 取消 | 关闭并重置表单，清空 `editingProduct` |
| confirmLoading | `createProduct.isPending \|\| updateProduct.isPending` |
| destroyOnClose | 是 |

### 表单字段（2 字段）

| # | Label | Field | Control | Required | Rules |
|---|-------|-------|---------|----------|-------|
| 1 | 商品名称 | `name` | `Input` | 是 | "请输入商品名称" |
| 2 | 商品链接 | `link` | `Input`（prefix: `LinkOutlined`） | 否 | — |

## 6. 交互流程

### 6.1 搜索筛选
1. 用户在 FilterBar 输入文本 → `searchText` 更新 → 前端 `filter()` 过滤 `products` → 表格刷新

### 6.2 添加商品
1. 点击"添加商品" → 重置表单 → 打开 Modal → 填写表单 → 确认 → `POST /api/products` → 关闭 Modal → react-query 自动刷新列表

### 6.3 编辑商品
1. 点击行内"编辑" → 回填表单（name, link） → 打开 Modal → 修改表单 → 确认 → `PUT /api/products/{id}` → 关闭 Modal → react-query 自动刷新列表

### 6.4 单条删除
1. 点击行内"删除" → Popconfirm 确认 → `DELETE /api/products/{id}` → 成功提示
2. 若商品有关联视频/文案 → 后端返回 409 → 前端显示错误提示

### 6.5 导航到详情
1. 点击商品名称链接 → `navigate('/product/{id}')` → 跳转到 `ProductDetail` 页面

---

## Issues

### [S1] 前端过滤 vs 后端搜索

- 位置: `ProductList.tsx` L40-42
- 当前: `products.filter(p => p.name.toLowerCase().includes(searchText.toLowerCase()))`
- 问题: 纯前端过滤，数据量大时性能差且无法利用后端分页
- 建议: 改用后端 `GET /api/products?name=` 查询参数（后端已支持）

### [P1] ProductCountCell N+1 查询

- 位置: `ProductList.tsx` L21-26
- 当前: 每行渲染 `ProductCountCell` 组件，分别调用 `useVideos(productId)` 和 `useCopywritings(productId)`
- 问题: N 条商品产生 2N 个额外 API 请求
- 建议: 后端 `GET /api/products` 响应增加 `video_count` / `copywriting_count` 聚合字段，前端直接渲染

### [A1] ActionBar 无批量操作

- 位置: `ProductList.tsx` L161-168
- 当前: 表格无 `rowSelection`，ActionBar 无批量删除按钮
- 说明: 与其他列表页（VideoList、CopywritingList 使用 `BatchDeleteButton`）不一致。若需要批量操作，应添加 `rowSelection` + `BatchDeleteButton` 共享组件

### [C1] confirmLoading 在编辑模式下的竞态

- 位置: `ProductList.tsx` L175
- 当前: `confirmLoading={createProduct.isPending || updateProduct.isPending}`
- 说明: 逻辑正确（OR 运算覆盖两种模式），无实际 bug。但可简化为根据 `editingProduct` 状态选择对应的 `isPending`

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Search conditions | 1（前端文本过滤） |
| Table columns | 6（含操作列） |
| Action buttons (toolbar) | 1（添加商品） |
| Action buttons (row) | 2（编辑 + 删除） |
| Modal forms | 1（添加/编辑商品，2 字段） |
