# 远端后端模块拆分建议

> 目标：给远端后端实现提供模块边界，避免把认证、授权、设备、审计混成一个大服务。

---

## 1. 推荐模块总览

建议至少拆成以下模块：

- `auth`
- `user`
- `license`
- `entitlement`
- `device`
- `session`
- `token`
- `admin`
- `audit`
- `common`

---

## 2. 模块职责说明

## 2.1 `auth`

### 职责

- 登录入口
- refresh 入口
- logout 入口
- `/me`
- 聚合返回 auth 上下文

### 不负责

- 长期授权配置编辑
- 管理员页面逻辑
- 审计查询接口

---

## 2.2 `user`

### 职责

- 用户资料
- 用户状态
- 登录标识管理

### 不负责

- token
- 设备绑定
- entitlement 判定

---

## 2.3 `license`

### 职责

- `license_status`
- 套餐与到期时间
- revoke / disabled / expired 规则
- offline grace 策略

### 不负责

- 用户密码
- token 发放

---

## 2.4 `entitlement`

### 职责

- 管理用户能力集合
- 计算 auth 返回里的 `entitlements`

### 不负责

- 登录
- refresh
- session 生命周期

---

## 2.5 `device`

### 职责

- 设备注册
- 设备绑定/解绑
- 设备状态判断
- device mismatch 判定

### 不负责

- token 发放
- 用户密码

---

## 2.6 `session`

### 职责

- session 建立
- session 查询
- session revoke
- 活跃 session 管理

### 不负责

- refresh token 具体轮转规则

---

## 2.7 `token`

### 职责

- access token 生成/验证
- refresh token 生成/轮转/吊销
- token 失效策略

### 不负责

- 用户展示信息
- license 业务语义

---

## 2.8 `admin`

### 职责

- 管理员登录/鉴权
- admin API RBAC
- 用户、设备、会话管理操作入口

### 不负责

- 普通用户 auth 主链路

---

## 2.9 `audit`

### 职责

- 审计记录写入
- 审计日志查询
- 操作追踪

### 不负责

- 业务决策
- 权限判断

---

## 2.10 `common`

### 职责

- 配置
- 错误码
- DTO
- trace_id / request_id
- 通用中间件

---

## 3. 推荐目录结构

```text
remote-backend/
  app/
    api/
      auth.py
      admin_users.py
      admin_devices.py
      admin_sessions.py
      admin_audit.py
    services/
      auth_service.py
      user_service.py
      license_service.py
      entitlement_service.py
      device_service.py
      session_service.py
      token_service.py
      audit_service.py
    models/
      user.py
      license.py
      entitlement.py
      device.py
      session.py
      audit_log.py
    schemas/
      auth.py
      admin.py
      common.py
    core/
      config.py
      security.py
      errors.py
      observability.py
      db.py
    repositories/
      user_repo.py
      license_repo.py
      device_repo.py
      session_repo.py
      audit_repo.py
```

---

## 4. 服务依赖关系建议

```text
Auth API
  -> AuthService
     -> UserService
     -> LicenseService
     -> EntitlementService
     -> DeviceService
     -> SessionService
     -> TokenService
     -> AuditService
```

Admin API 则建议：

```text
Admin Session API
  -> Admin/AuthZ Gate
  -> SessionService
  -> AuditService

Admin Device API
  -> Admin/AuthZ Gate
  -> DeviceService
  -> AuditService

Admin User API
  -> Admin/AuthZ Gate
  -> UserService
  -> LicenseService
  -> EntitlementService
  -> AuditService
```

---

## 5. 不建议的拆分方式

### 反例 1：所有逻辑都堆进 `auth_service`

问题：

- 后期会变成超大类
- revoke / device / session / admin 逻辑耦合严重

### 反例 2：把 admin 与普通 auth 共用一套完全无边界接口

问题：

- 容易把管理员能力暴露给普通用户
- 难做权限收口

### 反例 3：把 device mismatch 写死在前端判断

问题：

- 真相漂移
- 与本地/远端状态不一致

---

## 6. MVP 建议模块优先级

### 第一优先级

- `auth`
- `user`
- `license`
- `device`
- `session`
- `token`

### 第二优先级

- `admin`
- `audit`

### 第三优先级

- 多租户扩展
- 风控扩展

---

## 7. 一句话总结

推荐把远端后端拆成：

> **认证主链路模块 + 授权/设备/session 模块 + admin 管理模块 + audit 模块**

这样既能支撑当前本地 remote-auth，又方便后续扩展成真正的授权中心。
