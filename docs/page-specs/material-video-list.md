# 视频管理

> Layout Template: T1 Standard List
> Route: `/material/video`
> API: `GET /api/videos`, `POST /api/videos`, `DELETE /api/videos/{id}`, `POST /api/videos/upload`, `POST /api/videos/scan`, `POST /api/videos/batch-delete`
> Permissions: 无（当前未实现权限控制）

## 1. Toolbar

### 1.1 FilterBar（左侧）

| Element | Type | Behavior |
|---------|------|----------|
| 按商品筛选 | `ProductSelect`（allowClear, width: 160） | 选择后按 `product_id` 过滤视频列表；清空则显示全部 |

### 1.2 ActionBar（右侧）

| # | Element | Type | Icon | Behavior |
|---|---------|------|------|----------|
| 1 | 上传到商品 | `ProductSelect`（allowClear, width: 160） | — | 选择商品后，上传的视频自动关联该商品 |
| 2 | 上传视频 | `Upload` + `Button` | `UploadOutlined` | 触发文件选择，accept: `video/mp4,video/quicktime`，调用 `POST /api/videos/upload` |
| 3 | 扫描导入 | `Button` | `ScanOutlined` | 调用 `POST /api/videos/scan`，完成后弹出 `Modal.info` 显示扫描结果（扫描数/导入数/跳过数/失败数） |
| 4 | 手动添加 | `Button` | `PlusOutlined` | 打开"添加视频"Modal |
| 5 | 批量删除 | `BatchDeleteButton` | `DeleteOutlined` | 选中行数 > 0 时显示，Popconfirm 确认后调用 `POST /api/videos/batch-delete` |

## 2. Search Bar（1 条件）

| # | Label | Field | Control | Search Mode |
|---|-------|-------|---------|-------------|
| 1 | 按商品筛选 | `product_id` | `ProductSelect`（下拉选择） | 即时筛选（onChange 触发重新查询） |

## 3. Table Columns（7 列）

| # | Label | Field | Render | Sortable | Width |
|---|-------|-------|--------|----------|-------|
| 1 | 名称 | `name` | Text（ellipsis） | 否 | auto |
| 2 | 状态 | `file_exists` | `Tag`：`true` → 绿色"正常"，`false` → 红色"缺失" | 否 | 60 |
| 3 | 关联商品 | `product_name` | 有值 → `Tag`，无值 → 灰色"—" | 否 | 120 |
| 4 | 大小 | `file_size` | `formatSize()` 格式化显示 | 否 | 90 |
| 5 | 时长 | `duration` | `formatDuration()` 格式化显示 | 否 | 80 |
| 6 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 否 | 160 |
| 7 | 操作 | — | 操作按钮列 | 否 | 80 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `rowSelection`: 多选，选中行 ID 存入 `selectedIds` 状态

## 4. Action Column

| # | Button | Type | Behavior |
|---|--------|------|----------|
| 1 | 删除 | `Button`（type=link, danger, size=small） | `Popconfirm`（"确定删除？"）确认后调用 `DELETE /api/videos/{id}` |

## 5. Modal：添加视频

| 触发 | 手动添加按钮 |
|------|-------------|
| 标题 | 添加视频 |
| 确认 | 调用 `POST /api/videos`，成功后关闭并重置表单 |
| 取消 | 关闭并重置表单 |
| destroyOnClose | 是 |

### 表单字段（3 字段）

| # | Label | Field | Control | Required | Rules |
|---|-------|-------|---------|----------|-------|
| 1 | 视频名称 | `name` | `Input` | 是 | "请输入名称" |
| 2 | 文件路径 | `file_path` | `Input` | 是 | "请输入文件路径" |
| 3 | 关联商品 | `product_id` | `Select`（allowClear, 商品列表） | 否 | — |

## 6. 交互流程

### 6.1 筛选
1. 用户在 FilterBar 选择商品 → `useVideos(productId)` 重新查询 → 表格刷新

### 6.2 上传视频
1. 用户可选择"上传到商品"指定关联商品
2. 点击"上传视频" → 选择本地 mp4/mov 文件 → `POST /api/videos/upload` → 成功提示

### 6.3 扫描导入
1. 点击"扫描导入" → `POST /api/videos/scan` → 弹出 Modal.info 显示结果统计

### 6.4 手动添加
1. 点击"手动添加" → 打开 Modal → 填写表单 → 确认 → `POST /api/videos` → 关闭 Modal

### 6.5 单条删除
1. 点击行内"删除" → Popconfirm 确认 → `DELETE /api/videos/{id}` → 成功提示

### 6.6 批量删除
1. 勾选多行 → 出现"批量删除 (N)"按钮 → Popconfirm 确认 → `POST /api/videos/batch-delete` → 清空选中 → 成功提示

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Search conditions | 1 |
| Table columns | 7（含操作列） |
| Action buttons (toolbar) | 5（上传到商品选择器 + 上传视频 + 扫描导入 + 手动添加 + 批量删除） |
| Action buttons (row) | 1（删除） |
| Modal forms | 1（添加视频，3 字段） |
