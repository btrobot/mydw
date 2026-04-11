# 前后端接口清单与页面对应关系

## 1. 文档目的

这份文档解决两个问题：

1. 前端每个页面主要在做什么
2. 它实际打到了哪些后端接口域

注意：

- 这里不是把所有 API 原封不动抄一遍
- 而是按“页面 -> 用户动作 -> hooks / services -> 后端接口组”的方式组织

前端路由入口：

- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`

后端接口入口：

- `backend/main.py`
- `backend/api/*.py`

## 2. 顶层路由与页面总表

| 路由 | 页面文件 | 页面职责 | 主要后端接口组 |
|------|----------|----------|----------------|
| `/dashboard` | `pages/Dashboard.tsx` | 任务概览、发布控制、系统日志 | `system`, `tasks`, `publish` |
| `/account` | `pages/Account.tsx` | 账号 CRUD、连接、预览、健康检查 | `accounts` |
| `/task/list` | `pages/TaskList.tsx` | 任务查询、删除、清空、跳详情 | `tasks` |
| `/task/create` | `pages/task/TaskCreate.tsx` | 用素材和账号创建任务 | `tasks`, `profiles`, `accounts`, 素材接口 |
| `/task/:id` | `pages/task/TaskDetail.tsx` | 提交/取消合成、重试、取消、删除 | `tasks` |
| `/material/overview` | `pages/material/MaterialOverview.tsx` | 素材总览统计 | `system` |
| `/material/video` | `pages/material/VideoList.tsx` | 视频素材 CRUD、上传、扫描、批删 | `videos` |
| `/material/video/:id` | `pages/material/VideoDetail.tsx` | 视频详情 | `videos` |
| `/material/copywriting` | `pages/material/CopywritingList.tsx` | 文案 CRUD、导入、批删 | `copywritings` |
| `/material/cover` | `pages/material/CoverList.tsx` | 封面上传、删除、批删 | `covers`, `videos` |
| `/material/audio` | `pages/material/AudioList.tsx` | 音频上传、删除、批删 | `audios` |
| `/material/topic` | `pages/material/TopicList.tsx` | 话题 CRUD、搜索、批删 | `topics` |
| `/material/topic-group` | `pages/material/TopicGroupList.tsx` | 话题组 CRUD | `topic-groups`, `topics` |
| `/material/topic-group/:id` | `pages/material/TopicGroupDetail.tsx` | 话题组详情 | `topic-groups` |
| `/material/product` | `pages/product/ProductList.tsx` | 商品 CRUD、解析素材 | `products` |
| `/material/product/:id` | `pages/product/ProductDetail.tsx` | 商品详情、更新、解析素材 | `products` |
| `/ai-clip` | `pages/AIClip.tsx` | FFmpeg / AI 剪辑流程 | `ai` |
| `/settings` | `pages/Settings.tsx` | 备份、静态配置展示 | `system` |
| `/schedule-config` | `pages/ScheduleConfig.tsx` | 发布调度配置 | `publish` |
| `/profile-management` | `pages/ProfileManagement.tsx` | 配置档管理 | `profiles` |

## 3. 页面到接口的详细映射

## 3.1 Dashboard

页面文件：

- `frontend/src/pages/Dashboard.tsx`

主要用户动作：

- 查看任务统计
- 查看系统统计
- 查看系统日志
- 启动 / 暂停 / 停止发布

主要 hooks / services：

- `useSystemStats`
- `useSystemLogs`
- `useTaskStats`
- `usePublishStatus`
- `useControlPublish`

对应接口：

- `GET /api/system/stats`
- `GET /api/system/logs`
- `GET /api/tasks/stats`
- `GET /api/publish/status`
- `POST /api/publish/control`

备注：

- 看板的“发布控制”并不直接操作任务，而是操作调度器
- 日志面板读的是 `system_logs`，不是 `publish_logs`

## 3.2 账号管理页

页面文件：

- `frontend/src/pages/Account.tsx`

主要用户动作：

- 创建账号
- 编辑账号
- 删除账号
- 发起连接
- 监听连接进度
- 打开预览浏览器
- 关闭预览并可选保存 session
- 单账号健康检查
- 批量健康检查
- 标签 / 关键字筛选

主要 hooks：

- `useAccounts`
- `useCreateAccount`
- `useUpdateAccount`
- `useDeleteAccount`
- `usePreviewAccount`
- `useClosePreview`
- `usePreviewStatus`
- `useHealthCheck`
- `useBatchHealthCheck`
- `useBatchCheckStatus`

对应接口组：

- 账号 CRUD
  - `POST /api/accounts/`
  - `GET /api/accounts/`
  - `GET /api/accounts/{id}`
  - `PUT /api/accounts/{id}`
  - `DELETE /api/accounts/{id}`
- 连接 / 登录态
  - `POST /api/accounts/connect/{id}/send-code`
  - `POST /api/accounts/connect/{id}/verify`
  - `GET /api/accounts/connect/{id}/stream`
  - `GET /api/accounts/connect/{id}/status`
  - `POST /api/accounts/disconnect/{id}`
- 预览
  - `POST /api/accounts/{id}/preview`
  - `POST /api/accounts/{id}/preview/close`
  - `GET /api/accounts/preview/status`
- 健康检查
  - `POST /api/accounts/{id}/health-check`
  - `POST /api/accounts/batch-health-check`
  - `GET /api/accounts/batch-health-check/status`

备注：

- `useAccounts` 在没有扩展筛选时用生成客户端，有 `tag/search` 时回退到手写 Axios
- 账号连接是一条单独的 SSE 实时链路

## 3.3 任务列表页

页面文件：

- `frontend/src/pages/TaskList.tsx`

主要用户动作：

- 按状态 / 账号筛选任务
- 查看任务列表
- 删除单个任务
- 批量删除
- 清空所有任务
- 点击行进入详情
- 跳转创建任务

主要 hooks / services：

- `useAccounts`
- `useDeleteTask`
- `useDeleteAllTasks`
- 直接用 `api.get('/tasks')`

对应接口：

- `GET /api/tasks/`
- `DELETE /api/tasks/{id}`
- `DELETE /api/tasks/`

备注：

- 列表页没有直接“发布”按钮
- 任务详情页才承载合成、重试、取消等生命周期动作

## 3.4 任务创建页

页面文件：

- `frontend/src/pages/task/TaskCreate.tsx`

主要用户动作：

- 选择账号
- 选择配置档
- 从素材弹窗中加入视频 / 文案 / 封面 / 音频
- 一次性创建多个任务

主要 hooks / services：

- `useAccounts`
- `useProfiles`
- `useBatchAssemble`
- `ProductQuickImport`
- `MaterialSelectModal`

对应接口：

- `GET /api/accounts/`
- `GET /api/profiles`
- `POST /api/tasks/`
- 素材选择弹窗内部会进一步读取：
  - `videos`
  - `copywritings`
  - `covers`
  - `audios`

备注：

- 前端 hook 名叫 `useBatchAssemble`
- 实际调用的是 `POST /api/tasks/`
- 不是旧接口 `/tasks/assemble`

## 3.5 任务详情页

页面文件：

- `frontend/src/pages/task/TaskDetail.tsx`

主要用户动作：

- 查看任务详情
- 提交合成
- 查询合成状态
- 取消合成
- 快速重试
- 编辑重试
- 取消任务
- 删除任务

主要 hooks：

- `useTask`
- `useSubmitComposition`
- `useCompositionStatus`
- `useCancelComposition`
- `useRetryTask`
- `useEditRetryTask`
- `useCancelTask`
- `useDeleteTask`

对应接口：

- `GET /api/tasks/{id}`
- `POST /api/tasks/{id}/submit-composition`
- `GET /api/tasks/{id}/composition-status`
- `POST /api/tasks/{id}/cancel-composition`
- `POST /api/tasks/{id}/retry`
- `POST /api/tasks/{id}/edit-retry`
- `POST /api/tasks/{id}/cancel`
- `DELETE /api/tasks/{id}`

备注：

- 这里没有直接调用 `/api/tasks/{id}/publish`
- 当前主流程更偏向“进入 ready 后交给调度器”

## 3.6 数据看板相关配置页

### ScheduleConfig

页面文件：

- `frontend/src/pages/ScheduleConfig.tsx`

主要用户动作：

- 查看调度配置
- 修改发布间隔、时间窗口、日上限、乱序和自动启动

主要 services：

- 直接使用 `api.get('/publish/config')`
- 直接使用 `api.put('/publish/config')`

对应接口：

- `GET /api/publish/config`
- `PUT /api/publish/config`

备注：

- 前端页面叫“调度配置”
- 但后端这里仍走的是 `publish_config` 相关接口而不是 `schedule_config` 风格命名

### ProfileManagement

页面文件：

- `frontend/src/pages/ProfileManagement.tsx`

主要用户动作：

- 查看配置档列表
- 创建配置档
- 编辑配置档
- 删除配置档
- 设为默认配置档

主要 hooks：

- `useProfiles`
- `useCreateProfile`
- `useUpdateProfile`
- `useDeleteProfile`
- `useSetDefaultProfile`

对应接口：

- `GET /api/profiles`
- `POST /api/profiles`
- `PUT /api/profiles/{id}`
- `DELETE /api/profiles/{id}`
- `PUT /api/profiles/{id}/set-default`

## 3.7 素材总览页

页面文件：

- `frontend/src/pages/material/MaterialOverview.tsx`

主要用户动作：

- 查看各类素材数量
- 查看商品覆盖率
- 从概览跳转到各素材页

主要数据请求：

- `GET /api/system/material-stats`

对应接口组：

- `system`

## 3.8 视频素材页

页面文件：

- `frontend/src/pages/material/VideoList.tsx`

主要用户动作：

- 查看视频列表
- 新建视频记录
- 删除视频
- 批量删除视频
- 上传视频文件
- 扫描本地目录导入视频
- 打开视频详情

主要 hooks / services：

- `useCreateVideo`
- `useDeleteVideo`
- `useUploadVideo`
- `useScanVideos`
- `useBatchDeleteVideos`
- 直接 `api.get('/videos')`

对应接口：

- `GET /api/videos`
- `POST /api/videos`
- `DELETE /api/videos/{id}`
- `POST /api/videos/batch-delete`
- `POST /api/videos/upload`
- `POST /api/videos/scan`

## 3.9 文案素材页

页面文件：

- `frontend/src/pages/material/CopywritingList.tsx`

主要用户动作：

- 查看文案列表
- 新增文案
- 编辑文案
- 删除文案
- 批量删除
- 导入文案

对应接口：

- `GET /api/copywritings`
- `POST /api/copywritings`
- `PUT /api/copywritings/{id}`
- `DELETE /api/copywritings/{id}`
- `POST /api/copywritings/batch-delete`
- `POST /api/copywritings/import`

## 3.10 封面素材页

页面文件：

- `frontend/src/pages/material/CoverList.tsx`

主要用户动作：

- 查看封面列表
- 上传封面
- 删除封面
- 批量删除

还会读取视频列表作为封面关联上下文。

对应接口：

- `GET /api/covers`
- `POST /api/covers/upload`
- `DELETE /api/covers/{id}`
- `POST /api/covers/batch-delete`
- `GET /api/videos`

## 3.11 音频素材页

页面文件：

- `frontend/src/pages/material/AudioList.tsx`

主要用户动作：

- 查看音频列表
- 上传音频
- 删除音频
- 批量删除

对应接口：

- `GET /api/audios`
- `POST /api/audios/upload`
- `DELETE /api/audios/{id}`
- `POST /api/audios/batch-delete`

## 3.12 话题页

页面文件：

- `frontend/src/pages/material/TopicList.tsx`

主要用户动作：

- 查看话题列表
- 新建话题
- 删除话题
- 批量删除
- 搜索得物话题并导入

对应接口：

- `GET /api/topics`
- `POST /api/topics`
- `DELETE /api/topics/{id}`
- `POST /api/topics/batch-delete`
- `GET /api/topics/search`
- 旧全局话题接口：
  - `GET /api/topics/global`
  - `PUT /api/topics/global`

## 3.13 话题组页

页面文件：

- `frontend/src/pages/material/TopicGroupList.tsx`
- `frontend/src/pages/material/TopicGroupDetail.tsx`

主要用户动作：

- 查看话题组列表
- 创建 / 编辑 / 删除话题组
- 查看话题组详情

对应接口组：

- `topic-groups`
- `topics`

备注：

- 话题组页需要所有话题供多选，因此同时依赖 `topics`

## 3.14 商品页

页面文件：

- `frontend/src/pages/product/ProductList.tsx`
- `frontend/src/pages/product/ProductDetail.tsx`

主要用户动作：

- 商品 CRUD
- 批量删除商品
- 触发商品素材解析
- 查看商品详情

对应接口：

- `GET /api/products`
- `GET /api/products/{id}`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`
- `POST /api/products/{id}/parse-materials`
- 详情补充接口：
  - `GET /api/products/{id}/covers`
  - `GET /api/products/{id}/topics`
  - `GET /api/products/{id}/materials`

## 3.15 AI 剪辑页

页面文件：

- `frontend/src/pages/AIClip.tsx`

主要用户动作：

- 获取视频信息
- 检测高光片段
- 智能剪辑
- 添加背景音乐
- 添加封面
- 跑完整处理流程

主要 hooks：

- `useVideoInfo`
- `useDetectHighlights`
- `useSmartClip`
- `useAddAudio`
- `useAddCover`
- `useFullPipeline`

对应接口：

- `GET /api/ai/video-info`
- `GET /api/ai/detect-highlights`
- `POST /api/ai/smart-clip`
- `POST /api/ai/add-audio`
- `POST /api/ai/add-cover`
- `POST /api/ai/full-pipeline`

补充：

- Hook 里还定义了 `useTrimVideo`
- 但当前页面没有暴露单独 trim 操作

## 3.16 设置页

页面文件：

- `frontend/src/pages/Settings.tsx`

主要用户动作：

- 查看素材路径展示
- 执行数据备份

对应接口：

- `POST /api/system/backup`

备注：

- 当前素材路径是静态写在页面里的，不是实时读取系统配置
- 所以 Settings 页与 `GET /api/system/config` 并没有真正打通

## 4. 后端接口域清单

按当前 `backend/api` 可以归成这些接口域：

| 接口域 | 主要职责 |
|--------|----------|
| `accounts` | 账号 CRUD、连接流程、SSE、预览、健康检查 |
| `tasks` | 任务 CRUD、任务装配、重试、合成状态、取消 |
| `publish` | 调度配置、调度器控制、发布状态、发布日志 |
| `profiles` | 任务级配置档 |
| `products` | 商品管理与素材解析 |
| `videos` | 视频素材 |
| `copywritings` | 文案素材 |
| `covers` | 封面素材 |
| `audios` | 音频素材 |
| `topics` | 话题池和搜索 |
| `topic-groups` | 话题组模板 |
| `ai` | 本地 AI / FFmpeg 视频处理 |
| `system` | 系统统计、日志、配置、备份、素材统计 |

## 5. 页面与接口对应中的几个现实问题

### 5.1 有些页面已经用手写 Axios 补了生成客户端没覆盖的接口

典型例子：

- `useAccounts` 对 `tag/search`
- `TaskList` 直接 `api.get('/tasks')`
- `ScheduleConfig` 直接 `api.get('/publish/config')`

这说明 OpenAPI 生成客户端和当前真实接口已经有轻微漂移。

### 5.2 页面命名、模型命名、接口命名不完全统一

典型例子：

- 页面叫“调度配置”，接口却走 `/publish/config`
- 模型层主调度表是 `schedule_config`，接口层却仍使用 `PublishConfig` 风格

### 5.3 有些页面是“只部分打通”

典型例子：

- `Settings` 页没有真正用系统配置接口读取路径
- AI 剪辑页未暴露全部 AI hooks
- 任务详情页展示字段和后端真实资源集合模型仍有不完全对齐的痕迹

## 6. 一句话总结

如果把这个项目按前后端配对来理解，可以把它看成：

```text
Dashboard / Account / Task / Material / Product / AI / Settings
→ 各自命中 backend/api 的一个或多个接口域
→ 其中最复杂的是 accounts、tasks、publish 三条链
→ 其中最容易漂移的是 settings、schedule-config、task-detail 这几块
```
