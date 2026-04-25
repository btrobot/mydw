# Remote Step-Up Security Proposal v1（Day 5.6 / Slice 11）

日期：2026-04-26

## 1. 目标

为远端 auth/admin 体系补一份**最小风险 step-up security 设计稿**，给后续单独切片留入口，但**不把本轮 Day 5 扩成运行时大改造**。

本稿只回答三件事：

1. 哪些动作值得做 step-up
2. 候选方案如何取舍
3. 后续真正落地时，服务端应在哪里强制校验

---

## 2. 当前代码事实（2026-04-26）

### 2.1 当前管理端鉴权形态

- `remote/remote-backend/app/api/admin.py`
  - 管理端使用 Bearer access token
  - `/admin/login` 返回 `access_token + session_id`
- `remote/remote-backend/app/services/admin_service.py`
  - 统一通过 `_require_admin_session(...)` 做 session/role/permission 校验
  - 破坏性动作当前直接复用普通 admin session，无额外 re-auth / step-up
- `remote/remote-backend/app/services/admin_authz.py`
  - 已有权限粒度：
    - `users.write`
    - `devices.write`
    - `sessions.revoke`

### 2.2 当前高风险动作分布

来自 `app/api/admin.py` 与 `tests/api/test_admin_destructive_api.py` 的现状：

- `PATCH /admin/users/{user_id}`
  - 风险混合：`display_name` 偏低风险；`license_status`、`entitlements` 偏高风险
- `POST /admin/users/{user_id}/revoke`
- `POST /admin/users/{user_id}/restore`
- `POST /admin/devices/{device_id}/unbind`
- `POST /admin/devices/{device_id}/disable`
- `POST /admin/devices/{device_id}/rebind`
- `POST /admin/sessions/{session_id}/revoke`

### 2.3 当前自助端动作分布

- `remote/remote-backend/app/api/self_service.py`
  - 当前只有 `/self/me`、`/self/devices`、`/self/sessions`、`/self/activity`
  - 唯一写动作是 `POST /self/sessions/{session_id}/revoke`

结论：

- **当前真正需要优先 step-up 的，是 admin destructive API**
- end-user 自助端目前没有“改密码 / 改邮箱 / 关 2FA / 导出密钥”这类典型敏感动作
- 因此**首个 step-up runtime slice 不应把 admin 与 end-user 一起做**

### 2.4 Day 5.5 已提供的可复用基础

- `remote/remote-backend/app/core/security.py`
  - 账户密码与 token hash helper 已拆开
  - 账户密码已支持 `Argon2id + PBKDF2 兼容校验`
- 这意味着后续 step-up 若采用“二次密码确认”，可以直接复用现有账户密码验证链路

---

## 3. 哪些动作需要 step-up

### 3.1 v1 建议纳入 step-up 的动作

| 路由 / 动作 | 是否纳入 v1 | 原因 |
| --- | --- | --- |
| `POST /admin/users/{user_id}/revoke` | 是 | 直接影响用户可用性 |
| `POST /admin/users/{user_id}/restore` | 是 | 可恢复被撤销账号，属于状态逆转 |
| `POST /admin/devices/{device_id}/unbind` | 是 | 直接改变绑定关系 |
| `POST /admin/devices/{device_id}/disable` | 是 | 直接让设备失效 |
| `POST /admin/devices/{device_id}/rebind` | 是 | 可把设备切给其他用户 |
| `POST /admin/sessions/{session_id}/revoke` | 是 | 可强制踢出会话 |
| `PATCH /admin/users/{user_id}` 修改 `license_status` / `entitlements` | 是 | 会改变授权与能力边界 |

### 3.2 v1 不纳入 step-up 的动作

| 路由 / 动作 | 是否纳入 v1 | 原因 |
| --- | --- | --- |
| `GET /admin/*` 读接口 | 否 | 先不引入读取体验抖动 |
| `PATCH /admin/users/{user_id}` 仅修改 `display_name` | 否 | 风险较低 |
| `POST /self/sessions/{session_id}/revoke` | 否 | 偏自我保护动作，不宜先加摩擦 |
| `/login` `/refresh` `/logout` `/me` | 否 | 与 step-up 目标不匹配 |

### 3.3 未来可扩展到 step-up 的动作（但当前代码尚不存在）

- 改密码
- 改邮箱 / 改手机号
- 关闭 TOTP / 修改恢复码
- 导出敏感审计数据 / 导出密钥材料
- admin 角色提升 / admin 凭据重置

