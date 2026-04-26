# 远端 Day X.4：Users Update 编辑入口收口

## 背景

Users 页的编辑入口此前已经具备基础能力：

- Display name 直接保存
- 敏感字段更新命中后端 `step_up_required` 时自动走 step-up verify
- 成功后刷新列表 / 详情

但还剩两类“编辑态没完全收口”的问题：

1. **无法真正清空字段**
   - 尤其是 `license_expires_at`
   - 前端把空字符串视为“不发送”
   - 后端也只在字段非 `None` 时更新，导致无法表达“显式清空”

2. **PATCH 的 422 字段错误没有在编辑区内联显示**
   - 例如错误的 ISO-8601 时间字符串
   - 页面只能看到通用失败提示，无法定位具体字段

## 本次改动

### 1. 允许显式清空 Update 字段

前端 `buildUserUpdatePayload()` 现在会：

- 清空 `display_name` 时发送 `null`
- 清空 `license_expires_at` 时发送 `null`

后端 `AdminService.update_user()` 现在按 **字段是否显式传入** 来处理，而不是按“是否为 `None`”来处理。

这意味着：

- `PATCH /admin/users/{user_id}` 可以表达“把过期时间清掉”
- 敏感字段即使是清空，也仍然按 step-up 保护

### 2. PATCH 422 在编辑表单内联展示

Users 页编辑表单新增了最小字段错误映射：

- `display_name`
- `license_status`
- `license_expires_at`
- `entitlements`

当后端返回 `422 detail[]` 时：

- 顶部给出“Please fix the highlighted user fields and retry.”
- 对应字段显示内联错误
- 不会误弹 step-up modal

## 新增/补强回归

### 后端

补充 service 级回归：

- 清空 `license_expires_at` 仍然会要求 step-up
- 携带有效 step-up token 时可以成功清空 `license_expires_at`

### 前端 React / 浏览器级

补充 Users 页面回归：

- 清空 `license_expires_at` 会走 `PATCH { license_expires_at: null }`
- 敏感更新命中 step-up 后能重试成功
- `422` 字段错误会在编辑区内联展示，且不会进入 step-up

## 验证结果

已通过：

- `pytest remote/remote-backend/tests/services/test_admin_step_up_runtime.py -q`
- `npm run build`（`remote/remote-admin`）
- `npm run build:react && node --test --test-concurrency=1 --test-name-pattern "^users " tests/step-up.react.test.mjs`

## 风险判断

这次仍然是 **最小风险收口**：

- 不新增 Users Update 的新字段
- 不改变现有 step-up 策略
- 只让“已有编辑入口”更完整、更可用、更可回归

## 余留

Users CRUD 主线还可继续补：

- Users Update 的真实后端/浏览器联调证据
- Users revoke / restore / update 的更完整浏览器级差异回归
- 如果业务需要，再评估更完整的用户资料编辑字段，而不是继续只停留在授权治理字段
