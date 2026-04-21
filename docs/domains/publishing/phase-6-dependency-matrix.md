# Phase 6 Dependency Matrix

> Phase 6 / PR1 baseline  
> 目的：盘点旧字段 / 旧模型 / JSON-in-text 字段当前仍被哪些代码路径依赖，为后续 fence / cutover / delete 提供依据。

## 1. Legacy Task fields

| Surface | Current authoritative replacement | Active dependency paths | Dependency type | PR1 conclusion |
|---|---|---|---|---|
| `tasks.video_id` | `task_videos` + `TaskResponse.video_ids` | `backend/services/task_compat_service.py` compat helper；`backend/services/composition_service.py` 通过 helper fallback；`backend/api/video.py` 删除/批量删除 guard 通过 helper 计数 | compat fallback + guard | PR2 已把残余读取集中到 compat boundary |
| `tasks.copywriting_id` | `task_copywritings` + `TaskResponse.copywriting_ids` | `backend/services/task_compat_service.py` compat helper；`backend/api/copywriting.py` 删除/批量删除 guard 通过 helper 计数 | compat fallback + guard | PR2 已把残余读取集中到 compat boundary |
| `tasks.audio_id` | `task_audios` + `TaskResponse.audio_ids` | 未发现当前 backend 运行路径 reader（仅历史文档/迁移痕迹） | historical residue | 进入 delete-ready-later inventory |
| `tasks.cover_id` | `task_covers` + `TaskResponse.cover_ids` | 未发现当前 backend 运行路径 reader（仅历史文档/迁移痕迹） | historical residue | 进入 delete-ready-later inventory |
| `tasks.product_id` | product relation outside authoritative task resource semantics | 未发现当前 backend 高价值运行 reader | historical residue | 进入 delete-ready-later inventory |

## 2. Old model / legacy truth surfaces

| Surface | Current active paths | What it still means today | Risk |
|---|---|---|---|
| `PublishConfig` model | `backend/services/schedule_config_service.py` 兼容读取；`backend/services/topic_relation_service.py` dual-write / fallback；`backend/tests/test_publish_config_baseline.py` | 已不再是调度 canonical source；其 `global_topic_ids` 仅保留 compat fallback 角色 | 仍需等待 compat window 结束后才能进一步降级 |
| `ScheduleConfig` model | `backend/api/schedule_config.py`、`backend/api/publish.py`、`backend/services/scheduler.py` | 调度配置 canonical truth | Phase 6 不应重新打开其 truth |

## 3. Topic-bearing JSON fields

| Field | Active read/write paths | Current effective meaning | PR1 frozen conclusion |
|---|---|---|---|
| `publish_config.global_topic_ids` | `backend/services/topic_relation_service.py` fallback / dual-write；`backend/api/topic.py` global topics API | legacy singleton topic fallback surface | relation rows canonical；JSON 仅作 fallback |
| `publish_profiles.global_topic_ids` | `backend/services/topic_relation_service.py` fallback / dual-write；`backend/api/profile.py` CRUD；`backend/services/task_assembler.py` | profile-level default topics fallback surface | relation rows canonical；JSON 仅作 fallback |
| `topic_groups.topic_ids` | `backend/services/topic_relation_service.py` fallback / dual-write；`backend/api/topic.py` topic-group CRUD / response builder | named topic list fallback surface | relation rows canonical；JSON 仅作 fallback |

## 4. Other JSON-in-text fields

| Field | Active read/write paths | Current role | PR1 conclusion |
|---|---|---|---|
| `accounts.tags` | `backend/api/account.py` 读写 + tag filter；frontend Account 页面 tag filter / display | account tags 多值列表 | 已明确为 normalize-later，等待独立 tag model 方案 |
| `tasks.source_video_ids` | 模型 / schema / migrations / docs；未发现当前高价值 runtime reader | 迁移遗留观察字段 | 已明确为 delete-ready-later |
| `tasks.composition_params` | 模型 / schema；未发现当前高价值 runtime reader | task 级 opaque params | 已明确为 keep-json |
| `publish_profiles.composition_params` | `backend/api/profile.py` CRUD；`backend/services/composition_service.py` JSON 读取 | profile 级 opaque composition config | 已明确为 keep-json |

## 5. Frozen current topic semantics

Canonical write-up:
- `docs/phase-6-topic-compat-matrix.md`
- `docs/adr/ADR-016-topic-canonical-semantics-phase-6.md`

### 5.1 Global singleton topics
- Surface: `GET/PUT /api/topics/global`
- Storage today: `global_topics`
- Fallback: `PublishConfig.global_topic_ids`
- Meaning today: 一个 canonical singleton topic list（但不自动进入 `TaskAssembler`）

### 5.2 Profile-level default topics
- Surface: `PublishProfile.global_topic_ids`
- Storage today: `publish_profile_topics`
- Fallback: JSON text on `publish_profiles`
- Meaning today: `TaskAssembler` 会把它作为 default topics 合并进新任务

### 5.3 Topic groups
- Surface: `TopicGroup.topic_ids`
- Storage today: `topic_group_topics`
- Fallback: JSON text on `topic_groups`
- Meaning today: 命名列表 CRUD / response surface
- **Not true today**: 当前 task assembly 不会自动读取 topic groups

### 5.4 Task assembly precedence
当前 `TaskAssembler` 的 topic merge 规则是：
1. 先取调用方显式传入的 `topic_ids`
2. 再追加 `PublishProfile.global_topic_ids`
3. 保序去重
4. 不自动合并 `/api/topics/global`
5. 不自动合并 `TopicGroup.topic_ids`

## 6. PR2 / PR4 handoff state

PR2 / PR4 已完成的关键动作：

- `backend/services/task_compat_service.py` 新增 compat helpers，统一 residual legacy-FK reads
- `backend/services/composition_service.py` 改为优先读取 `task_videos`，缺失时才回退 `tasks.video_id`
- `backend/api/video.py` / `backend/api/copywriting.py` 删除与批量删除 guard 改为同时检查 relation rows + legacy fallback columns
- `backend/services/task_service.py` 不再保留无意义 `PublishConfig` 运行时依赖
- `backend/services/topic_relation_service.py` 新增 topic canonical-source helper，统一 relation-first / JSON-fallback 读取与 dual-write
- `backend/api/profile.py` / `backend/api/topic.py` 已切到 relation-first 读写
- `backend/services/task_assembler.py` 已切到 relation-first profile topic 读取

下一步目标不是立刻删列，而是：
- 保持新逻辑停止直接依赖旧列
- 把 compat fallback 限制在 helper 边界
- 用 `docs/phase-6-deletion-preconditions.md` 与 `docs/phase-6-legacy-deletion-preconditions.md` 作为后续 delete-ready-later 前置条件清单

对应交付物：
- `docs/phase-6-legacy-deletion-preconditions.md`
- `docs/phase-6-migration-ledger.md`
