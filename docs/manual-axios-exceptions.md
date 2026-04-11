# Manual Axios / Raw URL Exceptions

> Phase 3 / PR4 exception registry

原则：
- 默认应优先使用 generated client
- 只有当前 generated client 不适合或无法表达的场景，才允许保留手写 axios / raw URL
- 所有例外都必须登记在本文件

## 当前允许的例外

### 1. `API_BASE` 构造的媒体直链
这些场景依赖浏览器直接访问图片/视频流，不属于标准 JSON API 调用：

- `frontend/src/pages/material/VideoDetail.tsx`
  - `/videos/{id}/stream`
- `frontend/src/pages/material/VideoList.tsx`
  - `/videos/{id}/stream`
- `frontend/src/pages/material/CoverList.tsx`
  - `/covers/{id}/image`
- `frontend/src/pages/product/ProductDetail.tsx`
  - `/covers/{id}/image`

原因：
- 这是 `<video>` / `<img>` / `<Image>` 的原始资源 URL 消费
- generated client 不比直接 URL 更合适

### 2. `ConnectionModal` 的 SSE / connect flow
- `frontend/src/components/ConnectionModal.tsx`
  - `EventSource(.../accounts/connect/{id}/stream)`
  - raw axios POST `send-code`
  - raw axios POST `verify`

原因：
- SSE 订阅与验证码连接流程当前仍偏特殊交互流
- 这类流程需要和浏览器原生 `EventSource` 协作
- 后续如 generated client / dedicated wrapper 足够稳定，可再迁移

## 不再允许的范围

以下域在 Phase 3 后应优先使用 generated client，而不是继续新增 manual axios：

- account（普通 CRUD / preview status / health-check）
- task
- profile
- system
- schedule-config / publish 高价值路径
- material hooks
- product hooks
- topic / topic-group hooks

## 变更规则

新增例外前必须回答：
1. 为什么 generated client 不适合？
2. 这是暂时例外还是长期例外？
3. 是否需要在下一阶段消除？

若不能回答，不应新增手写调用。
