# 商品管理

> Layout Template: T1 Standard List  
> Route: `/material/product`  
> API: `GET /api/products`, `POST /api/products`, `PUT /api/products/{id}`, `DELETE /api/products/{id}`, `POST /api/products/{id}/parse-materials`  
> Permissions: 无（当前未实现权限控制）

## 1. Toolbar

### 1.1 Search

| Element | Type | Behavior |
| --- | --- | --- |
| 搜索商品名称 | `Input` | 通过 `GET /api/products?name=` 过滤列表 |

### 1.2 Primary Action

| # | Element | Type | Icon | Behavior |
| --- | --- | --- | --- | --- |
| 1 | 添加商品 | `Button`（type=primary） | `PlusOutlined` | 重置表单并打开“添加商品”弹窗 |

## 2. Table Columns（7 列）

| # | Label | Field | Render | Width |
| --- | --- | --- | --- | --- |
| 1 | ID | `id` | 文本 | 70 |
| 2 | 商品名称 | `name` | `Typography.Link`，点击跳转 `/material/product/{id}` | auto |
| 3 | 解析状态 | `parse_status` | `valueEnum` 状态标签 | 100 |
| 4 | 视频数 | `video_count` | 数字 | 80 |
| 5 | 文案数 | `copywriting_count` | 数字 | 80 |
| 6 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 160 |
| 7 | 操作 | — | 行内操作按钮 | 180 |

表格配置：

- `rowKey`: `id`
- `size`: `small`
- `pagination.pageSize = 10`
- 支持 `rowSelection`
- 选中行后显示批量删除操作

## 3. 行内操作

| # | Button | 显示条件 | Behavior |
| --- | --- | --- | --- |
| 1 | 重新解析 | `parse_status === 'error'` | 调用 `POST /api/products/{id}/parse-materials` |
| 2 | 编辑 | 始终显示 | 打开编辑弹窗，仅修改 `name` |
| 3 | 删除 | 始终显示 | `Popconfirm` 后调用 `DELETE /api/products/{id}` |

## 4. 弹窗：添加 / 编辑商品

| 项 | 当前行为 |
| --- | --- |
| 标题 | `editingProduct ? '编辑商品' : '添加商品'` |
| 提交 | 创建模式调用 `POST /api/products`；编辑模式调用 `PUT /api/products/{id}` |
| 成功后 | 关闭弹窗、重置表单、刷新列表 |
| confirmLoading | `createProduct.isPending || updateProduct.isPending` |
| destroyOnHidden | 是 |

### 4.1 创建模式字段

| # | Label | Field | Control | Required |
| --- | --- | --- | --- | --- |
| 1 | 商品名称 | `name` | `Input` | 是 |
| 2 | 分享文本 | `share_text` | `Input.TextArea` | 是 |

### 4.2 编辑模式字段

| # | Label | Field | Control | Required |
| --- | --- | --- | --- | --- |
| 1 | 商品名称 | `name` | `Input` | 是 |

## 5. 交互流程

### 5.1 搜索

1. 用户输入商品名称
2. 列表请求携带 `name` 查询参数
3. 表格刷新为过滤后的结果

### 5.2 添加商品

1. 点击“添加商品”
2. 填写 `name` 与 `share_text`
3. 调用 `POST /api/products`
4. 后端完成创建并立即触发解析
5. 前端提示成功并刷新列表

### 5.3 编辑商品

1. 点击行内“编辑”
2. 回填当前 `name`
3. 调用 `PUT /api/products/{id}`
4. 刷新列表

### 5.4 删除商品

1. 点击行内“删除”或使用批量删除
2. 调用 `DELETE /api/products/{id}`
3. 当前后端行为为“删除商品 + 解绑关联素材”

### 5.5 重新解析

1. 当商品处于 `error` 状态时显示“重新解析”
2. 点击后调用 `POST /api/products/{id}/parse-materials`
3. 成功后刷新列表

## 6. Hard Check

| 指标 | 数量 |
| --- | --- |
| Search conditions | 1 |
| Table columns | 7 |
| Toolbar primary actions | 1 |
| Row actions | 3（错误状态下为 3，否则为 2） |
| Create-form fields | 2 |
| Edit-form fields | 1 |
