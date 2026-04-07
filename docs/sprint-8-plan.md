# Sprint 8 — 素材管理 Phase 3：增强功能

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Planning
> Source: docs/material-task-breakdown.md

---

## Sprint 信息

| 项 | 值 |
|----|-----|
| Sprint | 8 |
| 名称 | 素材管理 Phase 3：增强功能 |
| 周期 | 2026-05-05 ~ 2026-05-16 (2 周) |
| 分支 | feat/dewu-assoc |
| 前置 | Sprint 6 (P0) Done, Sprint 7 (P1) Done |

## 目标

1. 视频去重 (SHA-256 file_hash)
2. 封面自动提取 (FFmpeg 截帧)
3. 音频元数据提取
4. 得物链接解析
5. 素材统计 API + 仪表盘
6. 全文搜索
7. 补齐 Sprint 7 遗留的批量删除

**完成标志**: 素材管理全部 27 个任务完成，功能完整。

---

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP8-01 | 视频去重 (SHA-256 file_hash) | Backend Lead | 0.5d | — | [ ] |
| SP8-02 | 封面自动提取 API (`POST /covers/extract`) | Automation Dev | 1d | — | [ ] |
| SP8-03 | 音频元数据提取 (FFprobe duration) | Backend Lead | 0.5d | — | [ ] |
| SP8-04 | 得物链接解析 (`POST /products/parse-url`) | Automation Dev | 1.5d | — | [ ] |
| SP8-05 | 素材统计 API (`GET /materials/stats`) | Backend Lead | 0.5d | — | [ ] |
| SP8-06 | 全文搜索 (视频名称 + 文案内容) | Backend Lead | 0.5d | — | [ ] |
| SP8-07 | 前端批量删除 (全部 Tab rowSelection) | Frontend Lead | 1d | — | [ ] |
| SP8-08 | 前端素材统计仪表盘 | Frontend Lead | 1d | SP8-05 | [ ] |
| SP8-09 | 前端封面提取入口 | Frontend Lead | 0.5d | SP8-02 | [ ] |
| SP8-10 | 前端全文搜索入口 | Frontend Lead | 0.5d | SP8-06 | [ ] |
| SP8-11 | 前端话题批量删除 | Frontend Lead | 0.5d | — | [ ] |

---

## 任务详述

### SP8-01: 视频去重

**对应**: BE-MAT-09 (M-05)

**做什么**:
- upload/scan 时计算 SHA-256 file_hash 并存入 Video.file_hash
- 已存在相同 hash 时返回提示（不阻塞，可选跳过）
- 复用 utils/ffprobe.py 模块或新建 utils/hash.py

**验收**: 上传重复视频时返回提示

---

### SP8-02: 封面自动提取

**对应**: BE-MAT-10 (M-08)

**做什么**:
- `POST /api/covers/extract` 接收 video_id + timestamp (秒)
- FFmpeg 截取指定帧，保存为 JPEG 到 MATERIAL_BASE_PATH/cover/
- 自动创建 Cover 记录并关联 video_id

**参考**: `backend/services/ai_clip_service.py` 已有 FFmpeg 封面处理

**验收**: 指定视频和时间点，生成封面图并入库

---

### SP8-03: 音频元数据提取

**对应**: BE-MAT-11 (M-10)

**做什么**:
- 音频上传时调用 FFprobe 提取 duration
- 复用 utils/ffprobe.py 的 extract_video_metadata（对音频同样有效）

**验收**: 上传音频后 duration 自动填充

---

### SP8-04: 得物链接解析

**对应**: BE-MAT-12 (M-13)

**做什么**:
- `POST /api/products/parse-url` 接收得物商品 URL
- 使用 Patchright 或 HTTP 请求解析页面提取商品名称、图片
- 返回解析结果，用户确认后创建商品

**验收**: 输入得物 URL，返回商品名称和图片

---

### SP8-05: 素材统计 API

**对应**: BE-MAT-13 (M-14)

**做什么**:
- `GET /api/system/material-stats` 返回各类素材数量
- 商品覆盖率（有视频的商品 / 总商品）
- 无素材商品列表

**验收**: API 返回正确统计数据

---

### SP8-06: 全文搜索

**对应**: BE-MAT-14 (M-16)

**做什么**:
- `GET /api/videos?keyword=` 按名称模糊搜索
- `GET /api/copywritings?keyword=` 按内容模糊搜索

**验收**: 搜索关键词返回匹配结果

---

### SP8-07: 批量删除

**对应**: FE-MAT-06 (M-15) — Sprint 7 遗留

**做什么**:
- VideoTab, CopywritingTab, CoverTab, AudioTab, TopicTab 增加 Table rowSelection
- 选中后显示"批量删除"按钮 + 选中数量
- 确认后逐个调用 DELETE

**验收**: 多选后批量删除成功

---

### SP8-08~11: 前端入口

SP8-08 素材统计仪表盘、SP8-09 封面提取入口、SP8-10 搜索框、SP8-11 话题批量删除 — 均为对应后端 API 的前端对接。

---

## 容量

| 指标 | 值 |
|------|-----|
| Sprint 工作日 | 10d |
| 总任务估计 | 8d |
| 缓冲 (20%) | 1.6d |
| 缓冲后总计 | 9.6d |
| 剩余容量 | 0.4d |
| 状态 | 紧凑但可行 |

---

## 执行顺序

```
Week 1 (后端并行 + 无依赖前端):
  Day 1:    SP8-01 (去重) + SP8-03 (音频元数据) + SP8-05 (统计) + SP8-06 (搜索)
  Day 1-2:  SP8-02 (封面提取)
  Day 1-3:  SP8-04 (得物链接解析)
  Day 2-3:  SP8-07 (批量删除) + SP8-11 (话题批量删除)

Week 2 (有依赖前端):
  Day 3-4:  SP8-08 (统计仪表盘)
  Day 4:    SP8-09 (封面提取入口) + SP8-10 (搜索入口)
  Day 5-10: 缓冲 + 全量回归测试
```

---

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 得物链接解析被反爬 | 中 | 中 | 降级为手动输入，解析作为辅助 |
| SHA-256 大文件计算慢 | 低 | 低 | 异步计算，不阻塞上传响应 |
| 容量紧凑 | 中 | 低 | 得物链接解析可降级到后续迭代 |

---

## Definition of Done

- [ ] 所有 11 个任务状态为 Done
- [ ] 重复视频上传有提示
- [ ] 封面可从视频自动提取
- [ ] 音频上传后 duration 自动填充
- [ ] 素材统计仪表盘展示正确数据
- [ ] 视频/文案支持关键词搜索
- [ ] 各 Tab 支持多选批量删除
- [ ] TypeScript tsc --noEmit 零错误
- [ ] Python import check 通过
- [ ] 素材管理全部 27 个需求点完成
