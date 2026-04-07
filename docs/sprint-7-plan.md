# Sprint 7 — 素材管理 Phase 2：体验完善

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Planning
> Source: docs/material-task-breakdown.md

---

## Sprint 信息

| 项 | 值 |
|----|-----|
| Sprint | 7 |
| 名称 | 素材管理 Phase 2：体验完善 |
| 周期 | 2026-04-21 ~ 2026-05-02 (2 周) |
| 分支 | feat/dewu-assoc |
| 前置 | Sprint 6 (Phase 1) Done |

## 目标

1. FFprobe 自动提取视频元数据（duration, width, height）
2. 文件存在性校验 + 前端标记
3. 文案批量导入
4. 补齐前端编辑入口（文案、商品）
5. 各模块批量删除
6. 删除前引用检查（防止孤儿任务）

**完成标志**: 素材管理的日常操作体验完整，编辑/批量操作/校验全部可用。

---

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP7-01 | FFprobe 元数据提取工具函数 + 集成到 upload/scan | Backend Lead | 1d | — | [ ] |
| SP7-02 | 文件存在性校验 API | Backend Lead | 0.5d | — | [ ] |
| SP7-03 | 文案批量导入 API (`POST /copywritings/import`) | Backend Lead | 0.5d | — | [ ] |
| SP7-04 | 删除前引用检查 (视频/文案/商品) | Backend Lead | 1d | — | [ ] |
| SP7-05 | 前端文案编辑入口 | Frontend Lead | 0.5d | — | [ ] |
| SP7-06 | 前端商品编辑入口 | Frontend Lead | 0.5d | — | [ ] |
| SP7-07 | 前端批量删除 (全部 Tab) | Frontend Lead | 1d | — | [ ] |
| SP7-08 | 前端文案批量导入入口 | Frontend Lead | 0.5d | SP7-03 | [ ] |
| SP7-09 | 前端文件存在性标记 | Frontend Lead | 0.5d | SP7-02 | [ ] |

注: BE-MAT-07 (视频删除清理文件) 已在 Sprint 6 中实现，不再列入。

---

## 任务详述

### SP7-01: FFprobe 元数据提取

**对应**: BE-MAT-04 (M-03)

**做什么**:
- 新建工具函数 `utils/ffprobe.py`: `extract_video_metadata(file_path) -> dict`
- 返回 duration, width, height, file_size
- FFprobe 不可用时 graceful fallback（仅 file_size）
- 集成到 `POST /videos/upload` 和 `POST /videos/scan`

**参考**: `backend/services/ai_clip_service.py` 已有 FFprobe 调用模式

**验收**: 上传/扫描视频后 duration, width, height 自动填充

---

### SP7-02: 文件存在性校验

**对应**: BE-MAT-05 (M-04)

**做什么**:
- VideoResponse 增加 `file_exists: bool` 字段（model_validator 中检查）
- 新增 `POST /api/videos/validate` 批量校验端点

**验收**: 列表返回 file_exists 字段，缺失文件标记为 false

---

### SP7-03: 文案批量导入

**对应**: BE-MAT-06 (M-06)

**做什么**:
- `POST /api/copywritings/import` 接收 .txt UploadFile + 可选 product_id
- 一行一条文案，空行跳过
- 返回导入统计

**验收**: 上传 .txt 文件，文案逐行入库

---

### SP7-04: 删除前引用检查

**对应**: BE-MAT-08 (BUG-03)

**做什么**:
- 删除视频前检查 Task.video_id 引用
- 删除文案前检查 Task.copywriting_id 引用
- 删除商品前检查关联的 Video/Copywriting
- 有引用时返回 409 Conflict + 引用数量

**验收**: 删除被任务引用的素材返回 409

---

### SP7-05: 文案编辑入口

**对应**: FE-MAT-04 (M-07)

**做什么**:
- CopywritingTab 表格操作列增加"编辑"按钮
- 编辑弹窗预填充内容和商品
- 调用 `PUT /api/copywritings/{id}`

**验收**: 点击编辑，修改内容后保存成功

---

### SP7-06: 商品编辑入口

**对应**: FE-MAT-05 (M-12)

**做什么**:
- ProductSection 商品卡片增加"编辑"按钮
- 编辑弹窗预填充名称和链接
- 调用 `PUT /api/products/{id}`

**验收**: 点击编辑，修改商品信息后保存成功

---

### SP7-07: 批量删除

**对应**: FE-MAT-06 (M-15)

**做什么**:
- 所有 Tab (Video, Copywriting, Cover, Audio, Topic) 增加 Table rowSelection
- 选中后显示"批量删除"按钮 + 选中数量
- 确认弹窗后逐个调用 DELETE

**验收**: 多选后批量删除成功，列表刷新

---

### SP7-08: 文案批量导入入口

**对应**: FE-MAT-07 (M-06)

**做什么**:
- CopywritingTab 增加 Upload 组件接受 .txt
- 调用 `POST /api/copywritings/import`
- 展示导入结果

**验收**: 上传 .txt 文件，展示导入统计

---

### SP7-09: 文件存在性标记

**对应**: FE-MAT-08 (M-04)

**做什么**:
- VideoTab 表格增加文件状态列
- file_exists=true 绿色标记，false 红色警告 + Tooltip

**验收**: 缺失文件的视频显示红色警告

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

剩余容量可提前启动 Phase 3 无依赖任务（BE-MAT-13 素材统计、BE-MAT-14 全文搜索）。

---

## 执行顺序

```
Week 1 (后端并行 + 无依赖前端):
  Day 1:    SP7-01 (FFprobe) — 后端核心
  Day 1:    SP7-02 (文件校验) + SP7-03 (文案导入) — 后端并行
  Day 2:    SP7-04 (引用检查) — 后端
  Day 2-3:  SP7-05 (文案编辑) + SP7-06 (商品编辑) — 前端无依赖

Week 2 (有依赖前端 + 批量操作):
  Day 3-4:  SP7-07 (批量删除) — 前端最大任务
  Day 4:    SP7-08 (文案导入入口) + SP7-09 (文件标记) — 前端
  Day 5-10: 缓冲 + 可选 Phase 3 提前启动
```

---

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| FFprobe 在 Windows 上路径问题 | 低 | 中 | 使用 shutil.which 检测，fallback 跳过 |
| 批量删除性能（逐个 DELETE） | 低 | 低 | 数据量小（桌面应用），后续可加批量端点 |
| 引用检查误阻塞用户 | 中 | 低 | 返回引用数量，让用户决定是否强制删除 |

---

## Definition of Done

- [ ] 所有 9 个任务状态为 Done
- [ ] 上传/扫描视频后 duration, width, height 自动填充
- [ ] 缺失文件的视频在列表中有红色标记
- [ ] 文案可编辑、可批量导入
- [ ] 商品可编辑
- [ ] 各 Tab 支持多选批量删除
- [ ] 删除被引用素材返回 409 而非静默删除
- [ ] TypeScript tsc --noEmit 零错误
- [ ] Python import check 通过
