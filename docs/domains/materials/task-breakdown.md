# 素材管理 — 任务分解

> Version: 1.0.0 | Updated: 2026-04-07
> Source: docs/material-requirements.md
> Owner: Tech Lead

---

## 功能概述

素材管理是 DewuGoJin 的核心支撑模块，为任务组装和自动发布提供全部内容素材。基于需求分析文档，分三个 Phase 实施，共 17 个缺失功能点，分解为可执行的开发任务。

---

## Phase 1 — P0：发布链路打通

> 目标：修复发布链路断裂 + 打通素材入库通道
> 完成标志：用户可通过上传或扫描导入视频，组装任务后完整发布（含封面）

### 后端任务

#### BE-MAT-01: Task.cover_id FK 迁移 (M-09/M-17)

**描述**: Task 模型增加 `cover_id` FK 指向 covers 表，修复 publish_service 中 `task.cover_path` 引用不存在字段的 BUG-01。

**验收标准**:
- [ ] 新增迁移脚本 `migrations/008_task_cover_fk.py`（幂等）
- [ ] Task 模型增加 `cover_id = Column(Integer, ForeignKey("covers.id"), nullable=True)`
- [ ] Task 模型增加 `cover = relationship("Cover")`
- [ ] TaskResponse schema 增加 `cover_id: Optional[int]`
- [ ] `publish_service.py:180` 改为 `task.cover.file_path if task.cover else None`
- [ ] `publish_service.py:94` selectinload 增加 `selectinload(Task.cover)`
- [ ] `task_assembler.py` assemble 方法支持 cover_id 参数
- [ ] TaskCreate schema 增加 `cover_id: Optional[int]`

**估计**: 1d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/models/__init__.py` (Task 模型, L48-78)
- `backend/schemas/__init__.py` (TaskCreate/TaskResponse, L281-337)
- `backend/services/publish_service.py` (L94, L152-180)
- `backend/services/task_assembler.py` (L95-102)
- `backend/migrations/` (新增 008)

---

#### BE-MAT-02: 视频文件上传 API (M-01)

**描述**: 新增视频文件上传端点，接收文件并存储到 MATERIAL_BASE_PATH，自动创建 Video 记录。

**验收标准**:
- [ ] `POST /api/videos/upload` 接收 UploadFile + 可选 product_id
- [ ] 文件类型校验：video/mp4, video/quicktime
- [ ] 文件大小限制：500MB（可配置）
- [ ] 文件名清理：`Path(filename).name.replace("..", "")`
- [ ] 存储路径：`MATERIAL_BASE_PATH/{product_name}/` 或 `MATERIAL_BASE_PATH/uncategorized/`
- [ ] 自动填充 file_size
- [ ] 返回 VideoResponse

**估计**: 1d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/api/video.py` (新增 upload 端点)
- `backend/core/config.py` (MATERIAL_BASE_PATH)
- 参考模式: `backend/api/cover.py:25-58` (封面上传实现)

---

#### BE-MAT-03: 目录扫描导入 API (M-02)

**描述**: 新增扫描导入端点，扫描 MATERIAL_BASE_PATH 下子目录，按商品名批量导入视频。

**验收标准**:
- [ ] `POST /api/videos/scan` 触发扫描
- [ ] 扫描 MATERIAL_BASE_PATH 一级子目录（子目录名 = 商品名）
- [ ] 识别 .mp4/.mov 文件为视频素材
- [ ] 自动创建或匹配已有 Product（按名称 UNIQUE 约束）
- [ ] 基于 file_path 去重（已存在的跳过）
- [ ] 批量 INSERT（非逐条提交）
- [ ] 返回导入统计：`{ total_scanned, new_imported, skipped, failed, details[] }`

