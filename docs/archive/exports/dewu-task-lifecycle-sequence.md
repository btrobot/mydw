# 任务从创建到发布成功的完整时序图

## 1. 文档范围

这份文档描述当前项目里“任务从创建到最终发布成功”的真实执行链路，并区分两种路径：

1. 不需要合成，直接进入待上传
2. 需要合成，先经过 Coze / 合成轮询，再进入待上传

说明基于当前代码，而不是只基于设计文档。

## 2. 关键参与者

- 用户
- 前端页面 `TaskCreate` / `TaskDetail` / `Dashboard`
- 前端 hooks：`useBatchAssemble`、`useSubmitComposition`、`useCompositionStatus`、`useControlPublish`
- 后端 API：`/api/tasks/*`、`/api/publish/*`
- `TaskDistributor`
- `TaskAssembler`
- `TaskService`
- `CompositionService`
- `TaskScheduler`
- `PublishService`
- `BrowserManager`
- `DewuClient`
- SQLite
- Coze 工作流
- 得物创作者平台

## 3. 路径 A：无需合成的任务

适用条件：

- 任务绑定的 `PublishProfile.composition_mode = "none"`
- 或没有显式 profile，但默认 profile 的模式也是 `none`

### 时序图

```mermaid
sequenceDiagram
    autonumber
    actor User as 用户
    participant TC as TaskCreate 页面
    participant TH as useBatchAssemble
    participant TA as /api/tasks/batch-assemble
    participant TD as TaskDistributor
    participant TAsm as TaskAssembler
    participant DB as SQLite
    participant Dash as Dashboard / 发布控制
    participant PH as useControlPublish
    participant PA as /api/publish/control
    participant SCH as TaskScheduler
    participant PS as PublishService
    participant BM as BrowserManager
    participant DC as DewuClient
    participant Dewu as 得物创作者平台

    User->>TC: 选择素材、账号、配置档，点击“创建任务”
    TC->>TH: mutate(batch-assemble)
    TH->>TA: POST /api/tasks/batch-assemble
    TA->>TD: distribute(video_ids, account_ids, ...)
    loop 每个账号生成一个任务
        TD->>TAsm: assemble(...)
        TAsm->>DB: 查询 PublishProfile
        alt composition_mode = none
            TAsm->>DB: 创建 Task(status=ready)
        else 其他模式
            TAsm->>DB: 创建 Task(status=draft)
        end
        TAsm->>DB: 写入 task_videos / task_copywritings / task_covers / task_audios / task_topics
    end
    TA-->>TH: 返回任务列表
    TH-->>TC: 创建成功，跳转任务列表

    User->>Dash: 点击“开始发布”
    Dash->>PH: mutate({action:"start"})
    PH->>PA: POST /api/publish/control
    PA->>SCH: start_publishing()
    loop 调度循环
        SCH->>PS: get_next_task()
        PS->>DB: 读取 schedule_config 与 ready 任务
        DB-->>PS: 返回优先级最高的可发布任务
        PS->>DB: 校验账号状态、读取任务资源
        PS->>BM: get_or_create_context(account_id, storage_state)
        BM-->>PS: 返回浏览器上下文
        PS->>DC: check_login_status()
        DC->>Dewu: 打开 creator.dewu.com
        Dewu-->>DC: 登录态有效
        PS->>DC: upload_video(video, content, topic, cover)
        DC->>Dewu: 上传视频并填写发布表单
        Dewu-->>DC: 发布成功
        PS->>DB: Task.status=uploaded, publish_time=now
        PS->>DB: 写入 PublishLog(status="uploaded")
    end
```

### 当前代码锚点

- 任务创建入口：`backend/api/task.py:298`
- 分发器：`backend/services/task_distributor.py`
- 组装器：`backend/services/task_assembler.py`
- 调度启动：`backend/api/publish.py:97`
- 调度循环：`backend/services/scheduler.py:36`
- 发布执行：`backend/services/publish_service.py`

## 4. 路径 B：需要合成的任务

适用条件：

- `PublishProfile.composition_mode = "coze"` 或其他非 `none` 模式

### 时序图

