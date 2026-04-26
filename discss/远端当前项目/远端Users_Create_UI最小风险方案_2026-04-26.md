# 远端 Users Create UI 最小风险方案

## 结论先行

**当前不能直接做前端 Users Create UI 落地**，因为现有后端 `admin v1` 合同里 **没有** `POST /admin/users`：

- 已有：
  - `GET /admin/users`
  - `GET /admin/users/{user_id}`
  - `PATCH /admin/users/{user_id}`
  - `POST /admin/users/{user_id}/revoke`
  - `POST /admin/users/{user_id}/restore`
- 缺失：
  - `POST /admin/users`

所以“最小风险方案”不是直接在前端硬加一个假按钮，而是：

1. **先补一个极小后端 create 合同**
2. **再接前端 client**
3. **最后用 modal/drawer 形式补 UI**

这样不会打破现在已经稳定的 users list/detail/update/revoke/restore 主线。

---

## 当前状态判断

### 已确认事实

1. `remote/remote-backend/app/api/admin.py` 里没有 `POST /admin/users`
2. `remote/remote-shared/docs/admin-mvp-api-contract-v1.md` 也没有 create user
3. `remote/remote-shared/openapi/remote-auth-v1.yaml` / runtime json 当前 users 面只覆盖 list/detail/update/revoke/restore
4. 数据模型里用户创建并不只是插一张 `users` 表，还至少涉及：
   - `users`
   - `user_credentials`
   - `licenses`
   - `user_entitlements`
5. 当前 managed-user 登录依赖 `username + password`，所以 create user **必须解决初始密码来源**

### 风险含义

这说明 Users Create 不是“纯前端补洞”，而是 **小型纵切功能**。

如果贸然在前端先做：

- 没法真实提交
- 会误导用户以为系统支持创建
- 后续还要返工成真实合同

因此不建议“先上 disabled 按钮 + later TODO”式假落地。

---

## 最小风险产品定义

### 本轮只做什么

只做 **最小可运营** 的用户创建：

- 管理员输入基础身份字段
- 设置初始密码
- 设置基础 license 状态
- 设置 entitlements
- 创建成功后选中新用户并刷新列表/详情

### 本轮明确不做什么

- 不做 invite/email onboarding
- 不做密码重置独立流程
- 不做批量导入
- 不做用户删除
- 不做更复杂的 license plan / offline grace / phone 扩展
- 不做跨页大改版

---

## 推荐的后端最小合同

### 新增路由

`POST /admin/users`

### 推荐 request payload

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

### 推荐 response

直接返回 `AdminUserResponse`

原因：

- 和现有 detail/update 响应模型一致
- 前端可直接复用当前 Users detail 展示
- 成功后可立即选中新用户，无需额外转换

### 权限 / step-up

推荐：

- 权限仍为 `users.write`
- **create user 一律要求 step-up**

原因：

- create 本质是高影响写操作
- 还伴随初始密码下发
- 规则比 update 更简单，前后端都更不容易出错

### 推荐错误语义

最小风险建议：

1. **字段格式/必填校验** → 走 FastAPI `422`
2. **用户名重复** → 也尽量收敛到 `422` 字段错误，而不是新增 `error_code`

原因：

- 当前 `error-code matrix` 冻结里没有 `conflict` / `already_exists`
- 新增新的 canonical `error_code` 会扩大合同面
- 用 `422` 能把风险控制在最小范围

前端 UX 上可以：

- 提交前做一次本地校验
- 提交后若命中 `422`，把错误回填到表单字段

---

## 推荐的后端实现边界

### service 层建议新增

- `AdminUserCreateRequest`
- `AdminService.create_user(...)`

### repository 层建议新增

- `create_user(...)`
- `create_user_credential(...)`
- 复用 `replace_entitlements(...)`
- 复用或显式创建 `License`

### create 时最小必做的持久化

1. 写 `users`
2. 写 `user_credentials`
3. 写 `licenses`
4. 写 `user_entitlements`
5. 写 audit：
   - 建议事件名：`admin_user_created`

### 推荐默认值

- `status`: `active`
- `license_status`: 默认 `active`
- `entitlements`: 默认 `[]`

---

## 推荐的前端最小 UI 方案

## 不建议

不建议直接把 create form 塞进当前右侧 detail panel。

原因：

