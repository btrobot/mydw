# 得物掘金工具数据库模型关系与字段职责

## 1. 文档目的

这份文档专门说明当前项目数据库层的 3 件事：

1. 有哪些核心表
2. 它们之间是什么关系
3. 每张表里的关键字段各自承担什么职责

当前代码的单一事实来源是：

- `backend/models/__init__.py`

需要特别注意：

- 现有 `docs/archive/reference/data-model.md` 中仍有部分旧字段和旧关系描述，没有完全跟上当前 ORM
- 本文优先以当前 ORM 和当前服务代码为准

## 2. 总体关系图

```text
Account
  └─ 1:N ── Task
              ├─ N:N ── Video         (via task_videos)
              ├─ N:N ── Copywriting   (via task_copywritings)
              ├─ N:N ── Cover         (via task_covers)
              ├─ N:N ── Audio         (via task_audios)
              ├─ N:N ── Topic         (via task_topics)
              ├─ N:1 ── PublishProfile
              ├─ 1:N ── CompositionJob
              └─ 1:N ── PublishLog

Product
  ├─ 1:N ── Video
  ├─ 1:N ── Copywriting
  ├─ 1:N ── Cover
  ├─ N:N ── Topic         (via product_topics)
  └─ 1:N ── Task          (兼容保留，主流程已弱化)

ScheduleConfig
  └─ 全局单例，控制调度器行为

PublishConfig
  └─ 旧发布配置表，仍在 ORM 中保留，但主调度逻辑已转向 ScheduleConfig

TopicGroup
  └─ 话题模板表，内部用 JSON topic_ids 聚合 Topic

SystemLog
  └─ 系统级操作日志
```

## 3. 当前主用表与兼容保留表

### 3.1 当前主用表

- `accounts`
- `tasks`
- `videos`
- `copywritings`
- `covers`
- `audios`
- `topics`
- `task_videos`
- `task_copywritings`
- `task_covers`
- `task_audios`
- `task_topics`
- `product_topics`
- `products`
- `composition_jobs`
- `publish_logs`
- `publish_profiles`
- `schedule_config`
- `topic_groups`
- `system_logs`

### 3.2 兼容保留或正在过渡中的表 / 字段

- `publish_config`
  仍在 ORM 中，但调度器当前读取的是 `schedule_config`
- `tasks.product_id`
- `tasks.video_id`
- `tasks.copywriting_id`
- `tasks.audio_id`
- `tasks.cover_id`

这些任务表里的单资源外键仍然存在，但注释已经明确说明它们属于兼容保留列，当前主要资源模型已经切换到任务与素材的多对多关联表。

## 4. 核心业务主线表

### 4.1 `accounts`

**职责**：保存得物账号身份、加密登录态和账号健康状态，是所有自动化发布的执行主体。

#### 关键关系

- `accounts.id` -> `tasks.account_id`

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `account_id` | 外部账号标识，业务唯一键 |
| `account_name` | 账号显示名，用于 UI 和操作识别 |
| `cookie` | 兼容保留的 Cookie 存储位，允许保存加密 cookie |
| `storage_state` | 当前主用登录态存储位，保存加密后的 Playwright storage state |
| `status` | 账号是否可用，驱动 UI 和发布前校验 |
| `last_login` | 最近一次成功登录时间 |
| `phone_encrypted` | 加密手机号，仅用于连接流程和回显 |
| `dewu_nickname` | 得物侧昵称，便于校验连接结果 |
| `dewu_uid` | 得物平台 UID |
| `avatar_url` | 头像展示数据 |
| `tags` | JSON 标签数组，用于分类和筛选 |
| `remark` | 运营备注 |
| `session_expires_at` | 会话预计过期时间，健康检查后更新 |
| `last_health_check` | 最近健康检查时间 |
| `login_fail_count` | 连续登录失败次数，便于风控与诊断 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- 账号不是简单资料表，而是“自动化执行身份表”
- 账号状态与连接过程状态不是一回事
- 持久化层只记录可恢复的业务状态，不记录 SSE 过程态

### 4.2 `tasks`

**职责**：任务是系统的核心主实体，承载从素材编排、合成、调度、上传到失败恢复的完整生命周期。

#### 关键关系

