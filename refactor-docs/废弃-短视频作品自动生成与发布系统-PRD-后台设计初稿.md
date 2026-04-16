# 短视频作品自动生成与发布系统 PRD + 后台设计初稿

> 版本：Draft v0.1  
> 更新时间：2026-04-16  
> 文档类型：产品需求文档 + 后台系统设计初稿  
> 适用角色：业务分析师、产品经理、后台开发、测试、运维

---

## 1. 项目背景

当前内容生产过程普遍存在以下问题：

- 素材来源分散：视频、封面、音频、商品信息、文案模板分散在不同来源。
- 生产过程依赖人工：下载、裁剪、选片、配文、合成、发布步骤繁琐且重复。
- 批量生产效率低：同类商品/素材需要重复操作，无法稳定批量产出。
- 过程不可追踪：失败原因、重试过程、发布结果缺少统一记录。
- 人工审核点不明确：自动生成结果与最终发布之间缺少清晰的人机协作环节。

因此，需要建设一套 **短视频作品自动生成与发布系统**，将素材采集、内容生成、成品合成、人工审核、自动发布串成标准化任务流程。

---

## 2. 产品目标

### 2.1 核心目标

构建一个面向内容运营场景的任务式工作流系统，实现：

1. 将视频、封面、音频、商品信息、文案模板统一组织为任务。
2. 自动完成视频切片、选片、文案生成、视频合成、成品打包。
3. 支持人工预览、人工修改、局部重试。
4. 支持将审核通过的作品自动发布到目标平台。
5. 支持全流程状态追踪、失败诊断、批量重试与审计留痕。

### 2.2 业务目标

- 提升内容生产效率。
- 降低人工重复操作成本。
- 提高作品产出的一致性和可控性。
- 为后续多渠道发布、多模板策略、多账号管理打基础。

---

## 3. 非目标

本期不包含：

- 复杂的素材智能理解（如镜头语义评分、人物识别、自动分镜推荐）。
- 多租户 SaaS 完整能力。
- 完整的商业化计费系统。
- 所有平台的官方发布 API 适配。
- 高度自动化无人值守发布策略中心。

---

## 4. 用户角色

| 角色 | 职责 |
|------|------|
| 运营人员 | 创建任务、录入素材、查看结果、提交审核/发布 |
| 内容审核人员 | 预览作品、修改文案、替换素材、审核通过/驳回 |
| 发布人员 | 选择发布账号、确认发布、跟踪发布结果 |
| 系统管理员 | 管理模板、滤词规则、账号配置、系统参数 |
| 后台任务系统 | 自动执行生成、重试、回写状态、留存日志 |

---

## 5. 核心概念模型

### 5.1 业务对象

- **任务 Task**：一次完整的作品生成与发布流程。
- **任务项 TaskItem**：任务下的一条具体作品产出。
- **素材 Asset**：视频、封面、音频、文本、商品资料等输入物料。
- **规则模板 RuleTemplate**：切片规则、选片规则、文案规则、发布规则。
- **作品包 Package**：最终产出的标准化作品目录及文件集合。
- **发布账号 PublishAccount**：用于目标平台发布的账号及会话信息。
- **发布记录 PublishRecord**：发布结果、失败原因、平台回执。

### 5.2 产物标准（四件套）

建议统一输出为标准作品包：

- `1.mp4`：最终合成视频
- `1.jpg`：封面图
- `商品名称.txt`：标题/商品名称
- `文案.txt`：正文文案

可扩展字段：

- `topics.json`：话题列表
- `manifest.json`：该作品包的结构化元信息
- `preview.gif`：用于审核列表快速预览

---

## 6. 业务流程总览

```text
创建任务
  → 上传/导入素材
  → 配置生成策略
  → 启动任务
  → 素材预处理（下载/校验/切片）
  → 文案生成与清洗
  → 选片与合成
  → 生成作品包
  → 人工审核/修改
  → 审核通过后发布
  → 回写发布结果
```

### 6.1 阶段拆分

1. **任务输入阶段**
   - 创建任务
   - 选择商品/主题/渠道/账号
   - 录入素材和模板

2. **素材预处理阶段**
   - 视频下载或归档
   - 格式校验
   - 视频切片
   - 封面图/音频候选池准备

3. **内容生成阶段**
   - 选片
   - 生成文案
   - 滤词清洗
   - 匹配商品信息和话题

4. **成品合成阶段**
   - 生成 concat 清单
   - 合成视频
   - 输出作品包

5. **审核确认阶段**
   - 预览封面/视频/文案
   - 允许替换封面、重生成文案、重合成视频

