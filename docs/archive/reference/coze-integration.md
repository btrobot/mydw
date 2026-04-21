# 扣子（Coze）接入方式

> 版本: 1.0.0 | 创建日期: 2026-04-08
> 作者: Tech Lead
> 状态: Draft

---

## 一、概述

本项目通过扣子（Coze）平台的工作流能力实现视频创作自动化。扣子本质是一个 AI 工作流编排平台，可以将大模型、文生图、图生视频、语音合成等 AI 能力像积木一样组合，实现从原始素材到成品视频的全自动生产。

### 在本项目中的定位

```
原始素材（视频片段/图片/文案）
  ↓ 上传到扣子
扣子工作流（AI 编排，平台侧配置）
  ↓ 异步执行，轮询获取结果
成品视频
  ↓ 下载到本地
Patchright 自动化上传到得物
```

我们的系统不需要关心扣子内部的工作流编排细节，只需要：

1. 把素材和参数传进去
2. 等待执行完成
3. 拿到成品视频

---

## 二、扣子视频创作能力

### 2.1 主流视频生成路径

| 技术路径 | 核心步骤 | 适用场景 |
|---------|---------|---------|
| 文生视频 | 文字提示词 → AI 模型直接生成视频 | 创意广告、概念短片、风格化视频 |
| 图生视频 | 图片 → AI 模型生成动态视频 | 产品展示、静态图动画化 |
| 链接转视频 | 短视频链接 → 提取内容 → AI 生成新视频 | 二次创作、爆款复刻 |
| 数字人视频 | 文案 → 数字人播报视频 | 知识科普、新闻播报 |

### 2.2 典型工作流节点

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  大模型   │───►│ 文生图/  │───►│ 图生视频/ │───►│ 音频合成 │
│ 生成脚本  │    │ 文生视频  │    │ 视频拼接  │    │ 背景音乐 │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     │
                                                     ▼
                                               ┌──────────┐
                                               │ 最终合成  │
                                               │ 输出视频  │
                                               └──────────┘
```

核心节点说明：

- **大模型节点** — 工作流的大脑，负责理解创意、生成脚本和提示词
- **插件节点** — 执行具体任务（文生图、图生视频、语音合成等），扣子提供官方和第三方插件
- **循环节点** — 实现批量生产（如将长剧本拆解为多个分镜，逐个生成视频）
- **代码节点** — 自定义逻辑处理（数据转换、格式化等）

---

## 三、技术集成方案

### 3.1 SDK 选择

使用扣子官方 Python SDK `cozepy`。

```bash
pip install cozepy
```

SDK 特性：
- 完整覆盖所有扣子开放 API
- 同步 / 异步双接口
- 原生流式支持（Stream / AsyncStream）
- 分页迭代器

### 3.2 认证方式

使用 Personal Access Token（PAT），从扣子平台获取。

获取地址：`https://www.coze.cn/open/oauth/pats`

```python
from cozepy import AsyncCoze, AsyncTokenAuth, COZE_CN_BASE_URL

coze = AsyncCoze(
    auth=AsyncTokenAuth(token="your_pat_token"),
    base_url=COZE_CN_BASE_URL  # 国内版
)
```

环境变量配置（`.env`）：

```env
COZE_API_TOKEN=pat_xxxxxxxxxxxxxxxx
COZE_API_BASE=https://api.coze.cn
COZE_WORKFLOW_ID=your_workflow_id
```

### 3.3 工作流调用模式

SDK 提供三种调用模式：

| 模式 | 方法 | 返回方式 | 适用场景 |
|-----|------|---------|---------|
| 同步 | `workflows.runs.create()` | 阻塞等待，直接返回结果 | 短任务（< 30s） |
| 流式 | `workflows.runs.stream()` | SSE 事件流，实时推送 | 需要进度反馈的中等任务 |
| 异步 | `workflows.runs.create(is_async=True)` | 立即返回 execute_id，轮询获取结果 | 长任务（视频合成） |

