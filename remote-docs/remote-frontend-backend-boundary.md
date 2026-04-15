# 远端系统前后台职责拆分说明

> 目标：明确远端“前台管理系统”和“后端授权中心”各自负责什么，避免职责混乱。

---

## 1. 总体定位

远端系统建议拆成两层：

### 远端前台

一个管理控制台，给运营 / 管理员 / 支持人员使用。

### 远端后端

一个授权控制中心，负责：

- 身份认证
- license / entitlement
- device binding
- session 管理
- revoke / disabled / version gate
- 审计日志

---

## 2. 前台职责

前台负责“展示与操作”，不负责授权真相本身。

### 主要功能

#### 用户管理

- 查看用户列表
- 查看用户状态
- 编辑用户资料
- 禁用/启用用户

#### 授权管理

- 查看 license
- 修改授权状态
- 设置到期时间
- 管理 entitlements
- revoke / restore

#### 设备管理

- 查看设备列表
- 查看设备绑定关系
- 解绑设备
- 标记设备失效
- 重绑设备

#### 会话管理

- 查看当前活跃会话
- 强制 revoke session

#### 审计查看

- 查看登录失败
- 查看 revoke 记录
- 查看 device mismatch
- 查看管理员操作记录

---

## 3. 后端职责

后端负责“规则与真相”。

### 认证职责

- 校验用户名/密码
- 发放 access token / refresh token
- refresh token 轮转
- `/me` 返回当前授权上下文

### 授权职责

- 返回 `license_status`
- 返回 `entitlements`
- 返回 `minimum_supported_version`
- 返回 `offline_grace_until`

### 设备职责

- 根据 `device_id` 做设备绑定判断
- 决定是 `bound`、`unbound` 还是 `device_mismatch`

### 会话职责

- 建立 session
- 跟踪活跃 session
- revoke session

### 管理职责

- 提供 admin API
- 校验 admin 身份和权限
- 写入审计日志

---

## 4. 前后端边界原则

### 原则 1：前台不推导授权真相

前台只能展示后端返回的：

- `license_status`
- `device_status`
- `entitlements`
- session 列表
- audit logs

不应在前端自己推断 revoke / mismatch / disabled。

### 原则 2：后端统一决定错误语义

例如：

- `invalid_credentials`
- `revoked`
- `device_mismatch`
- `minimum_version_required`

都应由后端返回稳定错误码，前台只负责映射展示。

### 原则 3：高风险动作必须由后端校验

包括：

- revoke 用户
- revoke session
- 解绑设备
- 修改 entitlements

前台只能发起动作，不能决定是否合法。

### 原则 4：审计必须后端落地

前台可以展示日志，但不能作为审计真相源。

---

## 5. 推荐 API 分层

建议后端路由按职责分组：

### Public Auth API

- `/login`
- `/refresh`
- `/logout`
- `/me`

### Admin User API

- `/admin/users`
- `/admin/users/{id}`
- `/admin/users/{id}/revoke`

### Admin Device API

- `/admin/devices`
- `/admin/devices/{id}`
- `/admin/devices/{id}/unbind`

### Admin Session API

- `/admin/sessions`
- `/admin/sessions/{id}/revoke`

### Admin Audit API

- `/admin/audit-logs`

---

## 6. 前台页面建议

可以按页面拆：

- 用户列表页
- 用户详情页
- 授权配置页
- 设备列表页
- 会话列表页
- 审计日志页

如果做得更轻量，MVP 可以先合并成：

- 用户/授权管理页
- 设备与会话管理页
- 审计日志页

---

## 7. MVP 拆分建议

### 第一阶段

后端先完成：

- login / refresh / logout / me
- user/license/device/session 数据模型
- revoke 逻辑

前台先完成：

- 用户列表
- 授权状态查看
- 设备列表
- session 列表

### 第二阶段

后端补：

- audit logs
- admin role / permission
- 更细粒度 entitlement 管理

前台补：

- revoke / restore 操作
- 解绑设备
- 查看详细审计

---

## 8. 一句话总结

远端前台是 **管理操作台**，远端后端是 **授权控制中心**。

前台负责：

- 展示
- 发起操作

后端负责：

- 真相
- 校验
- 状态
- 审计
