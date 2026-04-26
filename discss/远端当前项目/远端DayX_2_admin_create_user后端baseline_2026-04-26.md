# 远端 Day X.2：Admin Create User 后端 Baseline

## 目标

为 Remote Admin 补上 **Users Create 的最小后端合同**：

- 新增 `POST /admin/users`
- 复用 `users.write` 权限
- 一律要求 step-up
- 创建后返回 `AdminUserResponse`
- 保持与当前 users list/detail/update/revoke/restore 语义一致

## 本次范围

仅做后端 baseline：

1. schema：新增 create request
2. repository：补 managed user / credential / license 创建能力
3. service：补 `create_user(...)`
4. api：补 `POST /admin/users`
5. tests：补 route / runtime / openapi 最小合同回归

## 明确不做

- 前端 create modal
- invite / onboarding
- password reset 流程
- 用户删除
- 批量导入
- 静态 openapi yaml/runtime json 的额外手工同步（若未纳入本次 slice）

## 合同约束

- 路径：`POST /admin/users`
- 权限：`users.write`
- step-up：必需
- 成功响应：`AdminUserResponse`
- 字段校验失败：走 `422`
- 用户名重复：尽量收敛到 `422`

## 推荐最小 payload

```json
{
  "username": "alice2",
  "password": "TempSecret123!",
  "display_name": "Alice 2",
  "email": "alice2@example.com",
  "tenant_id": "tenant_1",
  "license_status": "active",
  "license_expires_at": "2026-07-01T00:00:00Z",
  "entitlements": ["dashboard:view"]
}
```

## 计划验证

```bash
pytest remote/remote-backend/tests/services/test_admin_step_up_runtime.py -q
pytest remote/remote-backend/tests/api/test_admin_destructive_api.py -q
pytest remote/remote-backend/tests/api/test_openapi_response_contract.py -q
```

## 实施结果（待回填）

### 已落地

- 后端已新增 `POST /admin/users`
- create 路由已复用 `users.write`
- create 流程已强制要求 step-up
- 成功响应已返回 `AdminUserResponse`
- 用户名重复已收敛为 `422 detail[]`
- 已补 route / runtime / openapi 最小合同回归

### 实际改动文件

- `remote/remote-backend/app/schemas/admin.py`
- `remote/remote-backend/app/repositories/admin.py`
- `remote/remote-backend/app/services/admin_service.py`
- `remote/remote-backend/app/api/admin.py`
- `remote/remote-backend/tests/services/test_admin_step_up_runtime.py`
- `remote/remote-backend/tests/api/test_admin_destructive_api.py`
- `remote/remote-backend/tests/api/test_openapi_response_contract.py`
- `remote/remote-shared/docs/admin-mvp-api-contract-v1.md`
- `remote/remote-shared/docs/remote-admin-platform-ui-spec-v1.md`
- `discss/远端DayX_2_admin_create_user后端baseline_2026-04-26.md`

### 验证结果

已执行：

```bash
pytest remote/remote-backend/tests/services/test_admin_step_up_runtime.py -q
pytest remote/remote-backend/tests/api/test_admin_destructive_api.py -q
pytest remote/remote-backend/tests/api/test_openapi_response_contract.py -q
```

结果：

- `test_admin_step_up_runtime.py` 10/10 通过
- `test_admin_destructive_api.py` 29/29 通过
- `test_openapi_response_contract.py` 34/34 通过

### 本 slice 保留风险

1. 静态 `remote-auth-v1.yaml` / runtime json 产物本次未手工同步，当前以运行时 OpenAPI 合同和测试为准
2. create 仅覆盖最小字段集，尚未扩展 invite / reset / plan_code / phone 等派生能力
3. 用户名重复目前统一收敛到 `422 detail[]`，前端后续需要在 modal/form 中把字段错误映射出来
