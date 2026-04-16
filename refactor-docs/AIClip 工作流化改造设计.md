# AIClip 工作流化改造设计

> 版本：Draft v0.1  
> 更新时间：2026-04-16  
> 依据文档：
> - `refactor-docs/短视频作品自动生成与发布系统-新版PRD-基于MVP现状.md`
> - `refactor-docs/作品实体与状态机详细设计.md`
> - `refactor-docs/人工检查流与版本管理设计.md`
> - `refactor-docs/作品工作台页面原型与交互流转.md`
> - `refactor-docs/发布池与调度器重构说明.md`
> - 当前 `frontend/src/pages/AIClip.tsx`
> - 当前 `frontend/src/hooks/useAIClip.ts`
> - 当前 `backend/api/ai.py`
> - 当前 `backend/services/ai_clip_service.py`

---

## 1. 文档目标

本文档用于把当前“AIClip 工具页”升级为可接入主业务流程的工作流能力，重点回答：

1. 当前 AIClip 为什么只能算工具页，不能算工作流。
2. AIClip 如何从“本地路径输入输出”升级为“作品生成能力”。
3. AIClip 与作品、版本、检查、发布池如何衔接。
4. 需要新增哪些 API、数据结构和页面交互。
5. 如何在不破坏当前工具能力的前提下渐进改造。

---

## 2. 现状结论先行

### 2.1 当前 AIClip 的真实定位

当前 AIClip 本质上是：

> **一个独立的本地视频处理工具页**

它可以：

- 获取视频信息
- 检测高光
- 做智能裁剪
- 添加音频
- 添加封面
- 运行完整流程

但它目前不能：

- 直接绑定作品
- 产出新版本
- 自动回写素材库
- 自动进入人工检查流
- 自动进入发布池

### 2.2 核心问题

当前 AIClip 的问题不在于能力不足，而在于 **没有进入主工作流**。

也就是说：

- 现在它能处理视频；
- 但处理完的结果只是本地文件；
- 系统并不知道这个文件属于哪个作品、哪个版本、该不该发布。

---

## 3. 当前实现分析

## 3.1 前端现状

当前 `AIClip.tsx` 的交互模式是：

- 输入 `videoPath`
- 可选输入 `audioPath / coverPath / outputDir`
- 点击按钮执行处理
- 拿到 `outputPath`
- 用户自己决定后续怎么用

这意味着当前前端是：

- **路径驱动**
- **工具式**
- **一次性操作**

而不是：

- 作品驱动
- 流程式
- 可追溯的业务操作

## 3.2 后端现状

当前 `backend/api/ai.py` 和 `backend/services/ai_clip_service.py` 提供的是纯能力接口：

- `/video-info`
- `/detect-highlights`
- `/smart-clip`
- `/add-audio`
- `/add-cover`
- `/trim`
- `/full-pipeline`

这些接口特点是：

- 只接收文件路径
- 不接收作品 ID / 版本 ID / 任务 ID
- 不落库
- 不建立业务关联

### 结论

当前 AIClip 是一个 **media utility service**，不是 **creative workflow service**。

---

## 4. 目标定位

## 4.1 新定位

建议将 AIClip 的后续定位拆成两层：

### A. Tool Layer（工具层）

保留当前能力：

- 视频探测
- 高光检测
- 裁剪
- 加音频
- 加封面
- 完整流水线

### B. Workflow Layer（工作流层）

新增作品化能力：

- 读取作品当前输入素材
- 生成最终视频输出
- 回写素材库
- 创建新版本
- 生成 PackageRecord
- 推动作品状态进入检查流

### 4.2 一句话定义

> AIClip 不再只是“帮用户生成一个 mp4 文件”，而是“作品生成链中的视频处理执行器”。

---

## 5. 工作流化改造目标

建议把 AIClip 从“独立工具页”升级成两种工作模式：

## 5.1 模式 A：独立工具模式（保留）

适合：

- 临时本地处理
- 试验参数
- 先做一版看看效果
- 非正式作品流

### 特点

- 继续输入路径
- 输出路径
- 不强制绑定作品

## 5.2 模式 B：作品工作流模式（新增主模式）

适合：

