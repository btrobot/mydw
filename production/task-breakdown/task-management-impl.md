# 任务管理领域模型实施 — 任务分解

> 创建日期: 2026-04-09
> 基于: docs/task-management-domain-model.md (v2.1)

---

## Phase 1: 数据模型

### BE-TM-01: 创建 publish_profiles 表

**描述**: 新建 migration 创建 publish_profiles 表，更新 SQLAlchemy 模型和 Pydantic schema

**验收标准**:
- [ ] migration 脚本创建 publish_profiles 表（所有字段按设计文档）
- [ ] SQLAlchemy PublishProfile 模型定义
- [ ] Pydantic PublishProfileCreate / PublishProfileUpdate / PublishProfileResponse schema
- [ ] 系统启动时自动创建默认 Profile（is_default=True, composition_mode='none'）

**负责人**: Backend Lead
**类型**: backend
**依赖**: 无

---

### BE-TM-02: 创建 composition_jobs 表

**描述**: 新建 migration 创建 composition_jobs 表，更新 SQLAlchemy 模型和 Pydantic schema

**验收标准**:
- [ ] migration 脚本创建 composition_jobs 表
- [ ] SQLAlchemy CompositionJob 模型定义
- [ ] Pydantic CompositionJobResponse schema
- [ ] Task → CompositionJob 关系定义（1:N）

**负责人**: Backend Lead
**类型**: backend
**依赖**: 无

---

### BE-TM-03: 创建 schedule_config 表并迁移数据

**描述**: 创建 schedule_config 表替代 publish_config，迁移现有数据，去掉 global_topic_ids 字段

**验收标准**:
- [ ] migration 脚本创建 schedule_config 表
- [ ] 从 publish_config 迁移现有数据
- [ ] SQLAlchemy ScheduleConfig 模型定义
- [ ] 更新 Pydantic schema（ScheduleConfigRequest / ScheduleConfigResponse）

**负责人**: Backend Lead
**类型**: backend
**依赖**: 无

---

### BE-TM-04: Task 表新增字段

**描述**: Task 表新增 profile_id、batch_id、failed_at_status 字段，激活 migration 016 已有的合成相关字段

**验收标准**:
- [ ] migration 脚本新增 profile_id（FK）、batch_id（VARCHAR）、failed_at_status（VARCHAR）
- [ ] 更新 SQLAlchemy Task 模型（新增字段 + 关系）
- [ ] 更新 Pydantic TaskCreate / TaskUpdate / TaskResponse schema
- [ ] 确认 migration 016 的字段（source_video_ids, composition_job_id, final_video_path 等）在模型中可用

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-01, BE-TM-02

---

## Phase 2: 状态机 + 调度器

### BE-TM-05: 实现新状态机

**描述**: 实现 7 状态枚举，更新 TaskService 的状态转换逻辑

**验收标准**:
- [ ] TaskStatus 枚举（draft, composing, ready, uploading, uploaded, failed, cancelled）
- [ ] 创建任务时根据 Profile.composition_mode 设置初始状态（none→ready, 其他→draft）
- [ ] 状态转换校验（只允许合法转换）
- [ ] 取消操作（任何非终态→cancelled）

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-04

---

### BE-TM-06: 实现快速重试和编辑重试

**描述**: 实现两种重试模式，利用 failed_at_status 字段

**验收标准**:
- [ ] 标记失败时记录 failed_at_status
- [ ] 快速重试 API：failed → failed_at_status 对应状态，retry_count += 1
- [ ] 编辑重试 API：failed → draft，清空 failed_at_status
- [ ] 重试次数校验（不超过 Profile.max_retry_count）

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-05

---

### BE-TM-07: 重构 UploadScheduler

**描述**: 重构现有 scheduler.py，改为单循环，从 status=ready 取任务，读 ScheduleConfig

**验收标准**:
- [ ] 单循环设计（去掉现有双循环）
- [ ] 从 status=ready 取任务（替代 pending）
- [ ] 从 schedule_config 表读取调度参数
- [ ] 上传成功：task.status=uploaded
- [ ] 上传失败：记录 failed_at_status=uploading，task.status=failed

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-05, BE-TM-03

---

### FE-TM-01: 前端状态标签更新

