# 登录链路说明：应用登录 vs 业务账号连接

本文用于澄清当前项目中“登录”相关概念，避免把**应用授权登录**与**业务账号连接**混为一谈。

---

## 1. 一句话结论

当前界面表面上看是一个登录页，但在这个 Electron + 本地 FastAPI 的架构里，它本质上不是单纯的 Web 表单登录，而是：

> **桌面客户端机器授权入口**

前端负责收集登录信息；真正的认证、会话落盘、设备绑定、刷新与状态判定，都由本地后端负责，再由本地后端去调用远端认证系统。

---

## 2. 两套容易混淆的“登录/连接”

项目里实际上存在两条不同的链路。

### A. 应用登录（本地应用授权）

目标：让操作者进入这个桌面应用。

- 前端入口：`frontend/src/features/auth/LoginPage.tsx`
- 前端路由：`/login`
- 本地接口：`/api/auth/login`
- 本地服务：`backend/api/auth.py`
- 编排层：`backend/services/auth_service.py`

这条链路解决的是：

- 操作者是谁
- 这台机器是否被允许使用
- 当前授权是否有效
- 本地是否可以恢复会话
- 远端授权是否被撤销 / 过期 / 设备不匹配

---

### B. 业务账号连接（得物账号连接）

目标：让应用内部的“账号”可用于业务发布、预览、导入导出 session 等操作。

- 相关接口：`/api/accounts/connect/*`
- 历史兼容别名：`/api/accounts/login/*`、`/api/accounts/logout/*`
- 主要后端：`backend/api/account.py`

这条链路解决的是：

- 某个业务账号是否已连接
- 会话是否可用
- 是否需要短信验证码
- 是否可截图 / 导出 / 导入 / 断开

---

## 3. 它们的关系

正确关系是：

```text
先登录应用（Auth）
    ↓
进入受保护的主界面
    ↓
再管理 / 连接 业务账号（Accounts Connect）
    ↓
创建任务、发布内容、查看诊断
```

所以：

> **应用登录是系统门禁；业务账号连接是业务能力。**

二者不是一回事。

---

## 4. 当前登录页真实在做什么

从实现上看，`LoginPage.tsx` 并不是直接把账号密码发到远端就结束，而是：

1. 收集用户名、密码
2. 附带本机 `device_id`
3. 附带客户端版本 `client_version`
4. 请求本地后端 `POST /api/auth/login`
5. 由本地后端再去调用远端认证系统
6. 把远端结果转成本地 machine session

也就是说，前端信任的不是“浏览器里自己算出来的登录态”，而是：

> **本地后端返回的授权状态真相**

---

## 5. 为什么它不只是一个普通登录页

因为当前实现额外承担了下面这些职责：

### 5.1 本地会话持久化

`AuthService` 会把远端登录结果整理为本地 session summary，并持久化：

- `auth_state`
- `remote_user_id`
- `display_name`
- `license_status`
- `entitlements`
- `expires_at`
- `offline_grace_until`
- `denial_reason`
- `device_id`

同时把 token 放在本地 secret store，而不是让前端自己保存和管理。

---

### 5.2 设备绑定

登录会显式传入 `device_id`。

前端设备标识来源：

- `frontend/src/features/auth/device.ts`

后端也会维护/固化设备标识：

- `AuthService._resolve_device_id(...)`
- `device_identity_store`

所以这里不是简单“用户密码正确即可”，而是还包含：

> **这个授权是否属于当前这台机器**

这就是 `device_mismatch` 状态存在的原因。

---

### 5.3 启动恢复与刷新

应用启动后，不是简单地重新跳登录页，而是先看本地 session：

- `/api/auth/session`
- `/api/auth/status`
- `/api/auth/refresh`

因此系统支持：

- 启动恢复
- token 刷新
- 主动/被动续期
- 过期判定
- 离线宽限

---

### 5.4 授权状态机

