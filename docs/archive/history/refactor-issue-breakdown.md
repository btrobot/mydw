# Historical Planning Reference — Refactor Issue Breakdown

> 状态：历史规划参考（historical planning reference），**不是当前 authoritative truth 文档**。  
> 当前阅读入口请先看：
> - `docs/README.md`
> - `docs/current-architecture-baseline.md`
> - `docs/current-runtime-truth.md`
>
> 说明：
> - 本文档记录的是重构任务拆分与阶段性 issue breakdown
> - `.omx` 历史 planning context 仍可能引用本文档，但这些引用不等于当前 truth source
> - 当前系统事实与边界应以 current docs 为准

# Epic 1：统一调度配置真相

## Task 1.1 盘点 PublishConfig / ScheduleConfig 的真实使用路径
**说明**

梳理以下链路分别读写哪张表、哪个接口、哪个页面：

- `backend/api/publish.py`
- `backend/services/scheduler.py`
- `backend/services/publish_service.py`
- `frontend/src/pages/ScheduleConfig.tsx`
- `frontend/src/hooks/usePublish.ts`
- `backend/models/__init__.py`

**验收标准**

- 输出一份 mapping 表
- 明确“当前唯一 runtime 真相来源”与“遗留兼容来源”
- 标出需要迁移的调用点

---

## Task 1.2 将 ScheduleConfig 定义为唯一调度配置模型
**说明**

把调度相关配置统一收口到 `ScheduleConfig`，`PublishConfig` 只保留兼容角色，不再作为新逻辑依赖。

**验收标准**

- 调度器只读 `ScheduleConfig`
- 发布控制相关配置读取路径只剩一套
- 代码注释/文档明确 `PublishConfig` 为 deprecated

---

## Task 1.3 新增明确的调度配置 API
**说明**

新增或切换为更清晰的接口：

- `GET /api/schedule-config`
- `PUT /api/schedule-config`

旧 `/api/publish/config` 短期兼容转发或标记废弃。

**验收标准**

- 新接口可稳定读写配置
- 旧接口有兼容策略或明确废弃策略
- Swagger/OpenAPI 中可见新接口

---

## Task 1.4 移除 publish API 中的平行状态真相
**说明**

`backend/api/publish.py` 当前 `_publish_status` 与 `scheduler` 存在双轨状态。改为 API 只读 scheduler 的真实状态。

**验收标准**

- 删除或弃用 `_publish_status`
- `/api/publish/status` 返回值来自 scheduler 实际状态
- 不再出现 API 状态与后台 loop 状态不一致

---

## Task 1.5 前端调度配置页切换到新接口
**说明**

更新：

- `frontend/src/pages/ScheduleConfig.tsx`
- 必要时新增 `frontend/src/hooks/useScheduleConfig.ts`

**验收标准**

- 页面保存后，调度器读取到的是同一份数据
- 页面不再直接依赖旧接口语义
- 页面错误提示与加载逻辑正常

---

# Epic 2：统一任务模型与执行语义

## Task 2.1 输出“任务资源集合 vs 执行语义”设计说明
**说明**

明确当前版本下这些资源的业务语义：

- video
- copywriting
- cover
- audio
- topic
- profile

尤其要定义：
- 哪些是合成输入
- 哪些是最终发布输入
- 哪些允许多选
- 哪些当前只支持单选

**验收标准**

- 形成 repo 内文档
- 前后端开发能据此实现一致行为
- 明确当前版本是否支持“多资源直接发布”

---

## Task 2.2 在发布前增加任务可执行性校验
**说明**

不要再在 `PublishService` 中静默取第一项。  
发布前必须显式校验任务是否满足当前发布语义。

涉及：
- `backend/services/publish_service.py`

**验收标准**

- 非法任务不会静默降级执行
- 返回明确错误原因
- 日志中能看出失败是“语义不支持”还是“运行异常”

---

## Task 2.3 在任务组装阶段增加约束或警告
**说明**

在 `TaskAssembler` 或任务创建 API 处增加输入约束，避免创建出“UI 看起来合法、但执行不合法”的任务。

涉及：
- `backend/services/task_assembler.py`
- `backend/api/task.py`

**验收标准**

- 非法组合在创建阶段即可被拒绝或标记
- 创建结果与后续执行语义一致
- 接口返回错误信息明确

---

## Task 2.4 前端任务创建页与详情页对齐真实语义
**说明**

更新：

- `frontend/src/pages/task/TaskCreate.tsx`
- `frontend/src/pages/task/TaskDetail.tsx`

