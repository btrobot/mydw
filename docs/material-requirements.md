# 素材管理子系统 — 需求分析文档

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Active

---

## 目录

| 章节 | 内容 |
|------|------|
| 1 | 业务背景与目标 |
| 2 | 领域模型 |
| 3 | 用例模型 |
| 4 | 功能需求矩阵 |
| 5 | 数据流 |
| 6 | 非功能需求 |
| 7 | 实施优先级 |

---

## 1. 业务背景与目标

### 1.1 系统定位

DewuGoJin 是得物平台自动化视频发布系统。素材管理是核心支撑模块，为下游的任务组装（TaskAssembler）和自动发布（PublishService）提供全部内容素材。

发布链路：素材入库 -> 任务组装 -> 自动发布 -> 得物平台

### 1.2 业务目标

| 目标 | 说明 |
|------|------|
| 素材集中管理 | 视频、文案、封面、音频、话题统一管理，按商品维度组织 |
| 高效入库 | 支持目录扫描批量导入，减少手动操作 |
| 发布链路完整 | 素材通过 FK 关联到任务，发布时自动读取，零手动干预 |
| 素材复用 | 同一素材可被多个任务引用，支持跨账号发布 |

### 1.3 用户角色

| 角色 | 操作 |
|------|------|
| 内容运营 | 管理素材（增删改查）、按商品分类、设置话题 |
| 任务组装器（系统） | 读取素材，自动匹配文案和话题，创建发布任务 |
| 发布引擎（系统） | 消费任务中的素材路径和内容，调用得物客户端上传 |

---

## 2. 领域模型

### 2.1 实体关系图

```
┌──────────────┐
│   Product    │  商品 — 素材的组织维度
│──────────────│
│ id       PK  │
│ name     UQ  │
│ link         │
│ dewu_url     │
│ image_url    │
│ description  │
└──────┬───────┘
       │
       ├─── 1:N ───┐
       │            │
       ▼            ▼
┌──────────────┐  ┌──────────────┐
│    Video     │  │ Copywriting  │
│──────────────│  │──────────────│
│ id       PK  │  │ id       PK  │
│ product_id FK│  │ product_id FK│
│ name         │  │ content      │
│ file_path    │  │ source_type  │
│ file_size    │  │ source_ref   │
│ duration     │  └──────────────┘
│ width        │
│ height       │
│ file_hash    │
│ source_type  │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐
│    Cover     │
│──────────────│
│ id       PK  │
│ video_id  FK │
│ file_path    │
│ file_size    │
│ width        │
│ height       │
└──────────────┘

┌──────────────┐  ┌──────────────┐
│    Audio     │  │    Topic     │
│──────────────│  │──────────────│
│ id       PK  │  │ id       PK  │
│ name         │  │ name     UQ  │
│ file_path    │  │ heat         │
│ file_size    │  │ source       │
│ duration     │  │ last_synced  │
└──────────────┘  └──────────────┘

下游消费:
┌──────────────────────────────────────────────────┐
│                    Task                          │
│──────────────────────────────────────────────────│
│ video_id FK -> videos                            │
│ copywriting_id FK -> copywritings                │
│ audio_id FK -> audios                            │
│ product_id FK -> products                        │
│ topics M:N via task_topics                       │
│ cover_id FK -> covers  [缺失 — 当前断裂点]       │
└──────────────────────────────────────────────────┘
```

### 2.2 聚合根与边界

| 聚合根 | 包含实体 | 生命周期 |
|--------|---------|---------|
| Product | Product | 独立，删除时需检查下游 Video/Copywriting 引用 |
| Video | Video -> Cover[] | 删除视频应级联删除关联封面 |
| Copywriting | Copywriting | 独立，通过 product_id 松耦合到商品 |
| Audio | Audio | 完全独立，无 FK 依赖商品 |
| Topic | Topic | 独立，通过 TaskTopic 中间表与任务关联 |

### 2.3 值对象

| 值对象 | 属性 | 说明 |
|--------|------|------|
| FileMetadata | file_path, file_size, duration, width, height, file_hash | 文件物理属性集合 |
| SourceInfo | source_type, source_ref | 素材来源追踪（manual / ai_clip / search / import） |

### 2.4 关键关系说明