**本项目使用异步模式**，因为视频合成通常耗时数分钟。

### 3.4 文件上传

素材文件需要先上传到扣子，获取 file_id 后传给工作流。

```python
file = await coze.files.upload(file="/path/to/video.mp4")
file_id = file.id  # 传给工作流作为输入参数
```

---

## 四、核心 API 调用流程

### 4.1 提交合成任务

```python
from cozepy import AsyncCoze, AsyncTokenAuth, COZE_CN_BASE_URL

coze = AsyncCoze(
    auth=AsyncTokenAuth(token=COZE_API_TOKEN),
    base_url=COZE_CN_BASE_URL
)

# 第 1 步：上传素材文件
file = await coze.files.upload(file="/path/to/source_video.mp4")

# 第 2 步：提交异步工作流
workflow_run = await coze.workflows.runs.create(
    workflow_id="your_workflow_id",
    is_async=True,
    parameters={
        "video_file_id": file.id,
        "subtitle_text": "今天开箱 AJ1 黑红配色...",
        "target_duration": 30,
        "style": "潮流种草"
    }
)

# 第 3 步：保存 execute_id 用于后续轮询
execute_id = workflow_run.execute_id
```

### 4.2 轮询查询状态

```python
from cozepy import WorkflowExecuteStatus

run_history = await coze.workflows.runs.run_histories.retrieve(
    workflow_id="your_workflow_id",
    execute_id=execute_id
)

match run_history.execute_status:
    case WorkflowExecuteStatus.RUNNING:
        # 仍在执行，稍后重试
        pass
    case WorkflowExecuteStatus.FAIL:
        # 失败，记录错误信息
        error = run_history.error_message
    case _:
        # 成功，解析输出
        output = run_history.output  # JSON 字符串，包含成品视频 URL
```

### 4.3 下载成品视频

工作流执行成功后，从 `output` 中解析成品视频的下载 URL，下载到本地。

```python
import json
import httpx

output = json.loads(run_history.output)
video_url = output["video_url"]  # 具体字段名取决于工作流输出配置

async with httpx.AsyncClient() as client:
    response = await client.get(video_url)
    local_path = f"/data/videos/final_{task_id}.mp4"
    with open(local_path, "wb") as f:
        f.write(response.content)
```

### 4.4 流式调用（可选）

如果需要实时进度反馈，可以使用流式模式：

```python
from cozepy import Stream, WorkflowEvent, WorkflowEventType

def handle_workflow_stream(stream: Stream[WorkflowEvent]):
    for event in stream:
        if event.event == WorkflowEventType.MESSAGE:
            print("进度消息:", event.message)
        elif event.event == WorkflowEventType.ERROR:
            print("错误:", event.error)
        elif event.event == WorkflowEventType.INTERRUPT:
            # 工作流中断，需要人工干预
            handle_workflow_stream(
                coze.workflows.runs.resume(
                    workflow_id=workflow_id,
                    event_id=event.interrupt.interrupt_data.event_id,
                    resume_data="继续",
                    interrupt_type=event.interrupt.interrupt_data.type,
                )
            )

handle_workflow_stream(
    coze.workflows.runs.stream(
        workflow_id=workflow_id,
        parameters=parameters,
    )
)
```

---

## 五、在本项目中的集成架构

### 5.1 新增组件

```
backend/
├── core/
│   └── coze_client.py          # 扣子 API 客户端封装
├── services/
│   └── composition_service.py  # 合成任务管理（提交、轮询、下载）
├── models/
│   └── (更新) __init__.py      # 新增 CompositionJob 模型
└── api/
    └── (更新) task.py          # 新增合成相关端点
```

### 5.2 CozeClient 封装

