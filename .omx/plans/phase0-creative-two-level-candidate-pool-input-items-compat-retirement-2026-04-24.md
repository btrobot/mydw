# Phase 0 Contract Freeze — `creative_input_items` Compatibility & Retirement

## Goal

冻结 `creative_input_items` 的迁移期边界，防止它继续混做真值面与执行面。

## Contract Table

| material_type | 迁移期角色 | 新权威面 | Allowed write? | Retirement slice |
|---|---|---|---|---|
| video | selected-media projection | selected video set | yes | 二阶段再评估物理退场 |
| audio | selected-media projection | selected audio set | yes | 二阶段再评估物理退场 |
| copywriting | read-only compatibility | `current_copywriting_*` | no | Slice 4 |
| cover | read-only compatibility | current cover contract | no | Slice 4 |
| topic | candidate / prompt reference only | candidate pool / prompt source | no | Slice 3-4 |

## Hard Rules

1. 从 Phase 0 开始，不再给 `copywriting/cover/topic` 新增基于 `creative_input_items` 的权威写路径。
2. 从 Slice 4 结束开始：
   - selected-media projection 成为 video/audio 唯一读口径
   - Workbench / Version / Publish 不得直接读取旧 orchestration 隐式拼装
3. `video/audio` 是否物理迁出 `creative_input_items`，留到二阶段评估；
   但 Phase 0 必须先冻结 cutover trigger。

## Cutover Trigger

若以下条件同时满足，则进入二阶段评估 `creative_selected_media_items`：

1. Slice 4 已完成且 selected-media projection 稳定
2. Slice 5 / 6 的 summary / freeze 链路全部只读 selected-media contract
3. 当前 `creative_input_items` 仅剩 `video/audio` 两类活跃写入
4. 再拆物理表可显著降低维护成本或简化服务代码

若不满足，允许继续保留物理表，但不允许恢复旧语义。
