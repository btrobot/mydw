# 任务管理实体关系（ER）设计

> 版本: 1.0.0 | 创建日期: 2026-04-08
> 作者: Tech Lead
> 状态: Draft

---

## 一、核心实体设计

### 1. Task（发布任务）- 主实体

**职责**：管理从素材编排到上传完成的完整生命周期

```sql
CREATE TABLE tasks (
  -- 主键
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- 基础信息
  name VARCHAR(256),                    -- 任务名称
  description TEXT,                     -- 任务描述
  
  -- 关联关系
  account_id INTEGER NOT NULL,          -- 上传账号
  product_id INTEGER,                   -- 关联商品
  
  -- 素材输入（原始素材）
  source_video_ids TEXT,                -- JSON array，原始视频片段 ID 列表 [1,2,3]
  copywriting_id INTEGER,               -- 文案 ID
  audio_id INTEGER,                     -- 音频 ID
  cover_id INTEGER,                     -- 封面 ID
  
  -- 合成配置
  composition_template VARCHAR(64),     -- 合成模板名称（如 "standard", "highlight"）
  composition_params TEXT,              -- JSON，合成参数（时长、转场效果等）
  
  -- 合成结果
  composition_job_id INTEGER,           -- 关联的合成任务 ID
  final_video_path VARCHAR(512),        -- 成品视频路径（合成后）
  final_video_duration INTEGER,         -- 成品视频时长（秒）
  final_video_size INTEGER,             -- 成品视频大小（字节）
  
  -- 任务状态
  status VARCHAR(32) DEFAULT 'draft',   -- 状态枚举（见下方状态机）
  
  -- 上传配置
  scheduled_time DATETIME,              -- 计划上传时间
  priority INTEGER DEFAULT 0,           -- 优先级（数字越大越优先）
  
  -- 执行结果
  uploaded_at DATETIME,                 -- 实际上传时间
  dewu_video_id VARCHAR(128),           -- 得物平台返回的视频 ID
  dewu_video_url VARCHAR(512),          -- 得物视频链接
  error_msg TEXT,                       -- 错误信息
  retry_count INTEGER DEFAULT 0,        -- 重试次数
  
  -- 审计字段
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- 外键约束
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (copywriting_id) REFERENCES copywritings(id),
  FOREIGN KEY (audio_id) REFERENCES audios(id),
  FOREIGN KEY (cover_id) REFERENCES covers(id),
  FOREIGN KEY (composition_job_id) REFERENCES composition_jobs(id)
);

-- 索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_account_id ON tasks(account_id);
CREATE INDEX idx_tasks_scheduled_time ON tasks(scheduled_time);
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

**状态枚举**：
```python
class TaskStatus(str, Enum):
    DRAFT = "draft"              # 草稿（编辑中）
    COMPOSING = "composing"      # 合成中
    READY = "ready"              # 待上传（合成完成）
    UPLOADING = "uploading"      # 上传中
    UPLOADED = "uploaded"        # 已上传
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
```

**状态机**：
```
draft（草稿）
  ↓ 提交合成
composing（合成中）
  ↓ 合成完成
ready（待上传）
  ↓ 开始上传
uploading（上传中）
  ↓ 上传完成
uploaded（已上传）

