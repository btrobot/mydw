# 远端系统数据库表设计草案

> 目标：支撑远端授权中心与远端管理后台。

---

## 1. 核心表总览

建议最少包含以下表：

- `users`
- `user_credentials`
- `licenses`
- `user_entitlements`
- `devices`
- `user_devices`
- `sessions`
- `refresh_tokens`
- `admin_users`
- `admin_roles`
- `admin_user_roles`
- `audit_logs`

如支持多租户，再扩展：

- `tenants`
- `tenant_users`
- `tenant_licenses`

---

## 2. 表设计草案

## 2.1 `users`

### 用途
保存远端普通用户基础信息。

### 建议字段

- `id`
- `username`
- `display_name`
- `email`
- `phone`
- `status`（active / disabled）
- `tenant_id`（可选）
- `created_at`
- `updated_at`

---

## 2.2 `user_credentials`

### 用途
保存认证凭证。

### 建议字段

- `user_id`
- `password_hash`
- `password_algo`
- `password_updated_at`
- `mfa_enabled`
- `mfa_secret`（可选）

---

## 2.3 `licenses`

### 用途
保存用户授权状态。

### 建议字段

- `id`
- `user_id`
- `license_status`
- `plan_code`
- `starts_at`
- `expires_at`
- `offline_grace_hours`
- `revoked_at`
- `disabled_at`
- `created_at`
- `updated_at`

### 关键说明

`license_status` 至少支持：

- `active`
- `expired`
- `disabled`
- `revoked`

---

## 2.4 `user_entitlements`

### 用途
保存细粒度授权能力。

### 建议字段

- `id`
- `user_id`
- `entitlement`
- `source`
- `created_at`

### 示例

- `dashboard:view`
- `publish:run`
- `materials:write`
- `auth:admin`

---

## 2.5 `devices`

### 用途
保存设备注册信息。

### 建议字段

- `id`
- `device_id`
- `device_name`
- `platform`
- `client_version`
- `status`
- `first_seen_at`
- `last_seen_at`
- `created_at`
- `updated_at`

### 状态建议

- `bound`
- `unbound`
- `disabled`

---

## 2.6 `user_devices`

### 用途
表示用户与设备的绑定关系。

### 建议字段

- `id`
- `user_id`
- `device_id`
- `binding_status`
- `bound_at`
- `unbound_at`
- `last_auth_at`
- `created_at`
- `updated_at`

### 关键用途

用于判断：

- 当前设备是否属于该用户
- 是否应该返回 `device_mismatch`

---

## 2.7 `sessions`

### 用途
表示活跃授权会话。

### 建议字段

- `id`
- `session_id`
- `user_id`
- `device_id`
- `auth_state`
- `issued_at`
- `expires_at`
- `last_seen_at`
- `revoked_at`
- `created_at`
- `updated_at`

### 作用

用于：

- 管理后台查看活跃会话
- 主动 revoke 某个 session

---

## 2.8 `refresh_tokens`

### 用途
管理 refresh token。

### 建议字段

- `id`
- `session_id`
- `token_hash`
- `issued_at`
- `expires_at`
- `rotated_from_id`
- `revoked_at`
- `revoke_reason`

### 关键要求

- 不保存明文 refresh token
- 支持轮转
- 支持失效/吊销

---

## 2.9 `admin_users`

### 用途
保存远端管理后台用户。

### 建议字段

- `id`
- `username`
- `display_name`
- `status`
- `created_at`
- `updated_at`

---

## 2.10 `admin_roles`

### 用途
定义后台角色。

### 建议字段

- `id`
- `role_name`
- `description`

### 示例角色

- `super_admin`
- `auth_admin`
- `support_readonly`

---

## 2.11 `admin_user_roles`

### 用途
管理员与角色关联。

### 建议字段

- `admin_user_id`
- `admin_role_id`
- `created_at`

---

## 2.12 `audit_logs`

### 用途
记录所有远端关键审计事件。

### 建议字段

- `id`
- `event_type`
- `actor_type`
- `actor_id`
- `target_user_id`
- `target_device_id`
- `target_session_id`
- `request_id`
- `trace_id`
- `details_json`
- `created_at`

### 建议记录的事件

- login success / failure
- refresh success / failure
- revoke
- disabled
- device mismatch
- minimum version block
- admin revoke user
- admin revoke session
- admin unbind device

---

## 3. 关系图（简化）

```text
users ──< licenses
users ──< user_entitlements
users ──< user_devices >── devices
users ──< sessions >── devices
sessions ──< refresh_tokens

admin_users ──< admin_user_roles >── admin_roles

audit_logs -> actor / target references
```

---

## 4. 索引建议

建议至少加索引：

- `users.username`
- `licenses.user_id`
- `licenses.license_status`
- `devices.device_id`
- `user_devices.user_id`
- `user_devices.device_id`
- `sessions.session_id`
- `sessions.user_id`
- `sessions.device_id`
- `refresh_tokens.session_id`
- `audit_logs.created_at`
- `audit_logs.event_type`
- `audit_logs.target_user_id`

---

## 5. MVP 最小落地

如果先做第一版，建议优先实现：

- `users`
- `user_credentials`
- `licenses`
- `user_entitlements`
- `devices`
- `user_devices`
- `sessions`
- `refresh_tokens`
- `audit_logs`

后台管理员体系可以先简化成：

- `admin_users`
- `admin_roles`
- `admin_user_roles`

---

## 6. 设计注意事项

### 安全

- refresh token 只存 hash
- 所有敏感操作必须审计
- device 解绑 / revoke 必须可追踪

### 可扩展

- entitlement 不要硬编码在 `users` 表
- device 与 session 分开建模
- license 与 user 解耦，方便未来支持升级/续费/套餐

### 与本地系统的契合点

远端需要稳定支持本地当前已实现的字段与状态：

- `license_status`
- `device_status`
- `minimum_supported_version`
- `offline_grace_until`
- `revoked`
- `device_mismatch`
