# 任务管理领域模型设计

> 版本: 2.1.0 | 创建日期: 2026-04-09
> 作者: Tech Lead
> 状态: Approved (Architecture Review 通过)

---

## 一、业务全景

```
素材编排 ──→ 视频合成（Coze / 本地 FFmpeg） ──→ 调度上传（Patchright → 得物）
```

任务贯穿这三个阶段。合成配置跟任务走（不同任务可用不同工作流），调度配置跟系统走（全局统一的时间窗口和频率控制）。

---

## 二、核心领域概念

| 概念 | 实体 | 职责 |
|------|------|------|
| 任务 | Task | 单个发布任务的全生命周期 |
| 合成配置档 | PublishProfile | 可复用的合成配置（合成方式 + 话题 + 重试策略） |
| 调度配置 | ScheduleConfig | 全局单例，上传调度参数（时间窗口 + 频率 + 限额） |
| 合成任务 | CompositionJob | 视频合成的执行过程和结果 |

### 为什么这样划分？

- **合成配置跟任务走** — 不同任务可以用不同的 Coze 工作流
- **调度配置跟系统走** — 时间窗口、间隔、日限额是全局运行参数，不是任务级参数
- **TaskBatch 降级为内部字段** — 用户日常关心单个任务状态，"批次"作为 Task.batch_id 追溯字段即可，不暴露为一级概念

---

## 三、实体设计

### 3.1 PublishProfile（合成配置档）

