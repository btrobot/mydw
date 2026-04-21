# 商品详情

> Layout Template: T3b Full Detail
> Route: `/product/:id`
> API: `GET /api/products` (list, client-side find), `PUT /api/products/{id}`, `GET /api/videos?product_id={id}`, `GET /api/copywritings?product_id={id}`
> Permissions: 无（当前未实现权限控制）

## 1. PageHeader

| Element | Type | Behavior |
|---------|------|----------|
| 返回 | `Button`（icon: `ArrowLeftOutlined`） | `navigate(-1)` 返回上一页 |
| 商品名称 | `Typography.Title`（level=4） | 显示 `product.name` |

布局：`Space` 水平排列，`marginBottom: 16`。

## 2. Descriptions（3 字段）

| # | Label | Field | Render |
|---|-------|-------|--------|
| 1 | 商品名称 | `name` | Text |
| 2 | 商品链接 | `link` | 有值 → `Text`（type=secondary, fontSize=12），无值 → "—" |
| 3 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` |

配置：
- `bordered`: 是
- `size`: `small`
- `extra`: 编辑按钮（`EditOutlined`），点击打开编辑 Modal

## 3. RelatedData Tabs（2 Tab）

### 3.1 Tab: 关联视频

Label: `关联视频 (${videos.length})`

数据源: `useVideos(productId)` → `GET /api/videos?product_id={id}`

#### Table Columns（4 列）

| # | Label | Field | Render | Width |
|---|-------|-------|--------|-------|
| 1 | 视频名称 | `name` | Text（ellipsis） | auto |
| 2 | 大小 | `file_size` | `formatSize()` | 100 |
| 3 | 时长 | `duration` | `formatDuration()` | 80 |
| 4 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 160 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `loading`: `videosLoading`

### 3.2 Tab: 关联文案

Label: `关联文案 (${copywritings.length})`

数据源: `useCopywritings(productId)` → `GET /api/copywritings?product_id={id}`

#### Table Columns（3 列）

| # | Label | Field | Render | Width |
|---|-------|-------|--------|-------|
| 1 | 文案内容 | `content` | Text（ellipsis） | auto |
| 2 | 来源 | `source_type` | Text | 100 |
| 3 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` | 160 |

表格配置：
- `rowKey`: `id`
- `size`: `small`
- `pagination`: `pageSize=10`, 显示总数（`共 N 条`）
- `loading`: `copywritingsLoading`

## 4. Modal: 编辑商品

| 触发 | Descriptions `extra` 编辑按钮 |
|------|-------------------------------|
| 标题 | 编辑商品 |
| 确认 | 调用 `PUT /api/products/{id}`（`useUpdateProductV2`），成功后关闭 Modal，提示"更新商品成功" |
| 取消 | 关闭 Modal |
| destroyOnClose | 是 |
| confirmLoading | `updateProduct.isPending` |

### 表单字段（2 字段）

| # | Label | Field | Control | Required | Rules | 初始值 |
|---|-------|-------|---------|----------|-------|--------|
| 1 | 商品名称 | `name` | `Input` | 是 | "请输入商品名称" | `product.name` |
| 2 | 商品链接 | `link` | `Input`（prefix: `LinkOutlined`） | 否 | — | `product.link` |

## 5. 状态与加载

| 状态 | 表现 |
|------|------|
| `productsLoading` | 全页居中 `Spin`（size=large） |
| `product` 不存在 | 显示返回按钮 + "商品不存在" 提示文字 |
| `videosLoading` / `copywritingsLoading` | 对应 Tab 内 Table `loading` 状态 |

## 6. 交互流程

### 6.1 进入页面
1. 从 URL 解析 `id` 参数 → `parseInt(id, 10)` → `productId`
2. `useProductsV2()` 获取全部商品列表，客户端 `find` 匹配当前商品
3. `useVideos(productId)` / `useCopywritings(productId)` 并行加载关联数据

### 6.2 编辑商品
1. 点击编辑按钮 → `form.setFieldsValue` 填充当前值 → 打开 Modal
2. 修改字段 → 点击确认 → `form.validateFields()` → `PUT /api/products/{id}` → 成功提示 → 关闭 Modal
3. 验证失败（`errorFields`）→ 静默返回，不弹错误提示

### 6.3 返回
1. 点击返回按钮 → `navigate(-1)` 回到上一页

---

## Issues

| # | Severity | Description |
|---|----------|-------------|
| 1 | Warning | 使用 `useProductsV2()` 获取全部商品列表后客户端 `find`，未使用单条查询 API（`GET /api/products/{id}`）。数据量大时性能不佳。 |
| 2 | Warning | `Descriptions` 仅展示 `name`、`link`、`created_at` 三个字段，`ProductResponse` 中的 `description`、`dewu_url`、`image_url`、`updated_at` 未展示。 |
| 3 | Suggestion | 编辑 Modal 仅支持修改 `name` 和 `link`，与 `ProductResponse` 中可用字段不完全对齐（缺少 `description`、`dewu_url`、`image_url`）。 |
| 4 | Suggestion | 关联视频/文案 Tab 为只读展示，无行操作（如跳转详情、取消关联等）。后续可能需要扩展。 |
| 5 | Warning | 大量 inline `style` 使用（`padding: 24`、`marginBottom` 等），违反 frontend CLAUDE.md 中"no inline styles"规则。 |

---

## Hard Check

| 指标 | 数量 |
|------|------|
| Descriptions fields | 3 |
| Tabs | 2（关联视频、关联文案） |
| Table columns (videos) | 4 |
| Table columns (copywritings) | 3 |
| Action buttons (header) | 2（返回、编辑） |
| Action buttons (row) | 0 |
| Modal forms | 1（编辑商品，2 字段） |