```python
# backend/core/coze_client.py（设计草案）

class CozeClient:
    """扣子 API 客户端封装"""

    def __init__(self, api_token: str, base_url: str, workflow_id: str):
        self.coze = AsyncCoze(
            auth=AsyncTokenAuth(token=api_token),
            base_url=base_url
        )
        self.workflow_id = workflow_id

    async def upload_file(self, file_path: str) -> str:
        """上传文件，返回 file_id"""
        file = await self.coze.files.upload(file=file_path)
        return file.id

    async def submit_composition(self, parameters: dict) -> str:
        """提交异步合成任务，返回 execute_id"""
        result = await self.coze.workflows.runs.create(
            workflow_id=self.workflow_id,
            is_async=True,
            parameters=parameters
        )
        return result.execute_id

    async def check_status(self, execute_id: str) -> tuple[str, dict | None]:
        """查询任务状态，返回 (status, output)"""
        history = await self.coze.workflows.runs.run_histories.retrieve(
            workflow_id=self.workflow_id,
            execute_id=execute_id
        )
        status = history.execute_status
        output = json.loads(history.output) if history.output else None
        return status, output
```

### 5.3 后台轮询服务

```python
# backend/services/composition_service.py（设计草案）

class CompositionPoller:
    """后台轮询扣子合成任务状态"""

    def __init__(self, coze_client: CozeClient, poll_interval: int = 10):
        self.coze_client = coze_client
        self.poll_interval = poll_interval  # 秒
        self._running = False

    async def start(self):
        """启动轮询循环"""
        self._running = True
        while self._running:
            await self._poll_pending_jobs()
            await asyncio.sleep(self.poll_interval)

    async def _poll_pending_jobs(self):
        """轮询所有 pending/processing 状态的合成任务"""
        jobs = await get_active_composition_jobs()  # 从 DB 查询
        for job in jobs:
            status, output = await self.coze_client.check_status(job.external_job_id)
            if status == WorkflowExecuteStatus.SUCCESS:
                await self._handle_success(job, output)
            elif status == WorkflowExecuteStatus.FAIL:
                await self._handle_failure(job)

    async def _handle_success(self, job, output):
        """合成成功：下载视频 → 更新状态"""
        video_path = await download_video(output["video_url"], job.task_id)
        # 更新 CompositionJob
        job.status = "completed"
        job.output_video_path = video_path
        # 更新 Task
        task.status = "ready"
        task.final_video_path = video_path

    async def _handle_failure(self, job):
        """合成失败：更新状态"""
        job.status = "failed"
        task.status = "failed"
```

### 5.4 完整数据流

```
用户操作                    系统内部                         扣子平台
   │
   ├─ 创建任务 ──────────► Task(status=draft)
   │                        │
   ├─ 提交合成 ──────────► coze.files.upload() ──────────► 接收素材文件
   │                        │
   │                       coze.workflows.runs.create() ──► 启动工作流
   │                        │
   │                       CompositionJob(status=pending)
   │                       Task(status=composing)
   │                        │
   │                       ┌─ CompositionPoller ─┐
   │                       │  每 10s 轮询一次     │
   │                       │  run_histories      │◄────────── 返回执行状态
   │                       │  .retrieve()        │
   │                       └─────────────────────┘
   │                        │
   │                       合成完成 → 下载视频
   │                       Task(status=ready)
   │                        │
   │                       ┌─ UploadScheduler ───┐
   │                       │  调度上传            │
   │                       │  Patchright 自动化   │──────────► 得物平台
   │                       └─────────────────────┘
   │                        │
   └─ 查看结果 ◄──────────  Task(status=uploaded)
```

---

## 六、配置项

### 6.1 环境变量

