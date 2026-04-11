# ADR-016: Phase 6 Topic Canonical Semantics Baseline

> Date: 2026-04-11  
> Status: Accepted

## Context

Phase 6 进入数据模型去历史包袱后，topic 领域存在多个并行 surface：

- `/api/topics/global` ↔ `PublishConfig.global_topic_ids`
- `PublishProfile.global_topic_ids`
- `TopicGroup.topic_ids`
- task create / assemble request 中的显式 `topic_ids`

在 PR3 之前，这些入口的“谁会影响 task assembly”容易被文档、测试、实现分别解释，给后续结构化迁移带来风险。

## Decision

在 Phase 6 / PR3 中，先冻结当前 canonical semantics：

1. task request 的显式 `topic_ids` 是 task 级显式输入
2. `PublishProfile.global_topic_ids` 是当前唯一自动并入 `TaskAssembler` 的 default-topic source
3. `/api/topics/global` 仍是 legacy singleton topic surface，不会自动注入 task assembly
4. `TopicGroup.topic_ids` 当前是命名列表 CRUD surface，不会自动注入 task assembly

当前 `TaskAssembler` topic merge precedence：

1. explicit task `topic_ids`
2. profile-level default topics
3. stable deduplication in first-seen order

## Alternatives considered

### A. 继续维持模糊状态，等 PR4 再统一
Rejected：会让 PR4 在未冻结语义的前提下直接做结构化迁移，风险过高。

### B. 直接宣布 `/api/topics/global` 成为 canonical default-topic source
Rejected：与当前实现和已冻结的 PR1 基线不一致，会在 PR3 引入行为变更。

### C. 让 TopicGroup 立即接管 task assembly 默认话题
Rejected：这属于结构迁移与 product semantics 变更，应放到后续 PR 明确设计，而不是在 PR3 偷渡。

## Consequences

### Positive

- PR4 可以在明确语义基线之上做结构化迁移
- 测试、文档、实现对 topic 语义的描述保持一致
- `PublishConfig.global_topic_ids` 的 legacy 角色被正式降级，而不是口头约定

### Negative

- 短期内 topic 领域仍保留多个 surface
- `PublishProfile.global_topic_ids` 继续承担 default-topic 语义，直到 PR4 结构化迁移完成

## Follow-ups

1. PR4 必须保持 API response shape 兼容，同时处理 `PublishConfig.global_topic_ids` 退出 truth position
2. 若后续要改变 default-topic semantics（例如 TopicGroup 接管），必须以新 ADR 显式记录
