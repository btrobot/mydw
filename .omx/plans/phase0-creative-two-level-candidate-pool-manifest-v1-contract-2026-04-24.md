# Phase 0 Contract Freeze — Manifest v1 Typed Contract

## Goal

冻结 version/package 使用的 `manifest v1` typed contract，避免 Slice 6 只留下字符串 JSON。

## Top-level Shape

```json
{
  "version": "v1",
  "creative_item_id": 0,
  "creative_version_id": 0,
  "primary_product_id": 0,
  "current_product_name": "",
  "current_cover": {
    "asset_type": "cover",
    "asset_id": 0
  },
  "current_copywriting": {
    "copywriting_id": 0,
    "text": "",
    "mode": "manual"
  },
  "selected_videos": [],
  "selected_audios": [],
  "frozen_at": "",
  "source": "version|package"
}
```

## Required Keys

- `version`
- `creative_item_id`
- `creative_version_id`
- `primary_product_id`
- `current_product_name`
- `current_cover`
- `current_copywriting`
- `selected_videos`
- `selected_audios`
- `frozen_at`
- `source`

## Selected Media Entry Shape

### selected_videos[i]

- `asset_id`
- `sort_order`
- `enabled`
- `trim_in`
- `trim_out`
- `slot_duration_seconds`

### selected_audios[i]

- `asset_id`
- `sort_order`
- `enabled`

## Rules

1. `manifest_json` 只是承载列，不是无约束字符串。
2. Version / Package 必须都使用同一份 `manifest v1` key 集与顺序语义。
3. `selected_videos` / `selected_audios` 必须来自 selected-media projection。
4. `current_cover` / `current_copywriting` 必须来自 current truth contracts。

## Acceptance Gate

- 未冻结此 contract，不得进入 Slice 6
