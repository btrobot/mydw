# 远端系统后端需求分析

## 1. 远端系统在当前架构中的位置

当前架构里：

- **远端系统**：授权真相源
- **本地 FastAPI**：机器会话真相源
- **前端 / Electron**：只消费本地 auth 状态，不长期持有授权真相

因此远端后端负责的是：

1. 身份认证
2. 授权状态
3. 设备绑定
4. license / entitlement 分发
5. 撤销 / 禁用 / 版本门禁
6. 给远端管理前台提供管理 API

它不负责本地任务、素材、调度等业务数据。

---

## 2. 必须有的核心认证 API

### 最小接口集

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /me`

### 成功响应至少要包含

- `access_token`
- `refresh_token`
- `expires_at`
- `token_type`
- `user`
  - `id`
  - `username`
  - `display_name`
  - `tenant_id`（可选）
- `license_status`
- `entitlements`
- `device_id`
- `device_status`
- `offline_grace_until`（可选）
- `minimum_supported_version`（可选）

### 至少支持的错误码

- `invalid_credentials`
- `token_expired`
- `revoked`
- `disabled`
- `device_mismatch`
- `minimum_version_required`
- `network_timeout`

这些是硬需求，因为本地系统已经按这个契约实现了状态机、事件、指标和 UX。

---

## 3. 远端后端的核心领域模型

### 3.1 用户

至少需要：

- 用户 ID
- 登录名
- 密码哈希 / 凭证
- 显示名
- 状态（active / disabled）
- 所属租户 / 组织（可选）

### 3.2 授权 / License

至少需要：

- `license_status`
  - `active`
  - `expired`
  - `disabled`
  - `revoked`
- 到期时间
- 套餐 / 版本
- 是否允许离线宽限
- 宽限策略

### 3.3 设备

至少需要：

- `device_id`
- 绑定用户
- 绑定状态
- 首次绑定时间
- 最近活跃时间
- 是否允许该设备继续访问

这是硬需求，因为当前本地逻辑把 `device_mismatch` 视为高优先级拒绝态。

---

## 4. 远端后端必须支持的业务规则

### 4.1 刷新规则

- refresh 成功时可以轮转 refresh token
- refresh 必须重新返回完整授权上下文
- refresh 失败必须区分：
  - 网络失败
  - 远端明确拒绝
  - token 失效
  - 设备不匹配

### 4.2 设备绑定规则

至少支持：

- 首次登录绑定设备
- 已绑定设备继续访问
- 非绑定设备访问返回 `device_mismatch`
- 管理员可解除 / 重绑设备

### 4.3 撤销规则

远端后端必须支持：

- 立即 revoke 用户授权
- revoke 后：
  - `/refresh` 返回 `revoked`
  - `/me` 返回 `revoked`
  - 本地进入锁定态

### 4.4 版本门禁

应支持：

- 最低客户端版本判断
- 若版本过低，返回：
  - `minimum_version_required`
  - `minimum_supported_version`

---

## 5. 远端管理前台所需的后台能力

如果要做“远端系统前后台”，远端前台通常是一个管理控制台，所以远端后端还需要这些管理 API。

### 5.1 用户管理

- 创建 / 编辑 / 禁用用户
- 重置密码
- 查询用户授权状态

### 5.2 授权管理

- 查看 / 修改 license
- 设置到期时间
- 设置 entitlement 集合
- revoke / restore

### 5.3 设备管理

- 查看用户已绑定设备
- 手动解除绑定
- 标记设备失效
- 重新授权设备

### 5.4 会话管理

- 查看活跃 token / session
- 强制使 token 失效
- 查看最近 refresh / me 调用情况

### 5.5 审计日志

- 登录成功 / 失败
- refresh 成功 / 失败
- revoke 操作
- device mismatch
- 管理员修改授权
- 管理员踢出设备

---

## 6. 建议的数据表

至少建议有：

- `users`
- `user_credentials`
- `licenses`
- `user_entitlements`
- `devices`
- `user_devices`
- `refresh_tokens` / `sessions`
- `audit_logs`
- `admin_users` / `admin_roles`
- `admin_operation_logs`

如果支持多租户，再加：

- `tenants`
- `tenant_users`
- `tenant_licenses`

---

## 7. 非功能需求

### 安全

- HTTPS only
- 密码哈希存储
- refresh token 可吊销 / 可轮转
- access token 有过期时间
- 管理 API RBAC
- 审计日志不可随意篡改

### 可用性

- `/login` `/refresh` `/me` 必须稳定
- 错误码语义不能漂移
- 远端故障时要让本地能进入 grace，而不是返回不稳定错误

### 可观测性

远端后端自己也要有：

- auth 请求日志
- revoke / device mismatch 审计
- metrics
- trace_id 贯穿

---

## 8. MVP 范围建议

### MVP 必做

- 用户登录
- refresh
- logout
- me
- 用户授权状态
- entitlement 下发
- device binding / mismatch
- revoke / disabled
- 最低版本门禁
- 管理员后台 API：
  - 用户列表
  - 授权编辑
  - 设备列表
  - revoke 用户 / 设备
  - 审计日志查看

### MVP 可后置

- 多租户复杂模型
- SSO
- 短信 / 邮箱二次验证
- 复杂套餐计费
- 细粒度组织权限
- 风控系统

---

## 9. 一句话总结

按当前架构，远端后端不是业务后端，而是 **授权控制中心**。

它至少需要提供：

- 标准 auth contract（login / refresh / logout / me）
- 用户 / 授权 / 设备模型
- revoke / disabled / mismatch / version gate
- 给远端管理前台使用的用户、设备、授权、审计管理 API
