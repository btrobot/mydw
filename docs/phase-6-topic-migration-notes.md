# Phase 6 Topic Migration Notes

> Phase 6 / PR4  
> 目的：记录 relation-table cutover 的读写优先级、回填方式与 rollback 边界。

## New canonical tables

- `global_topics`
- `publish_profile_topics`
- `topic_group_topics`

## Backfill source

- `publish_config.global_topic_ids` → `global_topics`
- `publish_profiles.global_topic_ids` → `publish_profile_topics`
- `topic_groups.topic_ids` → `topic_group_topics`

## Read precedence

所有 topic 相关读取统一遵循：

1. relation rows first
2. legacy JSON fallback second

适用范围：

- `/api/topics/global`
- `PublishProfileResponse.global_topic_ids`
- `TopicGroupResponse.topic_ids`
- `TaskAssembler` 读取 profile-level default topics

## Write strategy

当前 PR4 采用：

- relation rows canonical write
- legacy JSON dual-write

这样做的目的：

- 不改变现有 API shape
- 允许 partial rollback 时继续从 legacy JSON 恢复
- 让后续 PR5/删除阶段有观测和回退空间

## Rollback boundary

若需要回退 PR4：

- 优先保留 legacy JSON 列值
- 停止写 relation rows 或停止优先读取 relation rows
- API shape 不需要变化，仍返回 `topic_ids: number[]`

## Non-goals

- 本 PR 不删除 legacy JSON 列
- 本 PR 不改变 task assembly precedence
- 本 PR 不把 `/api/topics/global` 重新变成 task assembly 的自动输入源
