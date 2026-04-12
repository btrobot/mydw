# 得物掘金工具整体架构与数据流

## 1. 总体架构

这个项目可以理解成一个“三层系统”：

1. Electron 桌面壳
2. React 前端工作台
3. FastAPI 本地后端 + 自动化执行引擎

外部再连接 4 类系统：

- SQLite 本地数据库
- 得物创作者平台
- Coze 工作流
- FFmpeg / 本地素材目录

可以抽象成下面这张图：

```text
Electron 桌面壳
  ├─ Main Process
  │  ├─ 创建窗口 / 托盘 / 菜单
  │  └─ 拉起本地 FastAPI 后端进程
  └─ Renderer (React SPA)
     ├─ 页面与表单
     ├─ React Query / OpenAPI SDK / Axios
     └─ HTTP / SSE 调后端

FastAPI 后端
  ├─ API 层
  ├─ Service 业务层
  ├─ Core 基础设施层
  │  ├─ Patchright/Playwright 浏览器上下文
  │  ├─ DewuClient 得物自动化封装
  │  ├─ CozeClient 合成工作流封装
  │  └─ 配置 / 加密 / 日志
  └─ SQLite 本地数据库

外部系统
  ├─ 得物创作者平台
  ├─ Coze 工作流
  ├─ FFmpeg / ffprobe
  └─ 本地素材目录
```

## 2. 分层职责

### 2.1 Electron 层

Electron 主进程负责：

- 创建主窗口
- 管理系统托盘和菜单
- 在开发 / 生产模式下拉起后端进程
- 暴露少量 IPC 能力给前端

也就是说，应用不是“前端单独运行，后端另开”的浏览器产品，而是一个把前后端一起封装进桌面壳的本地工具。

### 2.2 前端层

前端是一个 React SPA，负责：

- 页面展示
- 表单录入
- 列表查询
- 任务操作
- 状态轮询和刷新

它本身不处理自动化发布，不直接碰浏览器驱动，只通过：

- OpenAPI 生成客户端
- Axios
- React Query
- SSE

来和后端交互。

### 2.3 后端层

后端是整个系统的业务中心，负责：

- 账号管理
- 任务管理
- 素材管理
- 调度配置
- 配置档解析
- 视频合成
- 自动发布
- 状态更新和日志记录

API 层比较薄，主要做参数校验和路由分发；核心逻辑集中在 `services/` 和 `core/`。

## 3. 核心领域对象

### 3.1 账号

`Account` 是自动化发布的前提，里面保存：

- 得物账号标识
- 加密手机号
- 加密后的 `storage_state`
- 当前账号状态
- 会话过期时间
- 健康检查时间

### 3.2 任务

`Task` 是系统的主线实体，贯穿整个流程。它不是一个简单的“待发布记录”，而是一个有生命周期的工作单。

它会经历：

- `draft`
- `composing`
- `ready`
- `uploading`
- `uploaded`
- `failed`
- `cancelled`

### 3.3 素材

素材实体包括：

- `Video`
- `Copywriting`
- `Cover`
- `Audio`
- `Topic`
- `Product`

任务通过关联表把这些资源挂到自己身上，而不是只绑定单个视频或文案。

### 3.4 配置

配置被拆成两层：

- `PublishProfile`
  任务级配置。决定任务是否合成、用哪个 Coze workflow、是否自动带全局话题、重试策略等。
- `ScheduleConfig`
  系统级配置。决定时间窗口、发布间隔、每日限额、是否打乱顺序等。

这个拆分很重要，因为“怎么处理一个任务”和“系统什么时候统一发”不是一回事。

## 4. 主数据流

整个项目最重要的是 4 条流。

### 4.1 启动流

```text
用户启动桌面应用
→ Electron Main 启动
→ spawn 本地 FastAPI
→ FastAPI startup
→ 初始化数据库
→ 确保默认 PublishProfile 存在
→ 前端通过本地 API 工作
```

这条链说明应用是“本地全栈一体化”运行的。

### 4.2 账号连接与会话流

```text
前端账号页
→ 打开连接弹窗
→ 建立 SSE 订阅
→ send-code
→ 后端启动 Patchright 浏览器
→ 打开得物登录页
→ 输入手机号 / 验证码
→ 登录成功
→ 保存 storage_state
→ 加密写入数据库
→ Account.status = active
```

这里有两个关键设计：

- 临时连接进度走内存状态和 SSE
- 长期可复用登录态走数据库持久化

