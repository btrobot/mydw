# Client Transport / Auth Propagation Model（Step 0 PR2）

> 状态：Frozen

---

## 1. Purpose

本文档冻结：

- 当前前端调用通道盘点
- auth 在这些通道中的传播模型
- renderer 与 local FastAPI 在认证真相中的职责边界

---

## 2. Transport inventory

当前仓库至少存在以下调用面：

1. generated OpenAPI client
2. `frontend/src/services/api.ts` 中的 axios client
3. raw axios 调用
4. SSE / `EventSource`

这些调用面后续都必须被纳入统一认证模型。

---

## 3. Auth truth model

v1 冻结以下原则：

### 3.1 Local FastAPI machine-session is the auth truth

前端的主要调用路径是：

> renderer -> local FastAPI

因此本地是否已授权，最终由：

> **local FastAPI machine-session**

决定。

### 3.2 Renderer is not the long-lived bearer truth source

v1 不采用：

> renderer 长期持有 bearer token，并把它作为每个请求的主真相

原因：

- 当前 repo 存在多种调用路径
- SSE / EventSource 不适合被设计成“每请求 header 注入”主模型
- 本地授权门禁真正应落在本地 FastAPI

### 3.3 Primary propagation path

v1 的主模型冻结为：

1. 用户通过前端触发登录
2. 本地 FastAPI 与远程 auth backend 交互
3. 本地 FastAPI 建立 machine-session
4. 前端通过 `/api/auth/session` 等本地接口读取状态
5. 本地 API 调用基于 machine-session 判定是否允许执行

---

## 4. SSE rule

SSE / `EventSource` 必须显式纳入认证设计，不得作为实现阶段才临时处理的例外洞口。

Step 0 只冻结原则，不指定最终技术细节实现。  
但明确：

- 不允许因为 SSE 特性限制而退化成“绕过 machine-session 的特殊未授权通道”
- 不允许把 SSE 留给代码 PR 再决定是否纳入 auth 模型

---

## 5. Non-goals of PR2

本文档不定义：

- SSE 具体实现代码
- axios / generated client 拦截器实现
- Electron preload / IPC 通信实现
- cookie / ephemeral token / signed URL 的最终实现细节

这些属于后续实现工作，不属于 Step 0 docs-only freeze。