- 当前右侧区域已经承担 selected user detail + edit + revoke/restore
- 再塞 create，会让“编辑现有用户”和“创建新用户”语义混在一起
- 容易导致 selection 状态复杂化

## 建议

在 Users 页头或筛选卡片右侧补一个：

- `Create user` 按钮

点击后打开：

- `Modal`（优先）

理由：

- 改动最小
- 不破坏当前 master-detail 结构
- 与 create 这种一次性表单任务更匹配

### modal 字段建议

第一版只放这些：

- Username（必填）
- Initial password（必填）
- Display name（可选）
- Email（可选）
- Tenant ID（可选）
- License status（默认 active）
- License expiry（可选）
- Entitlements（CSV / multiline）

### 成功后的前端行为

1. 关闭 modal
2. 刷新 users list
3. 自动选中新创建的 user
4. 刷新 detail
5. 显示成功提示

推荐提示文案：

`User created. The list and detail panel were refreshed from the backend.`

---

## 推荐的最小前端交互规则

### step-up

建议不要预先强制弹 verify。

仍然走当前成熟模式：

1. 先直接调用 create
2. 若后端返回 `step_up_required / invalid / expired`
3. 再弹 password verify
4. 带 `X-Step-Up-Token` retry

这样可与 users update / revoke / restore 保持一致。

### 表单校验

最小必做：

- username 必填
- password 必填
- password 最小长度提示
- entitlements 做 trim + 去重
- license_expires_at 允许空值

### 只做“创建”，不混“立即绑定设备/发通知”

这能把 create 保持成纯用户主数据写入，避免横向牵连 devices / sessions / notification。

---

## 推荐的落地顺序（最小风险）

## Slice A：后端 create 合同

目标：

- 补 `POST /admin/users`
- 补 schema/service/repository
- 补最小 route/service contract test

验收：

- super_admin / auth_admin 可创建
- readonly 仍 forbidden
- create 必须 step-up
- 422 校验生效
- 成功返回 `AdminUserResponse`

## Slice B：前端 client + contract test

目标：

- `auth-client.ts` 新增 `createAdminUser`
- 补 request header/body contract test

验收：

- 能正确发 `POST /admin/users`
- 能在 retry 时带 `X-Step-Up-Token`

## Slice C：Users Create modal UI

目标：

- 在 Users 页加 `Create user` 按钮
- 补最小 modal form
- 成功后 refresh + auto-select

验收：

- 不影响现有 edit/revoke/restore
- readonly 下按钮禁用且有解释
- 创建成功后新用户可立刻在 detail 中看到

## Slice D：React/browser 回归

目标：

- 补 create 的 React 级回归

建议至少覆盖：

1. open modal
2. create success without extra step-up UI regression
3. backend returns `step_up_required` → verify → retry success
4. token expired → redirect login
5. 422 field error surfaces in form

---

## 建议的测试矩阵

### 后端

1. `test_create_user_requires_step_up`
2. `test_create_user_succeeds_with_valid_step_up`
3. `test_create_user_rejects_readonly_role`
4. `test_create_user_returns_422_for_duplicate_username`
5. `test_create_user_persists_license_and_entitlements`

### 前端 contract

1. `createAdminUser` sends `POST /admin/users`
2. JSON body shape stable
3. optional `X-Step-Up-Token` forwarded

### React/browser

1. modal open/close
2. readonly disabled state
3. step-up retry flow
4. success refresh/select flow
5. 422 field error rendering

---

## 为什么这是“最小风险”而不是“最快补按钮”

因为它遵守了当前已经稳定的 3 个边界：

1. **合同先行**
   - 不在没有后端路由时做假 UI

2. **交互复用**
   - 继续复用当前成熟的 step-up verify + retry 模式

3. **页面结构不重构**
   - create 用 modal，而不是重写 users 主布局

---

## 我对下一步的明确建议

如果继续开做，建议直接按下面顺序：

### Day X.2

先做：

**Users Create Backend Baseline**

产出：

- `POST /admin/users`
- schema/service/repository
- route/service tests

### Day X.3

再做：

**Remote Admin Users Create Modal**

产出：

- `createAdminUser`
- create modal
- React/browser regression

---

## 一句话判断

**Users Create UI 的最小风险方案 = 先补一个严格收口的 `POST /admin/users` 后端合同，再用 modal 方式把前端 create 接上，并复用现有 users.write + step-up + refresh 模式。**
