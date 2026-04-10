# 素材管理需求分析与领域建模

## Context

用户要求以需求分析师视角，对"素材管理"子系统进行完整的需求分析和领域建模。素材管理是 DewuGoJin 系统的核心支撑模块，为下游的任务组装和自动发布提供所有内容素材。

本文档基于对现有代码的完整分析，梳理已实现功能、识别缺失需求、建立领域模型。

---

## 1. 业务背景与目标

素材管理服务于得物平台自动化视频发布场景。用户（内容创作者）需要：
- 管理大量视频、文案、封面、音频素材
- 按商品维度组织素材，实现"一个商品对应一套素材"
- 管理话题（得物平台标签），提升内容曝光
- 素材最终被"任务"引用，由发布引擎自动上传到得物平台

**核心价值**: 素材是发布的"弹药库"，素材管理的完整性直接决定发布成功率。

---

## 2. 领域模型

### 2.1 实体关系图 (ER)

```
┌──────────┐
│ Product  │ (商品 — 素材的组织维度)
│──────────│
│ id (PK)  │
│ name     │
│ link     │
│ dewu_url │
│ image_url│
└────┬─────┘
     │ 1:N
     ├──────────────────────┐
     │                      │
     ▼                      ▼
┌──────────┐         ┌─────────────┐
│  Video   │         │ Copywriting │
│──────────│         │─────────────│
│ id (PK)  │         │ id (PK)     │
│ product_id (FK)    │ product_id (FK)
│ name     │         │ content     │
│ file_path│         │ source_type │
│ file_size│         │ source_ref  │
│ duration │         └─────────────┘
│ width    │
│ height   │
│ file_hash│
│ source_type│
└────┬─────┘
     │ 1:N
     ▼
┌──────────┐
│  Cover   │
│──────────│
│ id (PK)  │
│ video_id (FK)
│ file_path│
│ file_size│
│ width    │
│ height   │
└──────────┘

┌──────────┐         ┌──────────┐
│  Audio   │         │  Topic   │
│──────────│         │──────────│
│ id (PK)  │         │ id (PK)  │
│ name     │         │ name (UQ)│
│ file_path│         │ heat     │
│ file_size│         │ source   │
│ duration │         │last_synced│
└──────────┘         └──────────┘

                     ┌───────────────┐
                     │  TaskTopic    │ (M:N 关联)
                     │───────────────│
                     │ task_id (FK)  │
                     │ topic_id (FK) │
                     └───────────────┘

下游消费:
┌──────────┐
│   Task   │ ← 引用 video_id, copywriting_id, audio_id, product_id
│──────────│   + topics (M:N via task_topics)
│ → 发布引擎 → DewuClient.upload_video(video_path, content, topic, cover_path, product_link)
└──────────┘
```

### 2.2 聚合根与边界

| 聚合根 | 包含实体 | 边界说明 |
|--------|---------|---------|
| Product | Product | 商品是素材的组织维度，独立生命周期 |
| Video | Video → Cover[] | 视频拥有封面，删除视频应级联删除封面 |
| Copywriting | Copywriting | 文案独立，通过 product_id 松耦合 |
| Audio | Audio | 音频独立，无 FK 依赖 |
| Topic | Topic | 话题独立，通过 TaskTopic 与任务关联 |

### 2.3 值对象

| 值对象 | 属性 | 说明 |
|--------|------|------|
| FileMetadata | file_path, file_size, duration, width, height, file_hash | 文件物理属性 |
| SourceInfo | source_type, source_ref | 素材来源追踪 (manual/ai_clip/import/search) |

---

## 3. 功能需求清单

### 3.1 已实现功能 (现状)

| 模块 | 功能 | 后端 | 前端 | 状态 |
|------|------|------|------|------|
| **商品** | CRUD | `api/product.py` | ProductSection | ✅ 完整 |
| **商品** | 名称搜索 | `GET /products?name=` | — | ✅ 后端有 |
| **视频** | CRUD | `api/video.py` | VideoTab | ✅ 完整 |
| **视频** | 按商品筛选 | `GET /videos?product_id=` | Select 筛选 | ✅ 完整 |
| **文案** | CRUD | `api/copywriting.py` | CopywritingTab | ✅ 完整 |
| **文案** | 按商品/来源筛选 | `GET /copywritings?product_id=&source_type=` | 商品筛选 | ✅ 完整 |
| **封面** | 上传/列表/删除 | `api/cover.py` | CoverTab | ✅ 完整 |
| **封面** | 按视频筛选 | `GET /covers?video_id=` | Input 筛选 | ✅ 完整 |
| **音频** | 上传/列表/删除 | `api/audio.py` | AudioTab | ✅ 完整 |
| **话题** | CRUD | `api/topic.py` | TopicTab | ✅ 完整 |
| **话题** | 得物搜索入库 | `GET /topics/search?keyword=` | 搜索卡片 | ✅ 完整 |
| **话题** | 全局话题设置 | `PUT/GET /topics/global` | 全局话题弹窗 | ✅ 完整 |
| **任务组装** | 自动匹配文案+话题 | `TaskAssembler` | — | ✅ 完整 |