6. **发布执行阶段**
   - 选择发布账号
   - 注入会话
   - 自动填充平台发布表单或调用适配接口
   - 回写结果

---

## 7. 产品交互设计初稿

## 7.1 页面结构建议

### 页面一：任务列表页

展示：

- 任务名称
- 任务类型
- 创建人
- 当前阶段
- 任务状态
- 作品数 / 成功数 / 失败数
- 创建时间 / 更新时间

操作：

- 创建任务
- 查看详情
- 重试失败项
- 取消任务
- 导出结果

### 页面二：任务创建页（向导式）

建议分 5 步：

1. 基本信息
2. 素材配置
3. 生成策略
4. 结果预览
5. 发布确认

### 页面三：任务详情页

展示：

- 任务级进度条
- 各阶段执行日志
- 作品项列表
- 失败原因
- 可执行操作（重试/审核/发布）

### 页面四：作品详情抽屉/详情页

展示：

- 视频预览
- 封面图
- 商品名称
- 文案
- 话题
- 发布状态
- 版本记录

操作：

- 替换封面
- 编辑商品名称
- 重生成文案
- 重选片
- 重新合成
- 审核通过 / 驳回

### 页面五：系统配置页

管理：

- 文案模板
- 滤词规则
- 切片策略
- 发布渠道配置
- 发布账号管理
- 存储与转码参数

---

## 7.2 关键交互规则

### 规则 1：整批任务 + 单条作品双层管理

- 任务级用于管理整批流程。
- 作品级用于人工介入和局部重试。
- 任一作品失败不应阻塞其他作品继续生成。

### 规则 2：自动化与人工确认分层

系统支持三种模式：

- 全自动生成 + 自动发布
- 自动生成 + 人工审核后发布（推荐）
- 自动生成 + 人工导出手工发布

### 规则 3：关键节点必须可重试

至少以下节点支持单独重试：

- 素材下载
- 视频切片
- 文案生成
- 视频合成
- 发布执行

### 规则 4：版本化管理

需要保留：

- 文案版本
- 视频渲染版本
- 封面替换记录
- 审核记录

---

## 8. 功能需求

## 8.1 任务创建

### 输入字段

| 字段 | 必填 | 说明 |
|------|------|------|
| 任务名称 | 是 | 用于标识任务 |
| 任务类型 | 是 | 单品、批量、模板化任务 |
| 渠道 | 是 | 目标发布渠道 |
| 发布账号 | 否 | 可后置选择 |
| 生成数量 | 是 | 预期生成作品数量 |
| 话题策略 | 否 | 固定话题/轮换话题/自动推荐 |
| 自动发布 | 否 | 是否审核通过后自动发布 |

### 校验要求

- 至少有 1 份视频素材。
- 至少有 1 张封面图或允许系统后续补齐。
- 至少有商品名称或标题来源。
- 若选择自动发布，必须绑定可用发布账号。

---

## 8.2 素材管理

### 支持素材类型

- 视频：URL、本地上传、对象存储引用
- 封面图：JPG/PNG
- 音频：MP3/WAV
- 商品信息：标题、卖点、SKU、标签
- 文案输入：模板、主题词、卖点词

### 关键能力

- 批量上传
- URL 导入
- 重复素材去重
- 素材状态跟踪（待处理/处理中/可用/失败）
- 元数据提取（时长、分辨率、大小、格式）

---

## 8.3 视频处理

### 功能要求

- 支持按固定时长切片。
- 支持候选片段池管理。
- 支持无放回抽样或自定义策略选片。
- 支持标准化输出为 9:16。
- 支持配音/背景音乐混流。
- 支持多种输出质量模板。

### MVP 默认策略

- 切片时长：2 秒
- 输出比例：1080 x 1920
- 候选池来源：全部切片结果
- 选片方式：随机无放回
- 音频来源：候选池中随机选择 1 条

---

## 8.4 文案生成

### 功能要求

- 支持模板化 Prompt。
- 支持变量替换（商品名、卖点、视频序号、话题等）。
- 支持调用外部大模型服务。
- 支持空结果/异常重试。
- 支持滤词清洗。
- 支持多条文案生成及映射。

### 输出规则

- 一条作品对应一条主文案。
- 若批量生成多条文案，按序号对应作品项。
- 文案为空时禁止进入发布阶段。

---

## 8.5 审核与编辑

### 审核动作

- 通过
- 驳回
- 退回重生成
- 手动修改后通过

### 可编辑项

- 封面图
- 商品名称
- 文案
- 话题
- 发布账号

### 审核限制

- 未通过审核的作品不得进入发布队列。
- 被驳回作品需生成新版本后重新审核。

---