---

## 4. 候选方案比较

## 方案 A：TOTP 作为第一版 step-up

### 优点

- 安全性强
- 与“高风险动作二次确认”模型一致

### 问题

- 需要新增 enrollment、解绑、恢复码、遗失恢复流程
- 需要补新 schema、前端设置页、恢复流程、客服/运维流程
- 与当前远端代码事实不匹配，明显超出 Day 5/下一个最小切片边界

### 结论

- **拒绝作为第一版**

---

## 方案 B：每次高风险动作都二次输入密码，不发 step-up grant

### 优点

- 后端概念最少
- 不需要额外 token / grant 表

### 问题

- 同一批操作需要反复输密码，体验差
- `PATCH /admin/users/{user_id}` 这类混合风险接口会很别扭
- 若为了减少输入而把“已验证状态”挂在 session 上，又会产生过宽的临时高权限窗口

### 结论

- **不作为首选**

---

## 方案 C：二次密码确认 + 短时 step-up token（推荐）

### 方案概述

1. admin 先使用当前密码发起二次确认
2. 服务端校验密码通过后，签发一个**短时、作用域受限、绑定当前 admin session** 的 step-up token
3. 破坏性 admin API 调用时，除普通 Bearer token 外，再附带 step-up token
4. 服务端校验：
   - session 合法
   - role/permission 合法
   - step-up token 未过期、未撤销、scope 匹配、session 绑定匹配

### 优点

- 复用现有 admin 密码体系，落地最直接
- 比“只在 session 上挂临时高权限”更收敛，泄露面更小
- 比“每次都输密码”更容易被前端接受
- scope 可与现有 admin permission 对齐，设计简单

### 问题

- 需要一个新的 grant/token 存储模型
- destructive route 需要新增一个 header/参数合同

### 结论

- **采纳为 v1 推荐方案**

---

## 5. 推荐方案（v1）

## 5.1 总体决策

后续单独切片中，优先做：

- **仅覆盖 admin destructive API**
- **验证方式先用二次密码确认**
- **授权凭据采用短时 step-up token**
- **不在同一切片引入 TOTP**
- **不把 end-user self-service step-up 一起拉进来**

## 5.2 推荐合同

### 新增校验入口

`POST /admin/step-up/password/verify`

请求体建议：

```json
{
  "password": "current-admin-password",
  "scope": "users.write"
}
```

响应体建议：

```json
{
  "step_up_token": "stepup_xxx",
  "scope": "users.write",
  "method": "password",
  "expires_at": "2026-04-26T12:00:00Z"
}
```

### destructive route 附加材料

沿用原 Bearer token，不替换原访问链路；额外增加一个 header：

- `X-Step-Up-Token: stepup_xxx`

### 错误语义建议

为避免引入新的 HTTP 码分支，v1 建议统一使用 **403**，只细分 `error_code`：

- `step_up_required`
- `step_up_invalid`
- `step_up_expired`

二次密码确认失败则可保持：

- `401 invalid_credentials`

## 5.3 scope 设计

推荐**直接复用现有 admin permission 作为 step-up scope**：

- `users.write`
- `devices.write`
- `sessions.revoke`

这样可直接与 `app/services/admin_authz.py` 现有模型对齐，避免引入第二套 scope 词汇表。

## 5.4 TTL 建议

- 默认 `5 分钟`
- 同 scope 可在 TTL 内复用
- 不建议跨 scope 通用

---

## 6. 数据模型建议

## 6.1 不推荐的做法

不推荐把 step-up 状态直接挂在 `admin_sessions` 上，例如：

- `step_up_until`
- `step_up_scope`

原因：

- 会把“普通 session”与“已提升 session”混成一个状态对象
- 一旦 access token 被窃取，在有效窗口内可直接继承 step-up 状态
- 后续难以做更细的 scope、撤销、审计

## 6.2 推荐做法

新增一张专用 grant 表，例如：

`admin_step_up_grants`

建议字段：

- `id`
- `admin_session_id`
- `scope`
- `token_hash`
- `method`
- `issued_at`
- `expires_at`
- `last_used_at`
- `revoked_at`

### 说明

- `admin_session_id`：与当前 admin session 强绑定
- `scope`：与 `users.write / devices.write / sessions.revoke` 对齐
- `token_hash`：只存 hash，不落明文 token
- `method`：首版固定 `password`
- `last_used_at`：便于审计与异常分析

