# Task 语义基线（Phase 2 / PR1）

> 目的：定义当前版本下 **Task 的 authoritative 语义**，并明确哪些字段/行为只是兼容遗留。

## 1. Authoritative 模型

当前版本中，`Task` 的 authoritative 模型是**资源集合模型**：

- `video_ids`
- `copywriting_ids`
- `cover_ids`
- `audio_ids`
- `topic_ids`
- `account_id`
- `profile_id`

后端真实数据来源是任务与资源的关联表：

- `task_videos`
- `task_copywritings`
- `task_covers`
- `task_audios`
- `task_topics`

因此：

- `TaskResponse` 以 `*_ids` 集合字段为主
- 单资源字段不再代表 authoritative truth

## 2. Legacy / compatibility 字段

以下字段仍存在，但仅用于兼容历史代码或迁移期观察：

- `tasks.video_id`
- `tasks.copywriting_id`
- `tasks.audio_id`
- `tasks.cover_id`
- `tasks.product_id`

这些字段：

- **不是**当前任务语义的主来源
- **不应**作为新代码、新测试、新页面的主判断依据
- 未来阶段可继续降级或移除

补充说明（Phase 6 / PR1）：

- `tasks.source_video_ids` 也不应再被视为 authoritative 任务视频来源；当前 authoritative source 是 `task_videos`
- 旧 FK / 历史 JSON 字段可以保留兼容观察价值，但不能重新定义 task semantics
- Phase 6 / PR5 最终结论：
  - `tasks.source_video_ids` → `delete-ready-later`
  - `tasks.composition_params` → `keep-json`

## 3. 当前版本的保守执行语义（Route A）

当前版本明确采用保守执行语义：

### direct publish（直接发布）
允许：
- 1 个最终视频
- 0/1 个文案主输出
- 0/1 个封面主输出
- 多话题

不应被静默允许：
- 多视频 direct publish
- 多文案 direct publish
- 多封面 direct publish
- 无视频 direct publish
- 携带独立音频输入的 direct publish

### publish-time enforcement（Phase 2 / PR2）

从 Phase 2 / PR2 开始，发布路径必须先解析 publishability：

- 合法任务：进入 upload path
- 非法任务：明确失败并返回可读错误
- 禁止再以“取第一个视频 / 文案 / 封面”的方式静默降级执行

#### 合成任务的特殊情况

若任务已经完成合成并产生 `final_video_path`：

- direct publish 应优先使用 `final_video_path`
- 关联的多视频 / 多音频可被视为合成输入，而不是 direct publish 输入

### composition input（合成输入）
当任务进入合成链路时，可以持有更宽的资源集合：

- 多视频
- 多文案
- 多封面
- 多音频

但这些 broader inputs **不等于** 当前版本的 direct publish 能力。

## 4. API contract 基线

### authoritative create contract
当前 authoritative create contract 是：

- `POST /api/tasks/`
- body: `TaskCreateRequest`

其特点：
- 接收资源集合字段
- 不以 legacy 单资源 FK 为输入模型
- 对 direct publish 组合执行保守 Route A 前移校验

### create-time enforcement（Phase 2 / PR3）

从 Phase 2 / PR3 开始：

- 当 `composition_mode` 为空或 `none` 时，create / assemble path 会执行 direct-publish 组合校验
- 非法组合会在创建阶段直接返回可读错误，而不是等到 publish 阶段才失败

当前 direct-publish 创建阶段不允许：

- 多视频
- 多文案
- 多封面
- 任意独立音频输入

当 `composition_mode` 为 `coze` / `local_ffmpeg` 时：

- broader composition inputs 仍然允许
- 这些资源语义被解释为合成输入，而不是 direct publish 输入

### compatibility endpoints
以下接口仍存在，但语义应按资源集合模型理解：

- `POST /api/tasks/assemble`
- `POST /api/tasks/batch-assemble`

它们是兼容入口，不应重新定义单资源时代的旧语义。

## 4.1 当前冻结的 topic semantics（Phase 6 / PR1）

补充参考（Phase 6 / PR3）：

- `docs/phase-6-topic-compat-matrix.md`
- `docs/adr/ADR-016-topic-canonical-semantics-phase-6.md`

在进入 Phase 6 结构化迁移前，先冻结当前版本的 topic 语义：

- `POST /api/tasks/` 传入的 `topic_ids`：仍是 task 的显式输入
- `PublishProfile.global_topic_ids`：当前 `TaskAssembler` 唯一会自动合并的 default topic source（canonical storage 已切到 `publish_profile_topics`，JSON 列仅作 fallback）
- `GET/PUT /api/topics/global`：当前仍是 legacy singleton topic surface（canonical storage 已切到 `global_topics`，`PublishConfig.global_topic_ids` 仅作 fallback）
- `TopicGroup.topic_ids`：当前只是命名话题列表的 CRUD surface（canonical storage 已切到 `topic_group_topics`，JSON 列仅作 fallback）

### 当前 task assembly precedence

当前 `TaskAssembler` 的 topic 合并顺序是：

1. 调用方显式传入的 `topic_ids`
2. `PublishProfile.global_topic_ids`
3. 保序去重

当前 **不会** 自动合并：

- `/api/topics/global`
- `TopicGroup.topic_ids`

## 5. 测试基线要求

从 Phase 2 / PR1 开始：

- 测试应断言 `video_ids` / `copywriting_ids` / `cover_ids` / `audio_ids` / `topic_ids`
- 测试不应再把 `video_id` / `copywriting_id` 当作主响应字段
- 若 legacy FK 请求被拒绝，应明确视为“contract 已切换”的预期行为，而不是回归
- Phase 6 / PR1 起，topic baseline tests 还应明确：
  - profile-level default topics 会自动并入 task assembly
  - `/api/topics/global` 不会自动注入 task assembly
  - `TopicGroup` 当前不参与 task assembly precedence

## 6. 前端基线要求

前端在 Phase 2 后续 PR 中需要逐步对齐：

- `TaskCreate`：清楚区分“合成输入”与“最终发布输入”
- `TaskDetail`：以 collection model / execution summary 为主
- hooks/types：不再以 legacy 单资源字段作为主模型

当前 PR1 只定义基线，不实现全部前端对齐。
