# 任务管理操作清单

> 版本: 1.0.0 | 创建日期: 2026-04-08
> 作者: Tech Lead
> 状态: Draft

---

## 一、操作域分类

任务管理系统分为 5 个核心操作域：

1. **任务编排（Task Orchestration）** - 创建和管理任务
2. **视频合成（Composition）** - 调用外部工作流合成视频
3. **上传调度（Upload Scheduling）** - 自动化上传到得物
4. **模板管理（Template Management）** - 管理合成模板
5. **监控统计（Monitoring）** - 任务执行监控和数据分析

---

## 二、操作域 1: 任务编排

### 1.1 创建单个任务

**业务场景**：手动创建一个发布任务

**输入**：
```json
{
  "name": "AJ1 黑红配色开箱",
  "account_id": 1,
  "product_id": 10,
  "source_video_ids": [101, 102, 103],
  "copywriting_id": 50,
  "audio_id": 20,
  "cover_id": 30,
  "topic_ids": [1, 2, 3],
  "composition_template": "standard_30s",
  "composition_params": {
    "target_duration": 30,
    "transition_effect": "fade"
  },
  "scheduled_time": "2026-04-09T10:00:00",
  "priority": 5
}
```

**输出**：
```json
{
  "id": 1001,
  "status": "draft",
  "created_at": "2026-04-08T14:30:00"
}
```

**API**：`POST /api/tasks`

**前置条件**：
- account_id 存在且状态正常
- source_video_ids 中的视频都存在
- 其他素材 ID 存在（如果提供）

**后置状态**：
- Task 记录创建（status = draft）
- 可以继续编辑或提交合成

---

### 1.2 批量组装任务

**业务场景**：将多个视频快速分配给多个账号

**输入**：
```json
{
  "video_ids": [101, 102, 103, 104, 105],
  "account_ids": [1, 2, 3],
  "strategy": "round_robin",
  "copywriting_mode": "auto_match",
  "composition_template": "standard_30s",
  "topic_ids": [1, 2]
}
```

**分配逻辑**（round_robin）：
- 视频 101 → 账号 1
- 视频 102 → 账号 2
- 视频 103 → 账号 3
- 视频 104 → 账号 1
- 视频 105 → 账号 2

**输出**：
```json
{
  "created_count": 5,
  "tasks": [
    {"id": 1001, "account_id": 1, "video_ids": [101]},
    {"id": 1002, "account_id": 2, "video_ids": [102]},
    ...
  ]
}
```

**API**：`POST /api/tasks/batch-assemble`

**文案匹配规则**（copywriting_mode）：
- `auto_match`: 按商品匹配 > 按关键词匹配 > 随机选择
- `manual`: 不自动匹配，需要后续手动指定
- `same_for_all`: 所有任务使用同一文案

---

### 1.3 编辑任务

**业务场景**：修改草稿状态的任务

**输入**：
```json
{
  "name": "AJ1 黑红配色开箱（修改）",
  "source_video_ids": [101, 102],
  "priority": 10
}
```

**API**：`PUT /api/tasks/{id}`

**限制**：
- 只能编辑 `draft` 状态的任务
- `composing/uploading` 状态不可编辑
- `failed` 状态可以编辑后重试

---

### 1.4 删除任务

**API**：`DELETE /api/tasks/{id}`

**限制**：
- `draft/failed/cancelled` 可直接删除
- `composing/uploading` 需先取消

**级联删除**：
- 删除任务时，关联的 CompositionJob 也会被删除（ON DELETE CASCADE）
- TaskTopic 关联记录也会被删除

---

### 1.5 查询任务列表

**API**：`GET /api/tasks`

**查询参数**：
```
?status=ready              # 按状态筛选
&account_id=1              # 按账号筛选
&product_id=10             # 按商品筛选
&start_date=2026-04-01     # 按创建时间范围
&end_date=2026-04-30
&keyword=AJ1               # 按任务名称搜索
&sort=priority             # 排序字段
&order=desc                # 排序方向
&limit=20                  # 分页大小
&offset=0                  # 分页偏移
```

**响应**：
```json
{
  "total": 100,
  "items": [
    {
      "id": 1001,
      "name": "AJ1 黑红配色开箱",
      "status": "ready",
      "account": {"id": 1, "name": "账号A"},
      "product": {"id": 10, "name": "AJ1"},
      "priority": 5,
      "created_at": "2026-04-08T14:30:00"
    }
  ]
}
```

