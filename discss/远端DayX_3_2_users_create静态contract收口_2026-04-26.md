# 远端 Day X.3.2：Users Create 静态 Contract 收口

## 背景

Users Create 的后端接口与前端联调已经打通，但仓库内静态契约仍有两类漂移：

1. `remote-auth-v1.yaml` 已落后于运行时 OpenAPI，缺少 `POST /admin/users`
2. 多个分页列表 schema 仍停留在旧合同，只声明了 `items` + `total`，而运行时与前端真实使用的是 `items` + `page` + `page_size` + `total`

这会导致：

- 静态 OpenAPI 与运行时不一致
- compat harness gate 无法通过
- 后续再做 Users / Devices / Sessions / Audit 相关 contract 校验时容易反复踩坑

## 本次收口内容

### 1. 补齐 Users Create 静态 OpenAPI

- 在 `remote/remote-shared/openapi/remote-auth-v1.yaml` 中补入 `POST /admin/users`
- 补入 `AdminUserCreateRequest` schema

### 2. 收敛分页列表 schema 漂移

统一为以下合同：

- `items`
- `page`
- `page_size`
- `total`

本次同步的 schema：

- `SelfDeviceListResponse`
- `SelfSessionListResponse`
- `SelfActivityListResponse`
- `AdminUserListResponse`
- `AdminDeviceListResponse`
- `AdminSessionListResponse`
- `AuditLogListResponse`

### 3. 补最小静态 contract 回归

新增：

- `remote/remote-backend/tests/api/test_admin_static_openapi_contract.py`

覆盖点：

- source yaml 与 runtime json 都必须包含 `POST /admin/users`
- 两边都必须包含 `AdminUserCreateRequest`
- Create request 的 required / property 集合保持一致

### 4. 同步 fixtures / manifest

为匹配分页合同，更新了 compat harness fixtures：

- `self-devices-success.json`
- `self-sessions-success.json`
- `self-activity-success.json`

并重建：

- `remote-auth-runtime.json`
- `phase0-manifest.json`
- `phase1-manifest.json`

## 验证结果

已通过：

- `python remote/remote-shared/scripts/compat-harness/validate_phase0_gate.py`
- `python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py`
- `pytest remote/remote-backend/tests/api/test_admin_static_openapi_contract.py -q`
- `pytest remote/remote-backend/tests/api/test_openapi_response_contract.py -q`

## 价值判断

这是一个“低风险但高止血价值”的收口：

- 不改运行时行为
- 只修静态合同、fixtures、manifest 与回归
- 把 Users Create 从“运行时可用但仓库契约漂移”收敛到“运行时 / 静态 / gate 一致”

## 余留

这次完成的是 **Users Create 合同闭环**，不是完整 Users CRUD 终局。后续仍可以继续补：

- Users Update 编辑入口
- Users 删除/停用与恢复入口的完整 CRUD 叙事收口
- 更细粒度的 admin users route contract / browser 回归
