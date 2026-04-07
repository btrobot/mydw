# Phase 1 素材域重建 — 任务分解

> 日期: 2026-04-07
> 来源: `docs/domain-model-analysis.md` Phase 1
> 范围: Material 表拆分为 Video/Copywriting/Cover/Audio/Topic + 数据迁移 + 新 API + 兼容层 + Product 迁移

---

## 功能概述

将当前通用的 Material 表（用 type 字段区分五种素材）拆分为五个独立的领域实体表，每个表有自己的特有字段和关联关系。同时将 Product API 从 `/api/system/products` 提升为一级资源 `/api/products`。

## 参与者

| 角色 | 职责 |
|------|------|
| Backend Lead | 模型定义、迁移脚本、API 端点、Schema |
| Frontend Lead | 新 API 对接、素材页面重构、hooks 更新 |
| QA Lead | 迁移验证、API 集成测试 |

## 依赖关系图

```
BE-P1-01 (Video 模型)  ──┐
BE-P1-02 (Copywriting)  ──┤
BE-P1-03 (Cover)        ──┼──> BE-P1-06 (数据迁移脚本) ──> BE-P1-08 (兼容层 API)
BE-P1-04 (Audio)        ──┤                                      │
BE-P1-05 (Topic)        ──┘                                      ▼
                                                          FE-P1-01 (hooks)
BE-P1-07 (新 API 端点) ──────────────────────────────────> FE-P1-02 (页面)
                                                                  │
BE-P1-09 (Product 迁移) ─────────────────────────────────> FE-P1-03 (Product)
                                                                  │
                                                          TEST-P1-01 (测试)
```

---

## 后端任务

### BE-P1-01: Video 模型定义

**描述**: 创建 Video 表，替代 Material(type=video)

**验收标准**:
- [ ] 字段: id, product_id(FK), name, file_path, file_size, duration, width, height, file_hash, source_type(original/composed/downloaded), origin_id(FK→self), cover_id(FK→Cover), created_at, updated_at
- [ ] Product 反向关系 `product.videos`
- [ ] Pydantic Schema: VideoCreate, VideoUpdate, VideoResponse, VideoListResponse

**估计**: 1d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P1-02: Copywriting 模型定义

**描述**: 创建 Copywriting 表，替代 Material(type=text)

**验收标准**:
- [ ] 字段: id, product_id(FK, 可空), content, source_type(manual/original/ai_generated), source_ref, created_at, updated_at
- [ ] Product 反向关系 `product.copywritings`
- [ ] Pydantic Schema: CopywritingCreate, CopywritingUpdate, CopywritingResponse

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P1-03: Cover 模型定义

**描述**: 创建 Cover 表，替代 Material(type=cover)

**验收标准**:
- [ ] 字段: id, video_id(FK, 可空), file_path, file_size, width, height, created_at
- [ ] Video 反向关系 `video.covers`
- [ ] Pydantic Schema: CoverCreate, CoverResponse

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P1-04: Audio 模型定义

**描述**: 创建 Audio 表，替代 Material(type=audio)

**验收标准**:
- [ ] 字段: id, name, file_path, file_size, duration, created_at
- [ ] Pydantic Schema: AudioCreate, AudioResponse

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P1-05: Topic 模型定义

**描述**: 创建 Topic 表，替代 Material(type=topic)，增加热度等字段

**验收标准**:
- [ ] 字段: id, name, heat(Integer), source(manual/search), last_synced(DateTime), created_at
- [ ] Pydantic Schema: TopicCreate, TopicResponse, TopicListResponse

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P1-06: Material → 新表数据迁移脚本

**描述**: 编写幂等迁移脚本 `migrations/003_material_split.py`，将 Material 表数据按 type 分流到五个新表

**验收标准**:
- [ ] 按 type=video 迁移到 Video 表（保留 product_id 关联）
- [ ] 按 type=text 迁移到 Copywriting 表（source_type=manual）
- [ ] 按 type=cover 迁移到 Cover 表
- [ ] 按 type=audio 迁移到 Audio 表
- [ ] 按 type=topic 迁移到 Topic 表（name=content, heat=0, source=manual）
- [ ] 幂等：重复执行不报错、不重复插入
- [ ] 迁移前自动备份数据库文件
- [ ] 在 `init_db()` 中注册

