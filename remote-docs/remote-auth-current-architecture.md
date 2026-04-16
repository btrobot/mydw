# Remote Auth 当前架构图（本地端 ↔ remote-backend ↔ remote-admin）

## 1. 总体关系图

```text
┌──────────────────────────────┐
│ 本地客户端 / 本地实现        │
│ local remote-auth consumer   │
│                              │
│ - login 触发                 │
│ - refresh / logout / /me     │
│ - 本地 auth 状态机           │
│ - machine-session truth      │
│ - 本地错误 UX                │
└──────────────┬───────────────┘
               │ HTTP / JSON
               │
               ▼
┌──────────────────────────────┐
│ remote-backend               │
│ 远端授权中心 / 真实授权源    │
│                              │
│ Public Auth APIs             │
│ - POST /login                │
│ - POST /refresh              │
│ - POST /logout               │
│ - GET  /me                   │
│                              │
│ Admin APIs                   │
│ - POST /admin/login          │
│ - GET  /admin/session        │
│ - GET  /admin/users          │
│ - GET  /admin/devices        │
│ - GET  /admin/sessions       │
│ - GET  /admin/audit-logs     │
│ - GET  /admin/metrics/summary│
│                              │
│ Domain Truth                 │
│ - users                      │
│ - licenses                   │
│ - entitlements               │
│ - devices                    │
│ - sessions                   │
│ - refresh tokens             │
│ - audit logs                 │
│                              │
│ Control / Policy             │
│ - revoke / restore           │
│ - disable                    │
│ - device binding             │
│ - device mismatch            │
│ - min version gate           │
│ - offline grace policy       │
│ - admin RBAC                 │
└──────────────┬───────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
     │ HTTP / JSON       │ HTTP / JSON
     ▼                   ▼
┌──────────────────┐   ┌──────────────────────┐
│ 本地客户端继续消费│   │ remote-admin         │
│ remote auth 结果  │   │ 远端管理后台前端     │
│                  │   │                      │
│ - access_token   │   │ - admin login        │
│ - refresh_token  │   │ - dashboard          │
│ - license_status │   │ - users              │
│ - entitlements   │   │ - devices            │
│ - device_status  │   │ - sessions           │
│ - error_code     │   │ - audit              │
└──────────────────┘   └──────────────────────┘
```

---

## 2. 三个核心角色

### A. 本地端（consumer / projection）
本地端不是授权真相源，而是：

- 调用远端 `/login /refresh /logout /me`
- 接收远端返回的授权上下文
- 在本地维护 machine-session truth / 状态机投影
- 根据远端错误语义执行本地 UX：
  - `revoked`
  - `disabled`
  - `device_mismatch`
  - `minimum_version_required`

一句话：

> **本地端负责“消费和执行”，不负责“定义授权真相”。**

---

### B. remote-backend（source of truth）
remote-backend 是整个 remote auth 的核心：

- 认证入口
- token / session 生命周期
- license / entitlement 真相
- device 绑定与 mismatch 判断
- revoke / disable / restore 控制
- admin RBAC
- audit / metrics / tracing

一句话：

> **remote-backend 是授权与控制的唯一真实来源。**

---

### C. remote-admin（operator console）
remote-admin 是管理与支持人员使用的控制台：

- 登录独立的 admin 账户
- 查看 dashboard / users / devices / sessions / audit
- 发起管理动作：
  - revoke user
  - restore user
  - disable / unbind / rebind device
  - revoke session
- 做运营排查与支持处理

一句话：

> **remote-admin 负责操作和展示，不负责授权规则判断。**

---

## 3. 主链路

## 3.1 终端用户认证链路

```text
本地客户端
  -> POST /login to remote-backend
  -> remote-backend 校验 user/license/device/version
  -> 返回 access_token / refresh_token / auth context
  -> 本地端写入本地 session truth 并进入 authenticated 状态
```

后续：

```text
本地客户端
  -> POST /refresh
  -> remote-backend 做 refresh token rotation + policy check
  -> 返回新 token 与最新 auth context
```

以及：

```text
本地客户端
  -> GET /me
  -> 获取当前授权上下文
```

---

## 3.2 管理员控制链路

```text
remote-admin
  -> POST /admin/login
  -> remote-backend 建立 admin session
  -> remote-admin 进入受保护后台
```

后台操作时：

```text
remote-admin
  -> /admin/users | /admin/devices | /admin/sessions | /admin/audit-logs
  -> remote-backend 做 RBAC 检查
  -> 返回管理数据
```

写操作时：

```text
remote-admin
  -> revoke / restore / disable / unbind / rebind / session revoke
  -> remote-backend 执行控制动作
  -> 写 actor-level audit
  -> 前台刷新当前视图
```

---

## 4. 关键边界

## 4.1 本地端与远端后端的边界
本地端只依赖 contract，不直接依赖 remote-backend 内部实现。

本地端读取的是：
- 成功 payload
- error_code
- details

而不是：
- 数据库结构
- 后端内部 service / repository 细节

---

## 4.2 remote-admin 与 remote-backend 的边界
remote-admin 只能做：
- 展示
- 过滤
- 发起动作
- 呈现错误 / 重试 / 空态 / in-flight 状态

remote-backend 才负责：
- 判断是否允许操作
- 判断设备是否 mismatch
- 判断 session 是否 revoked
- 记录 audit
- 生成 metrics

---

## 4.3 两类认证域分离
系统里有两类身份：

### managed-user auth domain
- 普通用户
- 用于 `/login /refresh /logout /me`

### admin-operator auth domain
- 管理员 / 支持人员
- 用于 `/admin/login /admin/session /admin/*`

一句话：

> **管理员认证和普通用户认证是两条独立链路。**

---

## 5. 当前已经具备的能力

### 本地端
- 接远端 auth contract
- 本地状态机
- 错误语义承接
- auth UX

### remote-backend
- auth core
- admin auth
- users/devices/sessions/audit/metrics
- RBAC
- actor audit
- bootstrap / gate / docs

### remote-admin
- dashboard
- users/devices/sessions/audit 页面
- filter / detail / destructive action UX
- retry / empty / error / in-flight 状态

---

## 6. 一句话结论

> **当前 remote auth 架构已经形成：本地端负责消费授权结果，remote-backend 负责定义授权真相，remote-admin 负责让管理员可见、可控、可追踪。**
