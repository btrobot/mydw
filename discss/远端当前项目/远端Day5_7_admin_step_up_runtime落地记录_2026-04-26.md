# 远端 Day 5.7：Admin destructive step-up runtime 落地记录

## 本次落地范围
- 仅覆盖 admin destructive 操作的二次确认能力
- 采用“密码确认 + 短时 step-up token”方案
- 复用既有 admin permission 作为 step-up scope：
  - `users.write`
  - `devices.write`
  - `sessions.revoke`
- 强制校验放在 `admin_service`，不是只放在 route

## 已完成实现

### 1. 运行时配置
- 新增 `STEP_UP_TOKEN_TTL_SECONDS`
- 新增 `ADMIN_STEP_UP_RATE_LIMIT_WINDOW_SECONDS`
- 新增 `ADMIN_STEP_UP_RATE_LIMIT_MAX_ATTEMPTS`

### 2. 安全辅助函数
- 在 `app/core/security.py` 新增：
  - `hash_step_up_token`
  - `verify_step_up_token`
- step-up token 采用随机 bearer token + sha256 指纹，不复用账号密码哈希链路

### 3. 数据模型与迁移
- 新增 `AdminStepUpGrant` 模型
- 新增 Alembic revision `20260425_0003_admin_step_up_grants.py`
- 新表 `admin_step_up_grants` 记录：
  - session 归属
  - scope
  - token_hash
  - method
  - issued/expires/last_used/revoked 时间

### 4. Repository 能力
- 新增 step-up grant 的创建、查询、touch、按 scope 撤销旧 grant 能力

### 5. Service 能力
- 新增 `verify_step_up_password`
- `_require_admin_session` 扩展为支持：
  - `step_up_scope`
  - `step_up_token`
- 新增统一 step-up 校验分支：
  - 缺失 token -> `403 step_up_required`
  - token 无效 / scope 不匹配 -> `403 step_up_invalid`
  - token 过期 -> `403 step_up_expired`
- 以下 destructive 操作现在要求 step-up：
  - `revoke_user`
  - `restore_user`
  - `unbind_device`
  - `disable_device`
  - `rebind_device`
  - `revoke_session`
- `update_user` 仅在修改敏感字段时要求 step-up：
  - `license_status`
  - `license_expires_at`
  - `entitlements`
- 仅改 `display_name` 不要求 step-up

### 6. API 能力
- 新增 `POST /admin/step-up/password/verify`
- destructive route 与敏感 `PATCH /admin/users/{user_id}` 支持读取 `X-Step-Up-Token`
- 新增 step-up verify 端点的独立 rate limit

## 测试补齐
- API：
  - `test_admin_step_up_api.py`
  - destructive route header 透传补测
  - OpenAPI contract 补 `/admin/step-up/password/verify`
- Service / runtime：
  - step-up verify 成功
  - destructive 无 token 拒绝
  - 正确 scope token 放行
  - display_name-only patch 免 step-up
  - 敏感 patch 必须 step-up
  - 错 scope token 拒绝
  - 过期 token 拒绝
- Migration / core helper：
  - schema table expectation 补 `admin_step_up_grants`
  - step-up token hash/verify helper 测试

## 验证结果
- 定向测试：通过
- 全量后端测试：`168 passed`

## 当前剩余风险
- 目前 step-up 仍是“单因子内二次确认”，未接入 TOTP / WebAuthn
- 目前 scope 复用 permission string，可继续观察是否需要更细粒度 action scope
- 前端尚未接入新的 verify / header 交互，本次仅先完成后端运行时与合同