---

### 1.6 任务详情

**API**：`GET /api/tasks/{id}/detail`

**响应**：
```json
{
  "id": 1001,
  "name": "AJ1 黑红配色开箱",
  "status": "ready",
  "account": {...},
  "product": {...},
  "source_videos": [
    {"id": 101, "name": "开箱片段1.mp4", "duration": 10}
  ],
  "copywriting": {"id": 50, "content": "今天开箱AJ1..."},
  "audio": {"id": 20, "name": "背景音乐.mp3"},
  "cover": {"id": 30, "file_path": "cover.jpg"},
  "topics": [
    {"id": 1, "name": "球鞋开箱"}
  ],
  "composition_job": {
    "id": 501,
    "status": "completed",
    "output_video_path": "/data/videos/final_1001.mp4",
    "duration": 30
  },
  "upload_logs": [
    {"status": "success", "message": "上传成功", "created_at": "..."}
  ],
  "timeline": [
    {"event": "created", "time": "2026-04-08T14:30:00"},
    {"event": "composition_started", "time": "2026-04-08T14:35:00"},
    {"event": "composition_completed", "time": "2026-04-08T14:40:00"},
    {"event": "upload_started", "time": "2026-04-08T15:00:00"},
    {"event": "uploaded", "time": "2026-04-08T15:05:00"}
  ]
}
```

---

## 三、操作域 2: 视频合成

### 2.1 提交合成

**业务场景**：将草稿任务提交给扣子工作流合成视频

**API**：`POST /api/tasks/{id}/submit-composition`

**前置条件**：
- Task.status = draft
- 必需素材已关联（根据模板要求）

**执行流程**：
```
1. 验证素材完整性
2. 创建 CompositionJob 记录（status = pending）
3. 调用扣子 API 提交工作流
   - 上传素材文件或提供下载链接
   - 传递合成参数
4. 保存 external_job_id
5. 更新 Task.status = composing
6. 更新 Task.composition_job_id
```

**请求示例**（调用扣子）：
```json
POST https://api.coze.com/v1/workflows/{workflow_id}/run
{
  "inputs": {
    "video_urls": [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4"
    ],
    "audio_url": "https://example.com/audio.mp3",
    "subtitle_text": "今天开箱AJ1...",
    "target_duration": 30,
    "transition_effect": "fade"
  },
  "callback_url": "https://dewugojin.com/api/composition-jobs/callback"
}
```

**响应**：
```json
{
  "success": true,
  "composition_job_id": 501,
  "external_job_id": "coze_job_abc123",
  "status": "pending"
}
```

---

### 2.2 批量提交合成

**API**：`POST /api/tasks/batch-submit-composition`

**输入**：
```json
{
  "task_ids": [1001, 1002, 1003]
}
```

**响应**：
```json
{
  "success_count": 2,
  "failed_count": 1,
  "results": [
    {"task_id": 1001, "success": true, "composition_job_id": 501},
    {"task_id": 1002, "success": true, "composition_job_id": 502},
    {"task_id": 1003, "success": false, "error": "素材不完整"}
  ]
}
```

---

### 2.3 查询合成进度

**API**：`GET /api/composition-jobs/{id}/progress`

**响应**：
```json
{
  "id": 501,
  "task_id": 1001,
  "status": "processing",
  "progress": 65,
  "estimated_remaining_seconds": 120,
  "current_step": "添加字幕",
  "logs": [
    {"time": "14:35:00", "message": "开始合成"},
    {"time": "14:36:00", "message": "视频拼接完成"},
    {"time": "14:37:00", "message": "添加背景音乐"},
    {"time": "14:38:00", "message": "添加字幕中..."}
  ]
}
```

---

### 2.4 合成回调（Webhook）

**业务场景**：扣子完成合成后回调通知

**API**：`POST /api/composition-jobs/callback`

**请求**（扣子发送）：
```json
{
  "job_id": "coze_job_abc123",
  "status": "completed",
  "output_video_url": "https://coze-cdn.com/output/video_abc123.mp4",
  "duration": 30,
  "file_size": 15728640,
  "error_message": null
}
```