任何阶段都可以 → failed（失败）或 cancelled（取消）
failed → 重试 → 回到对应阶段
```

---

### 2. CompositionJob（视频合成任务）- 新增

**职责**：管理视频合成的执行过程和结果

```sql
CREATE TABLE composition_jobs (
  -- 主键
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- 关联任务
  task_id INTEGER NOT NULL,             -- 所属任务
  
  -- 输入素材
  source_video_ids TEXT NOT NULL,       -- JSON array，原始视频 ID 列表
  audio_id INTEGER,                     -- 音频 ID
  cover_id INTEGER,                     -- 封面 ID
  copywriting_id INTEGER,               -- 文案 ID（用于字幕生成）
  
  -- 合成配置
  template VARCHAR(64),                 -- 模板名称
  params TEXT,                          -- JSON，合成参数
  
  -- 外部工作流
  workflow_type VARCHAR(32),            -- 'coze', 'local_ffmpeg', 'custom'
  workflow_id VARCHAR(128),             -- 扣子 workflow_id 或其他标识
  external_job_id VARCHAR(128),         -- 外部任务 ID（扣子返回的）
  
  -- 执行状态
  status VARCHAR(32) DEFAULT 'pending', -- pending/processing/completed/failed/cancelled
  progress INTEGER DEFAULT 0,           -- 进度 0-100
  
  -- 输出结果
  output_video_path VARCHAR(512),       -- 成品视频路径
  output_video_duration INTEGER,        -- 时长（秒）
  output_video_size INTEGER,            -- 文件大小（字节）
  output_video_url VARCHAR(512),        -- 扣子返回的视频下载链接
  
  -- 执行日志
  started_at DATETIME,
  completed_at DATETIME,
  error_msg TEXT,
  error_code VARCHAR(64),               -- 错误代码（用于分类统计）
  execution_log TEXT,                   -- JSON，详细执行日志
  
  -- 审计字段
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- 外键约束
  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
  FOREIGN KEY (audio_id) REFERENCES audios(id),
  FOREIGN KEY (cover_id) REFERENCES covers(id),
  FOREIGN KEY (copywriting_id) REFERENCES copywritings(id)
);