## 8.6 发布执行

### 功能要求

- 支持多账号管理。
- 支持会话有效性检测。
- 支持渠道适配层抽象。
- 支持自动填充标题、正文、话题、视频、封面。
- 支持发布结果回写。
- 支持失败重试。

### 发布模式

- 浏览器自动化发布
- 官方 API 发布（若渠道支持）
- 半自动辅助发布

### 发布结果

- 成功：记录平台作品 ID / URL / 时间
- 失败：记录错误码、错误信息、截图、重试次数

---

## 9. 状态机设计

## 9.1 任务状态

```text
CREATED
→ ASSETS_PENDING
→ ASSETS_READY
→ PROCESSING
→ COPY_GENERATING
→ RENDERING
→ PACKAGE_READY
→ WAITING_REVIEW
→ APPROVED
→ PUBLISHING
→ PUBLISHED
```

异常状态：

- `PART_FAILED`
- `FAILED`
- `CANCELED`

## 9.2 作品项状态

```text
PENDING
→ MATERIAL_READY
→ COPY_READY
→ RENDER_READY
→ WAITING_REVIEW
→ APPROVED
→ PUBLISHING
→ PUBLISHED
```

异常状态：

- `COPY_FAILED`
- `RENDER_FAILED`
- `REVIEW_REJECTED`
- `PUBLISH_FAILED`

---

## 10. 后台系统设计初稿

## 10.1 总体架构

建议采用 **任务编排 + 能力服务** 架构。

```text
Admin UI / API Client
        ↓
API Gateway / Backend API
        ↓
Task Orchestrator
   ├─ Asset Service
   ├─ Media Service
   ├─ Copywriting Service
   ├─ Package Service
   ├─ Publish Service
   ├─ Rule Service
   └─ Account Session Service
        ↓
DB + Object Storage + Queue + Worker + Log/Trace
```

### 架构原则

- 编排与执行分离。
- 元数据与文件分离存储。
- 渲染、文案、发布作为异步任务执行。
- 通过消息队列实现解耦和重试。
- 发布渠道通过适配器模式隔离。

---

## 10.2 模块划分

### 1）Task Orchestrator（任务编排服务）

职责：

- 创建任务
- 推进任务状态机
- 派发子任务
- 汇总阶段结果
- 触发重试/取消

### 2）Asset Service（素材服务）

职责：

- 上传/导入素材
- 下载 URL 素材
- 提取元数据
- 管理素材生命周期

### 3）Media Service（媒体处理服务）

职责：

- 视频切片
- 选片
- 生成 concat manifest
- FFmpeg 合成
- 音频混流
- 生成封面预览

### 4）Copywriting Service（文案服务）

职责：

- Prompt 模板渲染
- 调用外部模型
- 异常重试
- 滤词清洗
- 多版本存储

### 5）Package Service（作品包服务）

职责：

- 组织四件套输出
- 生成 manifest
- 完整性校验
- 生成审核预览数据

### 6）Publish Service（发布服务）

职责：

- 渠道适配
- 会话注入
- 自动发布
- 结果回写
- 失败截图/日志留存

### 7）Rule Service（规则服务）

职责：

- 管理切片规则
- 管理选片规则
- 管理文案模板
- 管理滤词规则
- 管理默认参数模板

### 8）Account Session Service（账号会话服务）

职责：

- 发布账号管理
- token/session 管理
- 会话校验与刷新
- 账号风险状态管理

---

## 10.3 异步任务与队列设计

建议拆分为以下 Job 类型：

- `asset_import_job`
- `asset_probe_job`
- `video_segment_job`
- `copy_generate_job`
- `render_job`
- `package_build_job`
- `publish_job`
- `retry_job`

### 执行策略

- 各任务项可并行执行。
- 单作品内部按依赖顺序串行执行。
- 长耗时任务必须异步。
- 每类 Job 记录开始时间、结束时间、耗时、重试次数、失败原因。

---

## 10.4 数据库表设计（初稿）

