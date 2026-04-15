# Remote Auth 架构图式说明（面向开发者）

## 1. 总体结构

```text
[Frontend React/Electron]
    │
    │ 调用 /api/auth/*
    ▼
[FastAPI auth API]
    │
    ▼
[AuthService]
    ├─ SecretStore           -> 保存 access/refresh token
    ├─ DeviceIdentityStore   -> 保存本机 device_id
    ├─ RemoteAuthClient      -> 调远端 auth 服务
    ├─ RemoteAuthSession     -> 本地 machine-session truth
    ├─ AuthEvents            -> 结构化事件日志/trace
    └─ AuthMetrics           -> 指标收集与 /metrics
```

## 2. 核心真相源

### 本地会话真相

```text
RemoteAuthSession (DB)
```

保存内容包括：

- `auth_state`
- `remote_user_id`
- `license_status`
- `expires_at`
- `last_verified_at`
- `offline_grace_until`
- `denial_reason`
- `device_id`

### Secret 与非 Secret 分离

```text
DB: non-secret session state
SecretStore: access_token / refresh_token
```

## 3. 核心流程

### 登录

```text
Frontend -> POST /api/auth/login
         -> AuthService.login()
         -> RemoteAuthClient.login()
         -> 写 SecretStore
         -> 更新 RemoteAuthSession
         -> 发 auth event
         -> 返回 LocalAuthSessionSummary
```

### 启动恢复

```text
Frontend bootstrap -> GET /api/auth/session
                   -> AuthService.get_session_summary() / restore_session()
                   -> 根据 token/grace/device 状态归一化
                   -> 返回当前 machine-session
```

### 刷新

```text
POST /api/auth/refresh
 -> AuthService.refresh_if_needed()
 -> RemoteAuthClient.refresh()
 -> 成功: 更新 token + session
 -> 失败: 进入 grace / expired / revoked / device_mismatch
```

### `/me` 校验

```text
GET /api/auth/me
 -> AuthService.get_me()
 -> RemoteAuthClient.me()
 -> 刷新 last_verified_at / device_id / profile info
```

## 4. 状态机

```text
unauthenticated
   ↓ login
authorizing
   ↓ success
authenticated_active
   ↓ network issue
authenticated_grace
   ↓ grace过期
expired
   ↓ refresh needed
refresh_required
   ↓ remote hard deny
revoked / device_mismatch
```

还存在：

```text
error
```

用于远端/本地异常态。

## 5. Backend 门禁

### Route / Service / Scheduler 共用 auth policy

```text
core/auth_dependencies.py
```

负责：

- active-only gate
- grace-readonly gate
- hard-stop state 判断
- policy decision -> HTTP error

影响范围：

- API 路由
- 服务层高风险操作
- scheduler / background task

## 6. 可观测性

### 事件

```text
core/auth_events.py
core/observability.py
```

事件覆盖：

- login success/failure
- refresh success/failure
- session restore
- revoked
- device mismatch
- grace used
- scheduler denied / background stopped

附带上下文：

- `trace_id`
- `request_id`
- `route_name`
- `method`
- `path`

### 指标

```text
core/auth_metrics.py
GET /metrics
```

包括：

- login attempts/failures
- refresh attempts/failures
- active sessions
- session duration
- grace usage duration

## 7. 状态透明化 API

```text
GET /api/auth/status
GET /api/auth/health
GET /api/auth/session/details
```

用途：

- frontend UX
- support / diagnostics
- admin/运维查看

## 8. 前端架构

```text
AuthBootstrapProvider
    ├─ fetch /auth/session
    ├─ 提供 session/authState
    └─ 安装 transport sync

AuthRouteGate
    ├─ active -> 正常进入
    ├─ grace -> 限制页面
    └─ revoked/device_mismatch/expired -> 跳状态页
```

新增 UX 模块：

- `AuthErrorBoundary`
- `AuthErrorMessage`
- `authErrorHandler`
- `useAuthStatus`

## 9. Admin 能力

```text
GET /api/admin/sessions
POST /api/admin/sessions/{id}/revoke
```

前端：

```text
/settings/auth-admin
```

注意点：

- 有独立 `auth:admin` entitlement gate
- revoke 当前会话才清 token
- revoke 历史会话不应污染当前 session