UI 要明确告诉用户：
- 当前哪些字段是“合成输入”
- 哪些是“最终发布输入”
- 多选时系统如何处理

**验收标准**

- 页面文案与后端规则一致
- 用户不会误以为多资源会全部参与直接发布
- 非法组合在 UI 上有提示

---

## Task 2.5 标记 Task 旧单资源 FK 为兼容遗留
**说明**

对 `Task` 上旧字段：

- `product_id`
- `video_id`
- `copywriting_id`
- `audio_id`
- `cover_id`

做正式退役管理。

**验收标准**

- schema / serializer 中标注 deprecated
- 新代码路径不再新增对旧 FK 的依赖
- 形成后续删除计划

---

# Epic 3：收口前后端接口契约

## Task 3.1 盘点所有手写 axios 补丁点
**说明**

统计哪些页面/hooks 已绕开生成客户端：

- `frontend/src/hooks/useAccount.ts`
- `frontend/src/pages/ScheduleConfig.tsx`
- 其他 hooks / pages

**验收标准**

- 输出补丁点清单
- 每个点标明原因：OpenAPI 缺字段 / 接口未建模 / 临时实现
- 给出优先级排序

---

## Task 3.2 修正后端 schema 使其反映真实接口
**说明**

梳理这些模块的 schema 与接口是否一致：

- account
- task
- profile
- publish / schedule-config
- topic / topic-group
- system

**验收标准**

- OpenAPI 能表达当前真实请求/响应结构
- 新增字段不再只存在于“代码里”
- 主要页面依赖的数据字段都有 schema 支撑

---

## Task 3.3 重新生成前端 API client
**说明**

基于更新后的 OpenAPI 重新生成：

- `frontend/src/api/*`

**验收标准**

- 成功生成
- 编译通过
- 主要页面可切换到生成客户端

---

## Task 3.4 用生成客户端替换高频手写请求
**说明**

优先替换高频、核心页面中的手写请求。

建议优先：
- account
- schedule config
- task
- profile

**验收标准**

- 高优先模块大多使用生成 client
- 手写 axios 仅保留少数特殊场景
- hooks 可维护性提升

---

## Task 3.5 建立 API 变更工作流文档
**说明**

定义以后变更接口时的固定流程：

1. 改 schema/API
2. 更新 OpenAPI
3. 生成前端 client
4. 接入页面
5. 更新文档

**验收标准**

- repo 内有明确流程文档
- 新增接口时团队知道标准路径
- 不再长期依赖“前端临时补洞”

---

# Epic 4：解耦 Electron 与后端运行环境

## Task 4.1 盘点 Electron 主进程对 backend 启动的硬编码依赖
**说明**

梳理 `frontend/electron/main.ts` 当前依赖的：

- Python 路径
- venv 结构
- dev/prod 启动方式
- backend 可执行文件路径

**验收标准**

- 输出依赖清单
- 标出哪些是平台耦合、哪些是必要协议
- 给出抽象边界建议

---

## Task 4.2 抽象统一的 backend 启动入口
**说明**

引入脚本或配置层，例如：

- `scripts/start-backend-dev.*`
- `scripts/start-backend-prod.*`

Electron 不再直接知道 Python venv 结构。

**验收标准**

- 主进程只调用统一入口
- backend 启动细节不再写死在 Electron 中
- dev/prod 启动逻辑更清晰

---

## Task 4.3 增加 backend 健康检查与启动等待机制
**说明**

Electron 在 backend ready 前不要假定系统可用。

**验收标准**

- 启动时有明确探活逻辑
- backend 未 ready 时有可观测行为
- 降低“前端先起但后端未就绪”的异常

---

## Task 4.4 精简 Electron 主进程职责
**说明**

主进程只保留：

- 窗口
- 托盘
- IPC
- backend 生命周期管理

避免继续承载业务逻辑或环境细节。

**验收标准**

- `main.ts` 复杂度下降
- 启动/停止逻辑更可测
- 平台相关代码集中管理

---

# Epic 5：清理系统设置与伪配置能力

## Task 5.1 盘点 system/config 与 Settings 页的真实可用能力
**说明**

梳理以下是否真生效：

- 素材路径
- auto backup
- log level
- backup
- 其他设置项

涉及：
- `backend/api/system.py`
- `frontend/src/pages/Settings.tsx`

**验收标准**

- 输出“真实能力 / 占位能力”清单
- 标出哪些应该做真，哪些应该下线
- 页面不再假装所有配置都可保存