**执行流程**：
```
1. 根据 external_job_id 查找 CompositionJob
2. 下载成品视频到本地
   - 保存到 /data/videos/final_{task_id}.mp4
3. 更新 CompositionJob:
   - status = completed
   - output_video_path = 本地路径
   - output_video_duration = 30
   - output_video_size = 15728640
   - completed_at = now()
4. 更新 Task:
   - status = ready
   - final_video_path = 本地路径
   - final_video_duration = 30
   - final_video_size = 15728640
5. 触发通知（可选）
```

**响应**：
```json
{
  "success": true,
  "message": "回调处理成功"
}
```

---

### 2.5 取消合成

**API**：`POST /api/tasks/{id}/cancel-composition`

**执行流程**：
```
1. 调用扣子 API 取消任务
2. 更新 CompositionJob.status = cancelled
3. 更新 Task.status = draft
```

---

### 2.6 重试合成

**API**：`POST /api/tasks/{id}/retry-composition`

**前置条件**：
- CompositionJob.status = failed
- Task.retry_count < max_retry（默认 3）

**执行流程**：
```
1. 创建新的 CompositionJob 记录
2. 重新提交到扣子
3. 更新 Task.composition_job_id = 新 ID
4. 更新 Task.retry_count += 1
```

---

## 四、操作域 3: 上传调度

### 3.1 手动触发上传

**API**：`POST /api/tasks/{id}/upload`

**前置条件**：
- Task.status = ready
- Account 状态正常（session 有效）

**执行流程**：
```
1. 验证账号状态
2. 更新 Task.status = uploading
3. 调用 Patchright 自动化上传
   - 打开得物创作者中心
   - 上传视频文件
   - 填写文案
   - 添加话题标签
   - 点击发布
4. 记录 PublishLog
5. 更新 Task:
   - status = uploaded/failed
   - uploaded_at = now()
   - dewu_video_id = 平台返回的 ID
   - error_msg = 错误信息（如果失败）
```

---

### 3.2 启动自动调度

**API**：`POST /api/upload/start`

**调度逻辑**：
```python
while scheduler_running:
    # 1. 检查时间窗口
    current_hour = datetime.now().hour
    if not (config.start_hour <= current_hour < config.end_hour):
        await asyncio.sleep(60)
        continue
    
    # 2. 获取下一个任务
    task = await get_next_ready_task(
        order_by=[Task.priority.desc(), Task.scheduled_time]
    )
    
    if not task:
        await asyncio.sleep(10)
        continue
    
    # 3. 检查账号限额
    today_count = await get_account_upload_count_today(task.account_id)
    if today_count >= config.max_per_account_per_day:
        await mark_task_paused(task.id, "账号今日限额已满")
        continue
    
    # 4. 检查账号会话
    is_valid = await check_account_session(task.account_id)
    if not is_valid:
        await mark_task_failed(task.id, "账号会话已过期")
        continue
    
    # 5. 执行上传
    await upload_task(task)
    
    # 6. 等待间隔
    await asyncio.sleep(config.interval_minutes * 60)
```

---

### 3.3 暂停/停止调度

**API**：
- `POST /api/upload/pause` - 暂停（可恢复）
- `POST /api/upload/stop` - 停止（清空队列）

---

### 3.4 调度配置

**API**：
- `GET /api/upload/config`
- `PUT /api/upload/config`

**配置项**：
```json
{
  "start_hour": 9,
  "end_hour": 22,
  "interval_minutes": 30,
  "max_per_account_per_day": 5,
  "max_concurrent_uploads": 1,
  "auto_retry_on_failure": true,
  "max_retry_count": 3
}
```

---

### 3.5 上传重试

**API**：`POST /api/tasks/{id}/retry-upload`

**前置条件**：
- Task.status = failed
- Task.retry_count < max_retry

**执行流程**：
```
1. 更新 Task.status = ready
2. 清空 error_msg
3. 更新 retry_count += 1
4. 重新进入上传队列
```

---

## 五、操作域 4: 模板管理

### 4.1 创建合成模板

**API**：`POST /api/workflow-templates`

**输入**：
```json
{
  "name": "highlight_15s",
  "display_name": "高光 15 秒",
  "description": "自动提取视频高光片段，合成 15 秒短视频",
  "workflow_type": "coze",
  "workflow_id": "coze_workflow_456",
  "params_schema": {
    "type": "object",
    "properties": {
      "target_duration": {"type": "integer", "default": 15},
      "highlight_threshold": {"type": "number", "default": 0.7}
    }
  },
  "min_video_count": 1,
  "max_video_count": 3,
  "required_audio": false,
  "required_copywriting": true
}
```

