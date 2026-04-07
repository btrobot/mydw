# 素材管理 — 用户手册 vs 当前实现偏差分析

> 日期: 2026-04-07
> 参考: docs/user-guide.md (产品手册)

---

## 手册描述的工作流

```
找爆款视频 → 下载到本地 → 扫描/导入 → 添加商品
    → AI合成(多视频拼接) → 提取标题文案 → 搜索话题
    → 创建任务(素材+商品+账号自动关联) → 定时发布
```

---

## 偏差清单

| # | 手册描述 | 当前实现 | 偏差程度 |
|---|----------|----------|----------|
| 1 | 选择 2个以上源视频合成 | AI剪辑只支持单视频输入（高光检测→裁剪），无多视频拼接 | **缺失** |
| 2 | 合成后点击"提取"自动提取标题和文案 | 无提取功能，文案只是 Material type=text 的静态文件 | **缺失** |
| 3 | 搜索热门话题，选择~5个，自动应用到后续所有视频 | 话题只是 Material type=topic 的文本文件，无搜索 API，无"全局话题"概念 | **缺失** |
| 4 | 商品在素材管理页面添加，素材与商品直接关联 | 商品 CRUD 在 `/api/system/products`，前端 Material.tsx 无商品入口；Material 模型无 product_id | **错位** |
| 5 | 创建任务时系统自动填入标题、文案、话题 | `auto_generate_tasks` 用轮询方式 `texts[i % len]` 机械分配，无智能匹配 | **粗糙** |
| 6 | 文案模式：勾选"原文案"或"自动文案" | 无文案模式选项，AI剪辑页面无文案相关 UI | **缺失** |
| 7 | 素材时长要求（单个素材最短30秒） | AI剪辑无最短时长校验 | **缺失** |
| 8 | 合成时长参数（2-5分钟） | 目标时长滑块范围 15-180秒，默认60秒，和手册"2-5分钟"不匹配 | **偏差** |
| 9 | 素材与商品绑定后发布时自动关联商品链接 | Task 有 product_id FK，但发布流程 PublishService 未读取 Product.link 填入发布页面 | **未打通** |
| 10 | `init-from-materials` 应该是核心流程 | 实际实现和 `auto-generate` 完全相同，都调用同一个 `auto_generate_tasks`，是个空壳 | **假实现** |

---

## 架构层面的根本问题

### 1. 素材模型太扁平

当前 Material 是一个通用的文件记录表，用 type 字段区分 video/text/cover/topic/audio。但手册的工作流需要的是一个**合成项目**的概念 — 多个源视频 + 商品 + 文案 + 话题组成一个发布单元。

相关代码:
- `backend/models/__init__.py` — Material 模型
- `backend/schemas/__init__.py` — MaterialCreate/MaterialResponse

### 2. AI剪辑和素材管理是割裂的

AI剪辑页面是独立的"工具"（输入路径 → 输出文件），剪辑结果不会自动回写到素材库，也不会关联到任务。手册描述的是一个连贯的 pipeline：合成 → 提取 → 入库 → 建任务。

相关代码:
- `frontend/src/pages/AIClip.tsx` — 独立的路径输入，无素材库联动
- `backend/services/ai_clip_service.py` — 纯 FFmpeg 工具，无数据库交互
- `backend/api/ai.py` — API 层无素材回写逻辑

### 3. 话题是静态的，不是动态搜索的

手册明确说"搜索热门话题及其热度"，这需要调用得物平台的话题搜索 API（通过 Playwright 自动化或平台接口）。当前只是把本地 .txt 文件当话题用。

相关代码:
- `backend/services/material_service.py` — topic 只是文件扫描
- `backend/core/dewu_client.py` — 无话题搜索方法

### 4. 商品管理位置错误

手册说商品在"素材管理"页面添加，但实际放在 system.py 的 `/api/system/products`。前端素材页面完全没有商品管理入口。

相关代码:
- `backend/api/system.py:155-182` — 商品 CRUD 在系统模块
- `frontend/src/pages/Material.tsx` — 无商品相关 UI

### 5. 任务自动生成是假实现

`/tasks/init-from-materials` 和 `/tasks/auto-generate` 调用的是同一个 `TaskService.auto_generate_tasks()`，用 `texts[i % len(texts)]` 轮询分配文案，无法实现手册描述的"系统自动填入标题、文案和话题"的智能关联。

相关代码:
- `backend/services/task_service.py:222-260` — auto_generate_tasks
- `backend/api/task.py:204-223` — init-from-materials 端点