所以它不是简单“登一次就算了”，而是把 session 变成后续任务可复用的系统资产。

### 4.3 素材到任务的组装流

```text
素材入库
→ 用户选择视频 / 文案 / 封面 / 音频 / 话题 / 账号 / 配置档
→ TaskDistributor / TaskAssembler 创建任务
→ 创建 Task 主记录
→ 创建任务与素材的关联记录
→ 根据 PublishProfile 决定初始状态
   - composition_mode = none  -> ready
   - composition_mode != none -> draft
```

这里说明任务创建不是“手工拼一个 payload 就发”，而是把素材资源结构化后再编排成任务。

### 4.4 合成与发布流

#### 不需要合成的任务

```text
Task = ready
→ 调度器挑选任务
→ PublishService 执行发布
→ DewuClient 打开得物上传页
→ 上传视频
→ 填写文案 / 话题 / 封面
→ 成功 uploaded / 失败 failed
```

#### 需要合成的任务

```text
Task = draft
→ 用户提交合成
→ CompositionService 创建 CompositionJob
→ 上传素材到 Coze
→ 提交异步工作流
→ Task.status = composing
→ CompositionPoller 定时轮询
→ 成功后下载成品视频到本地
→ Task.status = ready
→ 再进入发布调度链
```

所以“合成”不是附加功能，而是任务进入可发布状态前的一段前置流水。

## 5. 状态机在系统里的作用

这个项目的状态机不是文档上的装饰，而是后端设计的骨架。

### 5.1 Task 状态机

```text
draft
→ composing
→ ready
→ uploading
→ uploaded

失败分支：
composing / uploading
→ failed
→ quick retry 回到失败前状态
或 edit retry 回到 draft
```

这里体现两个恢复路径：

- 快速重试：适合临时性问题，例如网络或服务抖动
- 编辑重试：适合素材本身有问题，需要修改后重提

### 5.2 Account 状态机

账号状态和连接过程状态是分开的：

- `AccountStatus` 持久化，驱动 UI 和业务判断
- `ConnectionStatus` 存内存，通过 SSE 推送实时进度

这样可以把“业务可用状态”和“临时操作流程状态”拆开，避免模型混乱。

## 6. 浏览器自动化在架构中的位置

系统不是调一个官方发布 API，而是通过浏览器自动化驱动得物创作者页面。

链路是：

```text
数据库中的 storage_state
→ BrowserManager 还原浏览器上下文
→ DewuClient 复用 / 新建页面
→ 检查登录态
→ 访问上传页
→ 自动填写表单
→ 提交发布
→ 回写任务状态和日志
```

这意味着：

- 数据库负责保存系统真相
- Browser context 是执行现场
- DewuClient 是平台操作适配层
- 前端只是控制台，不直接参与自动化细节

## 7. 前端与后端的交互方式

前端主要用两种通信模式：

### 7.1 普通业务操作

通过 HTTP API 调后端：

- 查询列表
- 创建任务
- 更新任务
- 提交合成
- 取消 / 重试任务
- 读取统计

### 7.2 实时进度推送

账号连接流程走 SSE，用来推送：

- 当前连接状态
- 文案消息
- 进度百分比
- 终态事件

这个选择很合理，因为连接过程主要是单向通知，不需要引入更重的双向通道。

## 8. 配置和外部边界

### 8.1 本地配置

`Settings` 决定：

- 服务地址
- 数据库位置
- 素材根目录
- 浏览器 headless 模式
- Coze token 和轮询频率
- 默认发布时段等

### 8.2 外部边界

系统真正依赖的外部边界有 3 个：

1. 得物创作者平台
   实际发布目标，由 DewuClient + 浏览器自动化驱动
2. Coze
   提供异步视频工作流能力
3. FFmpeg
   提供本地视频处理能力

所以这不是一个纯 CRUD 项目，而是一个带强外部依赖和执行状态的本地工作流系统。

## 9. 总结

一句话概括：

这是一个“桌面化的本地运营中台”，用 Electron 承载 UI，用 FastAPI 编排业务，用 SQLite 保存状态，用 Patchright 驱动得物页面，用 Coze 和 FFmpeg 完成内容生产，再由调度器把任务推到发布链里。

它的核心不是某一个页面，而是把下面这条链做成可运行系统：

```text
账号登录态
→ 素材结构化
→ 任务编排
→ 合成（可选）
→ 调度上传
→ 状态回写
→ 失败恢复
```
