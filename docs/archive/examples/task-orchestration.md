# 任务编排功能 - 任务分解

> 版本: 1.0.0 | 创建日期: 2026-04-08
> Epic: 任务管理重构
> Feature: 任务编排（Task Orchestration）
> 负责人: Tech Lead

---

## 功能概述

任务编排是任务管理的核心模块，负责创建、编辑、查询和管理发布任务。

**核心用例**：
1. 创建单个任务（手动编排素材）
2. 批量组装任务（多视频+多账号自动分配）
3. 编辑任务（修改素材、配置）
4. 查询任务列表（筛选、排序、分页）
5. 查看任务详情（完整信息+执行日志）
6. 删除任务

**用户交互流程**：
```
用户 → 选择素材 → 配置参数 → 创建任务（draft）→ 提交合成 → 等待上传
```

---

## 参与者识别

| 角色 | 职责 |
|------|------|
| Backend Lead | 数据模型设计、API 实现、业务逻辑 |
| Frontend Lead | 页面开发、表单交互、列表展示 |
| Tech Lead | 架构设计、协调、Code Review |

---

## 任务分解

### 阶段 1: 数据模型重构（P0）

#### BE-TASK-01: Task 表结构迁移

**描述**: 修改 Task 表，增加视频合成相关字段

**验收标准**:
- [ ] 新增 `source_video_ids` 字段（TEXT, JSON array）
- [ ] 新增 `composition_template` 字段（VARCHAR(64)）
- [ ] 新增 `composition_params` 字段（TEXT, JSON）
- [ ] 新增 `composition_job_id` 字段（INTEGER, FK）
- [ ] 新增 `final_video_path` 字段（VARCHAR(512)）
- [ ] 新增 `final_video_duration` 字段（INTEGER）
- [ ] 新增 `final_video_size` 字段（INTEGER）
- [ ] 新增 `scheduled_time` 字段（DATETIME）
- [ ] 新增 `retry_count` 字段（INTEGER, DEFAULT 0）
- [ ] 新增 `dewu_video_id` 字段（VARCHAR(128)）
- [ ] 新增 `dewu_video_url` 字段（VARCHAR(512)）
- [ ] 修改 `status` 枚举（draft/composing/ready/uploading/uploaded/failed/cancelled）
- [ ] 创建迁移脚本 `migrations/016_task_composition_fields.py`
- [ ] 数据迁移：旧状态映射到新状态
- [ ] 数据迁移：video_id → source_video_ids (JSON array)

**估计**: 1d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

**文件**:
- `backend/migrations/016_task_composition_fields.py`
- `backend/models/__init__.py` (Task 模型)

---

#### BE-TASK-02: 更新 Task Schema

**描述**: 更新 Pydantic Schema 以支持新字段

**验收标准**:
- [ ] 更新 `TaskCreate` Schema（增加 source_video_ids, composition_template 等）
- [ ] 更新 `TaskUpdate` Schema
- [ ] 更新 `TaskResponse` Schema
- [ ] 新增 `TaskStatus` 枚举（draft/composing/ready/uploading/uploaded/failed/cancelled）
- [ ] 添加字段验证器（source_video_ids 非空数组、priority 范围等）
- [ ] 向后兼容：保留 video_id 字段（标记为 deprecated）

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: BE-TASK-01
**类型**: backend

**文件**:
- `backend/schemas/__init__.py`

---

### 阶段 2: 后端 API 实现（P0）

#### BE-TASK-03: 创建任务 API 重构

**描述**: 重构 POST /api/tasks，支持新的素材编排模式

**验收标准**:
- [ ] 接收 `source_video_ids` 数组（必填）
- [ ] 接收 `composition_template` 字段（可选）
- [ ] 接收 `composition_params` 字段（可选）
- [ ] 验证 source_video_ids 中的视频存在
- [ ] 验证 account_id 存在且状态正常
- [ ] 验证其他素材 ID（copywriting, audio, cover）
- [ ] 创建 Task 记录（status = draft）
- [ ] 返回完整 Task 信息
- [ ] 错误处理：素材不存在、账号无效等

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-TASK-02
**类型**: backend

**文件**:
- `backend/api/task.py` (create_task 函数)
- `backend/services/task_service.py` (create_task 方法)

---

#### BE-TASK-04: 批量组装任务 API 重构

