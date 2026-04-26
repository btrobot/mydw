# 远端 Day X.1：Users Update UI 最小落地计划

## 目标

在 **不引入用户创建 / 删除** 的前提下，为 Remote Admin 的 Users 页面补上最小可用的“编辑用户”能力：

- 支持在详情侧栏内修改用户资料
- 继续复用现有 list/detail 刷新模式
- 对敏感字段严格复用后端 step-up 合同
- 保持 diff 小、行为可回退、前端合同清晰

## 本次范围

仅覆盖以下前端最小闭环：

1. `PATCH /admin/users/{user_id}` 前端 client 接线
2. Users detail 区域补一个轻量 edit form
3. display name 非敏感直存
4. `license_status / license_expires_at / entitlements` 命中后端 step-up 规则时，按 **后端返回 `step_up_required` 后再补 verify + retry**
5. 成功后刷新列表 + 详情
6. 补最小 contract test 与 React 级 step-up 回归

明确 **不在本 slice 内处理**：

- 用户创建
- 用户删除
- 更大范围的 users 页面重构
- 额外的后端合同修改

## 后端合同摘要

已确认后端已具备：

- `PATCH /admin/users/{user_id}`
- payload 字段：
  - `display_name`
  - `license_status`
  - `license_expires_at`
  - `entitlements`

已确认 step-up 规则：

- **仅改 `display_name`**：不要求 step-up
- 触达以下任一字段：要求 step-up
  - `license_status`
  - `license_expires_at`
  - `entitlements`

step-up scope 复用：

- `users.write`

失败语义复用既有 destructive flow：

- `step_up_required`
- `step_up_invalid`
- `step_up_expired`
- `token_expired`

## 前端落地策略

### 1. client 层

在 `remote/remote-admin/src/features/auth/auth-client.ts`：

- 新增 `AdminUserUpdateRequest`
- 新增 `updateAdminUser(...)`
- 继续复用 `createAdminAuthHeaders(...)`
- 支持可选 `X-Step-Up-Token`

### 2. 页面层

在 `remote/remote-admin/src/pages/users/UsersPage.tsx`：

- 在当前 detail 描述块下方新增一个小型编辑卡片
- 表单字段：
  - Display name
  - License status
  - License expiry
  - Entitlements
- 保存时仅提交 **发生变化的字段**
- 若后端第一次返回 `step_up_required / invalid / expired`：
  - 打开现有 password verify modal
  - 获取 step-up token
  - 带 token 重试同一 PATCH
- 成功后执行现有 `refreshUsersState(...)`

### 3. 测试层

补两类最小回归：

- contract test：验证 `PATCH`、JSON body、`X-Step-Up-Token`
- React/browser test：
  - display name-only 更新不触发 step-up
  - sensitive 更新触发 step-up 并 retry 成功

## 预期改动文件

- `discss/远端DayX_1_users_update_ui最小落地计划_2026-04-26.md`
- `remote/remote-admin/src/features/auth/auth-client.ts`
- `remote/remote-admin/src/pages/users/UsersPage.tsx`
- `remote/remote-admin/tests/react-contract.test.mjs`
- `remote/remote-admin/tests/step-up.react.test.mjs`

## 验收标准

1. Users 页面出现可编辑表单，且不会破坏既有 revoke / restore
2. 只改 display name 时：
   - 不弹 step-up
   - PATCH 成功
   - 列表与详情刷新
3. 改 license / entitlements 等敏感字段时：
   - 首次 PATCH 命中 `step_up_required`
   - 弹出密码确认
   - verify 成功后带 `X-Step-Up-Token` 自动重试
   - 列表与详情刷新
4. session 过期时沿用既有跳转登录行为
5. contract test 与 React 级回归通过

## 计划验证命令

```bash
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build:react
npm --prefix remote/remote-admin test
npm --prefix remote/remote-admin run test:react-step-up
```

## 实施结果（待回填）

### 已落地

- Users detail 区域已新增最小 edit form
- 前端已接入 `PATCH /admin/users/{user_id}`
- display name-only 更新已走直存路径
- `license_status / entitlements / license_expires_at` 命中敏感更新时，已按后端返回结果触发 step-up verify + retry
- 更新成功后已复用既有 list/detail refresh 策略
- 已补 contract test 与 React 级 step-up 回归

### 实际改动文件

- `remote/remote-admin/src/features/auth/auth-client.ts`
- `remote/remote-admin/src/pages/users/UsersPage.tsx`
- `remote/remote-admin/tests/react-contract.test.mjs`
- `remote/remote-admin/tests/step-up.react.test.mjs`
- `discss/远端DayX_1_users_update_ui最小落地计划_2026-04-26.md`

### 验证结果

已执行：

```bash
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin test
npm --prefix remote/remote-admin run test:react-step-up
```

结果：

- `typecheck` 通过
- `react-contract.test.mjs` 17/17 通过
- `step-up.react.test.mjs` 17/17 通过

### 本 slice 仍保留的最小风险点

1. `license_expires_at` 当前采用 ISO 文本输入，优先保证合同稳定，暂未做更重的日期控件封装
2. 本次未扩展到 users create / delete，仍保持最小增量
3. build 仍会出现既有 Vite chunk size warning，但不影响本 slice 的功能正确性
