# 得物掘金工具前后端接口清单与页面对应关系

## 1. 文档目的

这份文档回答两个问题：

1. 前端每个页面主要调用哪些 hooks / API
2. 后端接口分组分别服务哪些页面

当前分析基于：

- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/pages/**`
- `frontend/src/hooks/**`
- `backend/api/*.py`

## 2. 页面路由总表

| 路由 | 页面文件 | 页面职责 |
|------|----------|----------|
| `/dashboard` | `pages/Dashboard.tsx` | 任务概览、发布控制、系统日志 |
| `/account` | `pages/Account.tsx` | 账号 CRUD、连接、预览、健康检查 |
| `/task/list` | `pages/TaskList.tsx` | 任务列表、筛选、删除 |
| `/task/create` | `pages/task/TaskCreate.tsx` | 任务组装与批量创建 |
| `/task/:id` | `pages/task/TaskDetail.tsx` | 任务详情、提交合成、重试、取消 |
| `/material/overview` | `pages/material/MaterialOverview.tsx` | 素材总览与导航入口 |
| `/material/video` | `pages/material/VideoList.tsx` | 视频素材管理 |
| `/material/video/:id` | `pages/material/VideoDetail.tsx` | 视频详情 |
| `/material/copywriting` | `pages/material/CopywritingList.tsx` | 文案管理 |
| `/material/cover` | `pages/material/CoverList.tsx` | 封面管理 |
| `/material/audio` | `pages/material/AudioList.tsx` | 音频管理 |
| `/material/topic` | `pages/material/TopicList.tsx` | 话题管理 |
| `/material/topic-group` | `pages/material/TopicGroupList.tsx` | 话题组列表 |
| `/material/topic-group/:id` | `pages/material/TopicGroupDetail.tsx` | 话题组详情 |
| `/material/product` | `pages/product/ProductList.tsx` | 商品列表与素材解析 |
| `/material/product/:id` | `pages/product/ProductDetail.tsx` | 商品详情与素材查看 |
| `/ai-clip` | `pages/AIClip.tsx` | AI 剪辑工具 |
| `/settings` | `pages/Settings.tsx` | 系统设置与数据备份 |
| `/schedule-config` | `pages/ScheduleConfig.tsx` | 发布调度配置 |
| `/profile-management` | `pages/ProfileManagement.tsx` | 合成配置档管理 |

## 3. 后端接口分组总表

| 接口分组 | 路由前缀 | 主要用途 |
|----------|----------|----------|
| 账号 | `/api/accounts` | 账号管理、连接、预览、健康检查、会话导入导出 |
| 任务 | `/api/tasks` | 任务 CRUD、批量组装、重试、合成状态 |
| 发布控制 | `/api/publish` | 调度配置、开始/暂停/停止、发布状态、发布日志 |
| 系统 | `/api/system` | 系统统计、系统日志、系统配置、备份、素材统计 |
| 商品 | `/api/products` | 商品 CRUD、解析素材、读取商品相关素材 |
| 视频 | `/api/videos` | 视频 CRUD、上传、扫描、校验、流媒体 |
| 文案 | `/api/copywritings` | 文案 CRUD、导入、批量删除 |
| 封面 | `/api/covers` | 封面上传、列表、删除、抽帧、预览 |
| 音频 | `/api/audios` | 音频上传、列表、删除 |
| 话题 | `/api/topics` | 话题 CRUD、搜索、全局话题 |
| 话题组 | `/api/topic-groups` | 话题组 CRUD |
| 配置档 | `/api/profiles` | PublishProfile CRUD、设默认 |
| AI 剪辑 | `/api/ai` | 视频信息、高光检测、剪辑、加音频、加封面、全流程 |

## 4. 页面与接口的详细对应关系

### 4.1 看板与系统页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `Dashboard` | `useSystemStats` | `GET /api/system/stats` | 读取系统概览 |
| `Dashboard` | `useSystemLogs` | `GET /api/system/logs` | 读取运行日志 |
| `Dashboard` | `useTaskStats` | `GET /api/tasks/stats` | 读取任务状态统计 |
| `Dashboard` | `usePublishStatus` | `GET /api/publish/status` | 读取调度器状态 |
| `Dashboard` | `useControlPublish` | `POST /api/publish/control` | 开始 / 暂停 / 停止发布 |
| `Settings` | 直接 `api.post` | `POST /api/system/backup` | 执行数据备份 |
| `Settings` | 无动态查询 | 无 | 当前素材路径是硬编码展示，不是实时配置 |
| `ScheduleConfig` | 直接 `api.get` / `api.put` | `GET/PUT /api/publish/config` | 读取与保存发布调度参数 |

### 4.2 账号页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `Account` | `useAccounts` | `GET /api/accounts` | 账号列表、筛选 |
| `Account` | `useCreateAccount` | `POST /api/accounts` | 新建账号 |
| `Account` | `useUpdateAccount` | `PUT /api/accounts/{id}` | 编辑账号 |
| `Account` | `useDeleteAccount` | `DELETE /api/accounts/{id}` | 删除账号 |
| `Account` | `usePreviewAccount` | `POST /api/accounts/{id}/preview` | 打开预览浏览器 |
| `Account` | `useClosePreview` | `POST /api/accounts/{id}/preview/close` | 关闭预览并可保存 session |
| `Account` | `usePreviewStatus` | `GET /api/accounts/preview/status` | 轮询预览状态 |
| `Account` | `useHealthCheck` | `POST /api/accounts/{id}/health-check` | 单账号健康检查 |
| `Account` | `useBatchHealthCheck` | `POST /api/accounts/batch-health-check` | 批量健康检查 |
| `Account` | `useBatchCheckStatus` | `GET /api/accounts/batch-health-check/status` | 批量检查进度 |
| `ConnectionModal` | 直接 SSE + `api.post` | `GET /api/accounts/connect/{id}/stream` | 实时接收连接状态 |
| `ConnectionModal` | 直接 `api.post` | `POST /api/accounts/connect/{id}/send-code` | 发送验证码 |
| `ConnectionModal` | 直接 `api.post` | `POST /api/accounts/connect/{id}/verify` | 校验验证码并完成登录 |

### 4.3 任务页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `TaskList` | 直接 `api.get('/tasks')` | `GET /api/tasks` | 列表、分页、筛选 |
| `TaskList` | `useDeleteTask` | `DELETE /api/tasks/{id}` | 删除单任务 |
| `TaskList` | `useDeleteAllTasks` | `DELETE /api/tasks` | 清空任务 |
| `TaskCreate` | `useAccounts` | `GET /api/accounts` | 读取账号选项 |
| `TaskCreate` | `useProfiles` | `GET /api/profiles` | 读取配置档选项 |
| `TaskCreate` | `useBatchAssemble` | `POST /api/tasks/batch-assemble` | 用素材集合批量生成任务 |
| `TaskDetail` | `useTask` | `GET /api/tasks/{id}` | 读取任务详情 |
| `TaskDetail` | `useSubmitComposition` | `POST /api/tasks/{id}/submit-composition` | 提交合成 |
| `TaskDetail` | `useCompositionStatus` | `GET /api/tasks/{id}/composition-status` | 轮询合成状态 |
| `TaskDetail` | `useCancelComposition` | `POST /api/tasks/{id}/cancel-composition` | 取消合成 |
| `TaskDetail` | `useRetryTask` | `POST /api/tasks/{id}/retry` | 快速重试 |
| `TaskDetail` | `useEditRetryTask` | `POST /api/tasks/{id}/edit-retry` | 编辑重试 |
| `TaskDetail` | `useCancelTask` | `POST /api/tasks/{id}/cancel` | 取消任务 |
| `TaskDetail` | `useDeleteTask` | `DELETE /api/tasks/{id}` | 删除任务 |

## 5. 素材中心页面与接口映射

### 5.1 总览页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `MaterialOverview` | 直接 `useQuery + api.get` | `GET /api/system/material-stats` | 读取素材统计与商品覆盖率 |

### 5.2 视频页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `VideoList` | `useVideos` | `GET /api/videos` | 查询视频列表 |
| `VideoList` | `useCreateVideo` | `POST /api/videos` | 新建视频记录 |
| `VideoList` | `useUploadVideo` | `POST /api/videos/upload` | 上传视频文件 |
| `VideoList` | `useDeleteVideo` | `DELETE /api/videos/{id}` | 删除视频 |
| `VideoList` | `useBatchDeleteVideos` | `POST /api/videos/batch-delete` | 批量删除 |
| `VideoList` | `useScanVideos` | `POST /api/videos/scan` | 扫描目录导入 |
| `VideoDetail` | `useVideo` | `GET /api/videos/{id}` | 读取视频详情 |

### 5.3 文案页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `CopywritingList` | `useCopywritings` | `GET /api/copywritings` | 查询文案列表 |
| `CopywritingList` | `useCreateCopywriting` | `POST /api/copywritings` | 新建文案 |
| `CopywritingList` | `useUpdateCopywriting` | `PUT /api/copywritings/{id}` | 更新文案 |
| `CopywritingList` | `useDeleteCopywriting` | `DELETE /api/copywritings/{id}` | 删除文案 |
| `CopywritingList` | `useImportCopywritings` | `POST /api/copywritings/import` | 批量导入文案 |
| `CopywritingList` | `useBatchDeleteCopywritings` | `POST /api/copywritings/batch-delete` | 批量删除 |

### 5.4 封面页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `CoverList` | `useCovers` | `GET /api/covers` | 查询封面 |
| `CoverList` | `useUploadCover` | `POST /api/covers/upload` | 上传封面 |
| `CoverList` | `useExtractCover` | `POST /api/covers/extract` | 从视频抽封面 |
| `CoverList` | `useDeleteCover` | `DELETE /api/covers/{id}` | 删除封面 |
| `CoverList` | `useBatchDeleteCovers` | `POST /api/covers/batch-delete` | 批量删除 |
| `ProductDetail` | 图片预览直连 | `GET /api/covers/{id}/image` | 查看封面图像 |

### 5.5 音频页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `AudioList` | `useAudios` | `GET /api/audios` | 查询音频 |
| `AudioList` | `useUploadAudio` | `POST /api/audios/upload` | 上传音频 |
| `AudioList` | `useDeleteAudio` | `DELETE /api/audios/{id}` | 删除音频 |
| `AudioList` | `useBatchDeleteAudios` | `POST /api/audios/batch-delete` | 批量删除 |

### 5.6 话题与话题组页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `TopicList` | `useTopics` | `GET /api/topics` | 查询话题 |
| `TopicList` | `useCreateTopic` | `POST /api/topics` | 新建话题 |
| `TopicList` | `useDeleteTopic` | `DELETE /api/topics/{id}` | 删除话题 |
| `TopicList` | `useSearchTopics` | `GET /api/topics/search` | 搜索话题 |
| `TopicList` | `useGlobalTopics` | `GET /api/topics/global` | 读取全局话题配置 |
| `TopicList` | `useSetGlobalTopics` | `PUT /api/topics/global` | 写入全局话题配置 |
| `TopicList` | `useBatchDeleteTopics` | `POST /api/topics/batch-delete` | 批量删除 |
| `TopicGroupList` | `useTopicGroups` | `GET /api/topic-groups` | 读取话题组列表 |
| `TopicGroupList` | `useCreateTopicGroup` | `POST /api/topic-groups` | 创建话题组 |
| `TopicGroupList` | `useDeleteTopicGroup` | `DELETE /api/topic-groups/{id}` | 删除话题组 |
| `TopicGroupDetail` | `useTopicGroup` | `GET /api/topic-groups/{id}` | 读取详情 |
| `TopicGroupDetail` | `useUpdateTopicGroup` | `PUT /api/topic-groups/{id}` | 更新话题组 |

### 5.7 商品页

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `ProductList` | 直接 `api.get('/products')` | `GET /api/products` | 商品列表 |
| `ProductList` | `useCreateProductV2` | `POST /api/products` | 创建商品 |
| `ProductList` | `useUpdateProductV2` | `PUT /api/products/{id}` | 更新商品 |
| `ProductList` | `useDeleteProductV2` | `DELETE /api/products/{id}` | 删除商品 |
| `ProductList` | `useBatchDeleteProducts` | 批量商品删除接口 | 批量删除 |
| `ProductList` | 直接 `api.post` | `POST /api/products/{id}/parse-materials` | 解析商品素材 |
| `ProductDetail` | `useProduct` | `GET /api/products/{id}` | 读取商品详情 |
| `ProductDetail` | `useUpdateProductV2` | `PUT /api/products/{id}` | 编辑商品 |
| `ProductDetail` | 直接 `api.post` | `POST /api/products/{id}/parse-materials` | 重新解析素材 |
| `ProductDetail` | 数据内嵌返回 | `GET /api/products/{id}` | 展示商品下视频 / 封面 / 文案 / 话题 |

## 6. AI 与配置类页面

| 页面 | 主要 hooks / 调用 | 对应后端接口 | 主要动作 |
|------|-------------------|--------------|----------|
| `AIClip` | `useVideoInfo` | `GET /api/ai/video-info` | 读取视频信息 |
| `AIClip` | `useDetectHighlights` | `GET /api/ai/detect-highlights` | 检测高光片段 |
| `AIClip` | `useSmartClip` | `POST /api/ai/smart-clip` | 智能剪辑 |
| `AIClip` | `useAddAudio` | `POST /api/ai/add-audio` | 给视频加音频 |
| `AIClip` | `useAddCover` | `POST /api/ai/add-cover` | 给视频加封面 |
| `AIClip` | `useFullPipeline` | `POST /api/ai/full-pipeline` | 执行完整剪辑流程 |
| `ProfileManagement` | `useProfiles` | `GET /api/profiles` | 读取配置档 |
| `ProfileManagement` | `useCreateProfile` | `POST /api/profiles` | 新建配置档 |
| `ProfileManagement` | `useUpdateProfile` | `PUT /api/profiles/{id}` | 编辑配置档 |
| `ProfileManagement` | `useDeleteProfile` | `DELETE /api/profiles/{id}` | 删除配置档 |
| `ProfileManagement` | `useSetDefaultProfile` | `PUT /api/profiles/{id}/set-default` | 设默认配置档 |

## 7. 后端接口清单

下面按接口组列出主要端点，便于从页面反查到后端实现。

### 7.1 `/api/accounts`

- `GET /`
- `POST /`
- `GET /stats`
- `GET /{account_id}`
- `PUT /{account_id}`
- `DELETE /{account_id}`
- `POST /{account_id}/health-check`
- `GET /preview/status`
- `POST /{account_id}/preview`
- `POST /{account_id}/preview/close`
- `POST /batch-health-check`
- `GET /batch-health-check/status`
- `POST /connect/{account_id}/send-code`
- `POST /connect/{account_id}/verify`
- `GET /connect/{account_id}/stream`
- `GET /connect/{account_id}/status`
- `POST /connect/{account_id}/export`
- `POST /connect/{account_id}/import`
- `GET /connect/{account_id}/screenshot`
- `POST /disconnect/{account_id}`

### 7.2 `/api/tasks`

- `POST /`
- `GET /`
- `GET /stats`
- `GET /{task_id}`
- `PUT /{task_id}`
- `DELETE /{task_id}`
- `DELETE /`
- `POST /{task_id}/cancel`
- `POST /{task_id}/retry`
- `POST /{task_id}/edit-retry`
- `POST /{task_id}/publish`
- `POST /batch`
- `POST /shuffle`
- `POST /assemble`
- `POST /batch-assemble`
- `POST /{task_id}/submit-composition`
- `POST /batch-submit-composition`
- `POST /{task_id}/cancel-composition`
- `GET /{task_id}/composition-status`

### 7.3 `/api/publish`

- `GET /config`
- `PUT /config`
- `GET /status`
- `POST /control`
- `POST /refresh`
- `POST /shuffle`
- `GET /logs`

### 7.4 `/api/system`

- `GET /stats`
- `GET /logs`
- `POST /logs`
- `GET /config`
- `PUT /config`
- `POST /backup`
- `GET /material-stats`

### 7.5 素材与商品相关

- `/api/videos`
- `/api/copywritings`
- `/api/covers`
- `/api/audios`
- `/api/topics`
- `/api/topic-groups`
- `/api/products`
- `/api/profiles`
- `/api/ai`

具体端点可直接参考 `backend/api/*.py` 中的路由定义。

## 8. 页面到接口映射里的几个现实特点

### 8.1 不是所有页面都只通过统一 hooks 层访问

当前前端存在三种调用方式并存：

1. OpenAPI 生成 client
2. 自定义 React Query hooks
3. 页面里直接 `api.get/api.post`

例如：

- `TaskList` 直接请求 `/tasks`
- `ScheduleConfig` 直接请求 `/publish/config`
- `Settings` 直接调用 `/system/backup`
- `MaterialOverview` 直接调用 `/system/material-stats`
- `ProductList` 直接调用 `/products/{id}/parse-materials`

### 8.2 生成客户端与手写接口并存

一些后端接口是后加的，前端只能通过手写 axios 补齐：

- 账号搜索 / 标签筛选
- 任务重试与合成状态
- 预览相关接口

### 8.3 页面和接口并不是完全一一对应

例如：

- `Dashboard` 同时依赖 `system`、`tasks`、`publish`
- `TaskCreate` 依赖 `accounts`、`profiles`、`tasks`
- `ProductDetail` 依赖 `products`、`covers`

所以这套系统更适合按“页面 -> hooks -> 接口组”三层来理解，而不是按单页面单接口来理解。

## 9. 一句话总结

如果压缩成一条主线，这个前后端映射大致是：

```text
页面负责交互
→ hooks 负责缓存与动作封装
→ API 分组负责领域边界
→ 后端 services 负责真正业务执行
```

其中任务、账号、发布控制、素材管理这四组接口，是当前前端页面最核心的支撑面。