```sql
CREATE TABLE publish_profiles (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  name                    VARCHAR(128) NOT NULL UNIQUE,
  is_default              BOOLEAN DEFAULT FALSE,          -- 缺省配置标记（全局唯一）

  -- 合成配置
  composition_mode        VARCHAR(32) DEFAULT 'none',     -- 'none' / 'coze' / 'local_ffmpeg'
  coze_workflow_id        VARCHAR(128),
  composition_params      TEXT,                           -- JSON

  -- 话题配置
  global_topic_ids        TEXT DEFAULT '[]',              -- JSON array

  -- 重试配置
  auto_retry              BOOLEAN DEFAULT TRUE,
  max_retry_count         INTEGER DEFAULT 3,

  -- 审计
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

缺省配置机制：
- `is_default=True` 全局唯一（应用层保证）
- 不指定 profile 的任务自动走缺省配置
- 系统启动时自动创建 `name="默认配置", is_default=True, composition_mode='none'`

### 3.2 ScheduleConfig（调度配置）

```sql
CREATE TABLE schedule_config (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  name                    VARCHAR(64) DEFAULT 'default',

  -- 调度参数
  start_hour              INTEGER DEFAULT 9,
  end_hour                INTEGER DEFAULT 22,
  interval_minutes        INTEGER DEFAULT 30,
  max_per_account_per_day INTEGER DEFAULT 5,

  -- 行为参数
  shuffle                 BOOLEAN DEFAULT FALSE,
  auto_start              BOOLEAN DEFAULT FALSE,

  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

全局单例，查询 `name='default'`。话题配置统一由 PublishProfile 管理，ScheduleConfig 不存话题。

### 3.3 Task（任务）

```sql
CREATE TABLE tasks (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,

  -- 关联
  profile_id              INTEGER REFERENCES publish_profiles(id),
  account_id              INTEGER NOT NULL REFERENCES accounts(id),
  product_id              INTEGER REFERENCES products(id),
  batch_id                VARCHAR(64),          -- 批量创建追溯标识（内部用）

  -- 素材
  video_id                INTEGER REFERENCES videos(id),
  copywriting_id          INTEGER REFERENCES copywritings(id),
  audio_id                INTEGER REFERENCES audios(id),
  cover_id                INTEGER REFERENCES covers(id),
  source_video_ids        TEXT,                 -- JSON array，多视频输入

  -- 合成结果
  composition_job_id      INTEGER REFERENCES composition_jobs(id),
  final_video_path        VARCHAR(512),
  final_video_duration    INTEGER,
  final_video_size        INTEGER,

  -- 状态机
  status                  VARCHAR(32) DEFAULT 'draft',
  priority                INTEGER DEFAULT 0,
  scheduled_time          DATETIME,
  retry_count             INTEGER DEFAULT 0,
  failed_at_status        VARCHAR(32),          -- 失败前状态（快速重试用）

  -- 上传结果
  uploaded_at             DATETIME,
  dewu_video_id           VARCHAR(128),
  dewu_video_url          VARCHAR(512),
  error_msg               TEXT,

  -- 审计
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 CompositionJob（合成任务）

```sql
CREATE TABLE composition_jobs (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id                 INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  workflow_type            VARCHAR(32),          -- 'coze' / 'local_ffmpeg'
  workflow_id              VARCHAR(128),         -- Coze workflow_id
  external_job_id          VARCHAR(128),         -- Coze execute_id
  status                   VARCHAR(32) DEFAULT 'pending',
  progress                 INTEGER DEFAULT 0,
  output_video_path        VARCHAR(512),
  output_video_url         VARCHAR(512),
  error_msg                TEXT,
  started_at               DATETIME,
  completed_at             DATETIME,
  created_at               DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at               DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

重试策略：
- 重试合成时创建新的 CompositionJob，不更新旧记录
- Task.composition_job_id 更新为最新 job ID
- 旧 CompositionJob 保留作为历史（用于失败原因分析）

---

## 四、状态机

### 4.1 状态枚举

```python
class TaskStatus(str, Enum):
    DRAFT     = "draft"       # 草稿（可编辑，等待提交合成）
    COMPOSING = "composing"   # 合成中（等待 Coze/FFmpeg）
    READY     = "ready"       # 待上传（合成完成或无需合成）
    UPLOADING = "uploading"   # 上传中（Patchright 执行中）
    UPLOADED  = "uploaded"    # 已上传（终态-成功）
    FAILED    = "failed"      # 失败（可重试）
    CANCELLED = "cancelled"   # 已取消（终态）
```

### 4.2 状态转换图

```
创建任务（composition_mode=none）──────────────────► ready
创建任务（composition_mode=coze/ffmpeg）──► draft
                                            │
                                            │ 提交合成
                                            ▼
                                         composing
                                            │
                              ┌─────────────┼─────────────┐
                              │ 合成完成     │              │ 合成失败
                              ▼             │              ▼
                           ready            │           failed
                              │             │              │
                              │ 调度上传     │   ┌──────────┤
                              ▼             │   │ 快速重试   │ 编辑重试
                          uploading         │   │ (自动继续)  │ (改素材)
                              │             │   │           │
                    ┌─────────┤             │   ▼           ▼
                    │ 成功     │ 失败        │ composing   draft
                    ▼         ▼             │ 或 ready
                 uploaded   failed ─────────┘

任何非终态 ──► cancelled（用户取消）
```

### 4.3 转换规则

| 从 | 到 | 触发条件 |
|----|-----|---------|
| (创建) | ready | composition_mode == 'none'，跳过 draft |
| (创建) | draft | composition_mode != 'none'，等待提交合成 |
| draft | composing | 用户提交合成 |
| composing | ready | CompositionJob 完成 |
| composing | failed | CompositionJob 失败 |
| ready | uploading | 调度器选中执行 |
| uploading | uploaded | 上传成功 |
| uploading | failed | 上传失败 |
| failed | composing | 快速重试（合成阶段失败） |
| failed | ready | 快速重试（上传阶段失败） |
| failed | draft | 编辑重试（修改素材后重新提交） |
| 任何非终态 | cancelled | 用户取消 |

### 4.4 两种重试模式

| 模式 | 操作 | 适用场景 | 用户动作 |
|------|------|---------|---------|
| 快速重试 | failed → 失败前的状态 | 临时性失败（网络超时、服务抖动） | 点"重试" |
| 编辑重试 | failed → draft | 素材有问题需要修改 | 点"编辑"，改完再提交 |

快速重试的目标状态由 `failed_at_status` 字段决定：

```python
# 标记失败时
task.failed_at_status = task.status  # 记录失败前状态
task.status = "failed"

# 快速重试时
task.status = task.failed_at_status  # 回到失败前状态
task.failed_at_status = None
task.retry_count += 1
```

---

## 五、配置解析机制

### 5.1 两级解析

```
Task.profile_id（任务级指定）
  → is_default=True 的 Profile（系统缺省）
```

### 5.2 解析逻辑

```python
async def resolve_profile(task: Task) -> PublishProfile:
    if task.profile_id:
        return await get_profile(task.profile_id)
    return await get_default_profile()
```

### 5.3 配置职责分离

| 配置 | 实体 | 跟谁走 | 示例 |
|------|------|--------|------|
| 合成方式 | PublishProfile | 跟任务 | "这批任务用 Coze 标准30s工作流" |
| 话题标签 | PublishProfile | 跟任务 | "这批任务打上球鞋话题" |
| 重试策略 | PublishProfile | 跟任务 | "最多重试3次" |
| 时间窗口 | ScheduleConfig | 跟系统 | "全局 9-22 点上传" |
| 上传间隔 | ScheduleConfig | 跟系统 | "全局每 30 分钟一个" |
| 账号日限额 | ScheduleConfig | 跟系统 | "全局每账号每天最多 5 个" |

---

## 六、调度架构

### 6.1 双调度器

```
┌──────────────────────────────────────────────┐
│              SchedulerManager                 │
│                                              │
│  ┌────────────────────┐  ┌─────────────────┐ │
│  │ CompositionPoller  │  │ UploadScheduler  │ │
│  │                    │  │                  │ │
│  │ 每 10s 轮询        │  │ 读 ScheduleConfig│ │
│  │ composing 任务     │  │ ready 任务        │ │
│  │ → Coze API 查状态  │  │ → 时间窗口检查    │ │
│  │ → 成功: task→ready │  │ → 账号限额检查    │ │
│  │ → 失败: task→failed│  │ → Patchright 上传 │ │
│  └────────────────────┘  └─────────────────┘ │
│                                              │
│  协作：通过 Task.status 解耦，无直接依赖       │
└──────────────────────────────────────────────┘
```

### 6.2 CompositionPoller

- 单循环设计，系统启动时自动启动
- 轮询间隔：`COZE_POLL_INTERVAL`（默认 10s）
- 每轮最多查询 10 个 `status=composing` 的任务，防止触发 Coze 速率限制
- 通过 `CompositionJob.external_job_id` 调 Coze API 查状态
- 成功：下载视频 → task.status=ready
- 失败：task.status=failed

### 6.3 UploadScheduler

- 单循环设计，1 个循环避免重复选取任务
- 从 `status=ready` 取任务
- 调度参数从全局 ScheduleConfig 读取
- 时间窗口 + 账号限额 + 间隔控制

---

## 七、ER 关系图

```
┌────────────────┐
│ PublishProfile │──1:N──► Task（合成配置）
│ (合成配置档)    │
└────────────────┘

┌────────────────┐
│ ScheduleConfig │         全局单例（调度参数）
│ (调度配置)      │
└────────────────┘

Account ──1:N──► Task
Product ──1:N──► Task

Task ──1:N──► CompositionJob（可选，重试时创建新记录）
Task ──N:N──► Topic（via task_topics）
Task ──N:1──► Video / Copywriting / Audio / Cover
Task ──1:N──► PublishLog
```

```
┌────────────────┐
│ PublishProfile │
│  composition_  │
│  mode/params   │
└───────┬────────┘
        │ 1:N
        ▼
┌──────────────────────────────────────────┐
│                 Task                      │
│  素材 + 状态机 + 上传结果                  │
│  draft→composing→ready→uploading→uploaded │
└───┬──────────────┬───────────────────────┘
    │ 1:N          │ 1:N
    ▼              ▼
┌──────────────┐  ┌────────────┐
│CompositionJob│  │ PublishLog  │
└──────────────┘  └────────────┘
```

---

## 八、实施计划

### Phase 1：数据模型

1. 创建 `publish_profiles` 表 + 默认 Profile
2. 创建 `composition_jobs` 表
3. 创建 `schedule_config` 表（替代 publish_config）
4. Task 表新增 `profile_id`、`batch_id`、`failed_at_status` 字段
5. 激活 migration 016 已有的合成相关字段
6. 迁移现有 publish_config 数据到 schedule_config

### Phase 2：状态机 + 调度器

1. 实现 TaskStatus 新枚举（7 状态）
2. 实现快速重试 / 编辑重试
3. UploadScheduler 单循环，从 `status=ready` 取任务
4. 前端状态标签更新

### Phase 3：Profile 管理

1. PublishProfileService CRUD + 缺省配置管理
2. TaskDistributor / TaskAssembler 接受 profile_id
3. 前端 Profile 管理页面 + 组装弹窗增加 Profile 选择

### Phase 4：Coze 合成集成

1. CozeClient（backend/core/coze_client.py）
2. CompositionService（提交合成、处理结果）
3. CompositionPoller（单循环后台轮询）
4. Task API 新增合成端点
5. 前端任务详情页展示合成进度

---

## 九、关键设计决策

| # | 决策 | 选择 | 理由 |
|---|------|------|------|
| 1 | 合成配置和调度配置是否放一起 | 拆开 | 合成跟任务走，调度跟系统走，职责不同 |
| 2 | TaskBatch 是否暴露为一级概念 | 不暴露 | 用户使用频率低，降级为内部追溯字段 |
| 3 | 重试是否统一回 draft | 区分两种 | 快速重试覆盖 80% 临时性失败场景 |
| 4 | none 模式是否经过 draft | 跳过 | 无需合成的任务直接 ready |
| 5 | Profile 与 Task 的关系 | 1:N（FK） | 简单直接 |
| 6 | 缺省配置实现 | is_default 标记 | 应用层保证唯一 |
| 7 | CompositionJob 是否独立表 | 独立 | 有自己的生命周期和外部 ID |
| 8 | 调度器协作方式 | Task.status 解耦 | 状态驱动，简单可靠 |
| 9 | 调度器循环数 | 单循环 | 避免重复选取任务 |
| 10 | 快速重试如何判断目标状态 | failed_at_status 字段 | 比解析 error_msg 可靠 |
| 11 | 合成重试时 CompositionJob 处理 | 创建新记录 | 旧记录保留为历史 |

---

## 附录

### 参考文档

- [扣子接入方式](./coze-integration.md)
- [任务管理业务流程分析](./archive/analysis/task-management-analysis.md)
- [任务管理 ER 设计](./archive/analysis/task-management-er-design.md)
- [任务管理操作清单](./archive/analysis/task-management-operations.md)
