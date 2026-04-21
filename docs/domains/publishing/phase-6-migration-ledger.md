# Phase 6 Migration Ledger

> Phase 6 / PR5  
> 目的：给剩余 JSON-in-text 字段一个**最终、可执行**的阶段性结论，并记录 compat → cutover → delete 的后续路线。

## Ledger statuses

- **keep-json**：继续保留 JSON/TEXT，不进入当前结构化计划
- **normalize-later**：明确值得结构化，但不在本轮实施
- **delete-ready-later**：authoritative source 已切走，等待前置条件满足后删除
- **compat-readonly**：旧字段已退出真相位，仅保留 dual-write / fallback / rollback 作用

## Final decisions for remaining JSON fields

| Field | Current role | Final decision | Why | Next step |
|---|---|---|---|---|
| `accounts.tags` | 账号标签列表，支持筛选与展示 | `normalize-later` | 已有真实查询/过滤需求，但当前缺少独立 tag model / junction-table 设计；贸然结构化会扩大 PR5 范围 | 后续单独立项 tag model / account_tags relation |
| `tasks.source_video_ids` | 旧的多视频 JSON 输入痕迹 | `delete-ready-later` | `task_videos` 已是 authoritative source；该列只剩迁移观察价值 | 满足 delete preconditions 后删列 |
| `tasks.composition_params` | task 级 opaque workflow params | `keep-json` | 当前无查询/约束/关联需求，更像低频配置载荷 | 继续保留 JSON，并避免扩展为关系模型 |
| `publish_profiles.composition_params` | profile 级 opaque workflow params | `keep-json` | 当前仅在 profile CRUD 与 composition runtime 中以整体 JSON 使用，无结构化收益证据 | 继续保留 JSON，并用现有 schema validator 约束合法性 |

## Topic legacy mirrors after PR4

这些字段已经不属于“剩余未决 JSON 字段”，但仍需要写入 ledger，避免 future delete 没有路径：

| Field | Current role | Final decision | Why | Next step |
|---|---|---|---|---|
| `publish_config.global_topic_ids` | global topics 的 JSON mirror | `compat-readonly` | canonical source 已切到 `global_topics`；JSON 仅为 dual-write / fallback | compat window 结束后删除 |
| `publish_profiles.global_topic_ids` | profile topics 的 JSON mirror | `compat-readonly` | canonical source 已切到 `publish_profile_topics`；JSON 仅为 dual-write / fallback | compat window 结束后删除 |
| `topic_groups.topic_ids` | topic group 的 JSON mirror | `compat-readonly` | canonical source 已切到 `topic_group_topics`；JSON 仅为 dual-write / fallback | compat window 结束后删除 |

## Compat → cutover → delete

### A. `accounts.tags`

1. **compat / current**
   - JSON array 存在于 `accounts.tags`
   - API / frontend tag filter 仍直接依赖该列
2. **future cutover**
   - 引入 tag 实体与 account-tag relation
   - API 查询从 JSON `contains` 切到 relation query
3. **delete**
   - account-tag relation 已稳定
   - frontend / API 不再依赖 JSON `contains`
   - backfill 与 rollback 已验证

### B. `tasks.source_video_ids`

1. **compat / current**
   - authoritative source 已是 `task_videos`
   - 列仅保留为历史迁移观察字段
2. **cutover**
   - 禁止任何新 runtime reader 增加
   - 用 tests / grep 持续证明 `task_videos` 是唯一真相
3. **delete**
   - 满足 `docs/phase-6-deletion-preconditions.md`
   - migration/backfill 可重跑且无分叉

### C. `tasks.composition_params`

1. **compat / current**
   - 作为 task 级 opaque JSON 存储
2. **cutover**
   - 无当前 cutover 计划
3. **delete**
   - 仅当未来确认字段彻底无用，或拆分出结构化参数模型时再考虑

### D. `publish_profiles.composition_params`

1. **compat / current**
   - 作为 profile 级 opaque JSON 存储
   - schema validator 保证 JSON 字符串合法
2. **cutover**
   - 无当前 cutover 计划
3. **delete**
   - 仅当未来 workflow 参数模型稳定、且不再以整体 JSON 透传时再考虑

### E. Topic legacy JSON mirrors

1. **compat / current**
   - relation rows canonical
   - JSON mirrors dual-written
2. **cutover**
   - compat window 内持续验证 relation-first / JSON-fallback
3. **delete**
   - fallback 统计为 0
   - rollback 窗口关闭
   - migration / API compatibility 已验证完成

## Guardrails for new development

从 PR5 起，新增代码必须遵守：

1. **不得**把 `tasks.source_video_ids` 重新当作 runtime truth
2. **不得**新增对 topic legacy JSON mirrors 的主读依赖
3. `composition_params` 若继续保留 JSON，必须被当作 opaque blob，而不是偷偷增加结构化查询语义
4. `accounts.tags` 若要继续扩展筛选/统计能力，应先开 normalize-later 的专门方案，而不是继续叠加 JSON contains 逻辑

## References

- `docs/phase-6-field-classification.md`
- `docs/phase-6-dependency-matrix.md`
- `docs/phase-6-deletion-preconditions.md`
- `docs/phase-6-legacy-deletion-preconditions.md`
- `docs/phase-6-topic-relation-cutover.md`