---

### 4.2 查询模板列表

**API**：`GET /api/workflow-templates`

**响应**：
```json
{
  "items": [
    {
      "id": 1,
      "name": "standard_30s",
      "display_name": "标准 30 秒",
      "is_active": true
    },
    {
      "id": 2,
      "name": "highlight_15s",
      "display_name": "高光 15 秒",
      "is_active": true
    }
  ]
}
```

---

### 4.3 从模板创建任务

**API**：`POST /api/tasks/from-template`

**输入**：
```json
{
  "template_id": 1,
  "account_ids": [1, 2],
  "video_ids": [101, 102],
  "copywriting_id": 50,
  "params": {
    "target_duration": 25
  }
}
```

---

## 六、操作域 5: 监控统计

### 5.1 任务统计

**API**：`GET /api/tasks/stats`

**响应**：
```json
{
  "total": 1000,
  "by_status": {
    "draft": 50,
    "composing": 10,
    "ready": 30,
    "uploading": 5,
    "uploaded": 850,
    "failed": 50,
    "cancelled": 5
  },
  "today": {
    "created": 20,
    "composed": 15,
    "uploaded": 12
  },
  "success_rate": 0.85,
  "avg_composition_duration": 300,
  "avg_upload_duration": 180
}
```

---

### 5.2 合成队列监控

**API**：`GET /api/composition-jobs/queue-status`

**响应**：
```json
{
  "pending_count": 5,
  "processing_count": 3,
  "avg_wait_time_seconds": 120,
  "queue": [
    {"task_id": 1001, "wait_time": 60},
    {"task_id": 1002, "wait_time": 120}
  ]
}
```

---

### 5.3 上传队列监控

**API**：`GET /api/upload/queue-status`

**响应**：
```json
{
  "ready_count": 10,
  "uploading_count": 1,
  "accounts_status": [
    {
      "account_id": 1,
      "account_name": "账号A",
      "today_uploaded": 3,
      "daily_limit": 5,
      "remaining": 2
    }
  ]
}
```

---

### 5.4 执行日志查询

**API**：`GET /api/tasks/{id}/logs`

**响应**：
```json
{
  "composition_logs": [
    {"time": "14:35:00", "level": "INFO", "message": "开始合成"},
    {"time": "14:40:00", "level": "INFO", "message": "合成完成"}
  ],
  "upload_logs": [
    {"time": "15:00:00", "level": "INFO", "message": "开始上传"},
    {"time": "15:05:00", "level": "INFO", "message": "上传成功"}
  ]
}
```

---

## 七、功能优先级总结

### P0（必须实现）

| 功能 | API | 说明 |
|------|-----|------|
| 创建任务 | POST /api/tasks | 基础功能 |
| 查询任务 | GET /api/tasks | 基础功能 |
| 任务详情 | GET /api/tasks/{id}/detail | 查看完整信息 |
| 提交合成 | POST /api/tasks/{id}/submit-composition | 核心流程 |
| 合成回调 | POST /api/composition-jobs/callback | 核心流程 |
| 手动上传 | POST /api/tasks/{id}/upload | 核心流程 |
| 启动调度 | POST /api/upload/start | 核心流程 |
| 失败重试 | POST /api/tasks/{id}/retry-* | 容错机制 |

### P1（重要优化）

| 功能 | API | 说明 |
|------|-----|------|
| 批量组装 | POST /api/tasks/batch-assemble | 效率提升 |
| 批量提交合成 | POST /api/tasks/batch-submit-composition | 效率提升 |
| 模板管理 | /api/workflow-templates | 可复用性 |
| 任务统计 | GET /api/tasks/stats | 数据分析 |
| 队列监控 | GET /api/*/queue-status | 运营监控 |

### P2（体验增强）

| 功能 | 说明 |
|------|------|
| 智能调度 | 根据账号活跃度动态调整 |
| 数据分析 | 素材使用频率、失败原因分类 |
| 导入导出 | Excel 批量操作 |

---

## 附录

### 参考文档
- [任务管理业务流程分析](./task-management-analysis.md)
- [任务管理 ER 设计](./task-management-er-design.md)
