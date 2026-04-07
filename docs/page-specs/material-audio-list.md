# 音频管理

> Layout Template: T1 Standard List
> Route: `/material/audio`
> API: `GET /api/audios`, `POST /api/audios/upload`, `DELETE /api/audios/{id}`, `POST /api/audios/batch-delete`
> Permissions: 无（当前未实现权限控制）

## 1. Toolbar

### 1.1 FilterBar（左侧）

无。

### 1.2 ActionBar（右侧）

> 排列原则：上传为主操作的页面，上传目标选择器排首位；添加为主操作的页面，添加按钮排首位。

| # | Element | Type | Icon | Behavior |
|---|---------|------|------|----------|
| 1 | 上传音频 | `Upload` + `Button` | `UploadOutlined` | 触发文件选择，accept: `audio/mpeg,audio/mp3,audio/wav,audio/aac,audio/ogg`，调用 `POST /api/audios/upload` |
| 2 | 批量删除 | `BatchDeleteButton` | `DeleteOutlined` | 选中行数 > 0 时显示，Popconfirm 确认后调用 `POST /api/audios/batch-delete` |

## 2. Search Bar

无。

## 3. Table Columns（5 列）

| # | Label | Field | Render | Sortable | Width |
|---|-------|-------|--------|----------|-------|
| 1 | 名称 | `name` | Text（ellipsis） | 否 | auto |
| 2 | 大小 | `file_size` | `formatSize()` 格式化显示 | 否 | 90 |
| 3 | 时长 | `duration` | `formatDuration()` 格式化显示 | 否 | 80 |
| 4 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 否 | 160 |
| 5 | 操作 | — | 操作按钮列 | 否 | 80 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `rowSelection`: 多选，选中行 ID 存入 `selectedIds` 状态

## 4. Action Column

| # | Button | Type | Behavior |
|---|--------|------|----------|
| 1 | 删除 | `Button`（type=link, danger, size=small） | `Popconfirm`（"确定删除？"）确认后调用 `DELETE /api/audios/{id}` |

## 5. Modal

无。

## 6. 交互流程

### 6.1 上传音频
1. 点击"上传音频" → 选择本地 mp3/wav/aac/ogg 文件 → `POST /api/audios/upload` → 成功提示

### 6.2 单条删除
1. 点击行内"删除" → Popconfirm 确认 → `DELETE /api/audios/{id}` → 成功提示

### 6.3 批量删除
1. 勾选多行 → 出现"批量删除 (N)"按钮 → Popconfirm 确认 → `POST /api/audios/batch-delete` → 清空选中 → 成功提示

---

## Issues Found

### Issue-1: 缺少 ProductSelect 筛选/关联（与 VideoList 不一致）

- **严重度**: Suggestion
- **说明**: `VideoList` 提供 FilterBar（按商品筛选）和 ActionBar 中的"上传到商品"选择器，`AudioList` 完全没有商品关联能力。后端 `Audio` 模型也没有 `product_id` 字段，所以当前代码是自洽的。但如果业务需要音频关联商品，需同时扩展后端模型和前端 UI。
- **结论**: 当前无 bug，属于功能差异。如需对齐，需产品确认。

### Issue-2: 缺少 file_exists 状态列（与 VideoList 不一致）

- **严重度**: Suggestion
- **说明**: `VideoList` 有"状态"列（`file_exists` → Tag 绿色"正常"/红色"缺失"），`AudioList` 没有。后端 `AudioResponse` 也未返回 `file_exists` 字段。如果音频文件可能被外部删除，建议补充。
- **结论**: 功能缺失，非 bug。视业务需要决定是否补充。

### Issue-3: 无 confirmLoading bug

- **严重度**: N/A
- **说明**: `AudioList` 没有 Modal，因此不存在 `confirmLoading` 相关问题。上传按钮正确使用 `uploadAudio.isPending`，`BatchDeleteButton` 正确使用 `batchDeleteAudios.isPending`。

### Issue-4: ActionBar 排列顺序合理

- **严重度**: N/A
- **说明**: 上传按钮在前，批量删除在后，符合"上传为主操作排首位"原则。

### Issue-5: 无 raw Select 问题

- **严重度**: N/A
- **说明**: 页面不涉及商品选择，未使用 `Select` 或 `ProductSelect`，无需检查。

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Search conditions | 0 |
| Table columns | 5（含操作列） |
| Action buttons (toolbar) | 1 按钮 + 1 批量删除（上传音频 + 批量删除） |
| Action buttons (row) | 1（删除） |
| Modal forms | 0 |