## A. task

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_no | varchar | 任务编号 |
| name | varchar | 任务名称 |
| task_type | varchar | 任务类型 |
| channel | varchar | 发布渠道 |
| status | varchar | 任务状态 |
| expected_count | int | 期望生成数 |
| auto_publish | boolean | 是否自动发布 |
| rule_template_id | bigint | 规则模板 |
| creator_id | bigint | 创建人 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## B. task_item

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_id | bigint | 所属任务 |
| seq_no | int | 序号 |
| status | varchar | 作品项状态 |
| product_name | varchar | 商品名称 |
| copy_text | text | 当前主文案 |
| topic_text | varchar | 当前话题 |
| cover_asset_id | bigint | 当前封面 |
| video_asset_id | bigint | 当前源视频 |
| audio_asset_id | bigint | 当前音频 |
| package_id | bigint | 当前作品包 |
| current_render_version | int | 渲染版本 |
| current_copy_version | int | 文案版本 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## C. asset

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| asset_type | varchar | video/image/audio/text |
| source_type | varchar | upload/url/import/generated |
| source_uri | text | 原始来源 |
| storage_key | varchar | 对象存储路径 |
| local_path | varchar | 本地缓存路径 |
| status | varchar | 素材状态 |
| format | varchar | 文件格式 |
| duration_ms | bigint | 时长 |
| width | int | 宽 |
| height | int | 高 |
| size_bytes | bigint | 文件大小 |
| checksum | varchar | 去重校验 |
| created_at | datetime | 创建时间 |

## D. copy_generation

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_item_id | bigint | 作品项 |
| version_no | int | 版本号 |
| prompt_template_id | bigint | 模板 |
| prompt_text | text | 实际 Prompt |
| raw_response | longtext | 原始返回 |
| cleaned_text | text | 清洗后文案 |
| status | varchar | 状态 |
| retry_count | int | 重试次数 |
| created_at | datetime | 创建时间 |

## E. render_job

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_item_id | bigint | 作品项 |
| version_no | int | 版本号 |
| segment_manifest | text | 片段清单 |
| render_params | json | 渲染参数 |
| output_asset_id | bigint | 输出视频 |
| status | varchar | 状态 |
| error_message | text | 错误原因 |
| started_at | datetime | 开始时间 |
| finished_at | datetime | 结束时间 |

## F. package

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_item_id | bigint | 作品项 |
| package_no | varchar | 作品包编号 |
| manifest_json | json | 结构化描述 |
| status | varchar | 状态 |
| output_dir | varchar | 输出目录/逻辑路径 |
| created_at | datetime | 创建时间 |

## G. publish_account

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| channel | varchar | 渠道 |
| account_name | varchar | 账号名称 |
| account_uid | varchar | 平台账号标识 |
| session_status | varchar | 会话状态 |
| credential_ref | varchar | 凭据引用 |
| last_validated_at | datetime | 最近校验时间 |
| risk_status | varchar | 风险状态 |
| created_at | datetime | 创建时间 |

## H. publish_record

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_item_id | bigint | 作品项 |
| account_id | bigint | 发布账号 |
| channel | varchar | 渠道 |
| status | varchar | 发布状态 |
| platform_post_id | varchar | 平台作品 ID |
| platform_post_url | text | 平台作品链接 |
| request_snapshot | json | 发布参数快照 |
| response_snapshot | json | 平台返回快照 |
| error_code | varchar | 错误码 |
| error_message | text | 错误信息 |
| screenshot_asset_id | bigint | 失败截图 |
| created_at | datetime | 创建时间 |

## I. audit_log

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| biz_type | varchar | task/item/account/publish |
| biz_id | bigint | 业务主键 |
| action | varchar | 操作类型 |
| operator_id | bigint | 操作人 |
| before_json | json | 变更前 |
| after_json | json | 变更后 |
| created_at | datetime | 创建时间 |

---

## 10.5 核心 API 设计（初稿）

## 任务 API

- `POST /api/tasks`：创建任务
- `GET /api/tasks`：任务列表
- `GET /api/tasks/{id}`：任务详情
- `POST /api/tasks/{id}/start`：启动任务
- `POST /api/tasks/{id}/cancel`：取消任务
- `POST /api/tasks/{id}/retry`：重试任务级失败项

## 素材 API

- `POST /api/assets/upload`：上传素材
- `POST /api/assets/import-url`：通过 URL 导入素材
- `GET /api/assets/{id}`：素材详情
- `POST /api/assets/{id}/probe`：重新提取元数据

## 作品项 API

- `GET /api/task-items/{id}`：作品项详情
- `POST /api/task-items/{id}/regenerate-copy`：重生成文案
- `POST /api/task-items/{id}/rerender`：重新合成视频
- `POST /api/task-items/{id}/replace-cover`：替换封面
- `POST /api/task-items/{id}/approve`：审核通过
- `POST /api/task-items/{id}/reject`：审核驳回

## 发布 API

- `POST /api/tasks/{id}/publish`：批量发布
- `POST /api/task-items/{id}/publish`：发布单条作品
- `GET /api/publish-records/{id}`：发布记录详情
- `POST /api/publish-records/{id}/retry`：重试发布

## 配置 API