| 关系 | 类型 | 约束 |
|------|------|------|
| Product -> Video | 1:N | video.product_id 可为 NULL（未分类视频） |
| Product -> Copywriting | 1:N | copywriting.product_id 可为 NULL |
| Video -> Cover | 1:N | cover.video_id 可为 NULL（独立封面） |
| Topic <-> Task | M:N | 通过 task_topics 中间表，UNIQUE(task_id, topic_id) |
| Audio -> Task | 被引用 | task.audio_id FK，Audio 无 product_id |

---

## 3. 用例模型

### 3.1 用例总览

```
                    ┌─────────────────────────────────────────┐
                    │          素材管理子系统                    │
                    │                                         │
  ┌──────┐         │  UC-01: 管理商品 (CRUD)                   │
  │      │────────>│  UC-02: 管理视频素材                       │
  │      │         │    UC-02a: 手动添加视频                    │
  │      │         │    UC-02b: 目录扫描导入 [待实现]            │
  │ 用户  │         │    UC-02c: 文件上传 [待实现]               │
  │      │────────>│  UC-03: 管理文案                          │
  │      │         │    UC-03a: 手动添加/编辑文案                │
  │      │         │    UC-03b: 批量导入文案 [待实现]            │
  │      │────────>│  UC-04: 管理封面 (上传/列表/删除)           │
  │      │         │  UC-05: 管理音频 (上传/列表/删除)           │
  │      │────────>│  UC-06: 管理话题                          │
  └──────┘         │    UC-06a: 手动添加话题                    │
                    │    UC-06b: 搜索得物话题并入库              │
       ┌──────┐    │    UC-06c: 设置全局话题                    │
       │任务   │<───│  UC-07: 素材->任务组装                    │
       │组装器 │    │  UC-08: 素材统计 [待实现]                  │
       └──────┘    └─────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    发布引擎        │
                    │ 消费: video_path,  │
                    │ content, topic,    │
                    │ cover_path,        │
                    │ product_link       │
                    └───────────────────┘
```

### 3.2 关键用例详述

#### UC-02b: 目录扫描导入（待实现，P0）

| 项 | 内容 |
|----|------|
| 前置条件 | MATERIAL_BASE_PATH 已配置（当前默认 `D:/系统/桌面/得物剪辑/待上传数据`） |
| 触发 | 用户点击"扫描导入"按钮 |
| 主流程 | 1. 扫描 MATERIAL_BASE_PATH 下一级子目录（子目录名 = 商品名） |
|        | 2. 每个子目录下的 .mp4/.mov 文件识别为视频素材 |
|        | 3. 自动创建或匹配已有 Product（按名称） |
|        | 4. FFprobe 提取视频元数据（duration, width, height, file_size） |
|        | 5. 计算 file_hash (SHA-256) 去重，跳过已存在视频 |
|        | 6. 批量入库，返回导入统计（新增/跳过/失败数量） |
| 后置条件 | 视频已入库并关联到对应商品 |
| 异常流 | 文件损坏 -> 跳过并记录日志；商品名冲突 -> 复用已有商品 |

#### UC-02c: 视频文件上传（待实现，P0）

| 项 | 内容 |
|----|------|
| 现状 | 当前只能手动输入 file_path 字符串，无真正的文件上传 |
| 目标 | 前端通过 Upload 组件选择文件，后端接收并存储到 MATERIAL_BASE_PATH |
| 约束 | 文件类型限制 video/mp4, video/quicktime；大小限制可配置 |

#### UC-09: cover_id FK 迁移（待实现，P0 — 发布链路断裂修复）

| 项 | 内容 |
|----|------|
| 现状 | `publish_service.py:180` 引用 `task.cover_path`，但 Task ORM 模型中无此字段 |
| 原因 | 迁移 005 将旧字段（video_path/content/topic/cover_path/audio_path）替换为 FK，但 cover_id 未添加 |
| 目标 | Task 模型增加 `cover_id` FK -> covers 表；publish_service 改为通过 `task.cover.file_path` 读取 |
| 影响范围 | Task 模型、publish_service、task_assembler、前端 Task 页面 |

---

## 4. 功能需求矩阵

### 4.1 已实现功能