### 3.2 缺失/待完善功能

| 编号 | 模块 | 功能 | 优先级 | 说明 |
|------|------|------|--------|------|
| M-01 | 视频 | 文件上传 (非手动填路径) | P0 | 当前只能手动输入 file_path，无真正的文件上传 |
| M-02 | 视频 | 目录扫描导入 | P0 | MATERIAL_BASE_PATH 下按商品子目录扫描，批量入库 |
| M-03 | 视频 | FFprobe 自动提取元数据 | P1 | 上传/导入时自动填充 duration, width, height, file_size, file_hash |
| M-04 | 视频 | 文件存在性校验 | P1 | 列表展示时标记文件是否存在，发布前校验 |
| M-05 | 视频 | 重复检测 (file_hash) | P2 | 基于 SHA-256 去重，避免同一视频多次入库 |
| M-06 | 文案 | 批量导入 (文本文件) | P1 | 从 .txt 文件批量导入文案，一行一条 |
| M-07 | 文案 | 编辑功能 | P1 | 前端缺少编辑入口（后端 PUT 已有） |
| M-08 | 封面 | 从视频自动提取 | P2 | 调用 FFmpeg 从视频指定时间点截取封面 |
| M-09 | 封面 | 与任务关联 | P1 | Task 模型缺少 cover_id FK，publish_service 仍用旧的 task.cover_path |
| M-10 | 音频 | 元数据提取 (duration) | P2 | 上传时 FFprobe 提取时长 |
| M-11 | 话题 | 批量删除 | P2 | 前端无批量操作 |
| M-12 | 商品 | 编辑功能 | P1 | 前端缺少编辑入口（后端 PUT 已有） |
| M-13 | 商品 | 得物链接解析 | P2 | 从得物 URL 自动提取商品名称和图片 |
| M-14 | 全局 | 素材统计仪表盘 | P2 | 各类素材数量、商品覆盖率、无素材商品提醒 |
| M-15 | 全局 | 批量删除 | P1 | 各 Tab 支持多选批量删除 |
| M-16 | 全局 | 关键词搜索 | P2 | 视频名称、文案内容全文搜索 |
| M-17 | 发布链路 | cover_id FK 迁移 | P1 | Task.cover_path (旧) → Task.cover_id (FK to covers) |

---

## 4. 用例模型

### 4.1 核心用例图

```
                    ┌─────────────────────────────────────┐
                    │          素材管理子系统               │
                    │                                     │
  ┌──────┐         │  UC-01: 管理商品                     │
  │      │────────►│  UC-02: 管理视频素材                  │
  │      │         │    UC-02a: 手动添加视频               │
  │ 用户  │         │    UC-02b: 目录扫描导入 [待实现]      │
  │      │         │    UC-02c: 文件上传 [待实现]          │
  │      │────────►│  UC-03: 管理文案                     │
  │      │         │    UC-03a: 手动添加文案               │
  │      │         │    UC-03b: 批量导入文案 [待实现]      │
  │      │────────►│  UC-04: 管理封面                     │
  │      │         │  UC-05: 管理音频                     │
  │      │────────►│  UC-06: 管理话题                     │
  │      │         │    UC-06a: 手动添加话题               │
  └──────┘         │    UC-06b: 搜索得物话题               │
                    │    UC-06c: 设置全局话题               │
       ┌──────┐    │                                     │
       │任务   │◄───│  UC-07: 素材→任务组装                │
       │组装器 │    │                                     │
       └──────┘    └─────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    发布引擎        │
                    │ 消费: video_path,  │
                    │ content, topic,    │
                    │ cover_path,        │
                    │ product_link       │
                    └───────────────────┘
```

### 4.2 关键用例详述

**UC-02b: 目录扫描导入 (待实现, P0)**

| 项 | 内容 |
|----|------|
| 触发 | 用户点击"扫描导入" |
| 前置 | MATERIAL_BASE_PATH 已配置 |
| 主流程 | 1. 扫描 MATERIAL_BASE_PATH 下子目录 (子目录名=商品名) |
|        | 2. 每个子目录下的 .mp4/.mov 文件作为视频 |
|        | 3. 自动创建/匹配 Product |
|        | 4. FFprobe 提取元数据 |
|        | 5. file_hash 去重，跳过已存在的视频 |
|        | 6. 批量入库，返回导入统计 |
| 后置 | 视频已入库并关联到对应商品 |
| 异常 | 文件损坏 → 跳过并记录; 商品名冲突 → 复用已有商品 |