**估计**: 2d
**负责人**: Backend Lead
**依赖**: BE-P1-01, BE-P1-02, BE-P1-03, BE-P1-04, BE-P1-05
**类型**: backend

**测试需求**:
- [ ] 空库迁移不报错
- [ ] 有数据迁移后新表记录数正确
- [ ] 重复执行幂等

---

### BE-P1-07: 新 API 端点

**描述**: 为五个新实体创建独立的 REST API

**验收标准**:
- [ ] `backend/api/video.py` — CRUD + 列表过滤(product_id) + 统计
- [ ] `backend/api/copywriting.py` — CRUD + 按 product_id 过滤
- [ ] `backend/api/cover.py` — CRUD + 按 video_id 过滤
- [ ] `backend/api/audio.py` — CRUD + 列表
- [ ] `backend/api/topic.py` — CRUD + 列表
- [ ] 在 `main.py` 注册路由: `/api/videos`, `/api/copywritings`, `/api/covers`, `/api/audios`, `/api/topics`
- [ ] 所有端点遵循 api-design-rules（RESTful、Pydantic 验证、正确状态码）

**估计**: 3d
**负责人**: Backend Lead
**依赖**: BE-P1-01, BE-P1-02, BE-P1-03, BE-P1-04, BE-P1-05
**类型**: backend

---

### BE-P1-08: 旧 `/api/materials` 兼容层

**描述**: 保留旧 API 端点，内部转发到新端点，标记 deprecated

**验收标准**:
- [ ] GET/POST `/api/materials` 内部按 type 路由到对应新服务
- [ ] 所有旧端点标记 `deprecated=True`
- [ ] 返回格式与旧 API 兼容（MaterialResponse）
- [ ] 日志记录兼容层调用，便于追踪迁移进度

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-P1-07
**类型**: backend

---

### BE-P1-09: Product API 提升为一级资源

**描述**: 将 Product 从 `/api/system/products` 和 `/api/materials/products` 迁移到 `/api/products`

**验收标准**:
- [ ] 新建 `backend/api/product.py` — 完整 CRUD
- [ ] Product 模型增加 dewu_url, image_url 字段
- [ ] 在 `main.py` 注册 `/api/products`
- [ ] 旧端点（system.py, material.py 中的商品端点）标记 deprecated
- [ ] Pydantic Schema 更新: ProductCreate 增加 dewu_url, image_url

**估计**: 1d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

## 前端任务

### FE-P1-01: 素材 Hooks 重构

**描述**: 将 useMaterial.ts 拆分为独立的 hooks，对接新 API

**验收标准**:
- [ ] `useVideo.ts` — useVideos, useCreateVideo, useDeleteVideo, useUpdateVideo
- [ ] `useCopywriting.ts` — useCopywritings, useCreateCopywriting, useDeleteCopywriting
- [ ] `useCover.ts` — useCovers, useUploadCover
- [ ] `useAudio.ts` — useAudios, useUploadAudio
- [ ] `useTopic.ts` — useTopics, useCreateTopic, useDeleteTopic
- [ ] `useProduct.ts` — useProducts, useCreateProduct, useDeleteProduct（从 useMaterial.ts 迁出）
- [ ] 更新 `hooks/index.ts` 导出

**估计**: 2d
**负责人**: Frontend Lead
**依赖**: BE-P1-07
**类型**: frontend

---

### FE-P1-02: 素材管理页面重构

**描述**: Material.tsx 重构为多实体管理页面

**验收标准**:
- [ ] 视频管理 Tab: 视频列表 + 关联商品下拉 + 上传 + 扫描导入
- [ ] 文案管理 Tab: 文案列表 + 关联商品 + 来源类型标签
- [ ] 封面管理 Tab: 封面列表 + 关联视频
- [ ] 音频管理 Tab: 音频列表 + 上传
- [ ] 话题管理 Tab: 话题列表 + 手动添加
- [ ] 统计卡片更新为各实体独立统计
- [ ] 无 `any` 类型，无 `console.log`

**估计**: 3d
**负责人**: Frontend Lead
**依赖**: FE-P1-01
**类型**: frontend

---

### FE-P1-03: Product 页面入口调整

**描述**: 商品管理对接新 `/api/products` 端点