| 编号 | 模块 | 功能 | 后端实现 | 前端实现 | 状态 |
|------|------|------|---------|---------|------|
| F-01 | 商品 | 创建/列表/详情/删除 | `api/product.py` 全 CRUD | ProductSection 卡片列表 | 完整 |
| F-02 | 商品 | 更新 | `PUT /products/{id}` | 无编辑入口 | 后端完整，前端缺失 |
| F-03 | 商品 | 名称模糊搜索 | `GET /products?name=` | 未接入 | 后端完整 |
| F-04 | 视频 | 创建/列表/详情/更新/删除 | `api/video.py` 全 CRUD | VideoTab 表格 | 完整 |
| F-05 | 视频 | 按商品筛选 | `GET /videos?product_id=` | Select 筛选器 | 完整 |
| F-06 | 文案 | 创建/列表/详情/删除 | `api/copywriting.py` 全 CRUD | CopywritingTab 表格 | 完整 |
| F-07 | 文案 | 更新 | `PUT /copywritings/{id}` | 无编辑入口 | 后端完整，前端缺失 |
| F-08 | 文案 | 按商品/来源筛选 | `GET /copywritings?product_id=&source_type=` | 商品筛选 | 完整 |
| F-09 | 封面 | 文件上传/列表/删除 | `api/cover.py` upload+list+delete | CoverTab 表格+Upload | 完整 |
| F-10 | 封面 | 按视频筛选 | `GET /covers?video_id=` | Input 数字筛选 | 完整 |
| F-11 | 音频 | 文件上传/列表/删除 | `api/audio.py` upload+list+delete | AudioTab 表格+Upload | 完整 |
| F-12 | 话题 | 创建/列表/删除 | `api/topic.py` CRUD | TopicTab 表格 | 完整 |
| F-13 | 话题 | 得物搜索入库 | `GET /topics/search?keyword=` | 搜索卡片+添加按钮 | 完整 |
| F-14 | 话题 | 全局话题设置 | `PUT/GET /topics/global` | 全局话题弹窗 | 完整 |
| F-15 | 话题 | 按热度/时间排序 | `GET /topics?sort=heat\|created_at` | Select 排序器 | 完整 |
| F-16 | 组装 | 自动匹配文案+话题 | `TaskAssembler.assemble()` | 任务页面调用 | 完整 |

### 4.2 缺失/待实现功能

| 编号 | 模块 | 功能 | 优先级 | 说明 |
|------|------|------|--------|------|
| M-01 | 视频 | 文件上传（非手动填路径） | P0 | 当前只能手动输入 file_path，无真正文件上传 |
| M-02 | 视频 | 目录扫描导入 | P0 | MATERIAL_BASE_PATH 下按商品子目录扫描批量入库 |
| M-03 | 视频 | FFprobe 自动提取元数据 | P1 | 上传/导入时自动填充 duration, width, height, file_size, file_hash |
| M-04 | 视频 | 文件存在性校验 | P1 | 列表展示时标记文件是否存在，发布前校验 |
| M-05 | 视频 | 重复检测 (file_hash) | P2 | 基于 SHA-256 去重，避免同一视频多次入库 |
| M-06 | 文案 | 批量导入（文本文件） | P1 | 从 .txt 文件批量导入文案，一行一条 |
| M-07 | 文案 | 前端编辑入口 | P1 | 后端 PUT 已有，前端缺少编辑按钮和弹窗 |
| M-08 | 封面 | 从视频自动提取 | P2 | 调用 FFmpeg 从视频指定时间点截取封面 |
| M-09 | 封面 | Task.cover_id FK | P0 | Task 模型缺少 cover_id FK，publish_service 引用不存在的 task.cover_path |
| M-10 | 音频 | 元数据提取 (duration) | P2 | 上传时 FFprobe 提取时长 |
| M-11 | 话题 | 批量删除 | P2 | 前端无批量操作 |
| M-12 | 商品 | 前端编辑入口 | P1 | 后端 PUT 已有，前端缺少编辑按钮和弹窗 |
| M-13 | 商品 | 得物链接解析 | P2 | 从得物 URL 自动提取商品名称和图片 |
| M-14 | 全局 | 素材统计仪表盘 | P2 | 各类素材数量、商品覆盖率、无素材商品提醒 |
| M-15 | 全局 | 批量删除 | P1 | 各 Tab 支持多选批量删除 |
| M-16 | 全局 | 关键词搜索 | P2 | 视频名称、文案内容全文搜索 |

