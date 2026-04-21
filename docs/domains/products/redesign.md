# Product Domain: Current Material Pack Model

> Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 本文记录 **当前已上线事实**，不是未来方案提案。商品域的正式 truth 以这里、页面规格和回归测试为准。

## 1. 域定位

在当前系统里，**商品（Product）不是传统电商商品档案**，而是：

- 一个由得物分享文本驱动的素材包入口
- 一个用户可命名、可检索、可复解析的素材容器
- 一个承载视频 / 封面 / 文案 / 话题的聚合节点

核心字段含义如下：

| 字段 | 当前语义 |
| --- | --- |
| `name` | 用户输入、用户拥有的商品显示名，也是列表 / 详情页的主标题 |
| `share_text` | 仅用于创建时提取得物链接；当前不支持编辑，也不做持久化展示 |
| `dewu_url` | 从 `share_text` 中提取出的得物商品页链接，创建后只读 |
| `parse_status` | `pending` / `parsing` / `parsed` / `error` |
| `video_count` / `cover_count` / `copywriting_count` / `topic_count` | 商品聚合后的素材计数 |

## 2. 当前用户可见流程

### 2.1 创建商品

入口：`/material/product` 列表页的“添加商品”弹窗。

当前创建表单 **必须** 同时填写：

1. `name`
2. `share_text`

后端创建流程：

1. 从 `share_text` 提取 `dewu_url`
2. 校验 `name` 与 `dewu_url` 唯一性
3. 创建 `Product(name=data.name, dewu_url=..., parse_status="parsing")`
4. 立即触发素材解析
5. 返回 `ProductDetailResponse`

这意味着当前 `POST /api/products` 已经是 **create + parse** 的一体化流程，而不是“先建空商品、再手动补链路”的旧模式。

### 2.2 解析 / 重新解析

当前保留 `POST /api/products/{id}/parse-materials`，用于：

- 创建后解析失败时重试
- 商品页素材更新后的手动刷新

解析 / 重解析会刷新商品关联素材，但**不会覆盖用户输入的 `product.name`**。

### 2.3 编辑商品

当前 `PUT /api/products/{id}` 只允许编辑：

- `name`

不支持编辑：

- `share_text`
- `dewu_url`

### 2.4 删除商品

当前 `DELETE /api/products/{id}` 的真实行为是：

- 解除 `Video` / `Cover` / `Copywriting` 对该商品的关联
- 删除 `product_topics` 关联
- 删除商品本身

也就是说，**当前不是 cascade delete 素材文件**，而是“商品删除 + 解绑关联素材”。

## 3. API / 合同事实

### 3.1 `POST /api/products`

请求：

```json
{ "name": "商品名", "share_text": "得物分享文本" }
```

当前合同：

- `201`：创建成功，返回 `ProductDetailResponse`
- `422`：缺字段、空字段或无法从分享文本中提取有效得物链接
- `409`：商品名重复，或提取出的 `dewu_url` 重复

### 3.2 `PUT /api/products/{id}`

请求：

```json
{ "name": "新的商品名" }
```

当前合同：

- 仅编辑商品名称
- `422`：空名称
- `404`：商品不存在
- `409`：名称冲突

### 3.3 `POST /api/products/{id}/parse-materials`

当前合同：

- 重新解析商品页素材
- 成功返回最新 `ProductDetailResponse`
- 失败时把商品状态置为 `error`

## 4. 领域规则

1. `Product.name` 是商品域的权威显示名，归用户输入所有。
2. `Product.name` 与 `Product.dewu_url` 当前都保持唯一。
3. 解析器得到的 `pack.title` **不能写回** `product.name`。
4. 解析得到的标题仍然会写入 `dewu_parse` 来源的文案记录。
5. 物料命名规则保持：
   - `Video.name` 优先使用解析标题，否则回退到 `product.name`
   - `Cover.name` 优先使用解析标题，否则回退到 `product.name`
6. `share_text` 仅是创建入口，不是后续编辑字段。

## 5. 前端落地事实

### 5.1 商品列表页

路径：`/material/product`

当前列表展示：

- 商品名称
- 解析状态
- 视频数
- 文案数
- 创建时间

创建弹窗：

- 新建模式：`name` + `share_text`
- 编辑模式：仅 `name`

行内操作：

- 解析失败时显示“重新解析”
- 编辑
- 删除

### 5.2 商品详情页

路径：`/material/product/:id`

当前详情展示：

- `name`
- `dewu_url`
- `parse_status`
- `created_at`
- 关联视频
- 关联封面
- 关联文案
- 关联话题

页头操作：

- 解析素材
- 编辑商品（仅改 `name`）

## 6. 验证锚点

当前事实由以下实现 / 测试共同兜底：

- `backend/tests/test_product_api.py`
- `backend/tests/test_openapi_contract_parity.py`
- `frontend/src/pages/product/ProductList.tsx`
- `frontend/src/pages/product/ProductDetail.tsx`
- `frontend/src/api/types.gen.ts`

如果后续行为发生变化，应先同步：

1. 本文
2. `docs/domains/products/requirements.md`
3. `docs/specs/page-specs/product-list.md`
4. `docs/specs/page-specs/product-detail.md`
5. 文档真相测试