```mermaid
sequenceDiagram
    autonumber
    actor User as 用户
    participant TC as TaskCreate 页面
    participant TH as useBatchAssemble
    participant TA as /api/tasks/batch-assemble
    participant TAsm as TaskAssembler
    participant DB as SQLite
    participant TDtl as TaskDetail 页面
    participant SH as useSubmitComposition
    participant TSA as /api/tasks/{id}/submit-composition
    participant CS as CompositionService
    participant Coze as CozeClient / Coze 工作流
    participant Poll as CompositionPoller
    participant Dash as Dashboard / 发布控制
    participant SCH as TaskScheduler
    participant PS as PublishService
    participant Dewu as 得物创作者平台

    User->>TC: 创建任务
    TC->>TH: POST /api/tasks/batch-assemble
    TH->>TA: 批量组装
    TAsm->>DB: 根据 profile 创建 Task(status=draft)
    TAsm->>DB: 写入任务与素材关联
    TA-->>TC: 返回 draft 任务

    User->>TDtl: 打开任务详情
    User->>TDtl: 点击“提交合成”
    TDtl->>SH: mutate(taskId)
    SH->>TSA: POST /api/tasks/{id}/submit-composition
    TSA->>CS: submit_composition(task_id)
    CS->>DB: 校验 Task.status == draft
    CS->>DB: 解析 PublishProfile
    alt composition_mode = coze
        CS->>Coze: upload_file(video.file_path)
        Coze-->>CS: file_id
        CS->>Coze: submit_composition(workflow_id, params)
        Coze-->>CS: external_job_id
    end
    CS->>DB: 创建 CompositionJob(status=pending)
    CS->>DB: Task.status = composing, composition_job_id = job.id
    TSA-->>TDtl: 返回 CompositionJob

    loop 轮询合成状态
        Poll->>DB: 查找 status=composing 的任务
        Poll->>Coze: check_status(workflow_id, external_job_id)
        alt 合成成功
            Coze-->>Poll: success + output.video_url
            Poll->>CS: handle_success(job_id, output)
            CS->>Coze: 下载成品视频到本地
            CS->>DB: CompositionJob.status=completed
            CS->>DB: Task.status=ready, final_video_path=...
        else 合成失败
            Coze-->>Poll: fail/error
            Poll->>CS: handle_failure(job_id, error)
            CS->>DB: CompositionJob.status=failed
            CS->>DB: Task.status=failed, failed_at_status=composing
        end
    end

    Note over Dash,SCH: 任务转为 ready 后，后续流程与“无需合成”路径一致
    Dash->>SCH: start_publishing()
    SCH->>PS: 选中 ready 任务并发布
    PS->>Dewu: 自动上传并发布
    PS->>DB: Task.status=uploaded + PublishLog
```

### 当前代码锚点

- 提交合成端点：`backend/api/task.py:318`
- 合成服务：`backend/services/composition_service.py`
- 合成轮询器：`backend/services/scheduler.py:135`
- 任务详情页的合成动作：`frontend/src/pages/task/TaskDetail.tsx:112`

## 5. 任务状态变化总表

| 阶段 | 触发入口 | 任务状态变化 | 主要落库内容 |
|------|----------|--------------|--------------|
| 创建任务 | `POST /api/tasks/batch-assemble` | `ready` 或 `draft` | `tasks` + 任务素材关联表 |
| 提交合成 | `POST /api/tasks/{id}/submit-composition` | `draft -> composing` | `composition_jobs` + `tasks.composition_job_id` |
| 合成成功 | 轮询器回调 | `composing -> ready` | `final_video_path`、作业完成状态 |
| 合成失败 | 轮询器回调 | `composing -> failed` | `error_msg`、`failed_at_status` |
| 开始上传 | 调度器选中任务 | `ready -> uploading` | 任务状态更新 |
| 发布成功 | `PublishService` | `uploading -> uploaded` | `publish_time`、`PublishLog` |
| 发布失败 | `PublishService` | `uploading -> failed` | `error_msg`、`failed_at_status`、`PublishLog` |

## 6. 前端实际参与点

### 6.1 创建阶段

- 页面：`frontend/src/pages/task/TaskCreate.tsx`
- 关键 hook：`useBatchAssemble`
- 关键组件：
  - `ProductQuickImport`
  - `MaterialSelectModal`

### 6.2 合成阶段

- 页面：`frontend/src/pages/task/TaskDetail.tsx`
- 关键 hooks：
  - `useSubmitComposition`
  - `useCompositionStatus`
  - `useCancelComposition`

### 6.3 调度与发布阶段

- 页面：`frontend/src/pages/Dashboard.tsx`
- 关键 hooks：
  - `useControlPublish`
  - `usePublishStatus`

## 7. 当前实现和“理想流程”之间的差异

这里是阅读代码时最容易误解的地方。

### 7.1 “立即发布”端点目前不是真正立即发布

`POST /api/tasks/{id}/publish` 当前只做了：

- 校验任务存在
- 校验任务不在 `uploading`
- 打一条“已添加到发布队列”的日志
- 直接返回成功

它没有直接调用 `PublishService.publish_task()`，也没有强制让调度器立即消费这个任务。

见：

- `backend/api/task.py:240-255`

### 7.2 发布控制当前只启动任务调度器

发布控制入口 `POST /api/publish/control` 调用的是：

- `scheduler.start_publishing()`

这会启动 `TaskScheduler`，但不会启动 `CompositionPoller`。

见：

- `backend/api/publish.py:105-113`
- `backend/services/scheduler.py:26-34`
- `backend/services/scheduler.py:283-321`

### 7.3 轮询器存在统一管理器，但当前发布入口没走它

代码里已经有 `SchedulerManager.start_all()`，它会同时启动：

- `TaskScheduler`
- `CompositionPoller`

但当前发布 API 还没有调用它。

## 8. 建议如何理解这条链路

如果只用一句话总结当前真实流程：

1. 创建任务时，任务先落到 `ready` 或 `draft`
2. 需要合成的任务先走 `CompositionJob`
3. 真正的上传动作由后台调度器循环触发
4. 发布成功后状态和日志再回写数据库

换句话说，系统的真正执行入口不是“任务详情页按钮本身”，而是：

- 合成入口：`/api/tasks/{id}/submit-composition`
- 发布入口：`/api/publish/control`