**估计**: 1.5d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/api/video.py` (新增 scan 端点)
- `backend/api/product.py` (复用 Product 创建逻辑)
- `backend/core/config.py` (MATERIAL_BASE_PATH)

---

### 前端任务

#### FE-MAT-01: 视频上传组件 (M-01)

**描述**: VideoTab 增加文件上传功能，替代手动输入路径。

**验收标准**:
- [ ] Upload 组件支持选择 .mp4/.mov 文件
- [ ] 上传时可选关联商品（Select）
- [ ] 上传进度展示
- [ ] 上传成功后自动刷新列表
- [ ] 保留手动添加入口（兼容）

**估计**: 1d
**负责人**: Frontend Lead
**依赖**: BE-MAT-02
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (VideoTab, L175-301)
- `frontend/src/hooks/useVideo.ts` (新增 useUploadVideo)
- 参考模式: `frontend/src/pages/Material.tsx` CoverTab Upload 实现 (L443-452)

---

#### FE-MAT-02: 扫描导入按钮与结果展示 (M-02)

**描述**: VideoTab 增加"扫描导入"按钮，调用后端扫描 API，展示导入结果。

**验收标准**:
- [ ] "扫描导入"按钮，点击后调用 `POST /api/videos/scan`
- [ ] Loading 状态展示
- [ ] 导入完成后展示统计结果（Modal 或 Notification）
- [ ] 自动刷新视频列表

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-MAT-03
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (VideoTab)
- `frontend/src/hooks/useVideo.ts` (新增 useScanVideos)

---

#### FE-MAT-03: Task 表单支持 cover_id (M-09)

**描述**: 任务创建/编辑表单增加封面选择。

**验收标准**:
- [ ] 任务创建表单增加封面 Select（从 covers 列表选择）
- [ ] TaskAssemble 流程支持传入 cover_id

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-MAT-01
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Task.tsx`
- `frontend/src/hooks/useTask.ts`
- `frontend/src/hooks/useCover.ts`

---

### 集成任务

#### INT-MAT-01: Phase 1 端到端验证

**描述**: 验证完整链路：视频上传/扫描 → 任务组装（含封面）→ 发布执行。

**验收标准**:
- [ ] 上传视频 → 创建任务（含 video_id + cover_id）→ publish_task 不报错
- [ ] 扫描导入 → 自动关联商品 → 组装任务 → 发布读取正确素材路径
- [ ] cover_path 正确传递到 DewuClient.upload_video

**估计**: 0.5d
**负责人**: QA Lead
**依赖**: BE-MAT-01, BE-MAT-02, BE-MAT-03, FE-MAT-01, FE-MAT-02, FE-MAT-03
**类型**: both

---

## Phase 2 — P1：体验完善

### 后端任务

#### BE-MAT-04: FFprobe 元数据提取 (M-03)

**描述**: 视频上传/导入时自动调用 FFprobe 提取元数据。

**验收标准**:
- [ ] 工具函数 `extract_video_metadata(file_path) -> dict` 返回 duration, width, height, file_size
- [ ] 上传端点和扫描端点调用此函数自动填充
- [ ] FFprobe 不可用时 graceful fallback（仅填充 file_size）
- [ ] 异步执行，不阻塞请求

**估计**: 1d
**负责人**: Backend Lead (委托 Automation Developer)
**依赖**: BE-MAT-02
**类型**: backend

**关键文件**:
- `backend/services/ai_clip_service.py` (已有 FFprobe 调用模式可参考)
- `backend/api/video.py`

---

#### BE-MAT-05: 文件存在性校验 API (M-04)

**描述**: 视频列表 API 增加文件存在性标记。

**验收标准**:
- [ ] VideoResponse 增加 `file_exists: bool` 字段
- [ ] 列表查询时批量检查文件是否存在
- [ ] 新增 `POST /api/videos/validate` 批量校验端点

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/api/video.py`
- `backend/schemas/__init__.py` (VideoResponse)

---

#### BE-MAT-06: 文案批量导入 API (M-06)

**描述**: 新增文案批量导入端点，从文本文件导入。

**验收标准**:
- [ ] `POST /api/copywritings/import` 接收 UploadFile (.txt)
- [ ] 一行一条文案，空行跳过
- [ ] 可选关联 product_id
- [ ] 返回导入统计

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/api/copywriting.py`

---

#### BE-MAT-07: 视频删除时清理物理文件 (BUG-02)

