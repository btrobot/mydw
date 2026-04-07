# 领域模型分析 — 从"以任务为中心"到"素材为核心 + 任务为编排层"

> 日期: 2026-04-07
> 作者: Tech Lead
> 状态: Proposed (待 Product Owner 确认)

---

## 一、问题诊断

### 1.1 当前模型的本质

当前系统是一个**以 Task 为中心的扁平模型**：

```
Account ──1:N──> Task <──N:1── Product
                  │
                  ├── video_path    (直接存路径)
                  ├── content       (直接存文案文本)
                  ├── topic         (直接存话题文本)
                  ├── cover_path    (直接存路径)
                  ├── audio_path    (直接存路径)
                  │
                  └──N:1──> Material (可选 FK，实际很少用)
```

Task 表同时承担了三个职责：
1. **素材容器** — 直接存储 video_path、content、topic 等
2. **发布单元** — status、publish_time、error_msg
3. **编排记录** — account_id、priority

Material 表虽然存在，但只是一个"文件登记簿"，用 type 字段区分 video/text/cover/topic/audio，没有结构化的关联关系。Task 通过 material_id FK 只能关联一个 Material，而实际业务需要一个任务关联多种素材。

### 1.2 这个设计导致的具体问题

| 问题 | 表现 | 根因 |
|------|------|------|
| 多视频合成无法建模 | AI 剪辑只支持单视频输入，合成结果不回写素材库 | 没有"合成项目"概念，没有源素材 → 产出素材的关系 |
| 素材复用困难 | 同一个视频要发到 3 个账号，需要创建 3 个 Task 并各自填写 video_path | 素材和任务是 1:1 绑定，不是独立管理 |
| 文案/话题机械分配 | `texts[i % len(texts)]` 轮询，无法按商品智能匹配 | 文案和视频没有通过商品建立语义关联 |
| 商品管理位置错误 | 商品 CRUD 在 `/api/system/products`，前端素材页无入口 | 商品被当作"系统配置"而非"素材域的核心实体" |
| AI 剪辑与素材库割裂 | 剪辑结果是临时文件，不进素材库，不关联任务 | AI 剪辑服务是纯工具函数，无数据库交互 |
| 话题是静态文件 | 无搜索 API、无热度、无全局话题概念 | 话题被当作和视频同级的"素材文件" |
| init-from-materials 是假实现 | 和 auto-generate 调用同一个函数 | 没有真正的"从素材组装任务"的领域逻辑 |

### 1.3 核心矛盾

**业务本质**：用户管理的是"素材"（视频、文案、封面、话题、商品），任务只是"把素材组装起来发到某个账号"的编排动作。

**当前实现**：Task 是一切的中心，素材信息直接内联在 Task 字段里，Material 表形同虚设。

---

## 二、领域分析（DDD 视角）

### 2.1 限界上下文（Bounded Contexts）