**描述**: 重构 POST /api/tasks/batch-assemble，支持新的素材模式

**验收标准**:
- [ ] 接收 `video_ids` 数组（原始视频片段）
- [ ] 接收 `account_ids` 数组
- [ ] 接收 `strategy` 参数（round_robin/random/manual）
- [ ] 接收 `copywriting_mode` 参数（auto_match/manual/same_for_all）
- [ ] 接收 `composition_template` 参数（可选）
- [ ] 接收 `topic_ids` 参数（可选）
- [ ] 按策略分配视频到账号
- [ ] 自动匹配文案（根据 copywriting_mode）
- [ ] 批量创建 Task 记录
- [ ] 返回创建的任务列表

**估计**: 1.5d
**负责人**: Backend Lead
**依赖**: BE-TASK-03
**类型**: backend

**文件**:
- `backend/api/task.py` (assemble_tasks 函数)
- `backend/services/task_distributor.py` (distribute 方法)
- `backend/services/task_assembler.py` (新增，文案匹配逻辑)

---

#### BE-TASK-05: 编辑任务 API

**描述**: 实现 PUT /api/tasks/{id}，支持编辑草稿任务

**验收标准**:
- [ ] 只允许编辑 `draft` 状态的任务
- [ ] 可修改字段：name, source_video_ids, copywriting_id, audio_id, cover_id, topic_ids, composition_template, composition_params, scheduled_time, priority
- [ ] 验证修改后的素材 ID 存在
- [ ] 更新 updated_at 时间戳
- [ ] 返回更新后的 Task 信息
- [ ] 错误处理：任务不存在、状态不允许编辑、素材无效

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: BE-TASK-03
**类型**: backend

**文件**:
- `backend/api/task.py` (update_task 函数)
- `backend/services/task_service.py` (update_task 方法)

---

#### BE-TASK-06: 查询任务列表 API 增强

**描述**: 增强 GET /api/tasks，支持更多筛选条件

**验收标准**:
- [ ] 支持按 status 筛选（多选）
- [ ] 支持按 account_id 筛选
- [ ] 支持按 product_id 筛选
- [ ] 支持按 created_at 时间范围筛选（start_date, end_date）
- [ ] 支持按 scheduled_time 时间范围筛选
- [ ] 支持按 name 关键词搜索
- [ ] 支持排序（priority, created_at, scheduled_time）
- [ ] 支持分页（limit, offset）
- [ ] 返回总数 + 任务列表
- [ ] 预加载关联数据（account, product, video, copywriting, topics）

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-TASK-02
**类型**: backend

**文件**:
- `backend/api/task.py` (list_tasks 函数)
- `backend/services/task_service.py` (get_tasks 方法)

---

#### BE-TASK-07: 任务详情 API

**描述**: 实现 GET /api/tasks/{id}/detail，返回完整任务信息

**验收标准**:
- [ ] 返回 Task 基础信息
- [ ] 预加载 account 信息（id, name, status）
- [ ] 预加载 product 信息（id, name）
- [ ] 预加载 source_videos 列表（id, name, duration, file_path）
- [ ] 预加载 copywriting 信息（id, content）
- [ ] 预加载 audio 信息（id, name, file_path）
- [ ] 预加载 cover 信息（id, file_path）
- [ ] 预加载 topics 列表（id, name）
- [ ] 预加载 composition_job 信息（如果存在）
- [ ] 预加载 publish_logs 列表（最近 10 条）
- [ ] 生成执行时间线（created → composing → ready → uploading → uploaded）
- [ ] 错误处理：任务不存在

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-TASK-02
**类型**: backend

**文件**:
- `backend/api/task.py` (get_task_detail 函数)
- `backend/services/task_service.py` (get_task_detail 方法)
- `backend/schemas/__init__.py` (TaskDetailResponse)

---

#### BE-TASK-08: 删除任务 API 增强

**描述**: 增强 DELETE /api/tasks/{id}，增加状态检查

**验收标准**:
- [ ] 允许删除 draft/failed/cancelled 状态的任务
- [ ] 禁止删除 composing/uploading 状态的任务（需先取消）
- [ ] 级联删除 TaskTopic 关联记录
- [ ] 级联删除 CompositionJob 记录（如果存在）
- [ ] 返回 204 No Content
- [ ] 错误处理：任务不存在、状态不允许删除

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: BE-TASK-02
**类型**: backend

