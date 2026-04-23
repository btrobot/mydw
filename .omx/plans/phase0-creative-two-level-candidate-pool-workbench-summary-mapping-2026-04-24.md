# Phase 0 Contract Freeze — Workbench Summary Mapping

## Goal

冻结 Workbench 新摘要字段的来源、展示落点与 query 语义，避免 Slice 5 半完成。

## Mapping

| field | source | row / global summary | filter/sort/preset |
|---|---|---|---|
| `current_product_name` | backend aggregated truth | row | display only |
| `current_cover_thumb` | current cover contract | row | display only |
| `current_copy_excerpt` | current copywriting contract | row | display only |
| `selected_video_count` | selected-media projection | row + global summary | display only（Phase 5 可评估 preset） |
| `selected_audio_count` | selected-media projection | row + global summary | display only |
| `candidate_video_count` | candidate pool | row + global summary | display only |
| `candidate_audio_count` | candidate pool | row + global summary | display only |
| `candidate_cover_count` | candidate pool | row + global summary | display only |
| `definition_ready` | backend readiness aggregator | row + global summary | Phase 5 后可评估 preset/filter |
| `composition_ready` | backend readiness aggregator | row + global summary | Phase 5 后可评估 preset/filter |
| `missing_required_fields` | backend diagnostics aggregator | row + drawer | drawer / preset optional after Phase 5 decision |

## Rules

1. Slice 5 前，新增字段默认 **展示优先**，不是自动进入 preset/filter/sort。
2. 若要进入 preset/filter/sort，必须在 Slice 5 PRD 中明确：
   - query 参数
   - 服务端过滤语义
   - E2E 回归用例
3. 前端禁止自行重复推导这些摘要字段作为长期方案。

## Acceptance Gate

- 未冻结此映射表，不得进入 Slice 5