### hash 策略建议

step-up token 属于**短时 bearer secret**，不应复用账户密码 helper。

建议：

- 单独提供 `hash_step_up_token / verify_step_up_token`
- 或抽成通用“非密码 secret helper”
- 但**不要再回到“账户密码与 token secret 共用同一 helper”** 的旧耦合

---

## 7. 服务端强制校验点

## 7.1 API 层

`remote/remote-backend/app/api/admin.py`

后续切片中，以下 route 需要把 `X-Step-Up-Token` 明确传入 service：

- `PATCH /admin/users/{user_id}`（仅在敏感字段变更时）
- `POST /admin/users/{user_id}/revoke`
- `POST /admin/users/{user_id}/restore`
- `POST /admin/devices/{device_id}/unbind`
- `POST /admin/devices/{device_id}/disable`
- `POST /admin/devices/{device_id}/rebind`
- `POST /admin/sessions/{session_id}/revoke`

## 7.2 Service 层

`remote/remote-backend/app/services/admin_service.py`

不要只在 route 层做 header 判断。推荐把强制校验收口到 service 内部，例如扩展：

- `_require_admin_session(access_token, permission=..., step_up_scope=..., step_up_token=...)`

这样可以避免未来从其他调用路径绕过 step-up 校验。

## 7.3 混合风险接口的特殊处理

`PATCH /admin/users/{user_id}` 当前既能改低风险字段，也能改高风险字段。

后续实现有两个可选做法：

1. **首选**：保留现有 route，但在 service 内根据 payload 判定是否需要 step-up
2. 次选：把高风险字段拆成单独 route

v1 建议先选 **做法 1**，因为 diff 更小、回归面更窄。

---

## 8. 审计与风控建议

建议新增审计事件：

- `admin_step_up_succeeded`
- `admin_step_up_failed`
- `admin_step_up_required`

建议 details 至少包含：

- `scope`
- `method`
- `target_user_id` / `target_device_id` / `target_session_id`（如适用）
- `client_ip`

另外建议单独增加 step-up rate limit：

- `ADMIN_STEP_UP_RATE_LIMIT_WINDOW_SECONDS`
- `ADMIN_STEP_UP_RATE_LIMIT_MAX_ATTEMPTS`

避免管理员密码在 step-up 入口被暴力尝试。

---

## 9. 测试建议（未来切片）

后续实现时最少应覆盖：

### route contract

- 缺少 step-up token -> `403 step_up_required`
- step-up token 过期 -> `403 step_up_expired`
- step-up token scope 不匹配 -> `403 step_up_invalid`
- 非敏感 `PATCH /admin/users/{user_id}` 不要求 step-up

### service

- 二次密码确认成功后可拿到 grant
- grant 绑定当前 `admin_session`
- 同 scope 在 TTL 内可复用
- grant 过期/撤销后不可再用

### migration / schema

- Alembic revision 能创建 `admin_step_up_grants`
- downgrade 可逆

### audit

- step-up success / failed / required 事件会写入 `audit_logs`

---

## 10. 明确不做什么

本 Day 5.6 设计稿明确**不进入以下实现**：

- 不新增运行时 step-up route
- 不改现有 admin destructive API 合同
- 不加 TOTP enrollment / recovery code
- 不扩到 end-user self-service 运行时
- 不在本轮修改前端页面交互

---

## 11. 推荐后续切片

建议把 step-up 真正实现拆成一个新的独立 slice，例如：

### Slice 11B：Admin destructive step-up（password + short-lived token）

包含：

1. schema：`admin_step_up_grants`
2. helper：`hash_step_up_token / verify_step_up_token`
3. route：`POST /admin/step-up/password/verify`
4. admin destructive route 增加 `X-Step-Up-Token`
5. service 强制校验
6. 审计与 rate limit
7. contract / service / migration 回归测试

---

## 12. 最终结论

基于当前代码事实，**Day 5.6 的正确落点不是直接实现 step-up runtime，而是把下一刀收敛成：**

- **范围只覆盖 admin destructive API**
- **方式优先选“二次密码确认 + 短时 step-up token”**
- **scope 复用现有 admin permission**
- **强制校验落在 service 内部，不只靠 route**
- **end-user 与 TOTP 延后，不混入首版实现**

这能把安全收益、实现复杂度、前端改造量和回归风险，压在当前阶段最可控的范围内。
