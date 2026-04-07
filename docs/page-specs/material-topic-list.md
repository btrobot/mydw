# 话题管理

> Layout Template: T1 Standard List (with prepended Search Card + Global Topics Card)
> Route: `/material/topic`
> API: `GET /api/topics`, `POST /api/topics`, `DELETE /api/topics/{id}`, `POST /api/topics/batch-delete`, `GET /api/topics/search`, `GET /api/topics/global`, `PUT /api/topics/global`
> Permissions: 无（当前未实现权限控制）

## 1. Search Card（页面顶部，独立 Card）

| 属性 | 值 |
|------|----|
| 标题 | `<SearchOutlined /> 搜索话题` |
| size | `small` |
| marginBottom | 12 |

### 1.1 搜索输入区

| Element | Type | Behavior |
|---------|------|----------|
| 关键词输入 | `Input`（width: 240, allowClear, placeholder: "输入关键词搜索话题"） | 输入关键词，回车或点击搜索按钮触发 `GET /api/topics/search?keyword=` |
| 搜索按钮 | `Button`（icon: `SearchOutlined`） | 点击触发搜索，loading 状态跟随 `isSearching` |

### 1.2 搜索结果区

| 状态 | 渲染 |
|------|------|
| 未搜索（`searchKeyword` 为空） | 不渲染 |
| 搜索中 | `Text type="secondary"` 显示"搜索中…" |
| 无结果 | `Empty`（PRESENTED_IMAGE_SIMPLE，"未找到相关话题"） |
| 有结果 | `Space wrap`：每条结果渲染 `Tag color="blue"` 话题名 + `Tag color="orange"` 热度 + `Button type="link" size="small"` "添加" |

> Issue [I-01]: `handleAddFromSearch` 仅弹出 `message.success` 提示"已在话题库中"，未做任何实际操作（搜索 API 已自动入库，该按钮行为可能误导用户）。建议：若搜索结果已自动入库，应移除"添加"按钮或改为"已入库"禁用态。

## 2. Global Topics Card（Search Card 下方，独立 Card）

| 属性 | 值 |
|------|----|
| 标题 | `<GlobalOutlined /> 全局话题` |
| size | `small` |
| marginBottom | 12 |
| extra | `Button size="small" icon=GlobalOutlined` "设置全局话题" → 打开全局话题 Modal |

### 2.1 展示区

| 状态 | 渲染 |
|------|------|
| 无全局话题 | `Empty`（PRESENTED_IMAGE_SIMPLE，"暂未设置全局话题"） |
| 有全局话题 | `Space wrap`：每个话题渲染 `Tag color="geekblue"` |

## 3. Toolbar（ListPageLayout 内）

### 3.1 FilterBar（左侧）

| Element | Type | Behavior |
|---------|------|----------|
| 排序选择 | `Select`（width: 120） | 选项：`最新`（created_at）/ `热度`（heat）；onChange 更新 `sort` 状态，触发 `useTopics(sort)` 重新查询 |

> Issue [I-02]: 使用原生 `Select` 而非项目共享组件。当前仅有两个静态选项，可接受，但若后续排序选项增多应考虑抽取。

### 3.2 ActionBar（右侧）

| # | Element | Type | Icon | Behavior |
|---|---------|------|------|----------|
| 1 | 添加话题 | `Button` | `PlusOutlined` | 打开"添加话题"Modal |
| 2 | 批量删除 | `BatchDeleteButton` | `DeleteOutlined` | 选中行数 > 0 时显示，Popconfirm 确认后调用 `POST /api/topics/batch-delete` |

## 4. Table Columns（5 列）

| # | Label | Field | Render | Sortable | Width |
|---|-------|-------|--------|----------|-------|
| 1 | 话题名称 | `name` | Text（ellipsis） | 否 | auto |
| 2 | 热度 | `heat` | `v.toLocaleString()` 千分位格式化 | 否 | 80 |
| 3 | 来源 | `source` | Text | 否 | 80 |
| 4 | 创建时间 | `created_at` | `new Date(v).toLocaleString('zh-CN')` | 否 | 160 |
| 5 | 操作 | — | 操作按钮列 | 否 | 80 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `rowSelection`: 多选，选中行 ID 存入 `selectedIds` 状态

## 5. Action Column

| # | Button | Type | Behavior |
|---|--------|------|----------|
| 1 | 删除 | `Button`（type=link, danger, size=small） | `Popconfirm`（"确定删除？"）确认后调用 `DELETE /api/topics/{id}` |