**验收标准**:
- [ ] useProduct hooks 指向 `/api/products`
- [ ] 商品卡片显示关联的视频数和文案数
- [ ] 支持 dewu_url 和 image_url 字段

**估计**: 0.5d
**负责人**: Frontend Lead
**依赖**: BE-P1-09, FE-P1-01
**类型**: frontend

---

## 集成任务

### INT-P1-01: API 契约对齐

**描述**: 前后端协调新 API 的请求/响应类型定义

**验收标准**:
- [ ] 后端 OpenAPI schema 生成并导出
- [ ] 前端 SDK 重新生成（或手动定义 TypeScript 类型）
- [ ] 双方确认字段命名和类型一致

**估计**: 0.5d
**负责人**: Frontend Lead + Backend Lead
**依赖**: BE-P1-07
**类型**: both

---

## 测试任务

### TEST-P1-01: 迁移与 API 集成测试

**描述**: 验证数据迁移正确性和新 API 功能

**验收标准**:
- [ ] 迁移测试: 构造 Material 测试数据 → 执行迁移 → 验证五个新表数据正确
- [ ] API 测试: 每个新端点的 CRUD 操作
- [ ] 兼容层测试: 旧 `/api/materials` 端点仍可用
- [ ] 回归测试: 现有任务创建、发布流程不受影响

**估计**: 2d
**负责人**: QA Lead
**依赖**: BE-P1-06, BE-P1-07, BE-P1-08
**类型**: both

---

## 任务汇总

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| BE-P1-01 | Video 模型定义 | Backend Lead | 1d | - | BE |
| BE-P1-02 | Copywriting 模型定义 | Backend Lead | 0.5d | - | BE |
| BE-P1-03 | Cover 模型定义 | Backend Lead | 0.5d | - | BE |
| BE-P1-04 | Audio 模型定义 | Backend Lead | 0.5d | - | BE |
| BE-P1-05 | Topic 模型定义 | Backend Lead | 0.5d | - | BE |
| BE-P1-06 | 数据迁移脚本 | Backend Lead | 2d | 01-05 | BE |
| BE-P1-07 | 新 API 端点 | Backend Lead | 3d | 01-05 | BE |
| BE-P1-08 | 兼容层 API | Backend Lead | 1d | 07 | BE |
| BE-P1-09 | Product 提升为一级资源 | Backend Lead | 1d | - | BE |
| FE-P1-01 | 素材 Hooks 重构 | Frontend Lead | 2d | BE-07 | FE |
| FE-P1-02 | 素材页面重构 | Frontend Lead | 3d | FE-01 | FE |
| FE-P1-03 | Product 入口调整 | Frontend Lead | 0.5d | BE-09, FE-01 | FE |
| INT-P1-01 | API 契约对齐 | Both Leads | 0.5d | BE-07 | both |
| TEST-P1-01 | 迁移与集成测试 | QA Lead | 2d | BE-06,07,08 | both |

## 统计

| 维度 | 值 |
|------|-----|
| 后端任务 | 9 个, 10d |
| 前端任务 | 3 个, 5.5d |
| 集成任务 | 1 个, 0.5d |
| 测试任务 | 1 个, 2d |
| **总计** | **14 个, 18d** |
| 缓冲 20% | 3.6d |
| **含缓冲** | **~22d** |

## 关键路径

```
BE-P1-01~05 (3d 并行) → BE-P1-06 (2d) → BE-P1-07 (3d) → BE-P1-08 (1d)
                                                │
                                                ▼
                                         INT-P1-01 (0.5d) → FE-P1-01 (2d) → FE-P1-02 (3d)
                                                                                    │
                                                                             TEST-P1-01 (2d)

关键路径长度: 3 + 2 + 3 + 0.5 + 2 + 3 + 2 = 15.5d
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 数据迁移丢失关联关系 | 中 | 高 | 迁移前备份 DB，迁移脚本含回滚逻辑 |
| 兼容层遗漏边界情况 | 中 | 中 | 旧 API 测试用例全部保留并运行 |
| 前端改动面大导致回归 | 中 | 中 | 逐 Tab 迁移，每个 Tab 独立验证 |
| 新旧 API 并存期间数据不一致 | 低 | 高 | 兼容层写操作转发到新服务，不双写 |