```
┌─────────────────────────────────────────────────────────┐
│                    得物掘金工具                            │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  素材上下文    │  │  任务上下文    │  │  账号上下文    │  │
│  │  Material BC  │  │   Task BC    │  │  Account BC  │  │
│  │              │  │              │  │              │  │
│  │  - 视频管理   │  │  - 任务编排   │  │  - 账号管理   │  │
│  │  - 文案管理   │  │  - 发布执行   │  │  - Session   │  │
│  │  - 商品管理   │  │  - 调度策略   │  │  - 健康检查   │  │
│  │  - 话题管理   │  │              │  │              │  │
│  │  - AI 合成    │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │          │
│         └────────引用──────┘────────引用──────┘          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  发布上下文    │  │  系统上下文    │                    │
│  │  Publish BC  │  │  System BC   │                    │
│  │              │  │              │                    │
│  │  - 发布策略   │  │  - 日志      │                    │
│  │  - 发布执行   │  │  - 配置      │                    │
│  │  - 发布日志   │  │              │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 聚合根、实体、值对象

#### 素材上下文 (Material BC)

| 类型 | 名称 | 说明 |
|------|------|------|
| **聚合根** | Product | 商品是素材组织的核心锚点，视频/文案围绕商品聚合 |
| **聚合根** | Video | 视频素材，可独立存在，可关联商品 |
| **聚合根** | Copywriting | 文案，独立管理，可关联商品 |
| **聚合根** | Topic | 话题，独立管理，有热度属性 |
| **实体** | Cover | 封面图，通常关联到视频 |
| **实体** | Audio | 音频素材，通常关联到视频 |
| **实体** | CompositionProject | AI 合成项目，记录源素材 → 产出素材的关系 |
| **值对象** | FileMeta | 文件元信息（路径、大小、时长、哈希） |
| **值对象** | CompositionParams | 合成参数（目标时长、超时等） |
| **值对象** | CopywritingMode | 文案模式枚举（手动/原文案/AI生成） |

#### 任务上下文 (Task BC)

| 类型 | 名称 | 说明 |
|------|------|------|
| **聚合根** | PublishTask | 发布任务，引用素材 ID（不内联素材数据） |
| **值对象** | TaskAssignment | 任务分配策略（手动指定/轮询分配） |
| **领域服务** | TaskAssembler | 从素材组装任务的领域逻辑 |
| **领域服务** | TaskDistributor | 任务分配到多账号的调度逻辑 |

#### 账号上下文 (Account BC)

保持现有设计，Account 作为聚合根，不变。

---

## 三、建议的 ER 模型

### 3.1 核心实体关系图

```
┌─────────────┐
│   Product    │  商品（聚合根）
│─────────────│
│ id           │
│ name         │
│ link         │
│ description  │
│ dewu_url     │  得物商品页 URL
│ image_url    │  商品图片
│ created_at   │
│ updated_at   │
└──────┬──────┘
       │
       │ 1:N
       ▼
┌─────────────┐         ┌──────────────┐
│    Video     │  ◄──1:N─┤  VideoSource  │  合成项目的源视频
│─────────────│         │──────────────│
│ id           │         │ id            │
│ product_id   │ FK      │ project_id    │ FK → CompositionProject
│ name         │         │ video_id      │ FK → Video
│ file_path    │         │ sort_order    │
│ file_size    │         │ created_at    │
│ duration     │         └──────────────┘
│ width        │
│ height       │                ┌───────────────────┐
│ file_hash    │                │ CompositionProject │  AI 合成项目
│ source_type  │ original/      │───────────────────│
│              │ composed/      │ id                 │
│              │ downloaded     │ name               │
│ origin_id    │ FK → self      │ output_video_id    │ FK → Video (产出)
│ cover_id     │ FK → Cover     │ status             │ pending/processing/
│ created_at   │                │                    │ done/failed
│ updated_at   │                │ target_duration    │ 目标时长(秒)
└──────┬──────┘                │ actual_duration    │ 实际时长(秒)
       │                       │ params_json        │ 合成参数
       │                       │ error_msg          │
       │                       │ created_at         │
       │                       │ updated_at         │
       │                       └───────────────────┘
       │
       │ 1:N (一个商品下多个文案)
       │
┌──────┴──────┐
│  Copywriting │  文案
│─────────────│
│ id           │
│ product_id   │ FK → Product (可空)
│ content      │ 文案正文
│ source_type  │ manual / original / ai_generated
│ source_ref   │ 来源引用（原视频ID / AI prompt 等）
│ created_at   │
│ updated_at   │
└─────────────┘

┌─────────────┐
│    Topic     │  话题
│─────────────│
│ id           │
│ name         │  话题名称（如 #得物好物）
│ heat         │  热度值
│ source       │  manual / search
│ last_synced  │  上次从平台同步时间
│ created_at   │
└─────────────┘

┌─────────────┐
│    Cover     │  封面
│─────────────│
│ id           │
│ video_id     │ FK → Video (可空)
│ file_path    │
│ file_size    │
│ width        │
│ height       │
│ created_at   │
└─────────────┘