- 作品生成
- 重合成视频
- 版本更新
- 人工检查后的返工

### 特点

- 输入 `creative_item_id` 或 `creative_version_id`
- 从素材库和当前版本中取输入
- 输出写入标准目录
- 自动回写版本和成品包
- 自动进入检查流

---

## 6. 工作流化后的主流程

## 6.1 初次生成流程

```text
选择商品/素材
  → 创建作品
  → 触发 AIClip 工作流
  → 生成最终视频
  → 回写 Video Asset / PackageRecord / CreativeVersion
  → 作品进入 WAITING_REVIEW
```

## 6.2 重合成流程

```text
作品详情页
  → 点击“重新合成视频”
  → 选择重合成参数/素材
  → AIClip 工作流执行
  → 创建新 CreativeVersion
  → 更新 current_version_id
  → 作品进入 WAITING_REVIEW
```

## 6.3 检查返工流程

```text
人工检查 → 需调整（video）
  → 触发 AIClip rerender flow
  → 生成新版本
  → 更新成品包
  → 再次进入 WAITING_REVIEW
```

---

## 7. 目标架构建议

## 7.1 当前架构

```text
AIClip Page
  → useAIClip Hooks
  → /api/ai/*
  → AIClipService
  → 本地输出文件
```

## 7.2 目标架构

```text
作品工作台 / 作品详情页 / AIClip 工具页
  → CreativeWorkflow API
  → AIClipWorkflowService
      ├─ AIClipService（底层媒体处理）
      ├─ Material Resolver
      ├─ Asset Persistence
      ├─ Creative Version Writer
      └─ Package Builder
```

### 分层原则

- `AIClipService`：继续做底层 FFmpeg / 媒体处理
- `AIClipWorkflowService`：做业务编排

这样能复用现有实现，同时避免把业务逻辑塞进底层工具服务。

---

## 8. 推荐新增的工作流服务

## 8.1 AIClipWorkflowService

建议新增一个上层服务，例如：

- `backend/services/ai_clip_workflow_service.py`

### 职责

1. 根据作品或版本解析输入素材
2. 构造 AIClip 参数
3. 调用 `AIClipService`
4. 把输出视频纳入素材库
5. 创建新 `CreativeVersion`
6. 创建/更新 `PackageRecord`
7. 更新 `CreativeItem.status`

### 输入模型建议

#### 初次生成

- `creative_item_id`
- `source_video_ids`
- `audio_asset_id`（可选）
- `cover_asset_id`（可选）
- `target_duration`
- `generation_reason`

#### 重合成

- `creative_item_id`
- `base_version_id`
- `override_materials`
- `target_duration`
- `generation_reason = rerendered_video`

---

## 8.2 PackageBuilder（建议独立）

由于作品生成最终要进入人工检查和发布池，建议把“成品包构建”也从 AIClip 中独立出来。

### 职责

- 生成标准目录
- 组织：
  - 视频
  - 封面
  - 标题
  - 文案
- 写 manifest
- 做完整性校验

### 原则

AIClip 只负责生成视频结果；PackageBuilder 负责把结果整理成业务可消费产物。

---

## 9. 数据流设计

## 9.1 输入来源

AIClip workflow 模式下，输入不应再只是裸路径，而应优先来自：

- 当前作品的 source material snapshot
- 当前版本绑定素材
- 素材库中的视频/封面/音频资产

## 9.2 输出去向

输出结果建议同时进入三处：

### A. 文件系统

- 存到标准 work/package 目录

### B. 素材库

- 新建 Video 资产记录（必要时）

### C. 作品层

- 创建新 `CreativeVersion`
- 关联 `PackageRecord`
- 更新 `CreativeItem.current_version_id`

---

## 10. API 设计建议

## 10.1 保留当前工具 API

保留：

- `GET /api/ai/video-info`
- `GET /api/ai/detect-highlights`
- `POST /api/ai/smart-clip`
- `POST /api/ai/add-audio`
- `POST /api/ai/add-cover`
- `POST /api/ai/trim`
- `POST /api/ai/full-pipeline`

## 10.2 新增工作流 API

建议新增：

