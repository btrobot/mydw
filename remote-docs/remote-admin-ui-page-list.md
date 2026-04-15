# 远端管理后台页面清单

> 目标：给远端前台（管理控制台）提供一份 MVP 到增强版的页面清单。

---

## 1. 页面分层建议

建议把远端管理后台页面分成三层：

1. **核心运营页**
2. **支持排障页**
3. **平台配置页**

---

## 2. MVP 页面清单

## 2.1 登录页

### 用途

管理员登录远端控制台。

### 最小功能

- 用户名/密码登录
- 登录失败提示
- 跳转 dashboard

---

## 2.2 Dashboard

### 用途

展示 auth 系统概况。

### 最小模块

- 活跃用户数
- 活跃 session 数
- 最近 revoke 数
- 最近 device mismatch 数
- 最近登录失败数

---

## 2.3 用户列表页

### 用途

查看所有授权用户。

### 建议字段

- 用户名
- 显示名
- 用户状态
- license 状态
- 设备数
- 最近活跃时间

### 操作

- 查看详情
- 禁用
- revoke

---

## 2.4 用户详情 / 授权页

### 用途

查看单个用户的授权详情。

### 建议模块

- 基础资料
- license 信息
- entitlement 列表
- 最近设备
- 最近会话

### 操作

- 修改到期时间
- 修改 entitlement
- revoke / restore

---

## 2.5 设备列表页

### 用途

查看所有设备绑定情况。

### 建议字段

- device_id
- 绑定用户
- 绑定状态
- 首次绑定时间
- 最近活跃时间

### 操作

- 查看详情
- 解绑
- 禁用
- 重绑

---

## 2.6 Session 列表页

### 用途

查看活跃授权会话。

### 建议字段

- session_id
- 用户
- device_id
- auth_state
- issued_at
- expires_at
- last_seen_at

### 操作

- revoke session

---

## 2.7 审计日志页

### 用途

支持运营与支持排查。

### 建议筛选

- 时间范围
- 用户
- 设备
- event_type
- actor

### 重点事件

- login_failed
- auth_revoked
- device_mismatch
- refresh_failed
- admin revoke
- admin unbind device

---

## 3. 第二阶段建议页面

## 3.1 设备详情页

### 用途

看某个 device 的完整历史。

### 内容

- 当前绑定关系
- 历史绑定记录
- 最近登录记录
- 最近 mismatch 记录

---

## 3.2 Session 详情页

### 用途

看单个 session 的生命周期。

### 内容

- 创建时间
- 失效时间
- refresh 历史
- revoke 原因

---

## 3.3 管理员操作页

### 用途

查看管理员操作历史。

### 内容

- 谁做了 revoke
- 谁解绑了设备
- 谁修改了 entitlement

---

## 4. 平台配置页（后置）

## 4.1 授权策略页

用于配置：

- 默认 grace 策略
- 最低支持版本
- 默认 entitlement 模板

## 4.2 角色权限页

用于配置：

- admin role
- 页面权限
- 操作权限

---

## 5. MVP 信息架构建议

可以采用侧边导航：

```text
Dashboard
用户管理
设备管理
会话管理
审计日志
```

如果做得更紧凑，也可以先这样：

```text
Dashboard
授权中心
  ├─ 用户
  ├─ 设备
  └─ 会话
审计日志
```

---

## 6. 每页与后端 API 的对应关系

### 用户列表页

- `GET /admin/users`

### 用户详情页

- `GET /admin/users/{id}`
- `PATCH /admin/users/{id}`
- `POST /admin/users/{id}/revoke`
- `POST /admin/users/{id}/restore`

### 设备列表页

- `GET /admin/devices`
- `GET /admin/devices/{id}`
- `POST /admin/devices/{id}/unbind`
- `POST /admin/devices/{id}/disable`

### Session 列表页

- `GET /admin/sessions`
- `POST /admin/sessions/{id}/revoke`

### 审计日志页

- `GET /admin/audit-logs`

---

## 7. UI 设计原则

### 原则 1：状态优先

优先把这些状态做得一眼可见：

- active
- expired
- disabled
- revoked
- bound
- unbound
- device mismatch

### 原则 2：危险操作明确确认

对于：

- revoke 用户
- revoke session
- 解绑设备
- 禁用设备

必须二次确认，并显示影响范围。

### 原则 3：支持排障

所有列表页都建议提供：

- 搜索
- 筛选
- 时间排序
- 详情跳转

---

## 8. 一句话总结

远端管理后台 MVP 建议至少包含：

> Dashboard、用户管理、设备管理、会话管理、审计日志 这 5 类页面。