**描述**: 修复视频删除时未删除物理文件的问题。

**验收标准**:
- [ ] 删除视频时同步删除物理文件（参考 cover/audio 的实现）
- [ ] 文件不存在时 warning 日志，不阻塞删除

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/api/video.py:105-117`
- 参考: `backend/api/cover.py:80-101`, `backend/api/audio.py:71-92`

---

#### BE-MAT-08: 删除前引用检查 (BUG-03)

**描述**: 删除素材/商品前检查是否被 Task 引用。

**验收标准**:
- [ ] 删除视频前检查 Task.video_id 引用
- [ ] 删除文案前检查 Task.copywriting_id 引用
- [ ] 删除商品前检查关联的 Video/Copywriting
- [ ] 有引用时返回 409 Conflict + 引用详情

**估计**: 1d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/api/video.py`, `backend/api/copywriting.py`, `backend/api/product.py`

---

### 前端任务

#### FE-MAT-04: 文案编辑入口 (M-07)

**描述**: CopywritingTab 增加编辑按钮和编辑弹窗。

**验收标准**:
- [ ] 表格操作列增加"编辑"按钮
- [ ] 编辑弹窗预填充当前内容和商品
- [ ] 调用 `PUT /api/copywritings/{id}`
- [ ] 编辑成功后刷新列表

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: 无（后端 PUT 已有）
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (CopywritingTab, L311-432)
- `frontend/src/hooks/useCopywriting.ts` (新增 useUpdateCopywriting)

---

#### FE-MAT-05: 商品编辑入口 (M-12)

**描述**: ProductSection 增加编辑功能。

**验收标准**:
- [ ] 商品卡片增加"编辑"按钮
- [ ] 编辑弹窗预填充当前名称和链接
- [ ] 调用 `PUT /api/products/{id}`

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: 无（后端 PUT 已有）
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (ProductSection, L66-165)
- `frontend/src/hooks/useProduct.ts`

---

#### FE-MAT-06: 批量删除 (M-15)

**描述**: 各素材 Tab 支持多选批量删除。

**验收标准**:
- [ ] Table 增加 rowSelection
- [ ] 选中后显示"批量删除"按钮 + 选中数量
- [ ] 确认弹窗后逐个调用 DELETE（或后端新增批量删除端点）
- [ ] 适用于: VideoTab, CopywritingTab, CoverTab, AudioTab, TopicTab

**估计**: 1d
**负责人**: Frontend Lead
**依赖**: 无
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (所有 Tab)

---

#### FE-MAT-07: 文案批量导入入口 (M-06)

**描述**: CopywritingTab 增加"批量导入"按钮。

**验收标准**:
- [ ] Upload 组件接受 .txt 文件
- [ ] 调用 `POST /api/copywritings/import`
- [ ] 展示导入结果

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-MAT-06
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (CopywritingTab)

---

#### FE-MAT-08: 文件存在性标记 (M-04)

**描述**: VideoTab 表格展示文件存在性状态。

**验收标准**:
- [ ] 文件存在显示绿色标记，不存在显示红色警告
- [ ] 不存在时 Tooltip 提示"文件缺失"

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-MAT-05
**类型**: frontend

**关键文件**:
- `frontend/src/pages/Material.tsx` (VideoTab columns)

---

## Phase 3 — P2：增强功能

### 后端任务

#### BE-MAT-09: 视频去重 (M-05)

**描述**: 基于 SHA-256 file_hash 检测重复视频。

**验收标准**:
- [ ] 上传/导入时计算 file_hash
- [ ] 已存在相同 hash 时返回提示（不阻塞，可选跳过或覆盖）

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: BE-MAT-04
**类型**: backend

---

#### BE-MAT-10: 封面自动提取 (M-08)

**描述**: 从视频指定时间点截取封面图。

**验收标准**:
- [ ] `POST /api/covers/extract` 接收 video_id + timestamp
- [ ] FFmpeg 截取指定帧，保存为 JPEG
- [ ] 自动创建 Cover 记录并关联 video_id

**估计**: 1d
**负责人**: Automation Developer
**依赖**: 无
**类型**: backend

