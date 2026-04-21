# 文案管理

> Layout Template: T1 Standard List
> Route: `/material/copywriting`
> API: `GET /api/copywritings`, `POST /api/copywritings`, `PUT /api/copywritings/{id}`, `DELETE /api/copywritings/{id}`, `POST /api/copywritings/import`, `POST /api/copywritings/batch-delete`
> Permissions: 无（当前未实现权限控制）

## 1. Toolbar

### 1.1 FilterBar（左侧）

| Element | Type | Behavior |
|---------|------|----------|
| 按商品筛选 | `ProductSelect`（allowClear, width: 160） | 选择后按 `product_id` 过滤文案列表；清空则显示全部 |

### 1.2 ActionBar（右侧）

> 排列原则：导入为主操作的页面，导入目标选择器排首位（与 VideoList 一致）。

| # | Element | Type | Icon | Behavior |
|---|---------|------|------|----------|
| 1 | 添加文案 | `Button` | `PlusOutlined` | 打开"添加文案"Modal（editingCw=null） |
| 2 | 导入到商品 | `ProductSelect`（allowClear, width: 140） | — | 选择商品后，导入的文案自动关联该商品 |
| 3 | 批量导入 | `Upload` + `Button` | `ImportOutlined` | 触发文件选择，accept: `.txt`，调用 `POST /api/copywritings/import` |
| 4 | 批量删除 | `BatchDeleteButton` | `DeleteOutlined` | 选中行数 > 0 时显示，Popconfirm 确认后调用 `POST /api/copywritings/batch-delete` |

> **[ISSUE] ActionBar 排序**：当前实现中"添加文案"排首位，"导入到商品"选择器排第二。应将导入目标选择器调至首位，与 VideoList 的排列原则一致（目标选择器 → 导入按钮 → 其他操作）。

## 2. Search Bar（1 条件）

| # | Label | Field | Control | Search Mode |
|---|-------|-------|---------|-------------|
| 1 | 按商品筛选 | `product_id` | `ProductSelect`（下拉选择） | 即时筛选（onChange 触发重新查询） |

## 3. Table Columns（5 列）

| # | Label | Field | Render | Sortable | Width |
|---|-------|-------|--------|----------|-------|
| 1 | 内容 | `content` | Text，截断前 80 字符，超出显示"…" | 否 | auto（ellipsis） |
| 2 | 关联商品 | `product_name` | 有值 → `Tag`，无值 → 灰色"—" | 否 | 120 |
| 3 | 来源 | `source_type` | 原始文本 | 否 | 80 |
| 4 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 否 | 160 |
| 5 | 操作 | — | 操作按钮列 | 否 | 120 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `rowSelection`: 多选，选中行 ID 存入 `selectedIds` 状态

## 4. Action Column

| # | Button | Type | Behavior |
|---|--------|------|----------|
| 1 | 编辑 | `Button`（type=link, size=small） | 将当前行数据填入表单，打开"编辑文案"Modal |
| 2 | 删除 | `Button`（type=link, danger, size=small） | `Popconfirm`（"确定删除？"）确认后调用 `DELETE /api/copywritings/{id}` |

## 5. Modal：添加 / 编辑文案

| 触发 | 添加文案按钮 / 行内编辑按钮 |
|------|---------------------------|
| 标题 | 编辑模式 → "编辑文案"；新增模式 → "添加文案" |
| 确认 | 新增 → `POST /api/copywritings`；编辑 → `PUT /api/copywritings/{id}`。成功后关闭并重置表单 |
| 取消 | 关闭并重置表单 |
| destroyOnClose | 是 |

> **[ISSUE] confirmLoading bug**：当前 `confirmLoading` 仅绑定 `createCopywriting.isPending`，编辑模式下提交时按钮不会显示 loading。应改为 `createCopywriting.isPending || updateCopywriting.isPending`。

### 表单字段（2 字段）

| # | Label | Field | Control | Required | Rules |
|---|-------|-------|---------|----------|-------|
| 1 | 文案内容 | `content` | `Input.TextArea`（rows=4） | 是 | "请输入文案内容" |
| 2 | 关联商品 | `product_id` | `Select`（allowClear, 手动构建 options） | 否 | — |

> **[ISSUE] product_id 组件**：当前使用原始 `Select` 并手动从 `useProductsV2` 构建 `productOptions`，应替换为共享 `ProductSelect` 组件（与 FilterBar、ActionBar 及 VideoList Modal 保持一致）。

## 6. 交互流程

### 6.1 筛选
1. 用户在 FilterBar 选择商品 → `useCopywritings(productId)` 重新查询 → 表格刷新

### 6.2 批量导入
1. 用户可选择"导入到商品"指定关联商品
2. 点击"批量导入" → 选择本地 `.txt` 文件 → `POST /api/copywritings/import` → 成功提示（"导入完成: N 条文案"）

### 6.3 添加文案
1. 点击"添加文案" → 打开 Modal（标题"添加文案"） → 填写表单 → 确认 → `POST /api/copywritings` → 关闭 Modal

### 6.4 编辑文案
1. 点击行内"编辑" → 将当前行数据填入表单 → 打开 Modal（标题"编辑文案"） → 修改 → 确认 → `PUT /api/copywritings/{id}` → 关闭 Modal

### 6.5 单条删除
1. 点击行内"删除" → Popconfirm 确认 → `DELETE /api/copywritings/{id}` → 成功提示

### 6.6 批量删除
1. 勾选多行 → 出现"批量删除 (N)"按钮 → Popconfirm 确认 → `POST /api/copywritings/batch-delete` → 清空选中 → 成功提示

---

## Known Issues

| # | Severity | Issue | Location | Fix |
|---|----------|-------|----------|-----|
| 1 | Bug | `confirmLoading` 仅绑定 `createCopywriting.isPending`，编辑模式下无 loading | L197 `confirmLoading={createCopywriting.isPending}` | 改为 `createCopywriting.isPending \|\| updateCopywriting.isPending` |
| 2 | Consistency | 表单 `product_id` 使用原始 `Select` + 手动 options | L206 `<Select allowClear placeholder="选择商品" options={productOptions} />` | 替换为 `<ProductSelect allowClear placeholder="选择商品" />` |
| 3 | Consistency | ActionBar 排序不符合 T1 模板规范 | L155-179 添加按钮排首位 | 导入目标选择器（导入到商品）应排首位，与 VideoList 一致 |

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Search conditions | 1 |
| Table columns | 5（含操作列） |
| Action buttons (toolbar) | 3 按钮 + 1 选择器（添加文案 + 导入到商品选择器 + 批量导入 + 批量删除） |
| Action buttons (row) | 2（编辑 + 删除） |
| Modal forms | 1（添加/编辑文案，2 字段） |
| Known issues | 3（1 bug + 2 consistency） |
