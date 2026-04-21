# 远程认证 API 契约 v1

> 状态：Frozen for Step 0 PR1  
> 适用范围：远程认证后端对本地授权代理层提供的上游契约  
> 关联计划：`.omx/plans/prd-remote-auth.md`、`.omx/plans/prd-remote-auth-step0-pr-plan.md`

---

## 1. Purpose

本文档冻结 **远程认证后端** 的 v1 契约，供后续实现以下能力使用：

- 本地 `remote_auth_client`
- 本地 `/api/auth/*` 代理层
- 前端登录与会话展示
- 后台授权校验与撤销响应

本契约文档只定义：

- endpoint list
- request / response fields
- error semantics
- example payloads
- versioning / change policy

本文档**不定义**：

- 本地 auth state machine
- 本地 machine-session 持久化
- transport propagation model
- 任何运行时代码

---

## 2. Design assumptions

### 2.1 Contract role

这个远程契约是：

> **远程认证真相源**

但不是最终本地执行门禁本身。  
本地门禁仍由本地 FastAPI 持有的 machine-session truth 决定。

### 2.2 Version policy

本文档冻结为：

- **Contract Version**: `v1`

后续若出现以下变化，必须升级契约版本或先补文档 PR：

1. 新增必填字段
2. 变更错误语义
3. 变更 token 结构或刷新规则
4. 变更 device binding 字段意义
5. 变更 `license_status` / `entitlements` 的判定语义

---

## 3. Transport and auth model assumptions

### 3.1 Remote transport

远程认证后端采用 HTTPS。

### 3.2 Token model

v1 固定采用：

- `access_token`
- `refresh_token`

字段命名不使用模糊名（如 `token` / `session_token`），避免后续实现歧义。

### 3.3 Device binding

v1 要求远程响应里显式返回设备绑定相关字段。  
设备绑定结果可出现在：

- `POST /login` 响应
- `POST /refresh` 响应
- `GET /me` 响应

本文档**不要求** v1 必须单独提供 `/device/bind` 端点，  
但要求设备绑定状态在核心响应中可判定。

---

## 4. Endpoint list

v1 冻结的远程认证核心接口如下：

1. `POST /login`
2. `POST /refresh`
3. `POST /logout`
4. `GET /me`

说明：

- 本地后续是否把这些映射为 `/api/auth/*` 是本地实现问题，不属于本契约文档范围
- 若未来需要单独的设备绑定接口，应通过后续契约文档版本更新明确

---

## 5. Shared response model

## 5.1 Token fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `access_token` | string | yes on login/refresh success | 远程访问令牌 |
| `refresh_token` | string | yes on login success / may rotate on refresh success | 刷新令牌 |
| `expires_at` | string (ISO 8601 UTC) | yes on login/refresh success | access token 过期时间 |
| `token_type` | string | optional | 默认应为 `Bearer` |

## 5.2 User fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `user.id` | string | yes on login success, refresh success, and `/me` success | 远程用户唯一标识 |
| `user.username` | string | yes on login success, refresh success, and `/me` success | 登录标识或用户名 |
| `user.display_name` | string | no | UI 展示名称 |
| `user.tenant_id` | string | no | 租户或组织标识 |

## 5.3 Authorization fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `license_status` | string | yes | 授权状态 |
| `entitlements` | array of string | yes | 可用能力列表 |
| `minimum_supported_version` | string | no | 最低支持客户端版本 |
| `offline_grace_until` | string (ISO 8601 UTC) | no | 离线宽限截止时间 |

### Allowed `license_status` values

v1 冻结以下值：

- `active`
- `expired`
- `disabled`
- `revoked`

若后续要新增状态值，必须先更新契约文档。

## 5.4 Device fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `device_id` | string | yes on login success, refresh success, and `/me` success | 当前远程识别的设备标识 |
| `device_status` | string | yes on login success, refresh success, and `/me` success | 设备绑定状态 |

### Allowed `device_status` values

- `bound`
- `unbound`

说明：

- `bound`：当前设备已与当前远程用户/授权上下文匹配
- `unbound`：当前登录允许完成首次绑定或尚未完成绑定
- 若远程判定设备不匹配，v1 应返回错误响应 `error_code=device_mismatch`，而不是返回成功态 `device_status`

---

## 6. Endpoint contracts

## 6.1 `POST /login`

### Request body

```json
{
  "username": "string",
  "password": "string",
  "device_id": "string",
  "client_version": "string"
}
```

### Request field rules

| Field | Required | Meaning |
|---|---:|---|
| `username` | yes | 用户登录标识 |
| `password` | yes | 用户口令或凭据 |
| `device_id` | yes | 本地机器生成并上报的设备标识 |
| `client_version` | yes | 当前桌面客户端版本 |

