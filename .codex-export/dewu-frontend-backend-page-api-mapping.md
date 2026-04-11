# 前后端接口清单与页面对应关系

## 1. 文档目的

这份文档把前端页面、主要用户动作、自定义 hooks / service 层，以及后端接口分组对应起来，帮助快速回答两个问题：

1. 某个页面背后实际打了哪些 API
2. 某个接口组当前主要被哪些页面消费

## 2. 全局规则

- 前端基础地址：`frontend/src/services/api.ts`
  - 默认 `http://127.0.0.1:8000/api`
- 数据访问主要通过两种方式：
  - OpenAPI 生成客户端 `@/api`
  - 手写 Axios `api`
- 当生成客户端落后于后端实际接口时，页面会回退到手写 Axios

## 3. 路由与页面映射表

| 路由 / 页面 | 主要用户动作 | 主要 hooks / service | 后端接口分组 |
|-------------|--------------|----------------------|--------------|
| `/dashboard` `Dashboard` | 查看任务概览、系统统计、运行日志、开始/暂停/停止发布 | `useSystemStats` `useSystemLogs` `useTaskStats` `usePublishStatus` `useControlPublish` | `/system/stats` `/system/logs` `/tasks/stats` `/publish/status` `/publish/control` |
| `/account` `Account` | 新建账号、编辑标签/备注、删除账号、连接账号、预览账号、单个健康检查、批量健康检查 | `useAccounts` `useCreateAccount` `useUpdateAccount` `useDeleteAccount` `usePreviewAccount` `useClosePreview` `usePreviewStatus` `useHealthCheck` `useBatchHealthCheck` `useBatchCheckStatus` | `/accounts` `/accounts/{id}` `/accounts/{id}/preview` `/accounts/{id}/preview/close` `/accounts/preview/status` `/accounts/{id}/health-check` `/accounts/batch-health-check` `/accounts/batch-health-check/status` |
| `/task/list` `TaskList` | 查看任务列表、按状态/账号筛选、删除单个任务、批量删除、清空所有任务 | `useAccounts` `useDeleteTask` `useDeleteAllTasks` + `api.get('/tasks')` | `/tasks` `/tasks/{id}` `DELETE /tasks` |
| `/task/create` `TaskCreate` | 选账号、选 profile、从素材篮组装任务、按商品快速导入素材 | `useAccounts` `useProfiles` `useBatchAssemble` `ProductQuickImport` `MaterialSelectModal` | `/accounts` `/profiles` `/tasks/batch-assemble` `/products` `/products/{id}/materials` `/videos` `/copywritings` `/covers` `/audios` |
| `/task/:id` `TaskDetail` | 查看任务详情、提交合成、取消合成、快速重试、编辑重试、取消任务、删除任务 | `useTask` `useSubmitComposition` `useCompositionStatus` `useCancelComposition` `useRetryTask` `useEditRetryTask` `useCancelTask` `useDeleteTask` | `/tasks/{id}` `/tasks/{id}/submit-composition` `/tasks/{id}/composition-status` `/tasks/{id}/cancel-composition` `/tasks/{id}/retry` `/tasks/{id}/edit-retry` `/tasks/{id}/cancel` |
| `/material/overview` `MaterialOverview` | 查看素材统计、跳转各素材页 | React Query `useQuery` + `api.get('/system/material-stats')` | `/system/material-stats` |
| `/material/video` `VideoList` | 查看视频、创建视频、上传视频、扫描目录、删除/批删视频 | `useVideos` `useCreateVideo` `useUploadVideo` `useScanVideos` `useDeleteVideo` `useBatchDeleteVideos` | `/videos` `/videos/upload` `/videos/scan` `/videos/{id}` `/videos/batch-delete` |
| `/material/video/:id` `VideoDetail` | 查看单个视频详情 | `useVideo` | `/videos/{id}` |
| `/material/copywriting` `CopywritingList` | 查看文案、创建、编辑、导入、删除/批删 | `useCopywritings` `useCreateCopywriting` `useUpdateCopywriting` `useImportCopywritings` `useDeleteCopywriting` `useBatchDeleteCopywritings` | `/copywritings` `/copywritings/{id}` `/copywritings/import` `/copywritings/batch-delete` |
| `/material/cover` `CoverList` | 查看封面、上传封面、删除/批删封面 | `useCovers` `useUploadCover` `useDeleteCover` `useBatchDeleteCovers` `useVideos` | `/covers` `/covers/upload` `/covers/{id}` `/covers/batch-delete` `/videos` |
| `/material/audio` `AudioList` | 查看音频、上传音频、删除/批删音频 | `useAudios` `useUploadAudio` `useDeleteAudio` `useBatchDeleteAudios` | `/audios` `/audios/upload` `/audios/{id}` `/audios/batch-delete` |
| `/material/topic` `TopicList` | 查看话题、创建、搜索得物话题、删除/批删 | `useTopics` `useCreateTopic` `useSearchTopics` `useDeleteTopic` `useBatchDeleteTopics` | `/topics` `/topics/search` `/topics/{id}` `/topics/batch-delete` |
| `/material/topic-group` `TopicGroupList` | 查看话题组、创建、编辑、删除、跳转详情 | `useTopics` `useTopicGroups` `useCreateTopicGroup` `useUpdateTopicGroup` `useDeleteTopicGroup` | `/topic-groups` `/topic-groups/{id}` `/topics` |
| `/material/topic-group/:id` `TopicGroupDetail` | 查看话题组详情 | `useTopicGroups` | `/topic-groups` |
| `/material/product` `ProductList` | 查看商品、创建、编辑、删除、批删、触发素材解析 | `useCreateProductV2` `useDeleteProductV2` `useUpdateProductV2` `useBatchDeleteProducts` + `api.post('/products/{id}/parse-materials')` | `/products` `/products/{id}` `/products/{id}/parse-materials` |
| `/material/product/:id` `ProductDetail` | 查看商品详情、更新商品、再次解析素材 | `useProduct` `useUpdateProductV2` + `api.post('/products/{id}/parse-materials')` | `/products/{id}` `/products/{id}/parse-materials` `/products/{id}/materials` |
| `/ai-clip` `AIClip` | 查看视频信息、检测高光、智能剪辑、加音频、加封面、跑完整流水线 | `useVideoInfo` `useDetectHighlights` `useSmartClip` `useAddAudio` `useAddCover` `useFullPipeline` | `/ai/video-info` `/ai/detect-highlights` `/ai/smart-clip` `/ai/add-audio` `/ai/add-cover` `/ai/full-pipeline` |
| `/settings` `Settings` | 查看素材路径说明、触发备份 | `api.post('/system/backup')` | `/system/backup` |
| `/schedule-config` `ScheduleConfig` | 查看和保存调度配置 | `api.get('/publish/config')` `api.put('/publish/config')` | `/publish/config` |
| `/profile-management` `ProfileManagement` | 查看配置档、创建、编辑、删除、设默认 | `useProfiles` `useCreateProfile` `useUpdateProfile` `useDeleteProfile` `useSetDefaultProfile` | `/profiles` `/profiles/{id}` `/profiles/{id}/set-default` |