**文件**:
- `backend/api/task.py` (delete_task 函数)
- `backend/services/task_service.py` (delete_task 方法)

---

### 阶段 3: 前端页面开发（P0）

#### FE-TASK-01: 任务列表页面重构

**描述**: 重构任务列表页面，支持新的状态和筛选

**验收标准**:
- [ ] 显示任务列表（ID, 名称, 账号, 状态, 优先级, 创建时间）
- [ ] 状态标签：draft/composing/ready/uploading/uploaded/failed/cancelled
- [ ] 筛选表单：状态（多选）、账号、商品、时间范围、关键词
- [ ] 排序：优先级、创建时间、计划时间
- [ ] 分页：每页 20 条
- [ ] 操作按钮：查看详情、编辑（draft）、删除
- [ ] 批量操作：批量删除（draft/failed）
- [ ] 空状态提示

**估计**: 1.5d
**负责人**: Frontend Lead
**依赖**: BE-TASK-06
**类型**: frontend

**文件**:
- `frontend/src/pages/Task.tsx`
- `frontend/src/hooks/useTask.ts`

---

#### FE-TASK-02: 创建任务表单

**描述**: 实现创建任务表单，支持素材选择和配置

**验收标准**:
- [ ] 表单字段：任务名称、上传账号、商品（可选）
- [ ] 素材选择：原始视频（多选）、文案、音频、封面、话题
- [ ] 合成配置：模板选择（可选）、参数配置（可选）
- [ ] 上传配置：计划时间、优先级
- [ ] 表单验证：必填项、视频至少选一个
- [ ] 素材预览：显示已选素材的缩略信息
- [ ] 提交按钮：保存为草稿
- [ ] 成功后跳转到任务详情页

**估计**: 2d
**负责人**: Frontend Lead
**依赖**: BE-TASK-03
**类型**: frontend

**文件**:
- `frontend/src/pages/TaskCreate.tsx`
- `frontend/src/components/TaskForm.tsx`
- `frontend/src/hooks/useTask.ts`

---

#### FE-TASK-03: 批量组装任务弹窗

**描述**: 实现批量组装任务弹窗，快速创建多个任务

**验收标准**:
- [ ] 弹窗表单：视频列表（多选）、账号列表（多选）
- [ ] 分配策略：轮询、随机、手动
- [ ] 文案模式：自动匹配、手动指定、统一文案
- [ ] 合成模板：下拉选择（可选）
- [ ] 话题标签：多选（可选）
- [ ] 预览分配结果：显示视频→账号的映射
- [ ] 提交按钮：确认组装
- [ ] 成功提示：显示创建的任务数量

**估计**: 1.5d
**负责人**: Frontend Lead
**依赖**: BE-TASK-04
**类型**: frontend

**文件**:
- `frontend/src/components/AssembleTaskModal.tsx`
- `frontend/src/hooks/useTask.ts`

---

#### FE-TASK-04: 任务详情页面

**描述**: 实现任务详情页面，显示完整信息和执行日志

**验收标准**:
- [ ] 基础信息：ID, 名称, 状态, 账号, 商品, 优先级, 创建时间
- [ ] 素材信息：原始视频列表、文案、音频、封面、话题
- [ ] 合成配置：模板、参数
- [ ] 合成结果：成品视频路径、时长、大小（如果已合成）
- [ ] 上传结果：得物视频 ID、链接（如果已上传）
- [ ] 执行时间线：创建→合成→上传的时间节点
- [ ] 执行日志：合成日志、上传日志
- [ ] 操作按钮：编辑（draft）、提交合成（draft）、重试（failed）、删除
- [ ] 面包屑导航：任务列表 > 任务详情

**估计**: 2d
**负责人**: Frontend Lead
**依赖**: BE-TASK-07
**类型**: frontend

**文件**:
- `frontend/src/pages/TaskDetail.tsx`
- `frontend/src/components/TaskTimeline.tsx`
- `frontend/src/hooks/useTask.ts`

---

#### FE-TASK-05: 编辑任务表单

**描述**: 实现编辑任务表单，支持修改草稿任务

**验收标准**:
- [ ] 复用创建任务表单组件
- [ ] 预填充现有数据
- [ ] 只允许编辑 draft 状态的任务
- [ ] 提交按钮：保存修改
- [ ] 成功后返回任务详情页

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: FE-TASK-02, FE-TASK-04
**类型**: frontend

