# Historical Planning Reference — 重构总目标

> 状态：历史规划参考（historical planning reference），**不是当前 authoritative truth 文档**。  
> 当前阅读入口请先看：
> - `docs/README.md`
> - `docs/current-architecture-baseline.md`
> - `docs/current-runtime-truth.md`
>
> 说明：
> - 本文档记录的是当时的重构规划视角，保留供历史回溯和 `.omx` 历史 planning context 参考
> - `.omx` 中仍出现对本文档的引用，并不表示它仍是当前系统真相
> - 当前系统的 present-tense 行为与权威边界应以 current docs 为准

# 重构总目标

用 3 个阶段解决 4 类问题：

1. **配置真相分裂**
2. **任务模型与执行语义不一致**
3. **前后端契约漂移**
4. **桌面壳与运行环境耦合过深**

原则：

- 不推倒重来
- 先统一事实，再抽象
- 先修主链路，再修外围
- 每阶段都可独立验收

---

# Phase 0：冻结现状与建立基线（1~2 天）

## 目标
先让后面的改动有“参考系”，避免一边改一边失真。

## 要做的事
### 1. 统一“当前真相”文档
以你 `~/docs` 里的分析为基础，整理一份 repo 内正式基线文档：

建议新增：
- `docs/current-architecture-baseline.md`
- `docs/current-runtime-truth.md`

内容只写当前真实行为，不写理想设计。

### 2. 列出真相冲突清单
建一个追踪文档：

- `docs/refactor-gap-list.md`

至少列这几项：
- `PublishConfig` vs `ScheduleConfig`
- 多资源任务 vs 发布只取第一项
- OpenAPI client vs 手写 axios
- Electron 启动 backend 的 Windows 路径依赖
- `system/config` 和 `Settings` 的伪配置

### 3. 建最小回归清单
不是先补齐所有测试，而是先明确必须保住的核心流程：

- 账号登录/会话检查
- 创建任务
- 合成任务转 ready
- 发布任务
- 调度启动/停止
- 配置保存并生效

## 交付物
- `docs/current-architecture-baseline.md`
- `docs/refactor-gap-list.md`
- `docs/regression-checklist.md`

## 验收标准
- 团队成员不需要靠猜代码来理解当前系统
- 后面每个重构任务都能对应到 gap list

---

# Phase 1：统一配置真相（3~5 天）

## 目标
把“调度配置”收口成一套唯一真相。

## 核心问题
当前：
- 页面走 `/api/publish/config`
- 调度器读 `ScheduleConfig`
- 模型里还有 `PublishConfig`

这是最先该打掉的分裂点。

## 要做的事
### 1. 确定唯一主模型
建议：
- **保留 `ScheduleConfig` 作为唯一调度配置模型**
- `PublishConfig` 进入兼容废弃状态

涉及文件：
- `backend/models/__init__.py`
- `backend/api/publish.py`
- `backend/services/scheduler.py`

### 2. 调整 API 边界
建议新增或迁移为更明确的接口：

- `GET /api/schedule-config`
- `PUT /api/schedule-config`

旧接口：
- `/api/publish/config`

处理方式：
- 短期兼容转发
- 明确标注 deprecated

### 3. 前端页面改成只依赖新接口
涉及：
- `frontend/src/pages/ScheduleConfig.tsx`
- `frontend/src/hooks/usePublish.ts` 或新增 `useScheduleConfig.ts`

### 4. 去掉 API 层的“平行状态”
`backend/api/publish.py` 里的 `_publish_status` 不应再作为真相源。

应改成：
- API 只读 scheduler 当前状态
- 不自己维护另一套 running/paused/idle 状态字典

## 交付物
- 单一配置模型
- 单一调度配置 API
- 页面已切换
- 旧接口兼容但不再扩展

## 验收标准
- 页面保存的配置 = 调度器实际读取配置
- 启停状态只从 scheduler 真实状态读取
- 不再出现“保存成功但运行不一致”

---

# Phase 2：统一任务语义（5~7 天）

## 目标
解决“模型支持多资源，但执行只取第一项”的语义裂缝。