## 6. Modal：添加话题

| 触发 | 添加话题按钮 |
|------|-------------|
| 标题 | 添加话题 |
| 确认 | 调用 `POST /api/topics`，成功后关闭并重置表单 |
| 取消 | 关闭并重置表单 |
| confirmLoading | `createTopic.isPending` |
| destroyOnClose | 是 |

### 表单字段（2 字段）

| # | Label | Field | Control | Required | Rules |
|---|-------|-------|---------|----------|-------|
| 1 | 话题名称 | `name` | `Input`（placeholder: "话题名称"） | 是 | "请输入话题名称" |
| 2 | 热度 | `heat` | `Input type="number"`（placeholder: "0"） | 否 | — |

> Issue [I-03]: `heat` 字段使用 `Input type="number"` 而非 Ant Design 的 `InputNumber` 组件。`Input type="number"` 返回 string 值，与 `TopicFormValues.heat?: number` 类型不匹配，可能导致提交时类型为 string。应改用 `InputNumber`。

## 7. Modal：设置全局话题

| 触发 | 全局话题 Card 右上角"设置全局话题"按钮 |
|------|--------------------------------------|
| 标题 | 设置全局话题 |
| width | 520 |
| 确认 | 调用 `PUT /api/topics/global`，成功后关闭 Modal |
| 取消 | 关闭 Modal |
| confirmLoading | `setGlobalTopics.isPending` |
| destroyOnClose | 是 |

### 表单内容

| Element | Type | Behavior |
|---------|------|----------|
| 说明文字 | `Text type="secondary"` | "从话题库中选择话题作为全局默认话题，发布时自动附加。" |
| 话题选择 | `Select mode="multiple"`（width: 100%, placeholder: "选择话题（可多选）"） | options 来自 `topics` 列表（label: name, value: id），支持 `filterOption` 本地搜索 |

> Issue [I-04]: 使用原生 `Select mode="multiple"` 而非项目共享选择组件。此处为话题专用多选，暂无通用 `TopicSelect` 组件，可接受。

## 8. 交互流程

### 8.1 搜索话题
1. 用户在 Search Card 输入关键词 → 回车或点击搜索 → `GET /api/topics/search?keyword=` → 搜索结果自动入库 → 展示结果标签列表
2. 点击结果中的"添加"按钮 → 仅弹出提示（见 Issue I-01）

### 8.2 查看/设置全局话题
1. Global Topics Card 展示当前全局话题标签
2. 点击"设置全局话题" → 打开 Modal → 从话题库多选 → 确认 → `PUT /api/topics/global` → 覆盖写入

### 8.3 排序
1. 用户在 FilterBar 切换排序方式 → `useTopics(sort)` 重新查询 → 表格刷新

### 8.4 添加话题
1. 点击"添加话题" → 打开 Modal → 填写表单 → 确认 → `POST /api/topics` → 关闭 Modal

### 8.5 单条删除
1. 点击行内"删除" → Popconfirm 确认 → `DELETE /api/topics/{id}` → 成功提示

### 8.6 批量删除
1. 勾选多行 → 出现"批量删除 (N)"按钮 → Popconfirm 确认 → `POST /api/topics/batch-delete` → 清空选中 → 成功提示（含跳过数）

## 9. Issues Summary

| ID | Severity | Description |
|----|----------|-------------|
| I-01 | Warning | `handleAddFromSearch` 是空操作（仅 message.success），搜索 API 已自动入库，"添加"按钮误导用户 |
| I-02 | Suggestion | FilterBar 排序使用原生 `Select`，非共享组件；当前两个选项可接受 |
| I-03 | Warning | `heat` 字段用 `Input type="number"` 而非 `InputNumber`，返回 string 与类型定义 `number` 不匹配 |
| I-04 | Suggestion | 全局话题 Modal 使用原生 `Select mode="multiple"`，暂无通用 TopicSelect，可接受 |

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Search conditions | 1（关键词搜索，独立 Card） |
| Table columns | 5（含操作列） |
| Action buttons (toolbar) | 1 按钮 + 1 条件按钮（添加话题 + 批量删除） |
| Action buttons (row) | 1（删除） |
| Modal forms | 2（添加话题 2 字段 + 设置全局话题 1 选择器） |
| Extra cards (above table) | 2（Search Card + Global Topics Card） |