-- 索引
CREATE INDEX idx_composition_jobs_task_id ON composition_jobs(task_id);
CREATE INDEX idx_composition_jobs_status ON composition_jobs(status);
CREATE INDEX idx_composition_jobs_external_job_id ON composition_jobs(external_job_id);
```

**状态枚举**：
```python
class CompositionStatus(str, Enum):
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
```

---

### 3. WorkflowTemplate（合成模板）- 新增

**职责**：定义可复用的视频合成模板

```sql
CREATE TABLE workflow_templates (
  -- 主键
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- 基础信息
  name VARCHAR(128) NOT NULL UNIQUE,    -- 模板名称
  display_name VARCHAR(128),            -- 显示名称
  description TEXT,                     -- 描述
  
  -- 工作流配置
  workflow_type VARCHAR(32),            -- 'coze', 'local_ffmpeg'
  workflow_id VARCHAR(128),             -- 扣子 workflow_id
  
  -- 模板参数定义
  params_schema TEXT,                   -- JSON Schema，定义可配置参数
  default_params TEXT,                  -- JSON，默认参数值
  
  -- 输入要求
  required_video_count INTEGER,         -- 需要几个视频片段（0=不限）
  min_video_count INTEGER DEFAULT 1,    -- 最少视频数
  max_video_count INTEGER,              -- 最多视频数（NULL=不限）
  required_audio BOOLEAN DEFAULT FALSE, -- 是否需要音频
  required_cover BOOLEAN DEFAULT FALSE, -- 是否需要封面
  required_copywriting BOOLEAN DEFAULT FALSE, -- 是否需要文案
  
  -- 输出配置
  output_duration_min INTEGER,          -- 输出视频最短时长（秒）
  output_duration_max INTEGER,          -- 输出视频最长时长（秒）
  output_format VARCHAR(16) DEFAULT 'mp4', -- 输出格式
  
  -- 状态
  is_active BOOLEAN DEFAULT TRUE,
  sort_order INTEGER DEFAULT 0,         -- 排序
  
  -- 审计字段
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_workflow_templates_is_active ON workflow_templates(is_active);
CREATE INDEX idx_workflow_templates_sort_order ON workflow_templates(sort_order);
```

**示例数据**：
```json
{
  "name": "standard_30s",
  "display_name": "标准 30 秒视频",
  "workflow_type": "coze",
  "workflow_id": "coze_workflow_123",
  "params_schema": {
    "type": "object",
    "properties": {
      "target_duration": {"type": "integer", "default": 30},
      "transition_effect": {"type": "string", "enum": ["fade", "slide", "none"]},
      "add_subtitle": {"type": "boolean", "default": true}
    }
  },
  "required_video_count": 0,
  "min_video_count": 1,
  "max_video_count": 5,
  "required_audio": false,
  "required_copywriting": true
}
```

---

### 4. UploadJob（上传任务）- 可选

**职责**：记录上传过程的详细信息（如果需要更细粒度的上传监控）

```sql
CREATE TABLE upload_jobs (
  -- 主键
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- 关联
  task_id INTEGER NOT NULL,
  account_id INTEGER NOT NULL,
  
  -- 上传内容
  video_path VARCHAR(512) NOT NULL,
  copywriting_content TEXT,
  topic_ids TEXT,                       -- JSON array
  
  -- 执行状态
  status VARCHAR(32) DEFAULT 'pending', -- pending/uploading/uploaded/failed
  progress INTEGER DEFAULT 0,           -- 进度 0-100
  
  -- 执行时间
  started_at DATETIME,
  completed_at DATETIME,
  
  -- 结果
  dewu_video_id VARCHAR(128),           -- 得物平台返回的视频 ID
  dewu_video_url VARCHAR(512),          -- 得物视频链接
  error_msg TEXT,
  error_code VARCHAR(64),
  
  -- 审计字段
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- 外键约束
  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- 索引
CREATE INDEX idx_upload_jobs_task_id ON upload_jobs(task_id);
CREATE INDEX idx_upload_jobs_status ON upload_jobs(status);
```

**说明**：
- 如果上传过程简单，可以不单独建表，直接在 Task 表记录
- 如果需要详细的上传监控、重试记录，建议单独建表

---

## 二、实体关系图（ER Diagram）

```
┌─────────────────┐
│   Account       │
│  (上传账号)      │
└────┬────────────┘
     │ 1
     │
     │ N
┌────▼─────────────────────────────────────────────────────┐
│                    Task (发布任务)                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 素材输入: source_video_ids[], copywriting,        │   │
│  │          audio, cover, topics                    │   │
│  │ 合成配置: template, params                        │   │
│  │ 合成结果: composition_job_id, final_video_path    │   │
│  │ 状态: draft→composing→ready→uploading→uploaded   │   │
│  └──────────────────────────────────────────────────┘   │
└────┬──────────────────────┬──────────────────────────────┘
     │ 1                    │ 1
     │                      │
     │ 1                    │ N
┌────▼──────────────────┐  ┌▼──────────────────┐
│  CompositionJob       │  │   TaskTopic        │
│  (视频合成任务)        │  │   (任务-话题)       │
│  ┌─────────────────┐  │  └───────┬───────────┘
│  │ 输入: 素材列表   │  │          │ N
│  │ 工作流: 扣子ID   │  │          │
│  │ 输出: 成品视频   │  │  ┌───────▼───────────┐
│  │ 状态: pending→   │  │  │   Topic            │
│  │      processing→ │  │  │   (话题标签)        │
│  │      completed   │  │  └────────────────────┘
│  └─────────────────┘  │
└───────┬───────────────┘
        │ N
        │
        │ 1
┌───────▼──────────────────┐
│  WorkflowTemplate        │
│  (合成模板)               │
│  ┌────────────────────┐  │
│  │ 扣子 workflow_id    │  │
│  │ 参数定义 (Schema)   │  │
│  │ 输入要求            │  │
│  └────────────────────┘  │
└──────────────────────────┘

素材实体（已存在）：
┌──────────┐  ┌──────────────┐  ┌────────┐  ┌────────┐
│  Video   │  │ Copywriting  │  │ Audio  │  │ Cover  │
│ (视频片段)│  │   (文案)      │  │ (音频) │  │ (封面) │
└────┬─────┘  └──────┬───────┘  └───┬────┘  └───┬────┘
     │               │              │           │
     └───────────────┴──────────────┴───────────┘
                     │
                     │ N
            ┌────────▼────────┐
            │    Product      │
            │    (商品)        │
            └─────────────────┘
```

---

## 三、关键关系说明

### 1. Task ↔ CompositionJob（1:1）
- 一个任务对应一个合成任务
- 合成任务失败后可以重新创建新的 CompositionJob
- `Task.composition_job_id` 指向当前/最新的合成任务

### 2. Task ↔ Videos（1:N）
- `Task.source_video_ids` 存储 JSON 数组 `[1, 2, 3]`
- 一个任务可以使用多个视频片段
- 通过 JSON 数组避免创建中间表

### 3. Task ↔ Topics（N:N）
- 通过 `task_topics` 中间表关联
- 一个任务可以有多个话题标签
- 一个话题可以被多个任务使用

### 4. CompositionJob ↔ WorkflowTemplate（N:1）
- 多个合成任务可以使用同一个模板
- 模板定义了合成的规则和参数

### 5. Task ↔ Account（N:1）
- 一个账号可以有多个任务
- 一个任务只能属于一个账号

---

## 四、数据迁移策略

### 阶段 1: 新增表
```sql
-- 创建新表
CREATE TABLE composition_jobs (...);
CREATE TABLE workflow_templates (...);
CREATE TABLE upload_jobs (...);  -- 可选
```

### 阶段 2: 修改 Task 表
```sql
-- 新增字段
ALTER TABLE tasks ADD COLUMN source_video_ids TEXT;
ALTER TABLE tasks ADD COLUMN composition_template VARCHAR(64);
ALTER TABLE tasks ADD COLUMN composition_params TEXT;
ALTER TABLE tasks ADD COLUMN composition_job_id INTEGER;
ALTER TABLE tasks ADD COLUMN final_video_path VARCHAR(512);
ALTER TABLE tasks ADD COLUMN final_video_duration INTEGER;
ALTER TABLE tasks ADD COLUMN final_video_size INTEGER;
ALTER TABLE tasks ADD COLUMN scheduled_time DATETIME;
ALTER TABLE tasks ADD COLUMN retry_count INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN dewu_video_id VARCHAR(128);
ALTER TABLE tasks ADD COLUMN dewu_video_url VARCHAR(512);

-- 修改状态枚举（需要迁移脚本）
-- 旧状态: pending/running/success/failed/paused
-- 新状态: draft/composing/ready/uploading/uploaded/failed/cancelled
```

### 阶段 3: 数据迁移
```python
# 迁移现有任务状态
status_mapping = {
    "pending": "ready",      # 待发布 → 待上传
    "running": "uploading",  # 发布中 → 上传中
    "success": "uploaded",   # 已发布 → 已上传
    "failed": "failed",      # 失败 → 失败
    "paused": "draft",       # 已暂停 → 草稿
}

# 迁移 video_id 到 source_video_ids
# 如果 video_id 不为空，转换为 JSON 数组 [video_id]
UPDATE tasks SET source_video_ids = json_array(video_id) WHERE video_id IS NOT NULL;
```

---

## 五、索引优化建议

### 高频查询索引
```sql
-- 任务列表查询（按状态、账号、时间）
CREATE INDEX idx_tasks_status_account ON tasks(status, account_id);
CREATE INDEX idx_tasks_scheduled_time_priority ON tasks(scheduled_time, priority);

-- 合成任务查询（按状态、外部 ID）
CREATE INDEX idx_composition_jobs_status_created ON composition_jobs(status, created_at);

-- 上传队列查询
CREATE INDEX idx_tasks_ready_priority ON tasks(status, priority) WHERE status = 'ready';
```

### 统计查询索引
```sql
-- 任务统计（按日期、状态）
CREATE INDEX idx_tasks_created_status ON tasks(created_at, status);
CREATE INDEX idx_tasks_uploaded_at ON tasks(uploaded_at) WHERE uploaded_at IS NOT NULL;
```

---

## 六、数据完整性约束

### 业务规则约束
```sql
-- 1. 任务必须有账号
ALTER TABLE tasks ADD CONSTRAINT chk_tasks_account_id CHECK (account_id IS NOT NULL);

-- 2. 合成任务必须有输入素材
ALTER TABLE composition_jobs ADD CONSTRAINT chk_composition_source 
  CHECK (source_video_ids IS NOT NULL AND source_video_ids != '[]');

-- 3. 优先级范围
ALTER TABLE tasks ADD CONSTRAINT chk_tasks_priority 
  CHECK (priority >= 0 AND priority <= 100);

-- 4. 进度范围
ALTER TABLE composition_jobs ADD CONSTRAINT chk_composition_progress 
  CHECK (progress >= 0 AND progress <= 100);
```

---

## 附录

### 参考文档
- [任务管理业务流程分析](./task-management-analysis.md)
- [数据模型](./data-model.md)
- [API 参考](./api-reference.md)