┌─────────────┐
│    Audio     │  音频
│─────────────│
│ id           │
│ name         │
│ file_path    │
│ file_size    │
│ duration     │
│ created_at   │
└─────────────┘
```

### 3.2 任务模型（编排层）

```
┌──────────────────┐
│   PublishTask     │  发布任务（编排层，引用素材 ID）
│──────────────────│
│ id                │
│ account_id        │ FK → Account
│ video_id          │ FK → Video          ← 替代 video_path
│ copywriting_id    │ FK → Copywriting    ← 替代 content 文本
│ product_id        │ FK → Product        ← 保留
│ audio_id          │ FK → Audio          ← 替代 audio_path
│                   │
│ status            │ pending/running/success/failed/paused
│ publish_time      │
│ error_msg         │
│ priority          │
│ created_at        │
│ updated_at        │
└────────┬─────────┘
         │
         │ N:M (一个任务可以有多个话题)
         ▼
┌──────────────────┐
│  TaskTopic       │  任务-话题关联表
│──────────────────│
│ task_id           │ FK → PublishTask
│ topic_id          │ FK → Topic
└──────────────────┘
```

### 3.3 完整 ER 关系总览

```
Product ──1:N──> Video
Product ──1:N──> Copywriting
Video   ──1:1──> Cover (可选)
Video   ──1:N──> CompositionProject (作为源，通过 VideoSource)
CompositionProject ──1:1──> Video (作为产出，output_video_id)

Account ──1:N──> PublishTask
Video   ──1:N──> PublishTask
Copywriting ──1:N──> PublishTask
Product ──1:N──> PublishTask
Audio   ──1:N──> PublishTask (可选)
PublishTask ──N:M──> Topic (通过 TaskTopic)
```

---

## 四、关键场景走查

### 4.1 多视频合成（2+ 视频 → 1 个新视频）

**当前**：AI 剪辑服务是纯 FFmpeg 工具，输入路径输出文件，不入库。

**建议**：

```
用户选择 Video A, Video B, Video C
    → 创建 CompositionProject (status=pending)
    → 创建 VideoSource 记录 (project_id, video_id, sort_order)
    → AI 合成服务执行 FFmpeg
    → 合成完成 → 创建新 Video (source_type=composed, origin_id=project.id)
    → 更新 CompositionProject (status=done, output_video_id=新Video.id)
    → 新 Video 自动进入素材库，可用于创建任务
```

关键点：CompositionProject 记录了"哪些源视频合成了哪个新视频"，可追溯、可重试。

### 4.2 素材与商品的关联

**当前**：Material 有 product_id FK，但商品管理在 system.py，前端素材页无入口。

**建议**：

```
商品管理移入素材上下文
    → Product 是素材域的聚合根
    → Video.product_id → 视频属于哪个商品
    → Copywriting.product_id → 文案属于哪个商品
    → 创建任务时，选择 Video 自动带出关联的 Product 和 Copywriting
```

### 4.3 任务自动分配到多账号（轮询）

**当前**：auto_generate_tasks 只接受单个 account_id。

**建议**：

```
TaskDistributor 领域服务:
    输入: video_ids[], account_ids[], strategy="round_robin"
    处理:
        for i, video_id in enumerate(video_ids):
            account_id = account_ids[i % len(account_ids)]
            创建 PublishTask(video_id, account_id, ...)
    输出: PublishTask[]
```

任务不再内联素材数据，只引用 video_id / copywriting_id，所以同一个 Video 可以分配给多个账号而不重复存储。

### 4.4 文案来源（手动/原文案/AI 生成）

**当前**：文案是 Material type=text 的文件内容，无来源区分。

**建议**：

```
Copywriting 表:
    source_type = "manual"        → 用户手动输入
    source_type = "original"      → 从源视频提取（source_ref = video_id）
    source_type = "ai_generated"  → AI 生成（source_ref = prompt/model info）

TaskAssembler 领域服务:
    根据用户选择的文案模式:
        manual      → 用户选择已有 Copywriting 或新建
        original    → 从 Video 关联的原始文案中复制
        ai_generated → 调用 AI 服务生成，存入 Copywriting 表
