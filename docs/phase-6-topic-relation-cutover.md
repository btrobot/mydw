# Phase 6 Topic Relation Cutover Notes

> Phase 6 / PR4  
> 目的：记录 relation-table cutover 后的读写优先级、dual-write 约定与回滚路径。

## New canonical relation tables

- `global_topics`
- `publish_profile_topics`
- `topic_group_topics`

这些表从 PR4 开始是 topic-bearing relation data 的 **canonical read source**。

## Legacy mirrors retained in PR4

以下 JSON 列继续保留，用于 rollback safety / compat fallback：

- `publish_config.global_topic_ids`
- `publish_profiles.global_topic_ids`
- `topic_groups.topic_ids`

PR4 不删这些列。

## Read precedence

### Global singleton topics
1. `global_topics`
2. fallback: `publish_config.global_topic_ids`

### Profile-level default topics
1. `publish_profile_topics`
2. fallback: `publish_profiles.global_topic_ids`

### Topic-group membership
1. `topic_group_topics`
2. fallback: `topic_groups.topic_ids`

## Write behavior

PR4 使用 **dual-write**：

- 写 relation tables
- 同步更新 legacy JSON mirror

这样保证：

- 新代码读取 canonical relation rows
- rollback / partial cutover 时仍能回退到 JSON mirrors

## Task assembly impact

`TaskAssembler` 当前继续遵守 PR3 冻结的语义：

1. explicit task `topic_ids`
2. profile-level default topics
3. stable dedupe

PR4 的变化仅是：

- profile-level default topics 的读取从“JSON-only”变成“relation-first, JSON-fallback”

以下来源仍 **不会** 自动注入 task assembly：

- `/api/topics/global`
- `TopicGroup.topic_ids`

## Rollback path

若 relation-table cutover 需要回滚：

1. 停止依赖 relation-table read path
2. 恢复 API / service 到 JSON mirror fallback-only
3. 保留已同步的 legacy JSON mirrors 作为兼容数据来源

这就是为什么 PR4 必须保持 dual-write，而不是只写 relation rows。

## Verification checklist

- migration rerun idempotent
- relation rows 优先于 JSON mirrors
- 删除 relation rows 后仍能 fallback 到 JSON mirrors
- API response shape 仍保持 `topic_ids: number[]`