**文件**:
- `frontend/src/pages/TaskEdit.tsx`
- `frontend/src/components/TaskForm.tsx`

---

### 阶段 4: 集成与测试（P0）

#### INT-TASK-01: API 类型定义

**描述**: 前后端协调 API 类型定义

**验收标准**:
- [ ] 定义 TypeScript 接口（TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse）
- [ ] 定义 Pydantic Schema（对应后端）
- [ ] 双方确认字段名称、类型、必填项
- [ ] 更新 OpenAPI 文档
- [ ] 前端重新生成 API 客户端（npm run api:generate）

**估计**: 0.5d
**负责人**: Frontend Lead + Backend Lead
**依赖**: BE-TASK-02
**类型**: both

**文件**:
- `backend/schemas/__init__.py`
- `frontend/src/types/task.ts`
- `backend/main.py` (OpenAPI 配置)

---

#### TEST-TASK-01: 任务编排单元测试

**描述**: 编写后端单元测试

**验收标准**:
- [ ] TaskService 单元测试（create, update, delete, get）
- [ ] TaskDistributor 单元测试（round_robin, random 策略）
- [ ] TaskAssembler 单元测试（文案匹配逻辑）
- [ ] Schema 验证测试（字段验证器）
- [ ] 覆盖率 > 80%

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-TASK-03, BE-TASK-04, BE-TASK-05
**类型**: backend

**文件**:
- `backend/tests/test_task_service.py`
- `backend/tests/test_task_distributor.py`

---

#### TEST-TASK-02: 任务编排 API 测试

**描述**: 编写 API 集成测试

**验收标准**:
- [ ] POST /api/tasks 测试（成功、失败场景）
- [ ] POST /api/tasks/batch-assemble 测试
- [ ] PUT /api/tasks/{id} 测试
- [ ] GET /api/tasks 测试（筛选、排序、分页）
- [ ] GET /api/tasks/{id}/detail 测试
- [ ] DELETE /api/tasks/{id} 测试
- [ ] 错误处理测试（404, 400, 403）

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-TASK-03~08
**类型**: backend

**文件**:
- `backend/tests/test_api_task.py`

---

#### TEST-TASK-03: 前端组件测试

**描述**: 编写前端组件测试

**验收标准**:
- [ ] TaskForm 组件测试（表单验证、提交）
- [ ] AssembleTaskModal 组件测试
- [ ] TaskTimeline 组件测试
- [ ] useTask Hook 测试

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: FE-TASK-02, FE-TASK-03, FE-TASK-04
**类型**: frontend

**文件**:
- `frontend/src/components/__tests__/TaskForm.test.tsx`
- `frontend/src/hooks/__tests__/useTask.test.ts`

---

#### TEST-TASK-04: E2E 测试

**描述**: 编写端到端测试

**验收标准**:
- [ ] 创建任务流程测试
- [ ] 批量组装任务流程测试
- [ ] 编辑任务流程测试
- [ ] 查询和筛选任务测试
- [ ] 删除任务测试

**估计**: 1d
**负责人**: QA Lead
**依赖**: FE-TASK-01~05, BE-TASK-03~08
**类型**: both

**文件**:
- `frontend/tests/e2e/task-orchestration.spec.ts`

---

## 任务汇总

### 后端任务（Backend）

| ID | 任务 | 估计 | 依赖 |
|----|------|------|------|
| BE-TASK-01 | Task 表结构迁移 | 1d | - |
| BE-TASK-02 | 更新 Task Schema | 0.5d | BE-TASK-01 |
| BE-TASK-03 | 创建任务 API 重构 | 1d | BE-TASK-02 |
| BE-TASK-04 | 批量组装任务 API 重构 | 1.5d | BE-TASK-03 |
| BE-TASK-05 | 编辑任务 API | 0.5d | BE-TASK-03 |
| BE-TASK-06 | 查询任务列表 API 增强 | 1d | BE-TASK-02 |
| BE-TASK-07 | 任务详情 API | 1d | BE-TASK-02 |
| BE-TASK-08 | 删除任务 API 增强 | 0.5d | BE-TASK-02 |
| **后端小计** | | **7d** | |

### 前端任务（Frontend）

