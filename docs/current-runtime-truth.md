# 当前运行真相（当前 canonical fact inventory）

> 目的：记录当前代码已经证明的 **runtime truth / canonical source**。  
> 本文档是事实清单，不承担完整架构导览职责；架构总入口见 `docs/current-architecture-baseline.md`。

## 1. 调度配置当前状态（PR3 后）

| 位置 | 当前行为 | 真相来源 |
|---|---|---|
| `backend/api/publish.py` → `GET/PUT /api/publish/config` | 遗留兼容配置接口 | `ScheduleConfig` |
| `backend/api/schedule_config.py` → `GET/PUT /api/schedule-config` | canonical 调度配置接口 | `ScheduleConfig` |
| `backend/services/scheduler.py` | 调度循环读取调度配置 | `ScheduleConfig` |
| `frontend/src/pages/ScheduleConfig.tsx` | 页面通过 canonical hook 保存/加载调度配置 | `/api/schedule-config` |
| `frontend/src/hooks/useScheduleConfig.ts` | 生成客户端 hooks 围绕 canonical API | `/api/schedule-config` |
| `frontend/src/hooks/usePublish.ts` | 仅保留发布控制/状态/日志 hooks | N/A |

### 结论
- backend 与 frontend 的调度配置 contract 已统一到 `ScheduleConfig`
- legacy `/api/publish/config` 仍保留给兼容调用方，但前端页面已不再依赖它

## 2. 发布运行状态当前状态（PR4 后）

| 位置 | 当前行为 | 真相来源 |
|---|---|---|
| `backend/api/publish.py` → `/api/publish/status` | API 状态读取 | `TaskScheduler.get_status()` / `current_task_id()` |
| `backend/services/scheduler.py` | 实际是否运行 / 暂停 / 当前任务 | `TaskScheduler` 内部 runtime state |

### 结论
- API status 已由 scheduler runtime truth 派生
- Phase 1 的配置 / 状态 split-brain 已全部收口

## 3. 当前 topic / default-topic 真相（Phase 6 / PR4 基线）

| 位置 | 当前行为 | 真相来源 |
|---|---|---|
| `backend/api/topic.py` → `GET/PUT /api/topics/global` | global topics API | `global_topics`（fallback: `PublishConfig.global_topic_ids`） |
| `backend/api/profile.py` → `PublishProfile.global_topic_ids` | profile-level default topics CRUD | `publish_profile_topics`（fallback: `PublishProfile.global_topic_ids`） |
| `backend/api/topic.py` → topic-group CRUD | named topic-list CRUD | `topic_group_topics`（fallback: `TopicGroup.topic_ids`） |
| `backend/services/task_assembler.py` | 创建任务时自动并入 default topics | `publish_profile_topics`（fallback: `PublishProfile.global_topic_ids`） |

### 结论
- 当前自动进入 task assembly 的 default topics **只有** profile-level topics
- `/api/topics/global` 仍然**不会**自动注入 task assembly
- `TopicGroup` 仍然不是 task assembly 的自动输入源
- 三个 legacy JSON 列仍保留 dual-write / fallback 角色，用于兼容与 rollback
- 更完整的 Phase 6 语义冻结见：
  - `docs/phase-6-topic-compat-matrix.md`
  - `docs/adr/ADR-016-topic-canonical-semantics-phase-6.md`

## 3.1 当前剩余 JSON 字段结论（Phase 6 / PR5）

| 字段 | 当前结论 | 说明 |
|---|---|---|
| `accounts.tags` | `normalize-later` | 有真实 filter/query 需求，但当前不在本轮结构化 |
| `tasks.source_video_ids` | `delete-ready-later` | `task_videos` 已是 authoritative source |
| `tasks.composition_params` | `keep-json` | 继续作为 task 级 opaque params |
| `publish_profiles.composition_params` | `keep-json` | 继续作为 profile 级 opaque params |

## 4. 当前 legacy-FK runtime fence 真相（Phase 6 / PR2 基线）

| 位置 | 当前行为 | 真相来源 |
|---|---|---|
| `backend/services/composition_service.py` | 合成上传素材时优先读取 collection-based task videos，缺失时才回退 legacy `tasks.video_id` | `task_videos` → fallback `tasks.video_id` |
| `backend/api/video.py` 删除/批量删除 | 删除前同时检查 relation rows 与 legacy `tasks.video_id` | `task_videos` + compat fallback |
| `backend/api/copywriting.py` 删除/批量删除 | 删除前同时检查 relation rows 与 legacy `tasks.copywriting_id` | `task_copywritings` + compat fallback |
| `backend/services/task_compat_service.py` | 集中承接 residual legacy-FK reads / counts | compat boundary |

### 结论
- 新 runtime 路径已不再把 `tasks.video_id` / `tasks.copywriting_id` 当作主真相
- 旧列仍保留兼容回退角色，但读取已被集中到 compat helper，而不再散落在业务逻辑里
- 物理删列前置条件已转移到 `docs/phase-6-deletion-preconditions.md`

## 5. 当前迁移边界

### 已经存在的迁移信号
- `backend/models/__init__.py` 中 `ScheduleConfig` 注释已表明它替代 `publish_config`
- `backend/migrations/019_schedule_config.py` 已提供从 `publish_config` 到 `schedule_config` 的迁移逻辑

### 尚未完成的收口
- Phase 1 已完成；后续聚焦其他主题

## 6. Phase 1 的基线要求

在 Phase 1 完成前，必须始终能回答下面两个问题：

1. **页面写到哪？**
2. **scheduler 读到哪？**

当前答案分别是：
- 页面：canonical `/api/schedule-config`
- scheduler：`ScheduleConfig` + scheduler runtime state

Phase 1 已完成配置与状态真相收口。