## 核心问题
当前最大风险不是代码报错，而是**静默降级**。

## 两种路线
### 路线 A：短期保守
当前版本明确规定：

- 发布阶段只支持：
  - 1 个最终视频
  - 0/1 文案主输出
  - 0/1 封面主输出
  - 话题可多选

多资源只允许作为“合成输入”，不允许直接当“发布输入”。

### 路线 B：中期增强
真正设计多资源发布语义。

例如：
- 多视频 = 合成输入
- 多文案 = 候选文案 / 轮播策略
- 多封面 = 候选封面 / 最终只选一个
- 多音频 = 合成输入，不是直接发布输入

**建议先走 A，再规划 B。**

## 要做的事
### 1. 明确 Task 的“执行视图”
把 Task 分成两个概念：

- **资源集合模型**
- **执行快照模型 / 可发布视图**

即便不马上新增表，也要先在服务层定义清楚。

涉及：
- `backend/services/task_assembler.py`
- `backend/services/publish_service.py`

### 2. 发布前做显式校验
不要再静默 `task.videos[0]`

应变成：
- 如果当前发布语义不支持多资源，返回明确错误
- 或在组装阶段就限制输入

### 3. 前端同步约束
涉及：
- `frontend/src/pages/task/TaskCreate.tsx`
- `frontend/src/pages/task/TaskDetail.tsx`

UI 要明确告诉用户：
- 哪些是“合成输入”
- 哪些是“最终发布输入”

### 4. 旧 FK 字段进入退役计划
`Task` 上这些兼容字段要正式标注：

- `product_id`
- `video_id`
- `copywriting_id`
- `audio_id`
- `cover_id`

短期：
- schema 标成 deprecated/compat
- 页面不再依赖它们

中期：
- 盘点残余依赖
- 为删除做准备

## 交付物
- 任务执行语义说明文档
- 发布前校验逻辑
- UI 文案与行为一致
- 旧 FK 进入退役清单

## 验收标准
- 用户创建“多资源任务”时，系统行为可预测
- 发布结果不再偷偷只取第一项
- API 返回语义与页面展示一致

---

# Phase 3：收口前后端契约（4~6 天）

## 目标
让 OpenAPI 再次成为唯一接口契约源。

## 核心问题
当前已经出现：
- 生成 client 不完整
- 前端 hooks 手写 axios 打补丁

这会快速把维护成本抬高。

## 要做的事
### 1. 先补 backend schema
梳理这些模块是否和真实接口一致：

- account
- task
- profile
- publish / schedule-config
- topic / topic-group
- system

涉及：
- `backend/schemas/*`
- `backend/api/*`

### 2. 重新生成前端 client
涉及：
- `frontend/openapi.config.ts`
- `frontend/src/api/*`

### 3. 清理手写 axios 补丁
优先清理这些点：
- `frontend/src/hooks/useAccount.ts`
- `frontend/src/pages/ScheduleConfig.tsx`
- 其他直接绕过生成 client 的 hooks/pages

### 4. 约定新增接口流程
以后统一流程：
1. 改 schema / API
2. 更新 OpenAPI
3. 重新生成 client
4. 前端接入
5. 补文档

## 交付物
- 更新后的 OpenAPI client
- hooks 基本回归生成客户端
- API 变更流程文档

## 验收标准
- 前端大多数请求都走生成 client
- 手写 axios 只保留极少数特殊场景
- 页面开发不再需要“读源码猜接口”

---

# Phase 4：解耦 Electron 与运行环境（3~4 天）

## 目标
把 Electron 从“知道 Python venv 布局”降级成“只负责拉起后端入口”。

## 核心问题
`frontend/electron/main.ts` 当前直接依赖：

- `backend/venv/Scripts/python.exe`

这非常脆。

## 要做的事
### 1. 抽象 backend 启动命令
建议统一成一层脚本/配置：

例如：
- `scripts/start-backend-dev.(bat|sh|js)`
- Electron 只调用这个入口

### 2. 区分开发/生产启动协议
Electron 关心的是：
- dev 如何启动
- prod 如何启动
- 如何探活
- 如何停止

而不是 Python 细节。