- N:1 `accounts`
- N:1 `publish_profiles`
- 1:N `composition_jobs`
- 1:N `publish_logs`
- N:N `videos`
- N:N `copywritings`
- N:N `covers`
- N:N `audios`
- N:N `topics`

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `account_id` | 指定由哪个账号执行上传 |
| `product_id` | 兼容保留商品外键，旧流程遗留 |
| `video_id` / `copywriting_id` / `audio_id` / `cover_id` | 兼容保留单资源外键，当前主流程不再作为唯一真实来源 |
| `status` | 任务状态机主字段，典型值为 `draft/composing/ready/uploading/uploaded/failed/cancelled` |
| `publish_time` | 实际发布成功时间 |
| `error_msg` | 最近一次失败原因 |
| `priority` | 调度优先级，数值越大越优先 |
| `name` | 任务名称，主要用于 UI 和批量管理 |
| `description` | 任务说明 |
| `source_video_ids` | 原始输入视频列表的 JSON 表示，偏过程型字段 |
| `composition_template` | 合成模板名称，偏旧设计保留 |
| `composition_params` | 合成参数 JSON |
| `composition_job_id` | 指向当前任务最近一次合成作业的快捷入口 |
| `final_video_path` | 合成后成品视频本地路径 |
| `final_video_duration` | 成品视频时长 |
| `final_video_size` | 成品视频文件大小 |
| `scheduled_time` | 计划执行时间，用于调度扩展 |
| `retry_count` | 重试次数 |
| `dewu_video_id` | 得物侧返回的视频 ID |
| `dewu_video_url` | 得物侧视频链接 |
| `profile_id` | 绑定的任务级配置档 |
| `batch_id` | 批量任务追溯 ID，不单独建批次实体 |
| `failed_at_status` | 失败前状态，支持快速重试回到原阶段 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- `tasks` 不再是“单视频 + 单文案”的简单表，而是资源集合的锚点
- 旧单资源外键还在，是为了兼容 SQLite 和历史数据/代码路径
- 当前真实的资源装配关系，应该优先看关联表而不是旧 FK

## 5. 素材域模型

### 5.1 `products`

**职责**：商品聚合根，用于把视频、文案、封面、话题等素材挂到同一商品上下文。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `name` | 商品名，业务唯一键 |
| `dewu_url` | 得物商品链接 |
| `parse_status` | 商品解析状态，如 `pending/parsing/parsed/error` |
| `video_count` | 反范式视频数，优化列表页统计 |
| `copywriting_count` | 反范式文案数 |
| `cover_count` | 反范式封面数 |
| `topic_count` | 反范式话题数 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 关系职责

- 一个商品可以挂多个视频、文案、封面
- 与话题通过 `product_topics` 关联
- 与任务的直接绑定已经被弱化，商品更多承担素材组织上下文

### 5.2 `videos`

**职责**：视频素材库记录，可来自人工导入、扫描、下载或后续生成。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `product_id` | 归属商品，可为空 |
| `name` | 素材显示名 |
| `file_path` | 本地文件路径，是落地执行的关键字段 |
| `file_size` | 文件大小 |
| `duration` | 视频时长 |
| `width` / `height` | 分辨率信息 |
| `file_hash` | 内容哈希，支持去重和安全删除 |
| `source_type` | 来源类型，如原始素材或其他来源 |
| `created_at` / `updated_at` | 审计时间戳 |

### 5.3 `copywritings`

**职责**：文案素材库记录，用于发布正文、标题或 AI 生成文本的持久化。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `product_id` | 归属商品 |
| `name` | 文案名称，方便列表识别 |
| `content` | 真实文案内容 |
| `source_type` | 来源，如手工、AI、导入 |
| `source_ref` | 来源追踪信息 |
| `created_at` / `updated_at` | 审计时间戳 |

### 5.4 `covers`

**职责**：封面图片素材库记录，可挂到视频，也可挂到商品。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `video_id` | 来源视频，可为空 |
| `product_id` | 所属商品，可为空 |
| `name` | 封面名称 |
| `file_path` | 本地路径 |
| `file_size` | 文件大小 |
| `width` / `height` | 图片尺寸 |
| `file_hash` | 内容哈希，支持去重和安全删除 |
| `created_at` | 创建时间 |

### 5.5 `audios`

**职责**：音频素材记录，通常用于合成或后处理。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `name` | 音频名称 |
| `file_path` | 本地路径 |
| `file_size` | 文件大小 |
| `duration` | 音频时长 |
| `file_hash` | 内容哈希，支持去重和安全删除 |
| `created_at` | 创建时间 |

