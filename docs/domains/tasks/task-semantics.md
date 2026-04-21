# Task 语义基线（当前真实版本）

> Status: Current  
> Last updated: 2026-04-20

本文定义当前仓库中 `Task` 的 authoritative semantics，重点收口：

- direct publish
- `coze`
- `local_ffmpeg V1`

---

## 1. authoritative create contract

当前 authoritative create contract 是：

- `POST /api/tasks/`
- 输入模型：`TaskCreateRequest`

输入应按资源集合理解，而不是旧版单 FK：

- `video_ids`
- `copywriting_ids`
- `cover_ids`
- `audio_ids`
- `topic_ids`
- `account_id`
- `profile_id`

---

## 2. direct publish 语义（`composition_mode = none`）

当前 direct publish 是保守语义：

### 2.1 允许

- 1 个最终视频
- 0/1 个文案
- 0/1 个封面
- 多个话题

### 2.2 不允许

- 0 个视频
- 多个视频
- 多个文案
- 多个封面
- 独立音频输入

也就是说，direct publish 并不会默默“取第一个视频/文案/封面”来降级执行。

---

## 3. `local_ffmpeg V1` 语义

### 3.1 输入约束

当前 `local_ffmpeg V1` 只支持：

- **1 个视频**
- **0/1 个音频**
- **0/1 个文案**
- **0/1 个封面**
- **多个话题**

### 3.2 输入解释

- 视频：本地合成主输入
- 音频：可选背景音频输入
- 文案 / 封面 / 话题：发布层元数据，不进入 V1 视频渲染语义

### 3.3 明确边界

当前 `local_ffmpeg V1` **不是** broader composition inputs surface。  
它不支持：

- multi-video montage
- multi-audio mixing beyond `0/1`
- subtitle burn-in
- cover embed into video

### 3.4 执行收口

当 `composition_mode = local_ffmpeg` 时：

1. 创建或提交任务时先做 V1 输入校验
2. `submit_composition()` 创建 `CompositionJob`
3. 任务进入 `composing`
4. 本地同步执行 FFmpeg
5. 成功时写回 `final_video_path`
6. 发布链路优先消费 `final_video_path`

---

## 4. `coze` 语义

当前 `coze` 路径仍是独立的 composition path：

- 依赖 `coze_workflow_id`
- 使用远端工作流
- 通过 `CompositionPoller` 轮询收口

`coze` 与 `local_ffmpeg` 都属于 “需要合成” 的任务模式，但它们**不是同一条实现链**：

| 模式 | 执行方式 | 收口方式 |
| --- | --- | --- |
| `coze` | 远端工作流 | `CompositionPoller` |
| `local_ffmpeg` | 本地同步 FFmpeg | `submit_composition()` 内直接写回 |

---

## 5. publish-time 语义

发布时的优先级：

1. 若存在 `final_video_path`，优先发布该最终视频
2. 若不存在 `final_video_path`，则按 direct publish 规则读取单视频输入

因此：

- `local_ffmpeg` 的职责是把任务收口成可发布的最终视频
- 发布服务不负责替 `local_ffmpeg` 做二次拼装判断

---

## 6. compatibility 字段与历史负担

以下字段可以继续保留兼容观察价值，但不应重新定义当前 Task 语义：

- `tasks.video_id`
- `tasks.copywriting_id`
- `tasks.audio_id`
- `tasks.cover_id`
- `tasks.source_video_ids`

新代码、新测试、新页面都不应再把这些字段当成 authoritative truth。

---

## 7. 设计结论

### 7.1 当前真实能力

- direct publish：严格、保守、可预测
- `coze`：远端合成链
- `local_ffmpeg V1`：最小可运行的本地合成链

### 7.2 当前不应宣称的能力

以下说法都不准确：

- “`local_ffmpeg` 允许 broader composition inputs”
- “`local_ffmpeg` 已支持复杂多素材拼接”
- “文案/封面天然参与 FFmpeg 合成”
- “`local_ffmpeg` 与 `coze` 共用同一套 poller 语义”

---

## 8. 参考

- `docs/task-management-domain-model.md`
- `docs/local-ffmpeg-composition.md`
- `backend/services/task_execution_semantics.py`
- `backend/services/composition_service.py`