### 3. 增加健康检查等待
当前最好显式等待：
- backend `/health` ready
- 再允许完整功能交互

### 4. 为跨平台留接口
即便现在主要跑 Windows，也别把路径结构写死在主进程。

## 交付物
- 统一 backend 启动脚本
- Electron 主进程精简
- 启动协议文档

## 验收标准
- 本地环境变化不会立刻打崩 Electron 启动
- 主进程不再硬编码 venv 结构
- dev/prod 启动逻辑更清晰

---

# Phase 5：清理“假配置 / 假功能”页面（2~3 天）

## 目标
让 Settings / System 接口只暴露真实生效能力。

## 核心问题
当前：
- `backend/api/system.py` 有 TODO / 硬编码
- `frontend/src/pages/Settings.tsx` 也偏展示性质

## 要做的事
### 1. 划分真实配置与占位配置
分成：
- 启动时配置：环境变量
- 运行时配置：数据库/文件
- 只读信息：展示型系统信息

### 2. Settings 页面只保留真实能力
例如：
- 数据备份
- 日志级别（如果真生效）
- 素材根目录（如果真可配）

没实现的：
- 明确标注“未开放”
- 不要伪装成可保存

### 3. system/config 要么做真，要么删掉
不要半真半假。

## 交付物
- 简化后的 Settings 页
- 真实可配置项清单
- 删除/隐藏伪能力

## 验收标准
- 页面上每个配置项都真能影响系统
- 用户不会被假按钮/假保存误导

---

# Phase 6：数据模型去历史包袱（1~2 周，可穿插进行）

## 目标
减少“兼容遗留”带来的长期认知负担。

## 优先处理
### 1. JSON-in-text 字段盘点
重点：
- `accounts.tags`
- `tasks.source_video_ids`
- `tasks.composition_params`
- `publish_profiles.composition_params`
- `publish_profiles.global_topic_ids`
- `topic_groups.topic_ids`
- `publish_config.global_topic_ids`

### 2. 决定哪些继续保留 JSON，哪些要结构化
建议：
- 真正需要查询/约束/关联的，逐步结构化
- 纯配置型、低查询需求的，可继续 JSON

### 3. 清理旧 FK
在确认无依赖后，规划移除：
- `Task` 旧单资源 FK 列

## 交付物
- 数据字段分类表
- 旧字段依赖盘点
- 迁移计划文档

## 验收标准
- 新开发不再依赖兼容旧字段
- 需要查询的结构不再藏在 text JSON 里

---

# 推荐执行顺序

## 第一波（最值得先做）
1. Phase 0 基线
2. Phase 1 配置收口
3. Phase 2 任务语义收口

## 第二波
4. Phase 3 OpenAPI 契约收口
5. Phase 4 Electron 解耦

## 第三波
6. Phase 5 假配置清理
7. Phase 6 模型去历史包袱

---

# 建议按周拆分

## 第 1 周
- 完成 Phase 0
- 完成 Phase 1
- 输出任务语义设计草案

## 第 2 周
- 完成 Phase 2
- 同步前端页面与提示文案
- 补最小回归测试

## 第 3 周
- 完成 Phase 3
- 重新生成 OpenAPI client
- 清理主要 axios 补丁

## 第 4 周
- 完成 Phase 4 + Phase 5
- 启动 Phase 6 的字段盘点

---

# 最小测试策略

建议不要一开始追求全量测试，先锁 6 条主链路：

1. 调度配置读取/保存一致
2. 创建单资源任务成功
3. 创建不合法多资源发布任务时能被拒绝/提示
4. 合成任务能从 `draft -> composing -> ready`
5. 调度器能启动/停止并读取真实状态
6. 发布成功/失败能正确回写 task 状态和日志

---

# 最后给你的执行建议

如果你要马上开始，我建议第一批 issue 就开这 5 个：

1. **统一调度配置模型与接口**
2. **移除 publish API 的平行状态真相**
3. **定义任务发布语义并加入发布前校验**
4. **前端任务页/调度页与真实后端语义对齐**
5. **更新 OpenAPI 并清理关键 axios 补丁**