### 5.6 `topics`

**职责**：全局话题池，既能给任务直接使用，也能给商品和配置档复用。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `name` | 话题名，业务唯一键 |
| `heat` | 热度分值 |
| `source` | 来源，如手工或同步 |
| `last_synced` | 最近同步时间 |
| `created_at` | 创建时间 |

### 5.7 `topic_groups`

**职责**：话题模板表，用一个 JSON 数组聚合多个话题 ID，便于运营快速复用话题集合。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 内部主键 |
| `name` | 话题组名称，业务唯一 |
| `topic_ids` | JSON 数组，保存话题 ID 集合 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- 这里没有单独的 `topic_group_topics` 关联表
- 目前使用 JSON 聚合，适合模板型小集合，但不如正规关联表易查询

## 6. 任务资源关联表

这些表的作用是把任务从旧的“单资源模型”升级为“资源集合模型”。

### 6.1 `task_videos`

**职责**：一个任务可关联多个视频，并保留排序。

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 任务引用 |
| `video_id` | 视频引用 |
| `sort_order` | 视频顺序，支持多素材拼接场景 |

约束：

- `UNIQUE(task_id, video_id)`

### 6.2 `task_copywritings`

**职责**：一个任务可关联多条文案，并保留排序。

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 任务引用 |
| `copywriting_id` | 文案引用 |
| `sort_order` | 顺序 |

### 6.3 `task_covers`

**职责**：任务与封面的多对多关联。

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 任务引用 |
| `cover_id` | 封面引用 |
| `sort_order` | 顺序 |

### 6.4 `task_audios`

**职责**：任务与音频的多对多关联。

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 任务引用 |
| `audio_id` | 音频引用 |
| `sort_order` | 顺序 |

### 6.5 `task_topics`

**职责**：任务与话题的多对多关联。

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 任务引用 |
| `topic_id` | 话题引用 |

#### 设计说明

- 任务话题最终来源可能有两部分：
  1. 用户手动选择的话题
  2. `PublishProfile.global_topic_ids` 自动并入的话题

## 7. 商品扩展关联表

### 7.1 `product_topics`

**职责**：把商品与全局话题池关联起来，用于商品维度的话题组织。

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `product_id` | 商品引用 |
| `topic_id` | 话题引用 |

约束：

- `UNIQUE(product_id, topic_id)`

## 8. 合成与发布执行表

### 8.1 `composition_jobs`

**职责**：记录一次具体的合成执行过程和结果，是任务进入 `ready` 之前的过程表。

#### 关键关系

- N:1 `tasks`

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 所属任务 |
| `workflow_type` | 合成类型，如 `coze` / `local_ffmpeg` |
| `workflow_id` | 外部工作流标识 |
| `external_job_id` | 外部平台返回的任务 ID |
| `status` | 合成作业状态 |
| `progress` | 进度百分比 |
| `output_video_path` | 下载到本地后的输出视频路径 |
| `output_video_url` | 外部平台返回的视频地址 |
| `error_msg` | 错误原因 |
| `started_at` | 开始时间 |
| `completed_at` | 完成时间 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- 一个任务可以有多条合成记录，便于保留失败历史
- `tasks.composition_job_id` 只是快捷指针，不等于只有一条作业

### 8.2 `publish_logs`

**职责**：发布执行日志表，记录任务上传过程中的结果事件。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `task_id` | 对应任务 |
| `account_id` | 对应账号 |
| `status` | 日志状态，如成功或失败 |
| `message` | 详细说明 |
| `created_at` | 事件时间 |

#### 设计说明

- 这是任务执行历史的附属表，不替代 `tasks.status`
- `tasks.status` 表示当前态，`publish_logs` 表示历史轨迹

### 8.3 `system_logs`

**职责**：系统级日志，记录非任务专属的操作和异常。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `level` | 日志级别 |
| `module` | 归属模块 |
| `message` | 日志主消息 |
| `details` | 附加细节 |
| `created_at` | 创建时间 |

## 9. 配置模型

### 9.1 `publish_profiles`

