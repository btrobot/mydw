# 远端 Day 5.8：admin 前端 destructive 流程接入 step-up verify 记录

## 本次目标

把 `remote/remote-admin` 里的管理端 destructive 操作接到后端已落地的 step-up 运行时上：

- destructive 前先做密码二次确认；
- 调用 `POST /admin/step-up/password/verify` 换取短时 `step_up_token`；
- destructive 请求自动补 `X-Step-Up-Token` header；
- 保持现有前端页面合同尽量不变，只在 destructive 交互前增加最小确认环节。

## 本次落地范围

### 1. auth client 层

文件：`remote/remote-admin/src/features/auth/auth-client.ts`

- 新增 step-up scope 常量：
  - `users.write`
  - `devices.write`
  - `sessions.revoke`
- 新增 `verifyAdminStepUpPassword(accessToken, password, scope)`
- 新增 `createAdminAuthHeaders(...)`，统一管理：
  - `Authorization`
  - `Content-Type`
  - `X-Step-Up-Token`
- 用户 / 设备 / 会话 destructive client 方法全部支持可选 `stepUpToken`
- 补充 step-up 相关错误映射：
  - `step_up_required`
  - `step_up_invalid`
  - `step_up_expired`
  - `mapStepUpVerifyError(...)`

### 2. 复用型 step-up UI hook

文件：`remote/remote-admin/src/features/auth/useAdminStepUp.tsx`

- 新增通用密码确认 modal hook
- 由页面传入：
  - scope
  - action label
  - description
- modal 内负责：
  - 输入密码
  - 调 verify 接口
  - 成功后 resolve `step_up_token`
  - verify 失败时展示错误
  - session 过期时触发页面已有的登出/跳转逻辑

### 3. users / devices / sessions 页面接线

文件：

- `remote/remote-admin/src/pages/users/UsersPage.tsx`
- `remote/remote-admin/src/pages/devices/DevicesPage.tsx`
- `remote/remote-admin/src/pages/sessions/SessionsPage.tsx`

接线方式一致：

1. 用户点击 destructive 按钮；
2. 页面先弹出 step-up password confirm modal；
3. 通过 verify 接口拿到短时 token；
4. destructive mutation 自动把 token 带到 `X-Step-Up-Token`；
5. mutation 成功后继续沿用当前页面已有的 refresh 策略：
   - users：刷新列表 + 详情
   - devices：刷新列表 + 详情
   - sessions：刷新列表并重选当前会话

## 这次为什么算“最小风险”

- 没有改 admin 前端已有页面结构和主路由；
- 没有改 destructive API 的 URL / body 合同；
- 只是把 destructive mutation 前面统一插入了一层 verify；
- header 注入集中到 `createAdminAuthHeaders(...)`，避免每个 API 调用点分散拼装；
- 页面刷新策略复用 Day 3 已经跑通的 list/detail refresh 模式，没有再引入新的状态模型。

## 额外补的前端回归

文件：`remote/remote-admin/tests/app.test.mjs`

新增/补稳的最小合同测试：

- `mapStepUpVerifyError(...)` 映射稳定
- `createAdminAuthHeaders(...)` 会正确拼：
  - `Authorization`
  - `Content-Type`
  - `X-Step-Up-Token`
- `verifyAdminStepUpPassword(...)` 会正确调用：
  - `POST /admin/step-up/password/verify`
  - body: `{ password, scope }`
- `revokeAdminUser(...)` 会透传 `X-Step-Up-Token`

## 验证结果

在 `remote/remote-admin` 目录执行：

```bash
npm run typecheck
npm run test
```

结果：

- `typecheck` 通过
- `test` 通过（27/27）

## 当前完成定义

这一步完成后，admin 前端里已经接上 step-up 的 destructive 流程包括：

- users revoke / restore
- devices unbind / disable / rebind
- sessions revoke

也就是说，前后端关于 step-up verify + token header 的主链路已经打通。

## 剩余观察项

- 目前只补了 auth client 层与已有页面 contract 测试，未补更高层的 React 交互测试；
- audit logs 当前是只读页，不需要 step-up；
- 后续如果 admin 侧再新增 destructive 页面，建议直接复用 `useAdminStepUp` + `createAdminAuthHeaders` 这套模式，避免再次分叉。
