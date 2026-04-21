# Phase 6 Legacy Deletion Preconditions

> Phase 6 / PR2 baseline  
> 目的：在真正删除旧字段前，先把“哪些兼容路径还活着、何时可以删”说清楚。

## Scope

当前只覆盖 PR2 已明确收口的 legacy runtime dependencies：

- `tasks.video_id`
- `tasks.copywriting_id`
- `PublishConfig` 作为非调度 runtime truth 的残余使用

## Deletion preconditions

### 1. `tasks.video_id`

删除前必须满足：

1. `CompositionService` 不再依赖 `tasks.video_id` 作为主读路径
2. 视频删除/批量删除检查已以 relation-table truth 为主（`task_videos` + legacy fallback）
3. 没有新的运行逻辑继续读取 `tasks.video_id`
4. 兼容窗口内仍能处理只剩 legacy `video_id` 的旧任务

当前状态（PR2 后）：

- 已满足 1、2、3
- 旧任务仍通过 compat helper fallback 支持 4

### 2. `tasks.copywriting_id`

删除前必须满足：

1. 文案删除/批量删除检查已以 relation-table truth 为主（`task_copywritings` + legacy fallback）
2. 没有新的运行逻辑继续把 `tasks.copywriting_id` 当作主来源
3. compat helper 能覆盖仅剩 legacy `copywriting_id` 的旧任务（若仍需要）

当前状态（PR2 后）：

- 已满足 1、2
- 兼容 helper 已具备 fallback 能力

### 3. `PublishConfig` 非调度真相残余

删除或进一步降级前必须满足：

1. 调度配置 canonical truth 继续稳定在 `ScheduleConfig`
2. 没有新的服务层逻辑把 `PublishConfig` 当作调度 truth
3. `/api/topics/global` 的 legacy singleton topic surface 在后续 PR 中完成 canonical 收口

当前状态（PR2 后）：

- 1、2 已满足
- 3 仍待 Phase 6 / PR3-PR4 完成

## What PR2 explicitly does **not** claim

- 不声称现在就能物理删除 `tasks.video_id` / `tasks.copywriting_id`
- 不声称 `PublishConfig` 已完全退出系统
- 不处理 `tasks.audio_id` / `tasks.cover_id` / `tasks.product_id` 的最终删除动作

## Recommended next checks before any column drop

1. 运行 grep / dependency inventory，确认无新的 legacy readers 扩散
2. 针对旧数据样本验证 compat fallback 路径
3. 在 migration PR 中验证：
   - backfill / fallback idempotence
   - partial rollback safety
   - old rows + new relation rows 同时存在时的 precedence
