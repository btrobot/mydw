# Phase 6 Legacy Deletion Preconditions

> Phase 6 / PR2 输出物  
> 目的：列出旧字段/旧表面在真正物理删除前必须满足的前置条件，避免把 compat fence 误当成 delete-ready。

## 1. Task legacy FK columns

### `tasks.video_id`
物理删除前必须满足：
- `backend/services/task_compat_service.py` 中对 `video_id` 的 fallback 统计连续为 0
- `CompositionService` 不再触发 `video_id` fallback
- 视频删除/批量删除 guard 已只依赖 relation tables，不再需要 legacy fallback
- 历史数据完成 backfill 且验证 `task_videos` 与旧列无分叉
- grep / tests 证明 repo 内无新的 `task.video_id` runtime reader

### `tasks.copywriting_id`
物理删除前必须满足：
- 文案删除/批量删除 guard 已只依赖 relation tables
- compat helper fallback 统计连续为 0
- 历史数据完成 backfill 且 `task_copywritings` 与旧列无分叉
- grep / tests 证明 repo 内无新的 `task.copywriting_id` runtime reader

### `tasks.audio_id`
物理删除前必须满足：
- 确认确实不存在 runtime reader / delete guard / serializer fallback
- `task_audios` 已覆盖所有仍需保留的历史引用
- 文档与测试都不再把该列视为 compat 读路径

### `tasks.cover_id`
物理删除前必须满足：
- 确认确实不存在 runtime reader / delete guard / serializer fallback
- `task_covers` 已覆盖所有仍需保留的历史引用
- 文档与测试都不再把该列视为 compat 读路径

### `tasks.product_id`
物理删除前必须满足：
- 明确哪些页面/API 仍通过 task→product 读取历史信息
- 这些读取已切到新的 authoritative model 或被删除
- 历史数据不再依赖该列做业务判断

## 2. `PublishConfig` residual surfaces

### `publish_config.global_topic_ids`
物理删除前必须满足：
- PR3 已冻结 canonical topic semantics
- PR4 已为 global topics 提供新的 canonical source（`global_topics`）
- `/api/topics/global` 读路径已优先使用 relation rows，`PublishConfig.global_topic_ids` 只保留 fallback
- 写路径不再把 `PublishConfig.global_topic_ids` 当作唯一真相
- 兼容窗口结束并完成 dual-read / rollback 验证

### `PublishConfig` model as a whole
物理删除前必须满足：
- 调度兼容桥接是否仍需要该模型已重新确认
- 话题 legacy surface 已迁走
- 没有 runtime service 继续 import `PublishConfig` 作为业务真相

## 3. Delete-ready evidence checklist

任一旧字段进入真实 delete PR 之前，至少需要：

- [ ] 当前 authoritative replacement 已明确
- [ ] compat helper fallback 统计为 0（若存在 helper）
- [ ] migration/backfill 已验证且可重跑
- [ ] rollback 路径已成文
- [ ] grep / tests 证明 repo 内无新增 runtime reader
- [ ] docs / API contract / tests 已同步去除对旧字段的主承诺
