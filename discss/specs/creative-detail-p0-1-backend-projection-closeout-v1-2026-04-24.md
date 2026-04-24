# 《CreativeDetail P0-1 后端页面投影收口说明 v1》

> 日期：2026-04-24  
> 范围：CreativeDetail / Slice P0-1 / backend projection

---

## 1. 本轮完成了什么

本轮已完成 **CreativeDetail 的后端页面友好投影层补齐**，目标是让前端在进入 P0-2 页面骨架改造前，不再必须从散字段硬推整页结构。

本轮新增到 `CreativeDetailResponse` 的核心页面投影：

- `current_selection`
- `product_zone`
- `free_material_zone`
- `readiness`
- `page_mode`

同时保留既有兼容字段：

- `product_links`
- `candidate_items`
- `input_items`
- `input_orchestration`
- `eligibility_status`
- 其余当前真相字段

即：**新增投影，不破坏旧合同。**

---

## 2. 具体落地内容

### 2.1 schema 层

在 `backend/schemas/__init__.py` 中新增：

- `CreativeDetailPageMode`
- `CreativeReadinessState`
- `CreativeSelectionState`
- `CreativeSelectionAdoptedFromResponse`
- `CreativeCurrentSelectionFieldResponse`
- `CreativeCurrentSelectionResponse`
- `CreativeZoneMaterialCandidateResponse`
- `CreativeProductNameCandidateResponse`
- `CreativePrimaryProductSummaryResponse`
- `CreativeProductZoneResponse`
- `CreativeFreeMaterialZoneResponse`
- `CreativeReadinessResponse`

并把这些字段接入 `CreativeDetailResponse`。

### 2.2 service 层

在 `backend/services/creative_service.py` 中补齐了 detail 专用 projection 构建：

- `page_mode` 推导
  - `definition`
  - `result_pending_confirm`
  - `published_followup`
- `readiness` 推导
  - `not_started`
  - `partial`
  - `ready`
  - 以及结果/发布模式下的状态替换
- `current_selection`
  - 当前商品名称
  - 当前封面
  - 当前文案
  - 当前音频
  - 当前视频集合
- `product_zone`
  - primary product summary
  - linked products
  - 商品名称候选
  - 商品封面 / 视频 / 文案候选
  - 当前是否已采用
- `free_material_zone`
  - 自由封面 / 视频 / 音频 / 文案候选
  - 当前是否已采用

同时把素材明细查询补到了 asset map 中，确保页面可直接拿到：

- `asset_name`
- `asset_excerpt`
- `asset_path`
- `duration_seconds`
- `product_id`

---

## 3. 本轮有意保持不做的事情

以下内容本轮明确 **不做**：

1. 不新增新的“双真相”字段
2. 不改公开路由
3. 不重写 Creative 聚合数据模型
4. 不新增 `selected_video_ids` 这类 JSON 真相字段
5. 不在 P0-1 里重做前端页面结构
6. 不在本轮落定 `current_audio_asset_id` / `audio_mode`

当前音频仍由现有 `input_items(material_type='audio')` 投影而来。

---

## 4. 当前实现边界

### 已实现

- 前端可直接消费整页主结构投影
- 商品区可直接拿到 primary product + product-derived 候选
- 自由素材区可直接拿到 free-material candidate 分组
- 首屏 readiness / page mode 不再需要前端重复推导

### 仍待下一切片处理

- P0-2：前端 route shell + section composition 骨架重构
- P0-3：区块联动与交互落位
- P0-4：状态语言 / CTA / 结果区后置

---

## 5. 验证结果

本轮已通过以下验证：

### 后端测试

```text
python -m pytest backend/tests/test_creative_schema_contract.py backend/tests/test_creative_api.py backend/tests/test_openapi_contract_parity.py -q
61 passed
```

```text
python -m pytest backend/tests/test_creative_workflow_contract.py backend/tests/test_creative_two_level_candidate_pool_phase0_contracts.py -q
10 passed
```

### 前端生成物 / 类型校验

```text
cd frontend && npm run api:generate
cd frontend && npm run typecheck
cd frontend && npm run generated:check
```

结果：通过。

---

## 6. 对下一步的建议

下一步应直接进入：

> **Slice P0-2：前端页面壳重构与新骨架落位**

建议使用本轮新增字段，直接把 `CreativeDetail.tsx` 改造成：

- route shell
- page mode orchestration
- header / readiness
- current selection section
- product zone section
- free material zone section
- follow-up section placeholder

不要再让前端从散字段二次拼页面。

---

## 7. 本轮一句话结论

> **CreativeDetail 的 P0-1 已把“页面怎么读后端数据”这件事先做对：当前入选区、商品区、自由素材区、readiness、page mode 都已有可直接消费的后端投影。**
