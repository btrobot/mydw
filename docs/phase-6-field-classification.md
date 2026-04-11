# Phase 6 Field Classification

> Phase 6 / PR1 baseline  
> 目的：先把“哪些字段只是历史包袱、哪些字段值得结构化、哪些字段可以继续保留 JSON”冻结下来，再决定后续迁移顺序。

## Classification meanings

- **keep-json**：保留为 JSON/TEXT，原因是当前属于低查询、弱约束、配置型数据
- **normalize-later**：当前已经表现出关系型/查询型需求，但不在本轮实施结构化
- **compat-readonly**：兼容遗留表面仍存在，但不应再作为新逻辑 authoritative source
- **delete-ready-later**：当前已被新真相替代，后续满足前置条件后可删

## Current field classification

| Field / Surface | Current storage | Current runtime truth | Classification | Why this classification | Planned follow-up |
|---|---|---|---|---|---|
| `accounts.tags` | `accounts.tags` TEXT(JSON array) | 账号 API 读写 + tag 过滤仍直接依赖该列 | `normalize-later` | 多值标签已具备真实查询/过滤需求，但当前缺少独立 tag model 设计，不在本轮结构化 | `docs/phase-6-migration-ledger.md` |
| `tasks.source_video_ids` | `tasks.source_video_ids` TEXT(JSON array) | `task_videos` 已是 authoritative 任务视频来源 | `delete-ready-later` | `021_task_resource_tables` 后资源集合真相已转移，`source_video_ids` 只剩迁移观察价值 | `docs/phase-6-migration-ledger.md` + delete preconditions |
| `tasks.composition_params` | `tasks.composition_params` TEXT(JSON) | 当前未发现高价值查询/关联使用面 | `keep-json` | 更接近 task 级 opaque workflow params，而不是关系数据 | `docs/phase-6-migration-ledger.md` |
| `publish_profiles.composition_params` | `publish_profiles.composition_params` TEXT(JSON) | `composition_service` 直接按 JSON 读取工作流参数 | `keep-json` | 当前是 profile 级 opaque 配置，仍以整体 JSON 透传使用 | `docs/phase-6-migration-ledger.md` |
| `publish_profiles.global_topic_ids` | `publish_profiles.global_topic_ids` TEXT(JSON array) + `publish_profile_topics` | relation rows first；`TaskAssembler` 自动并入 profile-level default topics；JSON 仅作 dual-write fallback | `compat-readonly` | PR4 已把 canonical source 切到 relation rows，旧 JSON 列进入兼容窗口 | PR5 decide when to drop legacy JSON |
| `topic_groups.topic_ids` | `topic_groups.topic_ids` TEXT(JSON array) + `topic_group_topics` | relation rows first；TopicGroup CRUD 仍返回兼容 `topic_ids` shape；JSON 仅作 dual-write fallback | `compat-readonly` | PR4 已把 canonical source 切到 relation rows，旧 JSON 列进入兼容窗口 | PR5 decide when to drop legacy JSON |
| `publish_config.global_topic_ids` | `publish_config.global_topic_ids` TEXT(JSON array) + `global_topics` | `/api/topics/global` 读 relation rows first；JSON 仅作 dual-write fallback | `compat-readonly` | 已退出真相位，只保留 rollback / compat 作用 | PR5 / later drop path |

## Legacy Task field classification

| Field | Current runtime role | Classification | Notes |
|---|---|---|---|
| `tasks.video_id` | 残余兼容字段；仍有 runtime readers / delete guards | `compat-readonly` | 当前最需要先 fence 的旧 FK |
| `tasks.copywriting_id` | 残余兼容字段；仍有 delete guards | `compat-readonly` | 不应再被新逻辑扩散 |
| `tasks.audio_id` | 未发现高价值 runtime reader | `delete-ready-later` | 保留列但已不应作为新逻辑依赖 |
| `tasks.cover_id` | 未发现高价值 runtime reader | `delete-ready-later` | 保留列但已不应作为新逻辑依赖 |
| `tasks.product_id` | 历史兼容字段 | `delete-ready-later` | `Task` authoritative 语义已不以该字段为中心 |

## Current topic semantics frozen by PR1

PR1 不做结构化迁移，但要先冻结“当前版本到底是谁在生效”：

1. **Explicit task topics**：`POST /api/tasks/` 传入的 `topic_ids` 仍是每个 task 的显式输入。
2. **Profile-level default topics**：`PublishProfile.global_topic_ids` 是当前 `TaskAssembler` 唯一会自动合并的 default topic source。
3. **Global singleton topics**：`/api/topics/global` 当前仍读写 `PublishConfig.global_topic_ids`，但 **不会自动注入** task assembly。
4. **Topic groups**：`TopicGroup.topic_ids` 当前只是命名话题列表 CRUD surface，**不会自动注入** task assembly。

PR4 已完成 relation-table cutover，但**没有改变上述语义本身**；改变的是 canonical storage / rollback boundary。

## Immediate conclusions for Phase 6

- Phase 6 不应把所有 JSON 都一把梭结构化。
- 最清晰的关系型候选已经在 PR4 收口为 **topic-bearing relation tables**。
- `accounts.tags` 被明确归为 `normalize-later`，不在当前阶段强行结构化。
- `tasks.source_video_ids` 已被 `task_videos` 取代，应进入删除准备而不是继续演化。
- `tasks.composition_params` / `publish_profiles.composition_params` 被明确保留为 `keep-json`。