## 4. 共享组件与接口映射

这些不是路由页，但它们对接口流转很关键。

| 组件 | 主要职责 | 主要接口 |
|------|----------|----------|
| `ConnectionModal` | 账号手机验证码连接、SSE 进度订阅 | `/accounts/connect/{id}/stream` `/accounts/connect/{id}/send-code` `/accounts/connect/{id}/verify` |
| `ProductQuickImport` | 按商品快速导入关联素材到任务创建篮子 | `/products` `/products/{id}/materials` |
| `MaterialSelectModal` | 在任务创建时从素材库挑选视频/文案/封面/音频 | `/videos` `/copywritings` `/covers` `/audios` |
| `ProductSelect` | 商品选择器 | `/products` |

## 5. 后端接口分组总览

| 接口组 | 主要用途 | 主要消费页面 |
|--------|----------|--------------|
| `/accounts` | 账号 CRUD、连接、预览、健康检查 | `Account` `ConnectionModal` |
| `/tasks` | 任务 CRUD、组装、重试、合成状态 | `TaskList` `TaskCreate` `TaskDetail` |
| `/publish` | 调度配置、发布控制、发布状态、发布日志 | `Dashboard` `ScheduleConfig` |
| `/profiles` | 任务级配置档管理 | `TaskCreate` `ProfileManagement` |
| `/system` | 系统统计、系统日志、系统配置、备份、素材统计 | `Dashboard` `Settings` `MaterialOverview` |
| `/products` | 商品 CRUD、商品解析、素材聚合 | `ProductList` `ProductDetail` `TaskCreate` |
| `/videos` | 视频素材管理 | `VideoList` `VideoDetail` `MaterialSelectModal` |
| `/copywritings` | 文案素材管理 | `CopywritingList` `MaterialSelectModal` |
| `/covers` | 封面素材管理 | `CoverList` `MaterialSelectModal` |
| `/audios` | 音频素材管理 | `AudioList` `MaterialSelectModal` |
| `/topics` | 话题库管理、全局话题、搜索 | `TopicList` `TopicGroupList` |
| `/topic-groups` | 话题组 CRUD 与详情 | `TopicGroupList` `TopicGroupDetail` |
| `/ai` | 本地 AI 剪辑流水线 | `AIClip` |