| ID | 任务 | 估计 | 依赖 |
|----|------|------|------|
| FE-TASK-01 | 任务列表页面重构 | 1.5d | BE-TASK-06 |
| FE-TASK-02 | 创建任务表单 | 2d | BE-TASK-03 |
| FE-TASK-03 | 批量组装任务弹窗 | 1.5d | BE-TASK-04 |
| FE-TASK-04 | 任务详情页面 | 2d | BE-TASK-07 |
| FE-TASK-05 | 编辑任务表单 | 0.5d | FE-TASK-02, FE-TASK-04 |
| **前端小计** | | **7.5d** | |

### 集成与测试（Integration & Testing）

| ID | 任务 | 估计 | 依赖 |
|----|------|------|------|
| INT-TASK-01 | API 类型定义 | 0.5d | BE-TASK-02 |
| TEST-TASK-01 | 任务编排单元测试 | 1d | BE-TASK-03~05 |
| TEST-TASK-02 | 任务编排 API 测试 | 1d | BE-TASK-03~08 |
| TEST-TASK-03 | 前端组件测试 | 0.5d | FE-TASK-02~04 |
| TEST-TASK-04 | E2E 测试 | 1d | FE-TASK-01~05, BE-TASK-03~08 |
| **测试小计** | | **4d** | |

---

## 总计

- **总工作量**: 18.5d
- **缓冲后**: 22d (~4.5 周)
- **并行开发**: 前后端可并行，实际日历时间约 2.5 周

---

## 实施计划

### Week 1: 数据模型 + 后端 API

**Day 1-2**: 
- BE-TASK-01: Task 表结构迁移
- BE-TASK-02: 更新 Task Schema

**Day 3-5**:
- BE-TASK-03: 创建任务 API 重构
- BE-TASK-04: 批量组装任务 API 重构
- BE-TASK-05: 编辑任务 API

### Week 2: 后端 API + 前端开发

**Day 1-2**:
- BE-TASK-06: 查询任务列表 API 增强
- BE-TASK-07: 任务详情 API
- BE-TASK-08: 删除任务 API 增强
- INT-TASK-01: API 类型定义

**Day 3-5** (并行):
- 后端：TEST-TASK-01, TEST-TASK-02
- 前端：FE-TASK-01, FE-TASK-02

### Week 3: 前端开发 + 测试

**Day 1-3**:
- FE-TASK-03: 批量组装任务弹窗
- FE-TASK-04: 任务详情页面
- FE-TASK-05: 编辑任务表单

**Day 4-5**:
- TEST-TASK-03: 前端组件测试
- TEST-TASK-04: E2E 测试

---

## 风险与依赖

### 关键依赖
1. **扣子 API 集成方式** - 需要先确认才能完成合成相关功能
2. **素材组合规则** - 影响表单设计和验证逻辑
3. **现有数据迁移** - 需要谨慎处理，避免数据丢失

### 技术风险
1. **数据库迁移** - 现有任务数据的状态映射可能有边界情况
2. **JSON 字段查询** - source_video_ids 是 JSON 数组，查询性能需要关注
3. **前端状态管理** - 任务状态较多，需要清晰的状态机逻辑

### 缓解措施
1. 迁移脚本充分测试，先在测试环境验证
2. 为 JSON 字段创建合适的索引
3. 使用状态机库（如 xstate）管理前端状态

---

## 验收标准

### 功能验收
- [ ] 可以创建单个任务（手动选择素材）
- [ ] 可以批量组装任务（多视频+多账号）
- [ ] 可以编辑草稿任务
- [ ] 可以查询和筛选任务列表
- [ ] 可以查看任务详情（完整信息+日志）
- [ ] 可以删除任务
- [ ] 状态流转正确（draft → composing → ready → uploading → uploaded）

### 质量验收
- [ ] 单元测试覆盖率 > 80%
- [ ] API 测试覆盖所有端点
- [ ] E2E 测试覆盖核心流程
- [ ] 无 TypeScript 类型错误
- [ ] 无 Python 类型检查错误
- [ ] 代码通过 Code Review

### 性能验收
- [ ] 任务列表加载时间 < 1s（100 条数据）
- [ ] 任务详情加载时间 < 500ms
- [ ] 批量创建 100 个任务 < 5s

---

## 后续工作

完成任务编排后，下一步工作：
1. **视频合成模块**（CompositionJob 相关功能）
2. **上传调度重构**（从 ready 状态取任务）
3. **模板管理**（WorkflowTemplate CRUD）