**关键文件**:
- `backend/services/ai_clip_service.py` (已有 FFmpeg 封面处理逻辑可参考)

---

#### BE-MAT-11: 音频元数据提取 (M-10)

**描述**: 音频上传时 FFprobe 提取时长。

**验收标准**:
- [ ] 上传音频后自动填充 duration 字段

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: BE-MAT-04 (复用 FFprobe 工具函数)
**类型**: backend

---

#### BE-MAT-12: 得物链接解析 (M-13)

**描述**: 从得物商品 URL 自动提取商品名称和图片。

**验收标准**:
- [ ] `POST /api/products/parse-url` 接收得物 URL
- [ ] 解析页面提取商品名称、图片 URL
- [ ] 返回解析结果，用户确认后创建商品

**估计**: 1.5d
**负责人**: Automation Developer
**依赖**: 无
**类型**: backend

---

#### BE-MAT-13: 素材统计 API (M-14)

**描述**: 新增素材统计端点。

**验收标准**:
- [ ] `GET /api/materials/stats` 返回各类素材数量
- [ ] 包含：视频数、文案数、封面数、音频数、话题数、商品数
- [ ] 商品覆盖率（有视频的商品 / 总商品）
- [ ] 无素材商品列表

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

---

#### BE-MAT-14: 全文搜索 (M-16)

**描述**: 视频名称和文案内容搜索。

**验收标准**:
- [ ] `GET /api/videos?keyword=` 按名称模糊搜索
- [ ] `GET /api/copywritings?keyword=` 按内容模糊搜索

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: 无
**类型**: backend

---

### 前端任务

#### FE-MAT-09: 话题批量删除 (M-11)

**描述**: TopicTab 支持多选批量删除。

**验收标准**:
- [ ] Table rowSelection + 批量删除按钮

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: 无
**类型**: frontend

---

#### FE-MAT-10: 素材统计仪表盘 (M-14)

**描述**: Material 页面顶部增加统计卡片。

**验收标准**:
- [ ] 展示各类素材数量
- [ ] 商品覆盖率进度条
- [ ] 无素材商品提醒

**估计**: 1d
**负责人**: Frontend Lead
**依赖**: BE-MAT-13
**类型**: frontend

---

#### FE-MAT-11: 封面自动提取入口 (M-08)

**描述**: CoverTab 增加"从视频提取"功能。

**验收标准**:
- [ ] 选择视频 + 输入时间点
- [ ] 调用提取 API，展示结果

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-MAT-10
**类型**: frontend

---

#### FE-MAT-12: 全文搜索入口 (M-16)

**描述**: VideoTab 和 CopywritingTab 增加搜索框。

**验收标准**:
- [ ] Input.Search 组件
- [ ] 输入关键词后筛选列表

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-MAT-14
**类型**: frontend

---

## 任务汇总

### Phase 1 — P0

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| BE-MAT-01 | Task.cover_id FK 迁移 | Backend Lead | 1d | — | BE |
| BE-MAT-02 | 视频文件上传 API | Backend Lead | 1d | — | BE |
| BE-MAT-03 | 目录扫描导入 API | Backend Lead | 1.5d | — | BE |
| FE-MAT-01 | 视频上传组件 | Frontend Lead | 1d | BE-MAT-02 | FE |
| FE-MAT-02 | 扫描导入按钮 | Frontend Lead | 0.5d | BE-MAT-03 | FE |
| FE-MAT-03 | Task 封面选择 | Frontend Lead | 0.5d | BE-MAT-01 | FE |
| INT-MAT-01 | 端到端验证 | QA Lead | 0.5d | 全部 P0 | both |

**Phase 1 小计**: 6d | 缓冲后: 7.5d (~8d)