---

## Task 5.2 让 system/config 要么真可配，要么下线
**说明**

避免半成品接口长期暴露。

**验收标准**

- 每个接口字段都对应真实配置源
- 无法生效的项被移除或标明未开放
- API 文档与页面行为一致

---

## Task 5.3 精简 Settings 页面
**说明**

Settings 只保留真实能力，例如：

- 数据备份
- 真正可配置的路径/日志级别
- 只读系统信息

**验收标准**

- 页面上的每个控制项都真能影响系统
- 没有“保存成功但没效果”的配置
- 页面内容与 backend capability 对齐

---

# Epic 6：数据模型去历史包袱

## Task 6.1 盘点 JSON-in-text 字段并分类
**说明**

重点关注：

- `accounts.tags`
- `tasks.source_video_ids`
- `tasks.composition_params`
- `publish_profiles.composition_params`
- `publish_profiles.global_topic_ids`
- `topic_groups.topic_ids`
- `publish_config.global_topic_ids`

分类标准：
- 配置型
- 查询型
- 关系型
- 临时兼容型

**验收标准**

- 每个字段有归类
- 明确哪些应继续 JSON，哪些应结构化
- 有后续迁移优先级

---

## Task 6.2 盘点旧字段与旧模型的残余依赖
**说明**

包括但不限于：
- `Task` 旧 FK
- `PublishConfig`
- 单资源假设相关代码

**验收标准**

- 输出依赖矩阵
- 明确删除前置条件
- 为后续 migration 提供依据

---

## Task 6.3 制定字段清理与迁移计划
**说明**

不是立即删除，而是形成可执行迁移路线：

- 兼容期
- 双写/只读期
- 删除期

**验收标准**

- 有明确版本化迁移计划
- 说明每一步风险和回滚策略
- 不再无限期保留历史包袱

---

# Epic 7：文档与版本真相收口

## Task 7.1 建立当前架构基线文档
**说明**

把你 `~/docs` 中更接近真实系统的内容整理进 repo：

建议文件：
- `docs/current-architecture-baseline.md`
- `docs/runtime-truth.md`

**验收标准**

- 新人能靠这份文档理解系统
- 文档描述与当前代码一致
- 不再只能依赖“私有分析文档”

---

## Task 7.2 清理过期文档并打过时标记
**说明**

清查：

- `README.md`
- `docs/archive/reference/system-architecture.md`
- 其他偏旧设计文档

**验收标准**

- 过期文档明确标记
- 当前推荐阅读路径清晰
- 不再混淆单资源旧模型与当前多资源模型

---

## Task 7.3 统一版本号与发布元信息
**说明**

当前：
- README 写 `0.2.0`
- 前后端代码仍 `0.1.0`

需要统一。

**验收标准**

- README / frontend / backend / about 信息一致
- 构建产物版本显示一致
- 不再出现多套版本号

---

# Epic 8：最小回归测试与验收闭环

## Task 8.1 建立核心业务链路回归清单
**说明**

锁定 6 条主链路：

1. 调度配置保存并生效
2. 单资源任务创建成功
3. 非法多资源任务被拒绝/提示
4. 合成任务状态推进
5. 调度器启动/停止状态正确
6. 发布成功/失败状态回写正确

**验收标准**

- 清单落地到 repo
- 每条链路有验收步骤
- 重构时可重复执行

---

## Task 8.2 为配置与任务语义补最小自动化测试
**说明**

优先给最易回归、最关键的点补测试：

- 调度配置 API
- 发布前校验
- 任务状态流转
- scheduler 状态读取

**验收标准**

- 关键行为有自动化保护
- 重构不会靠人工猜回归
- CI/本地可运行

---

## Task 8.3 建立“重构完成定义”
**说明**

定义每个 Epic 何时算完成：

- 代码已收口
- 页面已对齐
- 文档已更新
- 测试已覆盖主链路

**验收标准**

- 每个 Epic 都有明确 DoD
- 避免“代码改了但系统真相仍分裂”
- 后续迭代可复用该标准

---

# 推荐实施顺序

## 第一批立即开工
1. Epic 1：统一调度配置真相
2. Epic 2：统一任务模型与执行语义
3. Epic 8：补最小回归

## 第二批
4. Epic 3：收口前后端接口契约
5. Epic 7：文档与版本真相收口

## 第三批
6. Epic 4：解耦 Electron 与后端运行环境
7. Epic 5：清理系统设置与伪配置
8. Epic 6：数据模型去历史包袱