```

### 4.5 话题管理

**当前**：话题是 Material type=topic 的文本文件。

**建议**：

```
Topic 独立为一等实体:
    - 支持从得物平台搜索（通过 Playwright 自动化）
    - 记录热度值，支持排序
    - 通过 TaskTopic 关联表支持一个任务多个话题
    - 支持"全局话题"概念：用户选择的话题自动应用到后续所有任务
```

---

## 五、当前模型 vs 建议模型对比

### 5.1 实体对比

| 当前 | 建议 | 变化类型 |
|------|------|----------|
| Material (type=video) | Video | **拆分** — 从通用表拆为独立表 |
| Material (type=text) | Copywriting | **拆分** — 增加 source_type 语义 |
| Material (type=cover) | Cover | **拆分** — 关联到 Video |
| Material (type=topic) | Topic | **拆分** — 增加 heat、source 字段 |
| Material (type=audio) | Audio | **拆分** — 独立表 |
| (不存在) | CompositionProject | **新增** — AI 合成项目 |
| (不存在) | VideoSource | **新增** — 合成源视频关联 |
| (不存在) | TaskTopic | **新增** — 任务-话题多对多 |
| Task | PublishTask | **重构** — 移除内联字段，改为 FK 引用 |
| Product | Product | **增强** — 移入素材域，增加字段 |
| Account | Account | **不变** |
| PublishLog | PublishLog | **不变** |
| PublishConfig | PublishConfig | **不变** |
| SystemLog | SystemLog | **不变** |

### 5.2 关系对比

| 当前关系 | 建议关系 | 变化 |
|----------|----------|------|
| Task.video_path (字符串) | PublishTask.video_id → Video | 从内联路径改为 FK 引用 |
| Task.content (文本) | PublishTask.copywriting_id → Copywriting | 从内联文本改为 FK 引用 |
| Task.topic (字符串) | PublishTask ←N:M→ Topic | 从单字符串改为多对多 |
| Task.cover_path (字符串) | Video.cover_id → Cover | 封面关联到视频而非任务 |
| Task.audio_path (字符串) | PublishTask.audio_id → Audio | 从内联路径改为 FK 引用 |
| Task.material_id → Material | (移除) | Material 表废弃 |
| Material.product_id → Product | Video.product_id, Copywriting.product_id | 更精确的商品关联 |

### 5.3 API 变化

| 当前 API | 建议 API | 变化 |
|----------|----------|------|
| `/api/materials` (通用 CRUD) | `/api/videos`, `/api/copywritings`, `/api/topics`, `/api/covers`, `/api/audios` | 拆分为独立资源端点 |
| `/api/system/products` | `/api/products` | 移出 system，成为一级资源 |
| `/api/ai/clip` (纯工具) | `/api/compositions` | 升级为有状态的合成项目 |
| `/api/tasks/auto-generate` | `/api/tasks/assemble` | 语义更清晰 |
| `/api/tasks/init-from-materials` | (合并到 assemble) | 消除假实现 |
| (不存在) | `/api/topics/search` | 新增话题搜索 |

---

## 六、变更影响评估

### 6.1 破坏性变更（需要数据迁移）

| 变更 | 影响范围 | 迁移策略 |
|------|----------|----------|
| Material 表拆分为 Video/Copywriting/Cover/Topic/Audio | 后端模型、API、前端全部 | 编写迁移脚本，按 type 字段分流到新表 |
| Task 表移除内联字段，改为 FK 引用 | 后端模型、任务服务、发布服务、前端任务页 | 迁移时根据现有 video_path 匹配 Video 记录 |
| Product API 从 system 移到一级资源 | 前端 API 调用路径 | 前端更新 import 路径 |

### 6.2 增量变更（可渐进实施）

| 变更 | 影响范围 | 说明 |
|------|----------|------|
| 新增 CompositionProject 表 | 后端新增模型和 API | 不影响现有功能 |
| 新增 TaskTopic 关联表 | 后端新增模型 | 不影响现有功能 |
| 新增 Topic.heat / Topic.source 字段 | 后端模型扩展 | 可通过 ALTER TABLE 增量添加 |
| 新增 Copywriting.source_type 字段 | 后端模型扩展 | 可通过 ALTER TABLE 增量添加 |
| 新增话题搜索 API | 后端新增端点 | 不影响现有功能 |

### 6.3 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| Material 表拆分导致数据丢失 | 高 | 迁移前备份数据库，编写可回滚的迁移脚本 |
| Task 表重构导致发布流程中断 | 高 | 分阶段迁移：先双写（新旧字段并存），再切换，最后清理 |
| 前端大面积改动 | 中 | 后端先提供兼容层 API，前端逐步迁移 |
| AI 合成服务改造 | 低 | CompositionProject 是新增概念，不影响现有 FFmpeg 逻辑 |

---

## 七、建议实施路径

### Phase 1: 素材域重建（破坏性，但必须先做）

1. 创建新表：Video, Copywriting, Cover, Audio, Topic
2. 编写 Material → 新表的数据迁移脚本
3. 创建新的 API 端点（`/api/videos` 等）
4. 保留旧 `/api/materials` 作为兼容层（内部转发到新端点）
5. Product API 从 `/api/system/products` 迁移到 `/api/products`

### Phase 2: 合成项目（增量）

1. 创建 CompositionProject, VideoSource 表
2. 改造 AI 剪辑服务，增加数据库交互
3. 合成结果自动入库为新 Video (source_type=composed)

### Phase 3: 任务编排层重构（破坏性）

1. PublishTask 表增加 video_id, copywriting_id, audio_id FK
2. 创建 TaskTopic 关联表
3. 实现 TaskAssembler 领域服务
4. 实现 TaskDistributor 领域服务（多账号轮询）
5. 双写期：新旧字段并存，发布服务优先读新字段
6. 迁移完成后清理旧字段

### Phase 4: 话题增强（增量）

1. Topic 表增加 heat, source, last_synced 字段
2. 实现得物平台话题搜索（通过 Playwright 或 API）
3. 前端话题搜索 UI

---

## 八、ADR 记录

### ADR-001: 素材模型从通用表拆分为领域实体

**状态**: Proposed

**日期**: 2026-04-07

**上下文**:
当前 Material 表用 type 字段区分 video/text/cover/topic/audio 五种素材，是一个通用的文件登记表。这导致：
- 不同类型素材的特有属性无法建模（如视频的 width/height/fps，话题的 heat）
- 素材间的关联关系无法表达（如封面属于哪个视频，文案属于哪个商品）
- AI 合成的"多视频 → 一个新视频"关系无法建模

**决策**:
将 Material 表拆分为 Video、Copywriting、Cover、Audio、Topic 五个独立表，每个表有自己的特有字段和关联关系。废弃通用 Material 表。

**后果**:
- [正面] 每种素材有精确的数据模型，支持特有属性和关联
- [正面] 支持多视频合成、文案来源追踪、话题热度等业务场景
- [正面] API 语义更清晰（`/api/videos` vs `/api/materials?type=video`）
- [负面] 破坏性变更，需要数据迁移
- [负面] API 端点数量增加
- [中性] 代码量增加，但每个模块更简单、更聚焦

### ADR-002: Task 从"素材容器"重构为"编排引用层"

**状态**: Proposed

**日期**: 2026-04-07

**上下文**:
当前 Task 表直接存储 video_path、content、topic 等素材数据，导致素材和任务强耦合，同一素材发到多个账号需要重复存储，且无法追溯素材来源。

**决策**:
Task（重命名为 PublishTask）只存储素材的 FK 引用（video_id、copywriting_id、audio_id），不再内联素材数据。话题通过 TaskTopic 多对多关联表实现。

**后果**:
- [正面] 素材可复用，一个视频可分配给多个任务
- [正面] 素材更新自动反映到所有引用它的任务
- [正面] 支持多话题关联
- [负面] 破坏性变更，需要数据迁移和双写过渡期
- [负面] 查询任务详情需要 JOIN 多表
- [中性] 发布服务需要改为从关联表读取素材信息