| 变量名 | 说明 | 示例值 |
|-------|------|-------|
| `COZE_API_TOKEN` | 扣子 PAT 令牌 | `pat_xxxxxxxxxxxx` |
| `COZE_API_BASE` | API 基础地址 | `https://api.coze.cn` |
| `COZE_WORKFLOW_ID` | 默认工作流 ID | `7380000000000000000` |
| `COZE_POLL_INTERVAL` | 轮询间隔（秒） | `10` |
| `COZE_MAX_RETRY` | 最大重试次数 | `3` |
| `COZE_UPLOAD_TIMEOUT` | 文件上传超时（秒） | `300` |

### 6.2 pydantic-settings 配置

```python
# backend/core/config.py 新增字段

class Settings(BaseSettings):
    # ... 现有配置 ...

    # 扣子集成
    COZE_API_TOKEN: str = ""
    COZE_API_BASE: str = "https://api.coze.cn"
    COZE_WORKFLOW_ID: str = ""
    COZE_POLL_INTERVAL: int = 10
    COZE_MAX_RETRY: int = 3
    COZE_UPLOAD_TIMEOUT: int = 300
```

---

## 七、错误处理

### 7.1 错误分类

| 错误类型 | 原因 | 处理策略 |
|---------|------|---------|
| 认证失败 | Token 过期或无效 | 日志告警，暂停所有合成任务 |
| 文件上传失败 | 网络问题或文件过大 | 重试 3 次，失败后标记任务 failed |
| 工作流执行失败 | 扣子内部错误或参数错误 | 记录 error_message，支持手动重试 |
| 轮询超时 | 工作流执行时间过长 | 设置最大等待时间（如 30 分钟），超时标记 failed |
| 视频下载失败 | CDN 链接过期或网络问题 | 重试下载，失败后保留 URL 供手动下载 |

### 7.2 重试策略

```python
# 指数退避重试
retry_delays = [10, 30, 60]  # 第 1/2/3 次重试的等待秒数

async def retry_composition(task_id: int):
    task = await get_task(task_id)
    if task.retry_count >= COZE_MAX_RETRY:
        raise MaxRetryExceeded(f"任务 {task_id} 已达最大重试次数")
    task.retry_count += 1
    task.status = "draft"  # 回到草稿状态，允许重新提交
```

---

## 八、限制与注意事项

| 项目 | 说明 |
|-----|------|
| 速率限制 | 扣子 API 有调用频率限制，需要控制并发提交数量 |
| 文件大小 | 上传文件有大小限制，大视频文件可能需要分片或压缩 |
| 工作流配置 | 工作流在扣子平台侧配置，参数结构取决于工作流设计 |
| 网络依赖 | 依赖外网访问扣子 API，需要确保服务器网络通畅 |
| Token 安全 | PAT 令牌不能硬编码，必须通过环境变量管理 |
| 输出格式 | 工作流输出的 JSON 结构取决于平台侧配置，需要约定字段名 |

---

## 九、与现有系统的关系

| 现有模块 | 关系 |
|---------|------|
| `backend/core/config.py` | 新增 COZE_* 配置项 |
| `backend/models/__init__.py` | 新增 CompositionJob 模型 |
| `backend/services/scheduler.py` | 上传调度器从 `ready` 状态取任务（原来从 `pending`） |
| `backend/services/ai_clip_service.py` | 保留作为本地 FFmpeg 合成备选方案 |
| `frontend/src/pages/Task.tsx` | 新增合成状态展示、提交合成操作 |

---

## 附录

### 参考资料

- [cozepy SDK (GitHub)](https://github.com/coze-dev/coze-py) — 官方 Python SDK
- [扣子开放平台文档](https://www.coze.cn/docs/developer_guides/coze_api_overview) — API 概览
- [扣子 PAT 管理](https://www.coze.cn/open/oauth/pats) — 获取访问令牌

### 相关项目文档

- [任务管理业务流程分析](./archive/analysis/task-management-analysis.md)
- [任务管理 ER 设计](./archive/analysis/task-management-er-design.md)
- [任务管理操作清单](./archive/analysis/task-management-operations.md)
- [系统架构](./archive/reference/system-architecture.md)
