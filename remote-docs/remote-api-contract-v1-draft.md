# 远端系统 API 契约草案 v1

> 说明：这是基于当前本地 remote-auth 架构反推出来的远端系统接口草案，目标是给远端前后台实现提供一个稳定的后端契约起点。

---

## 1. 契约定位

该契约用于定义 **远端授权中心** 对本地授权代理层提供的上游接口。

远端是：

- 用户身份真相源
- license / entitlement 真相源
- device binding 真相源
- revoke / disabled / version gate 真相源

本地仍然负责：

- machine-session truth
- 本地门禁
- grace / expired / revoked 的本地执行行为

---

## 2. v1 核心接口

### 2.1 用户认证

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /me`

### 2.2 远端管理后台

- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}`
- `POST /admin/users/{user_id}/revoke`
- `POST /admin/users/{user_id}/restore`

- `GET /admin/devices`
- `GET /admin/devices/{device_id}`
- `POST /admin/devices/{device_id}/unbind`
- `POST /admin/devices/{device_id}/disable`
- `POST /admin/devices/{device_id}/rebind`

- `GET /admin/sessions`
- `POST /admin/sessions/{session_id}/revoke`

- `GET /admin/audit-logs`

---

## 3. 认证接口草案

## 3.1 `POST /login`

### Request

```json
{
  "username": "string",
  "password": "string",
  "device_id": "string",
  "client_version": "string"
}
```

### Success Response

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_at": "2026-04-20T10:00:00Z",
  "token_type": "Bearer",
  "user": {
    "id": "u_123",
    "username": "alice",
    "display_name": "Alice",
    "tenant_id": "tenant_1"
  },
  "license_status": "active",
  "entitlements": [
    "dashboard:view",
    "publish:run",
    "materials:write",
    "auth:admin"
  ],
  "device_id": "device_abc",
  "device_status": "bound",
  "offline_grace_until": "2026-04-21T10:00:00Z",
  "minimum_supported_version": "0.2.0"
}
```

---

## 3.2 `POST /refresh`

### Request

```json
{
  "refresh_token": "string",
  "device_id": "string",
  "client_version": "string"
}
```

### Success Response

结构与 `/login` 成功响应一致，但允许 refresh token 轮转。

---

## 3.3 `POST /logout`

### Request

```json
{
  "refresh_token": "string",
  "device_id": "string"
}
```

### Success Response

```json
{
  "success": true
}
```

---

## 3.4 `GET /me`

### Header

```http
Authorization: Bearer <access_token>
```

### Success Response

```json
{
  "user": {
    "id": "u_123",
    "username": "alice",
    "display_name": "Alice",
    "tenant_id": "tenant_1"
  },
  "license_status": "active",
  "entitlements": [
    "dashboard:view",
    "publish:run",
    "materials:write"
  ],
  "device_id": "device_abc",
  "device_status": "bound",
  "offline_grace_until": "2026-04-21T10:00:00Z",
  "minimum_supported_version": "0.2.0"
}
```

---

## 4. 管理接口草案

## 4.1 `GET /admin/users`

用于用户列表页。

### Response

```json
{
  "items": [
    {
      "id": "u_123",
      "username": "alice",
      "display_name": "Alice",
      "status": "active",
      "license_status": "active",
      "device_count": 2,
      "last_seen_at": "2026-04-15T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

## 4.2 `POST /admin/users/{user_id}/revoke`

用于管理员直接吊销用户授权。

### Response

```json
{
  "success": true,
  "user_id": "u_123",
  "license_status": "revoked"
}
```

---

## 4.3 `GET /admin/devices`

用于设备管理页。

### Response

```json
{
  "items": [
    {
      "device_id": "device_abc",
      "user_id": "u_123",
      "device_status": "bound",
      "first_bound_at": "2026-04-01T10:00:00Z",
      "last_seen_at": "2026-04-15T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

## 4.4 `GET /admin/sessions`

用于会话查看页。

### Response

```json
{
  "items": [
    {
      "session_id": "sess_123",
      "user_id": "u_123",
      "device_id": "device_abc",
      "auth_state": "active",
      "issued_at": "2026-04-15T10:00:00Z",
      "expires_at": "2026-04-15T18:00:00Z",
      "last_seen_at": "2026-04-15T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

## 4.5 `POST /admin/sessions/{session_id}/revoke`

用于管理员强制失效会话。

### Response

```json
{
  "success": true,
  "session_id": "sess_123"
}
```

---

## 4.6 `GET /admin/audit-logs`

用于远端后台查看审计记录。

### Response

```json
{
  "items": [
    {
      "id": "log_001",
      "event_type": "auth_revoked",
      "actor_type": "admin",
      "actor_id": "admin_1",
      "target_user_id": "u_123",
      "target_device_id": "device_abc",
      "created_at": "2026-04-15T12:00:00Z",
      "details": {
        "reason": "manual revoke"
      }
    }
  ],
  "total": 1
}
```

---

## 5. 枚举约束

### `license_status`

- `active`
- `expired`
- `disabled`
- `revoked`

### `device_status`

- `bound`
- `unbound`

### 远端错误码

- `invalid_credentials`
- `token_expired`
- `revoked`
- `disabled`
- `device_mismatch`
- `minimum_version_required`
- `network_timeout`
- `forbidden`
- `not_found`

---

## 6. 安全要求

- 所有接口仅通过 HTTPS
- access token 短期有效
- refresh token 支持轮转和吊销
- 管理接口必须 RBAC
- 所有 revoke / disable / rebind 操作必须写审计日志

---

## 7. 建议的实现顺序

1. `/login`
2. `/refresh`
3. `/me`
4. `/logout`
5. 用户与 license 管理 API
6. 设备管理 API
7. session 管理 API
8. audit log API