**UC-09 (M-09): cover_id FK 迁移**

| 项 | 内容 |
|----|------|
| 现状 | publish_service.py:180 仍引用 `task.cover_path` (旧字段) |
| 目标 | Task 增加 `cover_id` FK → covers 表 |
| 影响 | publish_service, task_assembler, 前端 Task 页面 |

---

## 5. 状态模型

### 5.1 素材生命周期

```
                ┌─────────┐
                │ Created │ (入库)
                └────┬────┘
                     │
              ┌──────▼──────┐
              │  Available  │ (可用 — 文件存在, 元数据完整)
              └──────┬──────┘
                     │ 被 Task 引用
              ┌──────▼──────┐
              │  In Use     │ (被任务引用中)
              └──────┬──────┘
                     │ 任务完成/删除
              ┌──────▼──────┐
              │  Available  │ (可复用)
              └──────┬──────┘
                     │ 用户删除
              ┌──────▼──────┐
              │  Deleted    │ (DB记录+文件删除)
              └─────────────┘

异常状态:
  File Missing — 文件被外部删除，DB记录仍在
  Orphaned — 无任何 Product 关联的素材
```

### 5.2 话题生命周期

```
  manual 创建 ──► 话题库 ◄── search 搜索入库
                    │
                    ├── 被选为全局话题 → PublishConfig.global_topic_ids
                    ├── 被任务引用 → TaskTopic
                    └── 删除
```

---

## 6. 数据流

### 6.1 素材 → 发布 完整链路

```
素材入库                    任务组装                      发布执行
────────                   ────────                     ────────
Video ──────────┐
                ├─► TaskAssembler.assemble() ──► Task ──► PublishService
Copywriting ────┤     auto_match by product_id     │      .publish_task()
                │                                  │         │
Product ────────┤     (提供 product.link)           │         ▼
                │                                  │    DewuClient
Audio ──────────┘                                  │    .upload_video(
                                                   │      video_path,
Topic ──► GlobalTopics ──► TaskTopic ──────────────┘      content,
                                                          topic,
Cover ──► (目前断裂: task.cover_path 旧字段) ──────────►   cover_path,
                                                          product_link)
```

### 6.2 目录结构约定 (MATERIAL_BASE_PATH)

```
D:/系统/桌面/得物剪辑/待上传数据/
├── 商品A/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── cover/
│       └── video1_cover.jpg
├── 商品B/
│   └── video3.mp4
├── audio/          ← 全局音频目录
│   └── bgm1.mp3
└── cover/          ← 全局封面目录 (上传封面存储位置)
    └── uploaded_cover.jpg
```

---

## 7. 非功能需求

| 类别 | 要求 |
|------|------|
| 性能 | 扫描导入支持 1000+ 文件，使用批量 INSERT |
| 文件安全 | 路径校验防止目录遍历 (`..` 检测) |
| 数据一致性 | 删除素材时同步删除物理文件 + DB 记录 |
| 引用完整性 | 删除被任务引用的素材时提示用户 |
| 幂等性 | 扫描导入基于 file_hash 去重，重复执行安全 |
| 编码 | 支持中文文件名和路径 |

---

## 8. 实施优先级建议

### Phase 1 — P0 (发布链路打通)
- M-01: 视频文件上传
- M-02: 目录扫描导入
- M-09/M-17: cover_id FK 迁移，修复发布链路断裂

### Phase 2 — P1 (体验完善)
- M-03: FFprobe 元数据提取
- M-04: 文件存在性校验
- M-06: 文案批量导入
- M-07: 文案编辑入口
- M-12: 商品编辑入口
- M-15: 批量删除

### Phase 3 — P2 (增强)
- M-05: 视频去重
- M-08: 封面自动提取
- M-10: 音频元数据
- M-11: 话题批量删除
- M-13: 得物链接解析
- M-14: 素材统计仪表盘
- M-16: 全文搜索

---

## 关键文件索引

| 文件 | 角色 |
|------|------|
| `backend/models/__init__.py` | 所有 ORM 模型定义 |
| `backend/schemas/__init__.py` | 所有 Pydantic Schema |
| `backend/api/video.py` | 视频 API |
| `backend/api/copywriting.py` | 文案 API |
| `backend/api/cover.py` | 封面 API |
| `backend/api/audio.py` | 音频 API |
| `backend/api/topic.py` | 话题 API |
| `backend/api/product.py` | 商品 API |
| `backend/services/task_assembler.py` | 任务组装器 (素材消费方) |
| `backend/services/publish_service.py` | 发布服务 (素材最终消费方, L152-180) |
| `backend/core/dewu_client.py` | 得物客户端 upload_video (L553) |
| `frontend/src/pages/Material.tsx` | 素材管理前端页面 (893行) |
| `backend/core/config.py` | MATERIAL_BASE_PATH 配置 |