**描述**: 更新前端 Task 页面的状态显示，适配 7 状态枚举

**验收标准**:
- [ ] statusMap 更新为 7 个状态的中文标签和颜色
- [ ] 统计卡片适配新状态（draft, composing, ready, uploading, uploaded, failed, cancelled）
- [ ] 任务列表筛选器适配新状态
- [ ] 重试按钮（快速重试 + 编辑重试）
- [ ] 取消按钮

**负责人**: Frontend Lead
**类型**: frontend
**依赖**: BE-TM-05, BE-TM-06

---

## Phase 3: Profile 管理

### BE-TM-08: PublishProfile CRUD API

**描述**: 实现 PublishProfile 的完整 CRUD 端点

**验收标准**:
- [ ] POST /api/profiles — 创建配置档
- [ ] GET /api/profiles — 列表查询
- [ ] GET /api/profiles/{id} — 详情
- [ ] PUT /api/profiles/{id} — 更新
- [ ] DELETE /api/profiles/{id} — 删除（不允许删除 is_default）
- [ ] PUT /api/profiles/{id}/set-default — 设为默认
- [ ] resolve_profile() 解析逻辑

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-01

---

### BE-TM-09: TaskAssembler / TaskDistributor 接入 Profile

**描述**: 重构任务组装和分配逻辑，接受 profile_id 参数

**验收标准**:
- [ ] TaskAssembler.assemble() 接受 profile_id，从 Profile 读取 global_topic_ids
- [ ] TaskDistributor.distribute() 传递 profile_id
- [ ] 创建任务时根据 Profile.composition_mode 设置初始状态
- [ ] 更新 AssembleTasksRequest schema 增加 profile_id 字段

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-05, BE-TM-08

---

### FE-TM-02: Profile 管理页面

**描述**: 在 Settings 页面新增 Profile 管理区域

**验收标准**:
- [ ] Profile 列表展示（名称、合成方式、是否默认）
- [ ] 创建 / 编辑 Profile 表单（composition_mode, coze_workflow_id, global_topic_ids, 重试配置）
- [ ] 删除 Profile（默认配置不可删除）
- [ ] 设为默认操作

**负责人**: Frontend Lead
**类型**: frontend
**依赖**: BE-TM-08

---

### FE-TM-03: 组装弹窗增加 Profile 选择

**描述**: 任务组装弹窗增加 Profile 下拉选择

**验收标准**:
- [ ] Profile 下拉选择器（默认选中 is_default 的 Profile）
- [ ] 选择后显示合成方式提示
- [ ] 提交时传递 profile_id

**负责人**: Frontend Lead
**类型**: frontend
**依赖**: BE-TM-09, FE-TM-02

---

## Phase 4: Coze 合成集成

### BE-TM-10: CozeClient 封装

**描述**: 实现 Coze API 客户端封装

**验收标准**:
- [ ] backend/core/coze_client.py
- [ ] AsyncCoze 初始化（从 config 读取 COZE_API_TOKEN, COZE_API_BASE）
- [ ] upload_file(file_path) → file_id
- [ ] submit_composition(workflow_id, parameters) → execute_id
- [ ] check_status(workflow_id, execute_id) → (status, output)
- [ ] config.py 新增 COZE_* 配置项

**负责人**: Backend Lead
**类型**: backend
**依赖**: 无

---

### BE-TM-11: CompositionService

**描述**: 实现合成任务的提交和结果处理

**验收标准**:
- [ ] submit_composition(task_id) — 上传素材 → 提交工作流 → 创建 CompositionJob → task.status=composing
- [ ] handle_success(job) — 下载视频 → 更新 CompositionJob → task.status=ready
- [ ] handle_failure(job) — 更新 CompositionJob → task.failed_at_status=composing → task.status=failed
- [ ] batch_submit_composition(task_ids) — 批量提交

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-10, BE-TM-05, BE-TM-02

---

### BE-TM-12: CompositionPoller

**描述**: 实现后台轮询服务，定期查询 Coze 合成状态

**验收标准**:
- [ ] 单循环设计，系统启动时自动启动
- [ ] 轮询间隔从 COZE_POLL_INTERVAL 读取（默认 10s）
- [ ] 每轮最多查询 10 个 composing 任务
- [ ] 成功调用 CompositionService.handle_success()
- [ ] 失败调用 CompositionService.handle_failure()
- [ ] 集成到 SchedulerManager

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-11

