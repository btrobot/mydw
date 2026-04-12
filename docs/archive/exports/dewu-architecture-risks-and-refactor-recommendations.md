# 当前架构里的风险点和重构建议

## 1. 文档目的

这份文档不是泛泛地说“架构有待优化”，而是基于当前代码指出：

1. 哪些地方已经出现结构性风险
2. 这些风险为什么会影响维护和运行
3. 更现实的重构顺序应该是什么

这里的“风险”优先看：

- 文档和代码的偏差
- 模型与执行链的不一致
- 配置分层漂移
- 状态管理边界模糊
- Electron 与后端耦合点
- JSON-in-text 的复杂度
- 测试覆盖缺口

## 2. 优先级最高的风险

## 2.1 配置模型分裂：`PublishConfig` 与 `ScheduleConfig` 并存

**现象**

- 调度器和发布服务当前读取的是 `schedule_config`
- 发布接口 `/api/publish/config` 仍然操作 `publish_config`
- 前端 `ScheduleConfig.tsx` 也还在调 `/api/publish/config`

**证据**

- `backend/services/scheduler.py`
- `backend/services/publish_service.py`
- `backend/models/__init__.py`
- `backend/api/publish.py`
- `frontend/src/pages/ScheduleConfig.tsx`

**风险**

- 前端改了“调度配置”，调度器未必真的读取到同一份配置
- 逻辑上看似一张配置表，实际上是两套来源
- 用户很难理解为什么页面保存成功，但运行行为可能不一致

**建议**

短期：

- 明确一个主表，建议统一到 `schedule_config`
- `backend/api/publish.py` 改为只读写 `schedule_config`
- 给旧 `publish_config` 标注为兼容保留，不再新增依赖

中期：

- 重命名接口，把“调度配置”从 `/publish/config` 抽成更明确的 `/schedule-config`
- 生成客户端后同步前端 hooks，去掉页面直写 Axios 的临时补丁

## 2.2 任务模型已经是“多资源”，发布执行仍是“单资源第一项”

**现象**

- `tasks` 已通过关联表支持多视频、多文案、多封面、多音频、多话题
- 但 `PublishService.publish_task` 发布时只取每类资源的第一项

**证据**

- `backend/models/__init__.py`
- `backend/services/task_assembler.py`
- `backend/services/publish_service.py`

**风险**

- 数据模型表达能力高于执行层能力
- 前端允许用户组装多素材任务，但最终发布结果可能只消费第一项
- 很容易让用户误以为“多素材已生效”，实际上执行结果并不符合预期

**建议**

短期二选一：

1. 明确限制任务发布阶段只支持单资源，并在前端创建页和详情页上提示
2. 或者在后端发布前显式校验多资源任务是否可执行，不允许静默降级为“取第一项”

中期：

- 明确多素材的业务语义
  - 多视频用于合成输入
  - 多文案是否轮播
  - 多封面是否只允许一个最终输出
- 把“任务资源集合模型”和“执行模型”统一成一套规则

## 2.3 任务表仍保留旧单资源 FK，增加理解和迁移成本

**现象**

- `tasks` 里仍有 `product_id/video_id/copywriting_id/audio_id/cover_id`
- 注释已写明是兼容保留列，代码主流程也转向关联表

**证据**

- `backend/models/__init__.py`
- `backend/api/task.py`
- `backend/services/task_assembler.py`

**风险**

- 新人会误判当前真实模型
- API / 页面 / schema 很容易混用旧字段和新关联模型
- 查询和序列化层更容易出现“看起来有值，但并不是主流程真相”的问题

**建议**

短期：

- 在 schema 和序列化层统一标记旧字段为兼容字段
- 任务接口返回中优先输出关联资源集合，不再鼓励消费旧 FK

中期：

- 盘点仍依赖旧 FK 的代码路径
- 迁移完成后在一次版本升级里删除旧字段及其前端假设

## 2.4 文档、接口、页面实现已经开始漂移

**现象**

- README 版本与代码版本不一致
- `docs/archive/reference/data-model.md` 仍把 `Task` 当作单资源模型
- API 文档未完全反映 `profiles`、`schedule_config`、任务合成接口等当前变化
- 前端大量出现“生成客户端不够用，直接 Axios 补”的情况

**证据**

