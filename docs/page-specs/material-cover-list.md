# 封面管理

> Layout Template: T1 Standard List
> Route: `/material/cover`
> API: `GET /api/covers`, `POST /api/covers/upload`, `DELETE /api/covers/{id}`, `POST /api/covers/batch-delete`
> Permissions: 无（当前未实现权限控制）

## 1. Toolbar

### 1.1 FilterBar（左侧）

| Element | Type | Behavior |
|---------|------|----------|
| 视频ID筛选 | `InputNumber`（min: 1, width: 140） | 输入视频 ID 后按 `video_id` 过滤封面列表；清空则显示全部 |

### 1.2 ActionBar（右侧）

> 排列原则：上传为主操作的页面，上传按钮排首位。

| # | Element | Type | Icon | Behavior |
|---|---------|------|------|----------|
| 1 | 上传封面 | `Upload` + `Button` | `UploadOutlined` | 触发文件选择，accept: `image/jpeg,image/png,image/webp`，调用 `POST /api/covers/upload`（若 videoFilter 有值则附带 `video_id` 参数） |
| 2 | 批量删除 | `BatchDeleteButton` | `DeleteOutlined` | 选中行数 > 0 时显示，Popconfirm 确认后调用 `POST /api/covers/batch-delete` |

## 2. Search Bar（1 条件）

| # | Label | Field | Control | Search Mode |
|---|-------|-------|---------|-------------|
| 1 | 视频ID筛选 | `video_id` | `InputNumber`（手动输入） | 即时筛选（onChange 触发重新查询） |

## 3. Table Columns（6 列）

| # | Label | Field | Render | Sortable | Width |
|---|-------|-------|--------|----------|-------|
| 1 | 文件路径 | `file_path` | Text（ellipsis） | 否 | auto |
| 2 | 关联视频 | `video_id` | 有值 → `Tag`（"视频 #N"），无值 → 灰色"—" | 否 | 100 |
| 3 | 大小 | `file_size` | `formatSize()` 格式化显示 | 否 | 90 |
| 4 | 尺寸 | `width` + `height` | 两者均有值 → "W×H"，否则 → "—" | 否 | 100 |
| 5 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 否 | 160 |
| 6 | 操作 | — | 操作按钮列 | 否 | 80 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `rowSelection`: 多选，选中行 ID 存入 `selectedIds` 状态

## 4. Action Column

| # | Button | Type | Behavior |
|---|--------|------|----------|
| 1 | 删除 | `Button`（type=link, danger, size=small） | `Popconfirm`（"确定删除？"）确认后调用 `DELETE /api/covers/{id}` |

## 5. Modal

无。当前页面没有 Modal。

## 6. 交互流程

### 6.1 筛选
1. 用户在 FilterBar 输入视频 ID → `useCovers(videoFilter)` 重新查询 → 表格刷新

### 6.2 上传封面
1. 点击"上传封面" → 选择本地 JPEG/PNG/WebP 文件 → `POST /api/covers/upload` → 成功提示
2. 若 FilterBar 中已填写视频 ID，上传时自动关联该视频

### 6.3 单条删除
1. 点击行内"删除" → Popconfirm 确认 → `DELETE /api/covers/{id}` → 成功提示

### 6.4 批量删除
1. 勾选多行 → 出现"批量删除 (N)"按钮 → Popconfirm 确认 → `POST /api/covers/batch-delete` → 清空选中 → 成功提示

---

## Issues

### ISSUE-1: FilterBar 使用原始 InputNumber 而非 VideoSelect 组件

- 位置: `CoverList.tsx` L101-106
- 严重度: Warning
- 说明: VideoList 使用 `ProductSelect` 共享组件进行筛选，CoverList 却使用原始 `InputNumber` 让用户手动输入视频 ID。应创建 `VideoSelect` 共享组件（下拉选择视频），或至少复用已有的选择器模式，提升用户体验和一致性。

### ISSUE-2: ActionBar 排列缺少"上传到视频"选择器

- 位置: `CoverList.tsx` L109-126
- 严重度: Suggestion
- 说明: VideoList 的 ActionBar 在上传按钮前放置了"上传到商品"选择器，让用户先选目标再上传。CoverList 虽然通过 FilterBar 的 `videoFilter` 间接关联上传目标，但这一行为不直观——用户可能不知道筛选条件会影响上传关联。建议在 ActionBar 增加独立的"上传到视频"选择器，与 VideoList 模式保持一致。

### ISSUE-3: 缺少缩略图预览列

- 位置: `CoverList.tsx` columns 定义
- 严重度: Suggestion
- 说明: 作为封面管理页面，没有图片缩略图预览列，用户只能看到文件路径，无法直观判断封面内容。建议增加缩略图列（使用 `Image` 组件）。

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Search conditions | 1 |
| Table columns | 6（含操作列） |
| Action buttons (toolbar) | 1 按钮 + 1 共享组件（上传封面 + 批量删除） |
| Action buttons (row) | 1（删除） |
| Modal forms | 0 |