---

## 5. 数据流

### 5.1 素材入库 -> 发布 完整链路

```
素材入库阶段                 任务组装阶段                    发布执行阶段
──────────                  ──────────                     ──────────

Video ──────────┐
                ├──> TaskAssembler.assemble() ──> Task ──> PublishService
Copywriting ────┤     auto_match by product_id     │       .publish_task()
                │                                  │          │
Product ────────┤     (提供 product.link)           │          ▼
                │                                  │     DewuClient
Audio ──────────┘                                  │     .upload_video(
                                                   │       video_path,
Topic ──> GlobalTopics ──> TaskTopic ──────────────┘       title,
                                                           content,
Cover ──> [断裂: task.cover_path 不存在] ──────────────>    cover_path,
                                                           product_link)
```

### 5.2 TaskAssembler 组装逻辑

```
输入: video_ids[], account_id, copywriting_mode

1. 查询 Video 列表（预加载 product 关系）
2. 收集所有 product_id，批量查询同商品文案
3. 读取 PublishConfig.global_topic_ids（全局话题）
4. 为每个 Video 创建 Task:
   - video_id = video.id
   - product_id = video.product_id
   - copywriting_id = auto_match 同商品文案（轮询分配）
   - account_id = 指定账号
5. 为每个 Task 创建 TaskTopic 关联（全局话题）
6. commit + 重新查询预加载关系

输出: Task[] (含 video, copywriting, product, topics 关系)
```

### 5.3 PublishService 素材消费

```
输入: Task (预加载 video, copywriting, audio, product, topics)

读取字段:
  video_path  = task.video.file_path
  content     = task.copywriting.content
  topic       = ", ".join(t.name for t in task.topics)
  product_link = task.product.link
  cover_path  = task.cover_path  [BUG: 字段不存在于 ORM 模型]

调用: DewuClient.upload_video(video_path, title, content, topic, cover_path, product_link)
```

### 5.4 目录结构约定

```
MATERIAL_BASE_PATH (默认: D:/系统/桌面/得物剪辑/待上传数据/)
├── {商品名A}/           <- 子目录名 = 商品名
│   ├── video1.mp4       <- 视频素材
│   ├── video2.mp4
│   └── ...
├── {商品名B}/
│   └── video3.mp4
├── audio/               <- 全局音频目录（音频上传存储位置）
│   └── bgm1.mp3
└── cover/               <- 全局封面目录（封面上传存储位置）
    └── uploaded_cover.jpg
```

---

## 6. 非功能需求

### 6.1 性能

| 指标 | 要求 | 说明 |
|------|------|------|
| 扫描导入 | 支持 1000+ 文件 | 使用批量 INSERT，避免逐条提交 |
| 列表查询 | < 200ms | 分页查询，默认 limit=100 |
| 文件上传 | 单文件 < 500MB | 视频文件可能较大 |
| 元数据提取 | < 5s/文件 | FFprobe 异步执行 |

### 6.2 安全

| 要求 | 实现方式 | 当前状态 |
|------|---------|---------|
| 路径校验 | Pydantic field_validator 检测 `..` | VideoCreate 已实现 |
| 文件类型校验 | content_type 白名单 | 封面/音频已实现，视频待实现 |
| 文件大小限制 | 读取后检查 len(content) | 封面 20MB / 音频 100MB 已实现 |
| 文件名清理 | `Path(filename).name.replace("..", "")` | 封面/音频已实现 |

### 6.3 数据一致性

| 场景 | 要求 |
|------|------|
| 删除素材 | 同步删除物理文件 + DB 记录（封面/音频已实现，视频未实现） |
| 删除被引用素材 | 删除前检查 Task 引用，有引用时提示用户（当前未实现） |
| 删除商品 | 检查关联的 Video/Copywriting，有关联时提示（当前未实现） |
| 扫描导入幂等 | 基于 file_hash 去重，重复执行安全 |

### 6.4 兼容性

| 要求 | 说明 |
|------|------|
| 中文路径 | 文件路径和文件名支持中文字符 |
| Windows 路径 | 使用 pathlib.Path 处理路径分隔符 |
| 视频格式 | .mp4, .mov（得物平台支持的格式） |
| 图片格式 | JPEG, PNG, WebP（封面） |
| 音频格式 | MP3, WAV, AAC, OGG |

