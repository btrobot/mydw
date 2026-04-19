# 任务管理领域模型（当前真实版本）

> Status: Current  
> Last updated: 2026-04-20  
> Scope: Task / PublishProfile / CompositionJob / 发布执行语义

本文只描述**当前仓库已经实现并可验证**的任务域模型。  
历史方案、未落地设想、旧版 Coze/FFmpeg 混合草案，不应再作为当前真相来源。

---

## 1. 当前任务主链

当前任务系统围绕 `Task` 运转，主链分成三种执行路径：

1. **direct publish / `composition_mode = none`**
   - 不需要合成
   - 任务创建后可直接进入可发布语义
2. **Coze composition / `composition_mode = coze`**
   - 走远端工作流
   - 由 `CompositionJob` 跟踪外部执行
   - 通过 `CompositionPoller` 轮询收口
3. **local_ffmpeg composition / `composition_mode = local_ffmpeg`**
   - 走本地 FFmpeg V1
   - 由 `CompositionJob` 记录执行结果
   - **不走 `CompositionPoller`**
   - 当前实现是**本地同步执行并立即写回结果**

可视化理解：

```text
素材选择 -> Task -> (none | coze | local_ffmpeg) -> ready -> uploading -> uploaded
```

---

## 2. 核心实体

### 2.1 Task

`Task` 是任务域的核心实体，负责承载：

- 资源关联
  - `videos`
  - `copywritings`
  - `covers`
  - `audios`
  - `topics`
- 执行状态
  - `draft`
  - `composing`
  - `ready`
  - `uploading`
  - `uploaded`
  - `failed`
  - `cancelled`
- 执行结果
  - `final_video_path`
  - `final_video_duration`
  - `final_video_size`
  - `error_msg`
  - `failed_at_status`

### 2.2 PublishProfile

`PublishProfile` 定义任务的执行模式与默认策略，当前与 PR-4 直接相关的字段有：

- `composition_mode`
  - `none`
  - `coze`
  - `local_ffmpeg`
- `coze_workflow_id`
- `composition_params`
- `global_topic_ids`

说明：

- `coze_workflow_id` 只对 `coze` 有意义
- `local_ffmpeg` 不允许把 `coze_workflow_id` 当成配置输入
- `composition_params` 在 `local_ffmpeg` 下是 **JSON object**，用于承载 V1 可识别参数

### 2.3 CompositionJob

`CompositionJob` 是合成执行记录，不是新的业务主实体。当前主要用于：

- 记录本次执行属于 `coze` 还是 `local_ffmpeg`
- 跟踪执行状态
- 挂接输出结果
- 记录错误原因

当前字段语义：

- `workflow_type`
  - `coze`
  - `local_ffmpeg`
- `workflow_id`
  - 仅 `coze` 路径需要
- `external_job_id`
  - 仅 `coze` 路径需要
- `output_video_path`
- `output_video_url`
- `error_msg`

---

## 3. authoritative 资源模型

当前任务输入的 authoritative model 是**资源集合模型**，而不是旧时代的单 FK 模型。

真实输入面以这些集合字段为准：

- `video_ids`
- `copywriting_ids`
- `cover_ids`
- `audio_ids`
- `topic_ids`

对应真实关联表：

- `task_videos`
- `task_copywritings`
- `task_covers`
- `task_audios`
- `task_topics`

以下字段仍可能存在于表结构或兼容层，但**不是当前真相来源**：

- `tasks.video_id`
- `tasks.copywriting_id`
- `tasks.audio_id`
- `tasks.cover_id`
- `tasks.source_video_ids`

---

## 4. local_ffmpeg V1 的冻结语义

`local_ffmpeg` 在当前仓库中已经落地为 **V1 最小可运行能力**。

### 4.1 支持什么

- **恰好 1 个视频输入**
- **0/1 个音频输入**
- **0/1 个文案**
- **0/1 个封面**
- **多个话题**

其中：

- 视频、音频参与本地 FFmpeg 处理
- 文案、封面、话题继续作为发布层元数据
- 合成成功后结果写回 `Task.final_video_path`

### 4.2 不支持什么

当前 `local_ffmpeg V1` **不支持**：

- multi-video montage
- multi-audio mixing strategy beyond `0/1`
- subtitle / copywriting burn-in
- cover embed into video
- 基于本地 FFmpeg 的异步 poller 架构

### 4.3 执行方式

当前 `local_ffmpeg` 路径不是远端任务轮询模型，而是：

```text
submit_composition()
  -> 创建 CompositionJob
  -> Task: draft -> composing
  -> 本地同步执行 FFmpeg
  -> 成功: Task -> ready, 写回 final_video_path
  -> 失败: Task -> failed, failed_at_status = composing
```

因此：

- `CompositionPoller` 只负责 `coze`
- `local_ffmpeg` 不应再被描述成 “等待 poller 回收结果” 的架构

---

## 5. 状态机（当前真实语义）

### 5.1 核心状态

```text
draft -> composing -> ready -> uploading -> uploaded
                    \-> failed
```

以及：

- 任意非终态可取消到 `cancelled`
- `failed_at_status` 用于支持失败后的快速重试

### 5.2 三种模式的入口差异

| composition_mode | 创建后起始语义 | 合成链路 |
| --- | --- | --- |
| `none` | 直接按可发布语义校验 | 无合成 |
| `coze` | 进入需要合成的任务语义 | 远端工作流 + poller |
| `local_ffmpeg` | 进入需要合成的任务语义 | 本地同步 FFmpeg V1 |

---

## 6. publish path 的真实规则

发布层读取的是 **publish execution view**：

1. 若 `Task.final_video_path` 存在，优先发布该最终视频
2. 否则 direct publish 只能消费单视频任务
3. 文案、封面允许 `0/1`
4. 话题允许多值
5. direct publish 不支持独立音频输入

这意味着：

- `local_ffmpeg` 合成后的任务会通过 `final_video_path` 与发布链路衔接
- 发布服务不需要理解本地 FFmpeg 内部细节，只消费最终输出

---

## 7. 文档与代码的对应关系

当前主题的 authoritative code references：

- `backend/services/task_execution_semantics.py`
- `backend/services/composition_service.py`
- `backend/services/local_ffmpeg_composition_service.py`
- `backend/tests/test_task_creation_semantics.py`
- `backend/tests/test_local_ffmpeg_contract.py`
- `backend/tests/test_local_ffmpeg_composition.py`

补充说明文档：

- `docs/task-semantics.md`
- `docs/local-ffmpeg-composition.md`

---

## 8. 读者应避免的误解

以下说法在当前仓库中都不再成立：

- “`coze / local_ffmpeg` 共用同一套轮询收口模型”
- “只要开启 `local_ffmpeg`，就天然支持 broader composition inputs”
- “文案、封面会自动被烧录进本地 FFmpeg 输出视频”
- “`source_video_ids` 仍然是任务视频输入的 authoritative source”

如果文档与代码冲突，请以：

1. 当前测试
2. 当前实现
3. 当前文档

这个顺序回溯真相。