- `README.md`
- `frontend/package.json`
- `backend/main.py`
- `docs/archive/reference/data-model.md`
- `docs/archive/reference/api-reference.md`
- `frontend/src/hooks/useAccount.ts`
- `frontend/src/pages/ScheduleConfig.tsx`

**风险**

- 文档不再是可信入口
- OpenAPI 生成客户端的收益下降
- 页面维护者只能靠读源码试错

**建议**

短期：

- 用 ORM 和真实 API 重新生成一版最小可信文档
- 对“已过时文档”加明显标记

中期：

- 固化一个文档刷新流程：
  1. 先改接口
  2. 刷 OpenAPI
  3. 重新生成前端客户端
  4. 再补文档

## 3. 中高优先级风险

## 3.1 `publish` 状态和调度器状态存在双轨真相

**现象**

- `backend/api/publish.py` 维护了内存变量 `_publish_status`
- 真正运行与否也由 `scheduler._loop_task` 决定

**风险**

- API 状态可能与真实调度任务状态不同步
- 进程异常、重启或边界错误时，内存状态很容易失真

**建议**

- 把发布状态统一收口到调度器对象
- API 层只读取调度器真实状态，不自己维护平行状态字典

## 3.2 系统配置接口还是半成品

**现象**

- `GET /api/system/config` 返回硬编码值
- `PUT /api/system/config` 只打日志，没有真正持久化
- `Settings.tsx` 甚至没有读取这个配置，只显示硬编码路径

**证据**

- `backend/api/system.py`
- `frontend/src/pages/Settings.tsx`
- `backend/core/config.py`

**风险**

- 用户以为“系统设置”是可配置的，但很多只是展示或假实现
- 环境变量、后端配置接口、前端显示值三者可能完全不一致

**建议**

短期：

- 明确哪些设置是真生效的，哪些只是占位
- 占位功能在 UI 上加说明，避免伪可配

中期：

- 建立统一配置源：
  - 环境变量负责启动时配置
  - 数据库或文件负责运行时配置
  - 页面只读写这一份真实源

## 3.3 Electron 主进程对后端启动路径依赖强且偏 Windows

**现象**

- 开发模式下 Electron 直接用 `backend/venv/Scripts/python.exe`
- 明显假设 Windows 虚拟环境布局

**证据**

- `frontend/electron/main.ts`

**风险**

- 跨平台开发困难
- 本地环境稍有不同就无法启动
- Electron 层和 Python 环境布局耦合过紧

**建议**

- 把后端启动命令抽到配置层或脚本层
- Electron 只关心“如何调用一个后端启动入口”，不要硬编码虚拟环境路径
- 开发模式优先走统一脚本，例如 `dev server command`

## 3.4 JSON-in-text 字段越来越多，影响约束与查询

**现象**

当前模型中有大量文本字段存 JSON：

- `accounts.tags`
- `tasks.source_video_ids`
- `tasks.composition_params`
- `publish_profiles.composition_params`
- `publish_profiles.global_topic_ids`
- `topic_groups.topic_ids`
- `publish_config.global_topic_ids`

**风险**

- 查询困难
- 约束难做
- 迁移复杂
- 前后端类型一致性依赖约定，不依赖数据库结构

**建议**

短期：

- 把 JSON 字段按“配置型”和“关系型”分类

中期：

- 关系型集合优先拆表，例如 `topic_groups` 最终可考虑正规关联表
- 纯配置型 JSON 可以保留，但要统一 schema 和校验

## 3.5 前端大量手写扩展类型，说明生成类型已过期

**现象**

- `TaskDetail` 自己定义扩展接口并强制 cast
- `AccountResponseExtended` 通过扩展类型补字段
- 多个页面直接绕过生成客户端，用 Axios 自己请求

**证据**

- `frontend/src/pages/task/TaskDetail.tsx`
- `frontend/src/hooks/useAccount.ts`
- `frontend/src/pages/ScheduleConfig.tsx`

**风险**

- 编译能过，但运行期更容易错
- 前后端字段变了，页面不一定会报类型错误
- “有类型”但不一定“类型可信”

**建议**

- 重新对齐 OpenAPI 文档和生成客户端
- 优先消灭强制 cast 和手写“扩展响应类型”
- 保留手写 Axios 只用于真正无法生成的极少数特殊接口

## 4. 中优先级风险

## 4.1 `Settings`、`ScheduleConfig`、`Dashboard` 之间配置职责边界不清