---

## 7. 实施优先级

### Phase 1 — P0：发布链路打通

| 编号 | 任务 | 影响 | 工作量估算 |
|------|------|------|-----------|
| M-09 | Task.cover_id FK 迁移 | 修复发布链路断裂（当前 task.cover_path 不存在） | 后端迁移 + publish_service + task_assembler 修改 |
| M-01 | 视频文件上传 | 用户无需手动输入路径 | 后端 upload endpoint + 前端 Upload 组件 |
| M-02 | 目录扫描导入 | 批量入库核心能力 | 后端 scan endpoint + FFprobe + 前端触发按钮 |

Phase 1 完成标志：用户可以通过上传或扫描导入视频，组装任务后完整发布（含封面）。

### Phase 2 — P1：体验完善

| 编号 | 任务 | 说明 |
|------|------|------|
| M-03 | FFprobe 元数据提取 | 上传/导入时自动填充 duration, width, height |
| M-04 | 文件存在性校验 | 列表标记 + 发布前校验 |
| M-06 | 文案批量导入 | .txt 文件一行一条 |
| M-07 | 文案前端编辑入口 | 后端 PUT 已有，补前端 |
| M-12 | 商品前端编辑入口 | 后端 PUT 已有，补前端 |
| M-15 | 各模块批量删除 | Table rowSelection + 批量 DELETE |

### Phase 3 — P2：增强功能

| 编号 | 任务 | 说明 |
|------|------|------|
| M-05 | 视频去重 | SHA-256 file_hash 检测 |
| M-08 | 封面自动提取 | FFmpeg 从视频截取指定帧 |
| M-10 | 音频元数据提取 | FFprobe 提取时长 |
| M-11 | 话题批量删除 | 前端多选操作 |
| M-13 | 得物链接解析 | 从 URL 自动提取商品信息 |
| M-14 | 素材统计仪表盘 | 数量统计、覆盖率、缺失提醒 |
| M-16 | 全文搜索 | 视频名称、文案内容搜索 |

---

## 附录 A：关键文件索引

| 文件 | 角色 |
|------|------|
| `backend/models/__init__.py` | 全部 ORM 模型定义（Video, Copywriting, Cover, Audio, Topic, Product, Task, TaskTopic） |
| `backend/schemas/__init__.py` | 全部 Pydantic Schema（请求/响应模型） |
| `backend/api/video.py` | 视频 CRUD API |
| `backend/api/copywriting.py` | 文案 CRUD API |
| `backend/api/cover.py` | 封面上传/列表/删除 API |
| `backend/api/audio.py` | 音频上传/列表/删除 API |
| `backend/api/topic.py` | 话题 CRUD + 搜索 + 全局话题 API |
| `backend/api/product.py` | 商品 CRUD API |
| `backend/services/task_assembler.py` | 任务组装器（素材消费方，自动匹配文案+话题） |
| `backend/services/publish_service.py` | 发布服务（素材最终消费方，L152-180 读取素材字段） |
| `backend/core/dewu_client.py` | 得物客户端 upload_video（L553，接收 cover_path 参数） |
| `backend/core/config.py` | MATERIAL_BASE_PATH 配置 |
| `frontend/src/pages/Material.tsx` | 前端素材管理页面（ProductSection + 5 个 Tab） |

## 附录 B：已知缺陷

| 编号 | 严重度 | 描述 | 位置 |
|------|--------|------|------|
| BUG-01 | 严重 | `publish_service.py:180` 引用 `task.cover_path`，但 Task ORM 模型无此属性，运行时会 AttributeError | `backend/services/publish_service.py:180` |
| BUG-02 | 中 | 删除视频时未删除物理文件（封面和音频已实现文件清理，视频未实现） | `backend/api/video.py:105-117` |
| BUG-03 | 中 | 删除商品时未检查关联的 Video/Copywriting，可能导致孤儿素材 | `backend/api/product.py:113-126` |
| BUG-04 | 低 | 封面列表 API 未返回 total 计数（返回 `list[CoverResponse]` 而非分页响应） | `backend/api/cover.py:61` |
| BUG-05 | 低 | 音频列表 API 未返回 total 计数（同上） | `backend/api/audio.py:58` |