## 6. 典型页面调用链

### 6.1 任务创建页

```text
TaskCreate
  ├─ useAccounts               -> /accounts
  ├─ useProfiles               -> /profiles
  ├─ ProductQuickImport        -> /products + /products/{id}/materials
  ├─ MaterialSelectModal       -> /videos /copywritings /covers /audios
  └─ useBatchAssemble          -> POST /tasks/batch-assemble
```

### 6.2 账号连接页

```text
Account
  ├─ useAccounts               -> /accounts
  ├─ ConnectionModal
  │    ├─ SSE                 -> /accounts/connect/{id}/stream
  │    ├─ 发送验证码           -> /accounts/connect/{id}/send-code
  │    └─ 验证码登录           -> /accounts/connect/{id}/verify
  ├─ usePreviewAccount         -> /accounts/{id}/preview
  ├─ useClosePreview           -> /accounts/{id}/preview/close
  ├─ useHealthCheck            -> /accounts/{id}/health-check
  └─ useBatchHealthCheck       -> /accounts/batch-health-check
```

### 6.3 发布控制页

```text
Dashboard
  ├─ useTaskStats              -> /tasks/stats
  ├─ useSystemStats            -> /system/stats
  ├─ useSystemLogs             -> /system/logs
  ├─ usePublishStatus          -> /publish/status
  └─ useControlPublish         -> /publish/control
```

## 7. 当前接口层的几个现实情况

### 7.1 生成客户端与后端接口并非完全同步

已经能看到这些补丁式写法：

- `useAccounts` 为了 `tag/search` 参数回退到手写 Axios
- `TaskDetail` 手写扩展接口并强制类型转换
- 一些页面直接 `api.get('/publish/config')`，没有统一走 hook

说明页面和后端接口的演进速度，已经快过 OpenAPI 客户端的再生成节奏。

### 7.2 同一业务有时存在“生成客户端 + 手写 Axios”双路径

例如：

- 发布配置：既有 `usePublishConfig` / `useUpdatePublishConfig`，也有 `ScheduleConfig.tsx` 直接用 Axios
- 任务列表：不是直接复用 `useTasks`，而是自己在表格 `request` 中调 `/tasks`

这会让页面层风格不统一。

### 7.3 页面粒度上已经形成比较清晰的模块边界

从当前结构看，接口组和页面模块的对应关系整体是清楚的：

- 账号模块对 `/accounts`
- 任务模块对 `/tasks`
- 调度模块对 `/publish`
- 素材模块对 `/videos` `/copywritings` `/covers` `/audios` `/topics`
- 商品模块对 `/products`
- 系统页对 `/system`

所以第二阶段重构，更适合做“接口收口与统一抽象”，而不是重新拆页面边界。