当前 auth 不是单状态，而是一组状态机。代码里可见的核心状态包括：

- `unauthenticated`
- `authenticated_active`
- `authenticated_grace`
- `expired`
- `revoked`
- `device_mismatch`
- `error`

这些状态会驱动路由守卫和状态页，而不是只在登录页里弹一个错误。

---

## 6. 前端路由是怎么接住这套状态机的

入口可见于：

- `frontend/src/App.tsx`
- `frontend/src/features/auth/AuthRouteGate.tsx`

其逻辑大致是：

- 登录页走公开路由：`/login`
- 主应用走受保护路由：`ProtectedAppShell`
- 如果 auth_state 不满足访问条件，就重定向到对应状态页

典型跳转包括：

- 未登录 → `/login`
- 设备不匹配 → `/auth/device-mismatch`
- 已撤销 → `/auth/revoked`
- 已过期 → `/auth/expired`
- 宽限模式 → `/auth/grace`

因此当前实现不是“登录成功就进首页”，而是：

> **整个应用都受本地授权状态机控制**

---

## 7. 当前登录链路流程图

### 7.1 应用登录流程

```text
用户打开应用
   ↓
前端启动 Auth Bootstrap
   ↓
请求本地 /api/auth/session + /api/auth/status
   ↓
根据本地 machine session 判定 auth_state
   ├─ unauthenticated → 进入 /login
   ├─ authenticated_active → 进入受保护主界面
   ├─ authenticated_grace → 进入宽限/可继续使用
   ├─ device_mismatch → 跳 /auth/device-mismatch
   ├─ revoked → 跳 /auth/revoked
   └─ expired → 跳 /auth/expired

在 /login 页面提交表单
   ↓
POST /api/auth/login
   ↓
本地 AuthService 调远端认证系统
   ↓
成功：保存 token + 落本地 session + 固化 device_id
   ↓
auth_state = authenticated_active
   ↓
进入主应用
```

---

### 7.2 业务账号连接流程

```text
用户已进入主应用
   ↓
进入账号管理
   ↓
调用 /api/accounts/connect/* 相关接口
   ↓
处理业务账号连接/验证码/session 导入导出
   ↓
业务账号可用于任务发布/预览/调试
```

注意：这一步依赖前面的“应用登录”已经通过。

---

## 8. 为什么会让人误以为“只是登录页”

因为从用户感知上，它确实只有这些动作：

- 输入用户名密码
- 登录
- 登录失败
- 退出登录

但从工程实现上，它还承担了：

- 本地授权代理
- token 管理
- 会话恢复
- 设备绑定
- 宽限期处理
- 吊销/设备不匹配硬拒绝
- 路由门禁
- 本地 admin session 管理

所以更准确的说法不是“只是登录页”，而是：

> **登录页是本地机器授权系统的 UI 入口。**

---

## 9. 推荐的认知模型

后续讨论这个模块时，建议统一用下面的术语：

### 术语 1：应用登录

指：

- `/api/auth/*`
- LoginPage
- AuthRouteGate
- 本地 machine session

本质：**桌面应用授权**

### 术语 2：业务账号连接

指：

- `/api/accounts/connect/*`
- 账号管理页中的连接/验证码/session 流程

本质：**业务账号能力接入**

---

## 10. 最终结论

当前登录界面的产品外观确实只是一个登录页；但就项目架构而言，它已经被实现为：

> **Electron 前端 + 本地 FastAPI + 远端认证系统 的本地机器授权壳**

因此它不是简单的“前端调用远端登录接口”，而是：

1. 前端收集登录信息  
2. 本地后端代理远端认证  
3. 本地后端维护机器级授权会话  
4. 前端全局按授权状态机进行路由与展示

如果只把它理解成“一个普通登录页”，就会低估当前实现的复杂度；  
如果把它理解成“本地授权门禁系统”，当前代码结构就容易理解得多。

