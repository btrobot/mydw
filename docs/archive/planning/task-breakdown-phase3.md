# Phase 3 任务编排层重构 — 任务分解

> 日期: 2026-04-07
> 来源: `docs/archive/analysis/domain-model-analysis.md` Phase 3
> 范围: Task 表增加素材 FK 引用 + TaskTopic 多对多 + TaskAssembler + TaskDistributor + 发布服务适配 + 前端任务页重构

---

## 功能概述

将 Task 从"素材容器"重构为"编排引用层"：移除内联字段（video_path, content, topic, cover_path, audio_path），改为 FK 引用 Phase 1 创建的素材实体。实现多账号轮询自动分配。采用双写过渡策略。

## 参与者

| 角色 | 职责 |
|------|------|
| Backend Lead | 模型重构、迁移、领域服务、发布服务适配 |
| Frontend Lead | 任务页面重构、hooks 更新 |
| QA Lead | 集成测试 |

## 依赖关系图

```
BE-P3-01 (Task 增加 FK) ──┐
BE-P3-02 (TaskTopic 表)  ──┼──> BE-P3-03 (数据迁移) ──> BE-P3-05 (发布服务适配)
                           │
BE-P3-04a (TaskAssembler) ─┤
BE-P3-04b (TaskDistributor)┘──> BE-P3-06 (API 重构)
                                      │
                               INT-P3-01 (契约对齐)
                                      │
                               FE-P3-01 (hooks) → FE-P3-02 (页面) → TEST-P3-01
```

---

## 后端任务

### BE-P3-01: Task 模型增加素材 FK（双写）

**描述**: 在现有 Task 表增加 video_id, copywriting_id, audio_id FK 列，保留旧字段不删

**验收标准**:
- [ ] 新增列: video_id(FK→videos), copywriting_id(FK→copywritings), audio_id(FK→audios)
- [ ] 关系: task.video, task.copywriting, task.audio
- [ ] 旧字段 video_path/content/topic/cover_path/audio_path 保留（双写期）
- [ ] 迁移脚本 `005_task_add_fk.py` 幂等添加列
- [ ] TaskResponse schema 增加 video_id, copywriting_id, audio_id 字段

**估计**: 1d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P3-02: TaskTopic 多对多关联表

**描述**: 创建 task_topics 关联表，支持一个任务关联多个话题

**验收标准**:
- [ ] TaskTopic 模型: task_id(FK→tasks), topic_id(FK→topics)
- [ ] Task 关系: task.topics (多对多)
- [ ] Topic 关系: topic.tasks (反向)
- [ ] TaskResponse 增加 topic_ids: List[int] 和 topic_names: List[str]

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P3-03: Task 数据迁移（旧字段→FK）

**描述**: 迁移脚本将现有 Task 的 video_path 匹配到 Video.id，content 匹配到 Copywriting.id 等

**验收标准**:
- [ ] video_path → 匹配 Video.file_path → 填充 video_id
- [ ] content → 匹配 Copywriting.content → 填充 copywriting_id
- [ ] topic → 拆分为多个 Topic → 创建 TaskTopic 记录
- [ ] audio_path → 匹配 Audio.file_path → 填充 audio_id
- [ ] 幂等：已有 FK 值的跳过
- [ ] 迁移脚本 `006_task_migrate_fk.py`

**估计**: 2d
**负责人**: Backend Lead
**依赖**: BE-P3-01, BE-P3-02
**类型**: backend

---

### BE-P3-04a: TaskAssembler 领域服务

**描述**: 从素材组装任务的领域逻辑，替代现有 auto_generate_tasks

**验收标准**:
- [ ] `backend/services/task_assembler.py`
- [ ] `assemble(video_ids, account_id) -> List[Task]`: 为每个视频自动匹配同 product 的文案、话题
- [ ] 写入新 FK 字段（video_id, copywriting_id），同时双写旧字段（video_path, content）
- [ ] 支持文案模式参数: manual / auto_match

**估计**: 1.5d
**负责人**: Backend Lead
**依赖**: BE-P3-01, BE-P3-02
**类型**: backend

---

### BE-P3-04b: TaskDistributor 领域服务

**描述**: 多账号轮询分配，替代单 account_id 模式

**验收标准**:
- [ ] `backend/services/task_distributor.py`
- [ ] `distribute(video_ids, account_ids, strategy="round_robin") -> List[Task]`
- [ ] 轮询逻辑: video_ids[i] → account_ids[i % len(account_ids)]
- [ ] 内部调用 TaskAssembler 组装每个任务
- [ ] 返回创建的任务列表

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-P3-04a
**类型**: backend

---

### BE-P3-05: 发布服务适配

**描述**: publish_service.py 优先从 FK 关系读取素材，兼容旧字段

**验收标准**:
- [ ] publish_task() 优先读 task.video.file_path，fallback 到 task.video_path
- [ ] 文案优先读 task.copywriting.content，fallback 到 task.content
- [ ] 话题从 task.topics 关系读取，fallback 到 task.topic
- [ ] 商品链接从 task.product.link 读取（已有）
- [ ] selectinload 预加载所有关系

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-P3-01
**类型**: backend

---

### BE-P3-06: 任务 API 重构

**描述**: 更新 task.py 端点，支持新的分配模式

