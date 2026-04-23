# Phase 0 Contract Freeze — Authority Matrix

## Scope

本矩阵冻结 creative 二级候选池模型在 Phase 0 的权威源边界。

执行门禁：

- 该矩阵未冻结，不得进入 Slice 1

## Matrix

| Concept | Write source | Read source | Freeze source | Compatibility source | Retirement slice |
|---|---|---|---|---|---|
| primary product | `creative_product_links.is_primary` 唯一写入口 | Detail 当前定义 / Workbench 摘要 / service 聚合 | Version / Package 通过 primary product 规则读取 | `creative_items.subject_product_id` 仅回读兼容 | Slice 2 后降为兼容镜像 |
| current product name | `creative_items.current_product_name` + `product_name_mode` | Detail / Workbench / generation inputs | Version / Package 冻结 `current_product_name` | `subject_product_name_snapshot` 仅回读兼容 | Slice 1 后旧字段降权 |
| current cover | `creative_items.current_cover_asset_type` + `current_cover_asset_id` + `cover_mode` | Detail / Workbench 摘要 / diagnostics | Version / Package 统一从 current cover contract 冻结 | 旧 `cover_ids` / 旧 input projection 仅回读兼容 | Slice 1 后旧路径降权 |
| current copywriting | `creative_items.current_copywriting_id` / `current_copywriting_text` / `copywriting_mode` | Detail / Workbench / generation inputs | Version / Package 冻结当前文案 | `main_copywriting_text` 与 copywriting input items 仅兼容回读 | Slice 1-4 |
| candidate items | `creative_candidate_items` | Detail 候选区 / diagnostics | 不直接冻结；冻结时经由 current truth / selected-media manifest | 运行时拼装候选仅短期兼容 | Slice 3 后以表为准 |
| selected video set | selected-media projection（迁移期可物理承载于 `creative_input_items`） | Detail 当前入选 / Workbench 摘要 / generation | Version / Package manifest | 旧 orchestration 读取路径仅短期兼容 | Slice 4 完成单一读口径 |
| selected audio set | selected-media projection（迁移期可物理承载于 `creative_input_items`） | Detail 当前入选 / Workbench 摘要 / generation | Version / Package manifest | 旧 orchestration 读取路径仅短期兼容 | Slice 4 完成单一读口径 |
| version freeze source | `creative_version_service.py` 按 current truth + selected-media projection 组装 | VersionPanel / version readback | `creative_versions` + `manifest v1` | 旧 snapshot / 旧 manifest 路径仅兼容回读 | Slice 6 |
| package freeze source | `publish_service.py` / `ai_clip_workflow_service.py` / `creative_generation_service.py` 按 current truth + selected-media projection 组装 | CheckDrawer / publish readback | `package_records` + `manifest v1` | 旧 package snapshot 路径仅兼容回读 | Slice 6 |
| workbench summary | backend summary aggregator | WorkbenchTable / SummaryCard / DiagnosticsDrawer | 不适用 | 前端重复推导禁止作为长期方案 | Slice 5 前统一后端聚合 |
| manifest v1 | `creative_version_service.py` / `publish_service.py` 统一组装 | VersionPanel / CheckDrawer / publish readback | `manifest_json` 的 typed-v1 内容 | 任意字符串 JSON 禁止视为完成标准 | Slice 6 |

## Non-negotiables

1. Workbench / Version / Publish 不得在 Slice 6 前继续新增对旧隐式路径的直接读取。
2. `creative_input_items` 迁移期只允许承载 `video/audio` selected-media projection。
3. `copywriting/cover/topic` 不再属于 `creative_input_items` 的新增权威语义面。
