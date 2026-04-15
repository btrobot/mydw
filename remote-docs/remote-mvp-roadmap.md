# 远端系统 MVP 路线图

> 目标：把“远端授权中心 + 远端管理后台”按最小可交付顺序拆成可执行阶段。

---

## 1. MVP 总目标

MVP 要先满足当前本地系统已经落地的 remote-auth 能力：

- 能登录
- 能 refresh
- 能 logout
- 能 `/me`
- 能返回 license / entitlement / device 状态
- 能 revoke
- 能支持 device mismatch
- 能支持最低版本门禁
- 能给管理后台提供用户 / 设备 / session 的基本管理能力

---

## 2. Phase 0 — 契约冻结与基础设计

### 目标

先把“接口、数据模型、职责边界”定清楚，避免后续实现漂移。

### 产出

- API 契约文档
- 数据库表设计
- 前后台职责拆分文档
- 状态/错误码枚举清单

### 完成标准

- `/login /refresh /logout /me` 的字段完全冻结
- 错误码与状态语义冻结
- users / licenses / devices / sessions / audit_logs 表有草案

---

## 3. Phase 1 — 远端认证核心链路

### 目标

打通最小 auth 主链路。

### 必做能力

- 用户登录
- access token 发放
- refresh token 发放
- refresh token 轮转
- `/me` 返回当前授权上下文
- `/logout`

### 后端模块

- 用户认证
- token service
- session service
- device binding 判断

### 完成标准

- 本地系统可以接远端 `/login /refresh /me /logout`
- 能正确返回：
  - `license_status`
  - `entitlements`
  - `device_id`
  - `device_status`

---

## 4. Phase 2 — 授权与设备控制

### 目标

让远端真正具备“控制本地授权”的能力。

### 必做能力

- revoke 用户授权
- disable 用户
- 设备绑定
- 设备失效
- device mismatch 判定
- minimum supported version gate
- offline grace 时间策略

### 完成标准

- revoke 后，本地 refresh / me 会收到 `revoked`
- 非绑定设备访问会收到 `device_mismatch`
- 低版本客户端收到 `minimum_version_required`

---

## 5. Phase 3 — 远端管理后台最小可用

### 目标

给管理员一个能操作的管理后台。

### MVP 页面

- 用户列表页
- 用户详情/授权页
- 设备列表页
- Session 列表页

### MVP API

- `GET /admin/users`
- `GET /admin/users/{id}`
- `PATCH /admin/users/{id}`
- `POST /admin/users/{id}/revoke`
- `GET /admin/devices`
- `POST /admin/devices/{id}/unbind`
- `GET /admin/sessions`
- `POST /admin/sessions/{id}/revoke`

### 完成标准

- 管理员可查看用户授权状态
- 可 revoke 用户/设备/session
- 能看到基础状态变化结果

---

## 6. Phase 4 — 审计与支持能力

### 目标

让远端系统具备支持和追踪能力。

### 必做能力

- 审计日志
- 管理员操作日志
- 登录失败日志
- revoke / device mismatch 日志
- session 活跃情况查看

### MVP API

- `GET /admin/audit-logs`

### 完成标准

- 能按时间、用户、设备筛选关键审计事件
- 支持支持人员排查“为什么被 revoke / 为什么 mismatch”

---

## 7. Phase 5 — 强化与扩展

### 可后置能力

- 多租户
- SSO
- MFA
- 套餐计费
- 更细粒度 admin RBAC
- 风控/异常登录检测
- 邮件/短信通知

---

## 8. 推荐实施顺序

```text
Phase 0 契约冻结
  ↓
Phase 1 认证主链路
  ↓
Phase 2 授权/设备控制
  ↓
Phase 3 管理后台 MVP
  ↓
Phase 4 审计/支持能力
  ↓
Phase 5 增强能力
```

---

## 9. MVP 范围的一句话定义

MVP 不追求“完整 IAM 平台”，而是先交付：

> 一个能支撑当前本地 remote-auth 正常运行、并能被管理员查看与撤销的远端授权中心。