- `POST /api/creative-workflows/ai-clip/generate`
- `POST /api/creative-workflows/ai-clip/rerender`
- `POST /api/creative-workflows/ai-clip/preview`
- `GET /api/creative-workflows/jobs/{id}`

### generate 请求示例

```json
{
  "creative_item_id": 101,
  "source_video_ids": [11, 12],
  "audio_asset_id": 8,
  "cover_asset_id": 6,
  "target_duration": 60,
  "generation_reason": "generated"
}
```

### rerender 请求示例

```json
{
  "creative_item_id": 101,
  "base_version_id": 3,
  "override_video_ids": [13, 14],
  "target_duration": 45,
  "generation_reason": "rerendered_video"
}
```

---

## 11. UI 交互改造建议

## 11.1 AIClip 页面保留，但分为两种入口

### 入口 1：工具模式

- 继续保留当前页面形态
- 输入路径，输出路径
- 给高级用户/调试使用

### 入口 2：作品模式

在作品详情页或工作台中触发：

- 不再输入裸路径
- 自动带出当前作品素材
- 提供少量参数调节
- 执行后直接生成新版本

## 11.2 作品详情页中的 AIClip 交互建议

### 按钮建议

- 重新合成视频
- 仅调整音频
- 仅调整封面
- 先预览生成效果（后续可选）

### 弹窗字段建议

- 目标时长
- 是否更换音频
- 是否更换封面
- 视频来源选择
- 输出说明（将生成新版本）

---

## 12. 与版本管理的协同规则

## 12.1 生成成功必须新建版本

AIClip 工作流模式下，一旦生成成功：

- 必须新建 `CreativeVersion`
- 不应覆盖旧版本

## 12.2 生成失败不新建正式版本

若处理中途失败：

- 可以保留临时文件
- 可以写执行日志
- 但不应创建正式版本

## 12.3 当前版本切换规则

默认建议：

- 新生成版本成功后，自动设为 `current_version_id`
- 作品状态 -> `WAITING_REVIEW`
- 旧版本的批准结论自动失效

---

## 13. 与发布池的协同规则

## 13.1 重合成后自动出池

若旧版本已在发布池中，而 AIClip 生成了新版本：

- 旧版本对应 pool item 失效/移除
- 新版本默认不自动入池
- 必须重新经过人工检查

## 13.2 AIClip 生成成功后不直接发布

即使作品之前是可发布状态，只要 AIClip 生成了新版本，也应该：

- 回到 `WAITING_REVIEW`
- 等待操作者再次确认

这样才能保证“每次影响最终内容的改动都重新检查”。

---

## 14. 状态流转建议

### 成功流

```text
REWORK_REQUIRED
→ GENERATING
→ WAITING_REVIEW
```

或

```text
PENDING_INPUT
→ GENERATING
→ WAITING_REVIEW
```

### 失败流

```text
GENERATING
→ GENERATE_FAILED
```

### 重试流

```text
GENERATE_FAILED
→ GENERATING
```

---

## 15. 落地顺序建议

## Phase A：低风险接入

- 保留当前 AIClip 页面
- 增加“导入到素材库”能力
- 处理结果至少能回写 Video 资产

## Phase B：版本化接入

- 新增 AIClipWorkflowService
- 在作品详情页接入“重新合成视频”
- 生成成功后创建新版本

## Phase C：全面工作流化

- 工作台直接发起生成
- 接入检查流
- 接入发布池
- AIClip 成为作品生成链的一部分

---

## 16. 风险与取舍

## 风险 1：把工具页和工作流混在一起会让实现变复杂

### 应对

坚持双层：

- Tool API
- Workflow API

不要把业务逻辑塞进现有 `AIClipService`。

## 风险 2：文件太多，回写逻辑复杂

### 应对

先定义统一输出目录和标准命名，再做资产入库和版本回写。

## 风险 3：工作流化后执行耗时更长，用户感知变差

### 应对

引入作业状态：

- pending
- processing
- completed
- failed

并在桌面端展示生成进度。

---

## 17. 一句话定义

> AIClip 的目标不是替代作品工作台，而是从一个“本地视频工具”升级成“作品生成链中的视频处理执行器”，让视频处理结果可以被版本化、被检查、被发布、被追踪。