### Success response

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
  "entitlements": ["dashboard:view", "publish:run", "materials:write"],
  "device_id": "device_abc",
  "device_status": "bound",
  "offline_grace_until": "2026-04-21T10:00:00Z",
  "minimum_supported_version": "0.2.0"
}
```

### Success rules

- 登录成功必须返回：
  - `access_token`
  - `refresh_token`
  - `expires_at`
  - `user`
  - `license_status`
  - `entitlements`
  - `device_id`
  - `device_status`
- 若服务器采用 version gate，应在成功响应中返回 `minimum_supported_version`

---

## 6.2 `POST /refresh`

### Request body

```json
{
  "refresh_token": "string",
  "device_id": "string",
  "client_version": "string"
}
```

### Success response

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_at": "2026-04-20T11:00:00Z",
  "token_type": "Bearer",
  "user": {
    "id": "u_123",
    "username": "alice",
    "display_name": "Alice",
    "tenant_id": "tenant_1"
  },
  "license_status": "active",
  "entitlements": ["dashboard:view", "publish:run", "materials:write"],
  "device_id": "device_abc",
  "device_status": "bound",
  "offline_grace_until": "2026-04-21T10:00:00Z",
  "minimum_supported_version": "0.2.0"
}
```

### Refresh rules

- v1 允许 refresh token 轮转，因此：
  - 成功响应里的 `refresh_token` 视为最新值
- refresh 成功时必须重新返回：
  - `user`
  - `license_status`
  - `entitlements`
  - `device_id`
  - `device_status`
- 如果 refresh 失败属于远程明确拒绝（如 revoke / disabled / device mismatch），后续本地不得把它当作纯网络错误

---

## 6.3 `POST /logout`

### Request body

```json
{
  "refresh_token": "string",
  "device_id": "string"
}
```

### Success response

```json
{
  "success": true
}
```

### Logout rules

- v1 只要求远程接受注销请求并返回成功/失败
- 本地注销 machine-session 的语义不在本文定义

---

## 6.4 `GET /me`

### Request

通过 `Authorization: Bearer <access_token>` 调用。

### Success response

```json
{
  "user": {
    "id": "u_123",
    "username": "alice",
    "display_name": "Alice",
    "tenant_id": "tenant_1"
  },
  "license_status": "active",
  "entitlements": ["dashboard:view", "publish:run", "materials:write"],
  "device_id": "device_abc",
  "device_status": "bound",
  "offline_grace_until": "2026-04-21T10:00:00Z",
  "minimum_supported_version": "0.2.0"
}
```

### `/me` rules

- `/me` 用于确认当前 access token 对应的：
  - 用户身份
  - 授权状态
  - 设备状态
  - 宽限信息

---

## 7. Error semantics

## 7.1 Error categories

v1 冻结以下错误语义：

| Category | Meaning | Expected HTTP |
|---|---|---:|
| `invalid_credentials` | 用户名/密码错误 | 401 |
| `token_expired` | access 或 refresh 已过期 | 401 |
| `revoked` | 远程授权已撤销 | 403 |
| `disabled` | 用户或 license 被禁用 | 403 |
| `device_mismatch` | 当前设备与远程记录不匹配 | 403 |
| `minimum_version_required` | 当前客户端版本过低 | 403 |
| `network_timeout` | 网络超时或上游不可达 | 503 / timeout class |

## 7.2 Error response shape

```json
{
  "error_code": "revoked",
  "message": "Remote authorization revoked",
  "details": {
    "minimum_supported_version": "0.2.0",
    "device_id": "device_abc"
  }
}
```

### Error response rules

- `error_code` 为机器可判定字段
- `message` 为人类可读信息
- `details` 为可选附加信息

### Allowed `error_code` values in v1

- `invalid_credentials`
- `token_expired`
- `revoked`
- `disabled`
- `device_mismatch`
- `minimum_version_required`
- `network_timeout`

若后续新增值，必须先更新契约文档。

---

## 8. Versioning and compatibility policy

## 8.1 Minor-compatible changes

以下变更可视为向后兼容，但仍需更新文档：

- 新增可选字段
- 新增非破坏性 `details` 子字段
- 增加新的示例 payload

## 8.2 Breaking changes

以下变更视为 breaking change，必须升级契约版本：

- 新增必填字段
- 修改或删除既有字段
- 修改错误码含义
- 修改 `license_status` / `device_status` 枚举语义
- 修改 refresh token 轮转规则

## 8.3 Implementation rule

后续代码 PR：

1. 必须引用本文档
2. 不得在实现 PR 内悄悄新增字段或错误码
3. 如需扩展契约，必须先补新的 docs PR

---

## 9. Non-goals for PR1

PR1 不定义：

- 本地 state machine
- 本地 machine-session 结构
- secret / non-secret persistence split
- SecretStore abstraction
- offline/revoke 的本地执行策略
- scheduler / poller 的停止/暂停规则
- SSE / axios / generated client 的本地传播模型

这些内容由后续 Step 0 PR 继续冻结。

---

## 10. Review checklist

- [ ] Endpoint list 完整
- [ ] 请求/响应字段完整
- [ ] 错误语义完整
- [ ] 示例 payload 与字段一致
- [ ] 无占位词
- [ ] 无本地状态机或 persistence 内容越界
- [ ] 后续实现 PR 可直接引用