---

### BE-TM-13: Task API 合成端点

**描述**: 新增合成相关的 API 端点

**验收标准**:
- [ ] POST /api/tasks/{id}/submit-composition — 提交单个任务合成
- [ ] POST /api/tasks/batch-submit-composition — 批量提交合成
- [ ] POST /api/tasks/{id}/cancel-composition — 取消合成
- [ ] GET /api/tasks/{id}/composition-status — 查询合成状态

**负责人**: Backend Lead
**类型**: backend
**依赖**: BE-TM-11

---

### FE-TM-04: 任务详情页 + 合成进度

**描述**: 新增任务详情页，展示完整信息和合成进度

**验收标准**:
- [ ] 任务详情弹窗或页面（素材信息、状态时间线、合成进度、上传结果）
- [ ] 提交合成按钮（draft 状态可用）
- [ ] 合成进度展示（composing 状态时轮询）
- [ ] 取消合成按钮

**负责人**: Frontend Lead
**类型**: frontend
**依赖**: BE-TM-13

---

## 任务汇总

| ID | 任务 | 负责人 | 依赖 | Phase |
|----|------|--------|------|-------|
| BE-TM-01 | 创建 publish_profiles 表 | Backend Lead | — | 1 |
| BE-TM-02 | 创建 composition_jobs 表 | Backend Lead | — | 1 |
| BE-TM-03 | 创建 schedule_config 表 | Backend Lead | — | 1 |
| BE-TM-04 | Task 表新增字段 | Backend Lead | 01, 02 | 1 |
| BE-TM-05 | 实现新状态机 | Backend Lead | 04 | 2 |
| BE-TM-06 | 实现快速重试和编辑重试 | Backend Lead | 05 | 2 |
| BE-TM-07 | 重构 UploadScheduler | Backend Lead | 05, 03 | 2 |
| FE-TM-01 | 前端状态标签更新 | Frontend Lead | 05, 06 | 2 |
| BE-TM-08 | PublishProfile CRUD API | Backend Lead | 01 | 3 |
| BE-TM-09 | TaskAssembler 接入 Profile | Backend Lead | 05, 08 | 3 |
| FE-TM-02 | Profile 管理页面 | Frontend Lead | 08 | 3 |
| FE-TM-03 | 组装弹窗增加 Profile 选择 | Frontend Lead | 09, FE-02 | 3 |
| BE-TM-10 | CozeClient 封装 | Backend Lead | — | 4 |
| BE-TM-11 | CompositionService | Backend Lead | 10, 05, 02 | 4 |
| BE-TM-12 | CompositionPoller | Backend Lead | 11 | 4 |
| BE-TM-13 | Task API 合成端点 | Backend Lead | 11 | 4 |
| FE-TM-04 | 任务详情页 + 合成进度 | Frontend Lead | 13 | 4 |

## 依赖关系图

```
Phase 1 (数据模型):
  BE-TM-01 ─┐
  BE-TM-02 ─┼──► BE-TM-04
  BE-TM-03 ─┘        │
                      ▼
Phase 2 (状态机):
              BE-TM-05 ──► BE-TM-06
                │    │
                │    └──► BE-TM-07 ◄── BE-TM-03
                │    │
                │    └──► FE-TM-01 ◄── BE-TM-06
                ▼
Phase 3 (Profile):
  BE-TM-08 ──► BE-TM-09
    │              │
    ▼              ▼
  FE-TM-02 ──► FE-TM-03

Phase 4 (Coze):
  BE-TM-10 ──► BE-TM-11 ──► BE-TM-12
                  │
                  └──► BE-TM-13 ──► FE-TM-04
```

## 并行机会

| 可并行任务 | 说明 |
|-----------|------|
| BE-TM-01 + BE-TM-02 + BE-TM-03 | Phase 1 三张表互不依赖 |
| BE-TM-06 + BE-TM-07 | 都依赖 05，但互不依赖 |
| BE-TM-08 + BE-TM-10 | Profile CRUD 和 CozeClient 互不依赖 |
| FE-TM-02 + BE-TM-09 | Profile 前端和后端接入可并行 |
