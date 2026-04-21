# 商品详情

> Layout Template: T3b Full Detail  
> Route: `/material/product/:id`  
> API: `GET /api/products/{id}`, `PUT /api/products/{id}`, `POST /api/products/{id}/parse-materials`  
> Permissions: 无（当前未实现权限控制）

## 1. Page Header

| Element | Type | Behavior |
| --- | --- | --- |
| 返回 | `PageContainer.onBack` | `navigate(-1)` |
| 解析素材 | `Button` | 调用 `POST /api/products/{id}/parse-materials` |
| 编辑 | `Button` | 打开编辑弹窗 |

页面标题直接显示 `product.name`。

## 2. 基础信息区（4 字段）

| # | Label | Field | Render |
| --- | --- | --- | --- |
| 1 | 商品名称 | `name` | 文本 |
| 2 | 得物链接 | `dewu_url` | 可点击外链 + copyable |
| 3 | 解析状态 | `parse_status` | `Tag` |
| 4 | 创建时间 | `created_at` | `toLocaleString('zh-CN')` |

组件配置：

- `ProDescriptions`
- `bordered = true`
- `size = small`
- `column = 2`

## 3. Tabs（4 个）

### 3.1 视频

- Label: `视频 (${videos.length})`
- 表格列：名称 / 大小 / 时长 / 创建时间

### 3.2 封面

- Label: `封面 (${covers.length})`
- 有数据时以图片网格展示
- 无数据时显示空状态文案

### 3.3 文案

- Label: `文案 (${copywritings.length})`
- 表格列：内容 / 来源 / 创建时间

### 3.4 话题

- Label: `话题 (${topics.length})`
- 以 `Tag` 列表展示
- 无数据时显示空状态文案

## 4. 编辑弹窗

| 项 | 当前行为 |
| --- | --- |
| 标题 | 编辑商品 |
| 提交 | `PUT /api/products/{id}` |
| 成功后 | 关闭弹窗并提示“更新商品成功” |
| `initialValues` | `{ name: product.name }` |
| destroyOnHidden | 是 |

### 表单字段

| # | Label | Field | Control | Required |
| --- | --- | --- | --- | --- |
| 1 | 商品名称 | `name` | `ProFormText` | 是 |

## 5. 状态与加载

| 状态 | 表现 |
| --- | --- |
| `productLoading` | 全页居中 `Spin` |
| `product` 不存在 | PageContainer + “商品不存在”提示 |
| `parsing` | “解析素材”按钮 loading |

## 6. 交互流程

### 6.1 进入页面

1. 从路由参数读取 `id`
2. 调用 `GET /api/products/{id}`
3. 一次性拿到商品详情及关联素材

### 6.2 编辑商品

1. 点击“编辑”
2. 修改 `name`
3. 调用 `PUT /api/products/{id}`
4. 成功后刷新当前商品查询

### 6.3 解析素材

1. 点击“解析素材”
2. 调用 `POST /api/products/{id}/parse-materials`
3. 成功后刷新详情查询
4. 解析过程不会覆盖 `product.name`

## 7. Hard Check

| 指标 | 数量 |
| --- | --- |
| Base fields | 4 |
| Tabs | 4 |
| Header actions | 2 |
| Edit-form fields | 1 |
