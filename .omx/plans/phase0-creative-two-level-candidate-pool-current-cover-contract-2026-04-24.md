# Phase 0 Contract Freeze — Current Cover Contract

## Goal

冻结“当前封面真值”的 DB / API / freeze 口径，避免 Slice 1 实现时猜字段。

## DB Contract

- `creative_items.current_cover_asset_type`
  - 首轮固定为 `cover`
- `creative_items.current_cover_asset_id`
  - `int | null`
- `creative_items.cover_mode`
  - `default_from_primary_product`
  - `adopted_candidate`
  - `manual`

## API Contract

Detail read/write surface 必须返回并接收：

- `current_cover_asset_type`
- `current_cover_asset_id`
- `cover_mode`

Detail 顶部“当前定义”区与 Workbench 列表封面摘要都以此合同读取。

## Read / Write / Freeze

- write source：
  - Detail 当前定义区的封面选择动作
- read source：
  - `CreativeDetailResponse`
  - Workbench summary aggregator
- freeze source：
  - `creative_version_service.py`
  - `creative_generation_service.py`
  - `publish_service.py`
  - `ai_clip_workflow_service.py`

## Compatibility

以下路径仅允许回读兼容，不再承担当前封面真值：

- 旧 `cover_ids`
- 旧 cover input items / 旧 orchestration projection

## Acceptance Gate

- 未冻结此合同，不得进入 Slice 1
