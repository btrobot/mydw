# Sprint 6 — 素材管理 Phase 1：发布链路打通

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Planning
> Source: docs/material-task-breakdown.md

---

## Sprint 信息

| 项 | 值 |
|----|-----|
| Sprint | 6 |
| 名称 | 素材管理 Phase 1：发布链路打通 |
| 周期 | 2026-04-07 ~ 2026-04-18 (2 周) |
| 分支 | feat/dewu-assoc |

## 目标

1. 修复 Task.cover_path 发布链路断裂 (BUG-01)
2. 实现视频文件上传（替代手动填路径）
3. 实现目录扫描批量导入
4. 前端对接上述三项后端能力

**完成标志**: 用户可通过上传或扫描导入视频，组装任务（含封面）后完整发布。

---

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP6-01 | Task.cover_id FK 迁移 + publish_service 修复 | Backend Lead | 1d | — | [ ] |
| SP6-02 | 视频文件上传 API (`POST /videos/upload`) | Backend Lead | 1d | — | [ ] |
| SP6-03 | 目录扫描导入 API (`POST /videos/scan`) | Backend Lead | 1.5d | — | [ ] |
| SP6-04 | 前端视频上传组件 | Frontend Lead | 1d | SP6-02 | [ ] |
| SP6-05 | 前端扫描导入按钮与结果展示 | Frontend Lead | 0.5d | SP6-03 | [ ] |
| SP6-06 | 前端 Task 表单支持 cover_id 选择 | Frontend Lead | 0.5d | SP6-01 | [ ] |
| SP6-07 | 端到端验证：上传/扫描 → 组装 → 发布 | QA Lead | 0.5d | SP6-01~06 | [ ] |

---

## 任务详述

### SP6-01: Task.cover_id FK 迁移

**对应**: BE-MAT-01 (M-09/M-17) — BUG-01 修复

**做什么**:
- 新增迁移 `migrations/008_task_cover_fk.py`（幂等，ALTER TABLE ADD COLUMN）
- Task 模型增加 `cover_id` FK + `cover` relationship
- TaskCreate/TaskResponse schema 增加 `cover_id`
- `publish_service.py:180` 改为 `task.cover.file_path if task.cover else None`
- `publish_service.py:94` selectinload 增加 `Task.cover`
- `task_assembler.py` assemble 支持传入 cover_id

**关键文件**: `backend/models/__init__.py`, `backend/schemas/__init__.py`, `backend/services/publish_service.py`, `backend/services/task_assembler.py`

**验收**: publish_task 执行时不再 AttributeError，cover_path 正确传递到 DewuClient

---

### SP6-02: 视频文件上传 API

**对应**: BE-MAT-02 (M-01)

**做什么**:
- `POST /api/videos/upload` 接收 UploadFile + 可选 product_id
- 文件类型校验: video/mp4, video/quicktime
- 大小限制: 500MB
- 存储到 `MATERIAL_BASE_PATH/{product_name}/` 或 `MATERIAL_BASE_PATH/uncategorized/`
- 文件名清理，自动填充 file_size

**参考**: `backend/api/cover.py:25-58` (封面上传模式)

**验收**: curl 上传 .mp4 文件成功，DB 记录正确，文件存储到正确目录

---

### SP6-03: 目录扫描导入 API

**对应**: BE-MAT-03 (M-02)

**做什么**:
- `POST /api/videos/scan` 扫描 MATERIAL_BASE_PATH 一级子目录
- 子目录名 = 商品名，自动创建/匹配 Product
- 识别 .mp4/.mov 文件，基于 file_path 去重
- 批量 INSERT
- 返回 `{ total_scanned, new_imported, skipped, failed }`

**验收**: 放置测试文件到 MATERIAL_BASE_PATH/商品A/，调用 scan，视频入库并关联商品

---

### SP6-04: 前端视频上传组件

**对应**: FE-MAT-01 (M-01)

**做什么**:
- VideoTab 增加 Upload 组件（.mp4/.mov）
- 上传时可选关联商品
- 上传成功后刷新列表
- 保留手动添加入口

**参考**: `Material.tsx` CoverTab Upload 实现 (L443-452)

**验收**: 前端选择文件上传成功，列表自动刷新

---

### SP6-05: 前端扫描导入

**对应**: FE-MAT-02 (M-02)

**做什么**:
- VideoTab 增加"扫描导入"按钮
- 调用 `POST /api/videos/scan`
- 展示导入统计结果（Modal）
- 刷新列表

**验收**: 点击扫描，展示导入结果，列表更新

---

### SP6-06: 前端 Task 封面选择

**对应**: FE-MAT-03 (M-09)

**做什么**:
- 任务创建表单增加封面 Select（从 covers 列表选择）
- 传递 cover_id 到后端

**验收**: 创建任务时可选封面，任务记录包含 cover_id

---

### SP6-07: 端到端验证

**对应**: INT-MAT-01

**做什么**:
- 验证链路 1: 上传视频 → 创建任务（含 cover_id）→ publish_task 不报错
- 验证链路 2: 扫描导入 → 自动关联商品 → 组装任务 → 发布读取正确路径
- 验证 cover_path 正确传递到 DewuClient.upload_video

---

## 容量

| 指标 | 值 |
|------|-----|
| Sprint 工作日 | 10d |
| 总任务估计 | 6d |
| 缓冲 (20%) | 1.2d |
| 缓冲后总计 | 7.2d |
| 剩余容量 | 2.8d |
| 状态 | 容量充足 |

剩余容量可用于：处理 code review 反馈、意外阻塞、或提前启动 Phase 2 的无依赖任务（FE-MAT-04 文案编辑、FE-MAT-05 商品编辑、BE-MAT-07 视频删除清理文件）。

---

## 执行顺序

```
Week 1 (并行启动后端):
  Day 1-2:  SP6-01 (cover_id 迁移) ──────────────► SP6-06 (前端封面选择)
  Day 1-2:  SP6-02 (视频上传 API) ────────────────► SP6-04 (前端上传组件)
  Day 1-3:  SP6-03 (扫描导入 API) ────────────────► SP6-05 (前端扫描按钮)

Week 2 (前端对接 + 验证):
  Day 3-4:  SP6-04, SP6-05, SP6-06 (前端任务并行)
  Day 5:    SP6-07 (端到端验证)
  Day 6-10: 缓冲 + 可选提前启动 Phase 2 任务
```

---

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| cover_id 迁移影响现有 Task 数据 | 低 | 中 | nullable=True，幂等迁移，不影响已有记录 |
| 大文件上传超时 | 中 | 中 | 配置 FastAPI upload 限制，先支持 500MB，后续考虑分片 |
| 中文路径编码问题 | 低 | 低 | 使用 pathlib.Path，测试中文目录名 |
| MATERIAL_BASE_PATH 不存在 | 低 | 低 | 扫描前检查目录存在性，不存在时返回友好错误 |

---

## Definition of Done

- [ ] 所有 7 个任务状态为 Done
- [ ] cover_id FK 迁移完成，publish_service 不再引用 task.cover_path
- [ ] 视频可通过文件上传入库
- [ ] 视频可通过目录扫描批量入库并自动关联商品
- [ ] 任务创建支持选择封面
- [ ] 端到端链路验证通过
- [ ] 代码通过 typecheck（前端）和类型注解检查（后端）