**现象**

- Dashboard 控发布
- ScheduleConfig 管发布参数
- Settings 看起来也像系统配置入口
- 但这三者背后的后端真实配置源并不统一

**风险**

- 用户概念层混淆
- 页面边界不清
- 后续很容易继续堆功能到错误页面

**建议**

- 重新定义页面边界：
  - Dashboard：只展示状态 + 控制运行
  - ScheduleConfig：只配置调度参数
  - Settings：只放系统级运行配置和数据维护

## 4.2 发布日志和系统日志的边界还不够清晰

**现象**

- Dashboard 展示系统日志
- 发布接口单独有 `publish_logs`
- 用户如果想看“某条任务为什么失败”，需要跨多个位置理解

**风险**

- 排障入口分散
- 发布链观察性弱

**建议**

- 任务详情页直接串联：
  - 当前状态
  - 最近失败原因
  - 相关 `publish_logs`
  - 相关 `composition_jobs`

## 4.3 一些接口仍带明显 TODO，占位逻辑进入主干

**现象**

- `system/config`
- `system/backup`
- `publish/refresh`

都还有占位或部分实现。

**风险**

- 页面看起来可用，但实际语义不完整
- 后续维护者会误把占位接口当稳定能力继续依赖

**建议**

- 对占位接口统一打标签
- UI 上对未完成能力给出明确说明
- 不要再让新页面依赖这些半实现接口

## 5. 测试覆盖风险

## 5.1 数据模型和任务状态机变化快，但缺少同层次的契约测试

**现象**

- 后端测试已有不少文件
- 但从当前代码结构看，关于“配置档 + 任务组装 + 合成状态机 + 调度发布”的跨层契约测试仍然不明显

**证据**

- `backend/tests/`
- `backend/services/task_assembler.py`
- `backend/services/composition_service.py`
- `backend/services/publish_service.py`

**风险**

- 任务状态机非常依赖多个服务协作
- 任何一层小改动都可能破坏整体流程

**建议**

- 补 4 类回归测试：
  1. 创建任务时根据 profile 正确得到 `draft/ready`
  2. 提交合成后状态正确推进到 `composing`
  3. 合成成功后回写 `ready + final_video_path`
  4. 发布成功后回写 `uploaded + publish_log`

## 5.2 Electron 到后端启动这层缺少可验证性

**现象**

- 后端路径和启动方式写死在 Electron 主进程
- 这部分通常不在普通单元测试覆盖范围里

**风险**

- 一旦目录布局或环境变化，应用可能直接起不来

**建议**

- 至少补一层启动自检
- 启动失败时把错误明确展示到桌面端，而不是只打控制台日志

## 6. 建议的重构顺序

如果按投入产出比排序，我建议这样做。

### 第 1 阶段：统一真相源

目标：

- 先消除最危险的双轨配置和双轨状态

动作：

1. 统一 `publish_config` / `schedule_config`
2. 统一发布状态来源，不再平行维护 `_publish_status`
3. 清理最明显的文档漂移和接口漂移

### 第 2 阶段：统一任务模型与执行模型

目标：

- 让“任务支持什么”与“发布实际会做什么”一致

动作：

1. 定义多资源任务的执行语义
2. 在发布层去掉“静默取第一项”的不透明行为
3. 明确淘汰旧单资源 FK 的计划

### 第 3 阶段：清理前后端契约

目标：

- 重新让 OpenAPI 和前端类型系统变可信

动作：

1. 刷新 schema
2. 重新生成前端客户端
3. 去掉扩展 cast 和大量手写 Axios 补丁

### 第 4 阶段：整理系统配置与运维入口

目标：

- 让 Settings、ScheduleConfig、Dashboard 的职责真正清晰

动作：

1. 实现真实可持久化的系统配置
2. 整理备份、自检、日志、运行状态显示
3. 让桌面端启动失败可观测

## 7. 最后总结

当前项目最大的问题不是“技术选型错了”，而是系统已经从单体原型长成了多阶段工作流，但有几处关键边界还停留在过渡态：

- 配置边界未完全收口
- 模型能力与执行能力未完全一致
- 文档和生成客户端开始失真
- 系统设置和桌面启动链仍带明显占位痕迹

如果先解决“真相源统一”和“任务执行语义统一”，后面的文档、前端类型、页面边界和测试体系都会顺很多。