**验收标准**:
- [ ] POST /api/tasks/assemble — 替代 auto-generate 和 init-from-materials
- [ ] 请求体: { video_ids[], account_ids[], strategy: "round_robin"|"manual", copywriting_mode: "auto_match"|"manual" }
- [ ] 旧端点 auto-generate / init-from-materials 标记 deprecated
- [ ] GET /api/tasks 返回的 TaskResponse 包含素材详情（video_name, copywriting_preview, topic_names）

**估计**: 1.5d
**负责人**: Backend Lead
**依赖**: BE-P3-04b, BE-P3-05
**类型**: backend

---

## 前端任务

### FE-P3-01: 任务 Hooks 更新

**描述**: useTask.ts 适配新 API，新增 useAssembleTasks hook

**验收标准**:
- [ ] useAssembleTasks — 调用 POST /api/tasks/assemble
- [ ] useTask 返回类型增加 video_id, copywriting_id, topic_names
- [ ] 移除对旧 auto-generate / init-from-materials 的调用

**估计**: 1d
**负责人**: Frontend Lead
**依赖**: BE-P3-06
**类型**: frontend

---

### FE-P3-02: 任务管理页面重构

**描述**: Task.tsx 重构，支持多账号分配和素材选择

**验收标准**:
- [ ] "创建任务"改为"组装任务"：选择视频 → 选择账号（多选）→ 选择分配策略
- [ ] 任务表格显示: 视频名称、文案预览、话题标签、关联商品、账号、状态
- [ ] 移除"AI生成任务"和"从素材初始化"按钮，替换为"组装任务"
- [ ] 乱序按钮降级（PM 说不用，但保留为次要操作）

**估计**: 2d
**负责人**: Frontend Lead
**依赖**: FE-P3-01
**类型**: frontend

---

## 集成任务

### INT-P3-01: API 契约对齐

**描述**: 前后端协调 /api/tasks/assemble 的请求/响应类型

**验收标准**:
- [ ] AssembleRequest TS 类型
- [ ] TaskResponse TS 类型更新（含素材详情）
- [ ] 双方确认

**估计**: 0.5d
**负责人**: Both Leads
**依赖**: BE-P3-06
**类型**: both

---

## 测试任务

### TEST-P3-01: 任务编排集成测试

**描述**: 验证任务组装、分配、发布全流程

**验收标准**:
- [ ] test_assemble_tasks — 组装任务，验证 FK 正确填充
- [ ] test_distribute_round_robin — 10视频3账号，验证轮询分配
- [ ] test_publish_reads_fk — 发布服务从 FK 关系读取素材
- [ ] test_backward_compat — 旧字段仍可用

**估计**: 1.5d
**负责人**: QA Lead
**依赖**: BE-P3-05, BE-P3-06
**类型**: both

---

## 任务汇总

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| BE-P3-01 | Task 增加素材 FK | Backend Lead | 1d | - | BE |
| BE-P3-02 | TaskTopic 关联表 | Backend Lead | 0.5d | - | BE |
| BE-P3-03 | Task 数据迁移 | Backend Lead | 2d | 01,02 | BE |
| BE-P3-04a | TaskAssembler 服务 | Backend Lead | 1.5d | 01,02 | BE |
| BE-P3-04b | TaskDistributor 服务 | Backend Lead | 1d | 04a | BE |
| BE-P3-05 | 发布服务适配 | Backend Lead | 1d | 01 | BE |
| BE-P3-06 | 任务 API 重构 | Backend Lead | 1.5d | 04b,05 | BE |
| FE-P3-01 | 任务 Hooks 更新 | Frontend Lead | 1d | BE-06 | FE |
| FE-P3-02 | 任务页面重构 | Frontend Lead | 2d | FE-01 | FE |
| INT-P3-01 | API 契约对齐 | Both Leads | 0.5d | BE-06 | both |
| TEST-P3-01 | 编排集成测试 | QA Lead | 1.5d | BE-05,06 | both |

## 统计

| 维度 | 值 |
|------|-----|
| 后端任务 | 7 个, 8.5d |
| 前端任务 | 2 个, 3d |
| 集成任务 | 1 个, 0.5d |
| 测试任务 | 1 个, 1.5d |
| **总计** | **11 个, 13.5d** |
| 缓冲 20% | 2.7d |
| **含缓冲** | **~16d** |

## 关键路径

```
BE-P3-01+02 (1d并行) → BE-P3-04a (1.5d) → BE-P3-04b (1d) → BE-P3-06 (1.5d)
                                                                    │
                                                             INT-P3-01 (0.5d)
                                                                    │
                                                             FE-P3-01 (1d) → FE-P3-02 (2d)
                                                                                    │
                                                                             TEST-P3-01 (1.5d)

关键路径: 1 + 1.5 + 1 + 1.5 + 0.5 + 1 + 2 + 1.5 = 10.5d
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 旧字段→FK 匹配失败（路径不一致） | 中 | 高 | 迁移脚本用模糊匹配 + 手动修复兜底 |
| 双写期数据不一致 | 中 | 中 | 写入时同步更新新旧字段，读取优先新字段 |
| 发布服务改动导致发布中断 | 中 | 高 | fallback 到旧字段，渐进切换 |
| 前端多账号选择 UX 复杂 | 低 | 低 | 默认全选活跃账号，用户可调整 |
