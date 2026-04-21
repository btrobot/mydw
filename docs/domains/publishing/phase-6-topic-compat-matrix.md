# Phase 6 Topic Compatibility Matrix

> Phase 6 / PR4 cutover baseline  
> 目的：记录 topic 领域在 relation-table cutover 后的 canonical source、compat surface 与 rollback 边界。

## Canonical semantics summary

当前 PR4 后的结论：

1. **Explicit task topics**：`POST /api/tasks/` / `POST /api/tasks/assemble` 传入的 `topic_ids` 是 task 的显式输入
2. **Profile-level default topics**：canonical source 已切到 `publish_profile_topics`
3. **Global singleton topics**：canonical source 已切到 `global_topics`
4. **Topic groups**：canonical source 已切到 `topic_group_topics`
5. 三个 legacy JSON 列仍保留 **dual-write / dual-read fallback**，用于 rollback 与兼容窗口

## Surface matrix

| Surface | Stored in | Current meaning | Auto-injected into task assembly? | Canonical status in PR4 | Planned follow-up |
|---|---|---|---|---|---|
| explicit `topic_ids` in task create/assemble request | request payload → `task_topics` | task-specific explicit topics | Yes | canonical task input | keep |
| `publish_profile_topics` + `PublishProfile.global_topic_ids` | relation rows + JSON dual-write fallback | profile-level default topics | Yes | relation rows first, JSON fallback | later remove legacy JSON after compat window |
| `global_topics` + `PublishConfig.global_topic_ids` | relation rows + JSON dual-write fallback | legacy/global singleton topic list | No | relation rows first, JSON fallback | later remove `PublishConfig.global_topic_ids` |
| `topic_group_topics` + `TopicGroup.topic_ids` | relation rows + JSON dual-write fallback | named topic-list CRUD surface | No | relation rows first, JSON fallback | later remove legacy JSON after compat window |

## Current task assembly precedence

`TaskAssembler` 目前的 precedence：

1. explicit task `topic_ids`
2. profile-level default topics
3. stable deduplication in first-seen order

明确 **不参与** 当前 precedence 的来源：

- `/api/topics/global`
- `TopicGroup.topic_ids`

## Why PR3 stops here

## PR4 cutover rules

- API response shape 保持兼容：仍返回 `topic_ids: number[]`
- task assembly precedence 不变：
  1. explicit task `topic_ids`
  2. profile-level default topics
  3. stable dedupe
- 读取优先级：
  - relation rows first
  - legacy JSON fallback second
- 写入策略：
  - relation rows canonical
  - legacy JSON dual-written for rollback safety

## Rollback note

若 PR4 发生 partial rollback：

- 只要 legacy JSON 列仍保留最近一次 dual-write 值，API 读路径仍可回退工作
- 真正删除 legacy JSON 列必须等 compat window 结束后再做

更多实现级说明见：`docs/phase-6-topic-migration-notes.md`

补充说明：
- `docs/domains/publishing/phase-6-topic-relation-cutover.md`
- `docs/phase-6-migration-ledger.md`