### Phase 2 — P1

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| BE-MAT-04 | FFprobe 元数据提取 | Backend Lead | 1d | BE-MAT-02 | BE |
| BE-MAT-05 | 文件存在性校验 | Backend Lead | 0.5d | — | BE |
| BE-MAT-06 | 文案批量导入 API | Backend Lead | 0.5d | — | BE |
| BE-MAT-07 | 视频删除清理文件 | Backend Lead | 0.5d | — | BE |
| BE-MAT-08 | 删除前引用检查 | Backend Lead | 1d | — | BE |
| FE-MAT-04 | 文案编辑入口 | Frontend Lead | 0.5d | — | FE |
| FE-MAT-05 | 商品编辑入口 | Frontend Lead | 0.5d | — | FE |
| FE-MAT-06 | 批量删除 | Frontend Lead | 1d | — | FE |
| FE-MAT-07 | 文案批量导入入口 | Frontend Lead | 0.5d | BE-MAT-06 | FE |
| FE-MAT-08 | 文件存在性标记 | Frontend Lead | 0.5d | BE-MAT-05 | FE |

**Phase 2 小计**: 6.5d | 缓冲后: 8d

### Phase 3 — P2

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| BE-MAT-09 | 视频去重 | Backend Lead | 0.5d | BE-MAT-04 | BE |
| BE-MAT-10 | 封面自动提取 | Automation Dev | 1d | — | BE |
| BE-MAT-11 | 音频元数据提取 | Backend Lead | 0.5d | BE-MAT-04 | BE |
| BE-MAT-12 | 得物链接解析 | Automation Dev | 1.5d | — | BE |
| BE-MAT-13 | 素材统计 API | Backend Lead | 0.5d | — | BE |
| BE-MAT-14 | 全文搜索 | Backend Lead | 0.5d | — | BE |
| FE-MAT-09 | 话题批量删除 | Frontend Lead | 0.5d | — | FE |
| FE-MAT-10 | 素材统计仪表盘 | Frontend Lead | 1d | BE-MAT-13 | FE |
| FE-MAT-11 | 封面提取入口 | Frontend Lead | 0.5d | BE-MAT-10 | FE |
| FE-MAT-12 | 全文搜索入口 | Frontend Lead | 0.5d | BE-MAT-14 | FE |

**Phase 3 小计**: 7d | 缓冲后: 8.5d (~9d)

---

## 总计

| Phase | 任务数 | 原始估计 | 缓冲后 |
|-------|--------|---------|--------|
| Phase 1 (P0) | 7 | 6d | 8d |
| Phase 2 (P1) | 10 | 6.5d | 8d |
| Phase 3 (P2) | 10 | 7d | 9d |
| **合计** | **27** | **19.5d** | **25d** |

---

## 依赖关系图

```
Phase 1 (并行启动):
  BE-MAT-01 ──────────────────────► FE-MAT-03
  BE-MAT-02 ──────────────────────► FE-MAT-01
  BE-MAT-03 ──────────────────────► FE-MAT-02
  FE-MAT-01 + FE-MAT-02 + FE-MAT-03 ──► INT-MAT-01

Phase 2 (Phase 1 完成后):
  BE-MAT-02 ──► BE-MAT-04 (FFprobe)
  BE-MAT-04 ──► Phase 3 BE-MAT-09, BE-MAT-11
  BE-MAT-05 ──► FE-MAT-08
  BE-MAT-06 ──► FE-MAT-07
  FE-MAT-04, FE-MAT-05, FE-MAT-06 无依赖可并行

Phase 3 (Phase 2 完成后):
  BE-MAT-13 ──► FE-MAT-10
  BE-MAT-10 ──► FE-MAT-11
  BE-MAT-14 ──► FE-MAT-12
  其余无依赖可并行
```

---

## 风险与注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| cover_id 迁移影响现有数据 | 已有 Task 的 cover_id 为 NULL | 迁移脚本设 nullable=True，渐进迁移 |
| 大文件上传超时 | 视频文件可能 > 200MB | 配置 Nginx/FastAPI 上传限制，考虑分片上传 |
| FFprobe 不可用 | 元数据无法提取 | graceful fallback，仅填充 file_size |
| 中文路径编码 | Windows 下路径编码问题 | 使用 pathlib.Path，避免 os.path 字符串拼接 |
| 扫描大量文件性能 | 1000+ 文件扫描耗时 | 批量 INSERT + 异步执行 + 进度反馈 |