- `GET /api/rule-templates`
- `POST /api/rule-templates`
- `GET /api/publish-accounts`
- `POST /api/publish-accounts`
- `POST /api/publish-accounts/{id}/validate-session`

---

## 10.6 渠道适配设计

为避免与具体平台强耦合，发布层建议抽象为 `PublisherAdapter`：

```text
PublisherAdapter
  ├─ validateSession()
  ├─ uploadCover()
  ├─ uploadVideo()
  ├─ submitPost()
  ├─ queryResult()
  └─ captureFailureContext()
```

### 适配策略

- 若平台有官方 API，优先使用 API 模式。
- 若平台无开放 API，可使用浏览器自动化适配。
- 同一渠道支持多实现时，通过配置切换。

---

## 10.7 文件与存储设计

### 存储建议

- 原始素材：对象存储
- 中间产物：对象存储 + 本地 worker 临时目录
- 最终作品包：对象存储标准路径
- 失败截图 / 执行日志：对象存储归档

### 建议路径规范

```text
/raw/{task_no}/{asset_id}/...
/work/{task_no}/{task_item_id}/{job_type}/...
/package/{task_no}/{task_item_id}/1.mp4
/package/{task_no}/{task_item_id}/1.jpg
/package/{task_no}/{task_item_id}/商品名称.txt
/package/{task_no}/{task_item_id}/文案.txt
```

### 临时文件治理

- Job 完成后定时清理临时目录。
- 保留关键中间产物用于排查，但需设置 TTL。

---

## 10.8 日志、监控与审计

### 日志维度

- 任务日志
- 作品项日志
- Job 执行日志
- 渠道发布日志
- 审核操作日志

### 监控指标

- 任务成功率
- 文案生成成功率
- 渲染成功率
- 发布成功率
- 平均处理耗时
- 各阶段重试次数

### 审计要求

以下动作必须审计：

- 创建/取消任务
- 修改规则模板
- 替换素材
- 人工修改文案
- 审核通过/驳回
- 发布账号变更
- 发布执行/重试

---

## 10.9 安全与权限

### 权限建议

- 运营：可创建任务、查看结果、发起重试
- 审核：可编辑作品内容、执行审核
- 发布：可执行发布、查看账号状态
- 管理员：可维护模板、账号、系统配置

### 安全要求

- token/session 不直接明文展示给前台。
- 凭据统一加密存储。
- 高风险操作需审计。
- 发布接口需要幂等控制和权限校验。

---

## 11. 非功能需求

| 项目 | 要求 |
|------|------|
| 可用性 | 关键异步任务支持失败重试 |
| 可扩展性 | 支持新增渠道适配器和规则模板 |
| 可观察性 | 全链路日志、指标、任务追踪 |
| 性能 | 批量任务支持并发处理 |
| 一致性 | 任务状态、作品状态、发布状态具备明确边界 |
| 可维护性 | 模块职责清晰，规则配置化 |

---

## 12. MVP 实施建议

### 第一阶段（建议先做）

1. 任务创建与任务列表
2. 素材上传/URL 导入
3. 视频切片与基础合成
4. 文案模板生成 + 滤词
5. 作品包生成与预览
6. 人工审核
7. 单渠道发布适配

### 第二阶段

1. 批量模板化任务
2. 多账号调度
3. 多渠道发布
4. 局部重试优化
5. 审核版本对比

### 第三阶段

1. 智能选片策略
2. 素材评分与推荐
3. 自动发布时间策略
4. 报表与运营分析

---

## 13. 风险与待确认项

### 已识别风险

1. 外部大模型接口稳定性与成本波动。
2. 视频渲染对机器资源要求高。
3. 渠道发布适配可能因页面变动失效。
4. 登录会话管理涉及安全与风控风险。
5. 批量发布失败时需要明确补偿与幂等策略。

### 待确认问题

1. 当前系统是否以单渠道为 MVP，还是需要预留多渠道。
2. 发布执行是采用浏览器自动化还是已有渠道接口。
3. 商品名称来源是人工录入、商品系统同步还是素材解析。
4. 文案模板是否需要按品类管理。
5. 审核流程是否需要双人复核。

---

## 14. 推荐下一步产出

建议基于本稿继续补齐以下文档：

1. 《页面原型与交互流转图》
2. 《数据库 Schema 详细设计》
3. 《任务编排状态机与重试策略设计》
4. 《发布渠道适配接口规范》
5. 《媒体处理服务 FFmpeg 参数规范》

---

## 15. 一句话定义

> 这是一个面向内容运营场景的“短视频作品生产工作流系统”，通过任务化编排将素材输入、内容生成、视频合成、人工审核和自动发布串联起来，稳定地产出可发布作品。
