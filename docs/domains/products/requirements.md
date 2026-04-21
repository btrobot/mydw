# 商品（Product）当前需求与验收基线

> Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 本文聚焦商品域当前需求边界、用户可见行为和验收点，用于吸收已完成的 `product-create-name-share-text` planning。

## 1. 目标

当前商品域需要同时满足三件事：

1. 让用户为商品输入稳定、可读的名称
2. 用得物分享文本驱动素材解析
3. 把解析结果沉淀为后续任务 / 发布可复用的素材包

## 2. 当前需求边界

### 2.1 创建

创建商品时，用户必须提供：

- 商品名称 `name`
- 得物分享文本 `share_text`

系统职责：

- 从 `share_text` 提取 `dewu_url`
- 校验商品名称唯一
- 校验 `dewu_url` 唯一
- 创建商品后立即触发解析
- 返回带素材聚合信息的详情响应

### 2.2 列表页

路径：`/material/product`

当前必须支持：

- 按商品名称搜索（通过 `GET /api/products?name=`）
- 查看解析状态
- 查看视频数 / 文案数
- 新建商品
- 编辑商品名称
- 删除商品
- 解析失败时手动“重新解析”
- 选择多条商品后批量删除

### 2.3 详情页

路径：`/material/product/:id`

当前必须展示：

- 商品名称
- 得物链接 `dewu_url`
- 解析状态
- 创建时间
- 视频列表
- 封面列表
- 文案列表
- 话题列表

当前必须提供：

- “解析素材”
- “编辑商品”

### 2.4 更新

当前更新能力只覆盖：

- 修改 `name`

不在当前范围内：

- 编辑 `share_text`
- 改写 `dewu_url`

### 2.5 删除

删除商品时，当前系统要求（`DELETE /api/products/{id}`）：

- 删除商品记录
- 解绑已关联的视频 / 封面 / 文案
- 删除商品-话题关系
- 不把素材文件随商品一并级联删除

## 3. 当前验收标准

### 3.1 创建合同

`POST /api/products`

请求体：

```json
{ "name": "商品名", "share_text": "得物分享文本" }
```

验收点：

1. 成功创建返回 `201`
2. 响应中的 `name` 等于用户输入值
3. 响应中的 `dewu_url` 来自分享文本提取
4. 缺失 / 空白 `name` 返回 `422`
5. 缺失 / 空白 `share_text` 返回 `422`
6. 分享文本无法提取得物链接返回 `422`
7. 重复 `name` 返回 `409`
8. 重复 `dewu_url` 返回 `409`

### 3.2 更新合同

`PUT /api/products/{id}`

验收点：

1. 只接受 `name`
2. 空白名称返回 `422`
3. 商品不存在返回 `404`
4. 重名冲突返回 `409`

### 3.3 解析合同

`POST /api/products/{id}/parse-materials`

验收点：

1. 能返回最新 `ProductDetailResponse`
2. 解析 / 重解析不会覆盖 `product.name`
3. 解析得到的标题会进入 `dewu_parse` 文案
4. 解析失败时 `parse_status` 会进入 `error`

### 3.4 命名规则

验收点：

1. `product.name` 始终以用户输入为准
2. `Video.name` 优先使用解析标题，否则回退到 `product.name`
3. `Cover.name` 优先使用解析标题，否则回退到 `product.name`

## 4. 明确非目标

当前不做：

- 新增 `parsed_title` 字段
- 持久化并再次编辑原始 `share_text`
- 恢复旧的 `link` / `description` / `image_url` 编辑面
- 把解析标题回写成商品名

## 5. 正式文档落点

本需求基线已经落入以下正式文档：

- `docs/domains/products/redesign.md`
- `docs/specs/page-specs/product-list.md`
- `docs/specs/page-specs/product-detail.md`
- `docs/specs/requirements-spec.md`
- `docs/guides/user-guide.md`

## 6. 回归证据

当前由以下回归点提供事实保障：

- `backend/tests/test_product_api.py`
- `backend/tests/test_openapi_contract_parity.py`
- `backend/tests/test_doc_truth_fixes.py`