**职责**：任务级配置档，决定任务如何合成、默认附带哪些全局话题、失败后如何重试。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `name` | 配置档名，业务唯一 |
| `is_default` | 是否系统默认配置档 |
| `composition_mode` | 合成模式，如 `none` / `coze` / `local_ffmpeg` |
| `coze_workflow_id` | Coze workflow 标识 |
| `composition_params` | 合成参数 JSON |
| `global_topic_ids` | 默认并入任务的话题 ID 列表 |
| `auto_retry` | 是否允许自动重试 |
| `max_retry_count` | 最大重试次数 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- 这是任务级配置，不是系统全局配置
- 一个任务可以显式绑定某个 profile；未绑定时回退到默认档案

### 9.2 `schedule_config`

**职责**：系统级调度配置表，控制调度器什么时候发布、多久发一次、每账号每天最多发多少。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `name` | 配置名称，当前默认用 `default` |
| `start_hour` | 每日调度开始时间 |
| `end_hour` | 每日调度结束时间 |
| `interval_minutes` | 两次发布之间的间隔 |
| `max_per_account_per_day` | 单账号每日上限 |
| `shuffle` | 是否打乱 ready 任务优先级 |
| `auto_start` | 应用启动时是否自动开始调度 |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- 这是全局行为配置，不是任务属性
- 调度器当前明确读取的是 `schedule_config`

### 9.3 `publish_config`

**职责**：旧版发布配置表，仍保留在 ORM 中。

#### 字段职责

| 字段 | 职责 |
|------|------|
| `id` | 主键 |
| `name` | 配置名 |
| `interval_minutes` | 发布间隔 |
| `start_hour` / `end_hour` | 发布时段 |
| `max_per_account_per_day` | 账号日上限 |
| `shuffle` | 是否打乱 |
| `auto_start` | 是否自动启动 |
| `global_topic_ids` | 旧设计里的全局话题 JSON |
| `created_at` / `updated_at` | 审计时间戳 |

#### 设计说明

- 新逻辑已经把“调度参数”和“话题配置”拆开
- 调度归 `schedule_config`
- 话题配置归 `publish_profiles`

## 10. 这套模型的设计特点

### 10.1 从单资源任务转向资源集合任务

`tasks` 里保留了旧式单资源外键，但当前主设计已经转向：

- 一个任务可挂多视频
- 一个任务可挂多文案
- 一个任务可挂多封面
- 一个任务可挂多音频
- 一个任务可挂多话题

这使任务能覆盖更复杂的编排和合成场景。

### 10.2 配置拆层清晰

- `publish_profiles` 负责任务如何加工
- `schedule_config` 负责系统何时执行

这是比旧 `publish_config` 更合理的职责划分。

### 10.3 状态与历史分开

- `tasks.status` 表示任务当前状态
- `composition_jobs` 保存合成过程历史
- `publish_logs` 保存发布过程历史
- `system_logs` 保存系统级历史

这种拆分让“当前态”和“历史轨迹”不会混在一张表里。

## 11. 当前模型层需要注意的现实情况

### 11.1 文档与代码有轻微偏差

旧文档里还存在这些过时点：

- 把 `Task` 仍写成单素材任务
- 把 `PublishConfig` 当成当前主配置表
- 漏掉 `PublishProfile`、`ScheduleConfig`、`TopicGroup` 等新表

### 11.2 兼容字段仍在

`tasks` 表里旧 FK 还未彻底移除，说明模型层正处于兼容演进期。读代码时应优先看：

- `TaskAssembler`
- `TaskDistributor`
- `CompositionService`
- `PublishService`

而不是只根据旧字段名推断当前业务。

### 11.3 JSON 字段较多

这些字段不是正规拆表，而是文本存 JSON：

- `accounts.tags`
- `tasks.source_video_ids`
- `tasks.composition_params`
- `publish_profiles.composition_params`
- `publish_profiles.global_topic_ids`
- `topic_groups.topic_ids`
- `publish_config.global_topic_ids`

这对快速演进有利，但会增加查询、约束和迁移复杂度。

## 12. 最后总结

如果只记一句话，这套数据库模型的核心可以概括为：

`Account` 提供执行身份，`Task` 承担业务生命周期，素材表提供资源池，关联表完成任务装配，`CompositionJob` 和 `PublishLog` 负责过程追踪，`PublishProfile` 与 `ScheduleConfig` 负责配置分层。

也可以把它看成这样一条关系链：

```text
账号
→ 绑定任务
→ 任务关联素材集合
→ 配置档决定是否需要合成
→ 合成作业产出成品
→ 调度器在全局配置下执行发布
→ 发布日志和系统日志回写结果
```
