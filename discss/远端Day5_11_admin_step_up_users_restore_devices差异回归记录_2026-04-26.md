# 远端 Day 5.11：admin step-up 的 users restore / devices unbind-rebind 差异回归记录

## 本次目标

在 Day 5.10 已经覆盖：

- users revoke
- devices disable
- sessions revoke

之后，再补上**差异动作本身**的最小浏览器级回归：

- `users restore`
- `devices unbind`
- `devices rebind`

这里不重复铺满 verify 失败 / token 过期的通用场景，而是聚焦这些动作与已测链路不同的地方：

- action label / description 是否正确
- destructive endpoint 是否切换正确
- payload/header 是否正确
- 刷新后的页面状态是否符合该动作预期

## 本次改动

文件：`remote/remote-admin/tests/step-up.react.test.mjs`

### 1. users restore

新增 `REVOKED_USER` 测试数据，并让 users harness 支持：

- 自定义初始 user 状态
- mock `/admin/users/:id/restore`

新增浏览器级用例：

- 从 revoked 用户详情点击 `Restore user`
- 校验 restore 专属 modal 标题与描述
- 输入密码后继续 verify
- 校验 restore 请求带 `X-Step-Up-Token`
- 校验页面刷新为 `Current state: active-or-readable`

### 2. devices unbind

扩展 devices harness，新增：

- mock `/admin/devices/:id/unbind`
- 记录 `unbindHeaders`

新增浏览器级用例：

- 点击 `Unbind device`
- 校验 unbind 专属 modal 标题与描述
- 校验 verify scope 仍为 `devices.write`
- 校验 unbind 请求带 `X-Step-Up-Token`
- 校验刷新后状态变成 `unbound`

### 3. devices rebind

新增 `UNBOUND_DEVICE` 测试数据，并扩展 devices harness：

- mock `/admin/devices/:id/rebind`
- 记录 `rebindRequests`
- 捕获请求 body

新增浏览器级用例：

- 从 unbound 设备详情填写：
  - `Target user id = u_2`
  - `Client version = 0.3.0`
- 点击 `Rebind device`
- 校验 rebind 专属 modal 标题与描述
- 校验 verify scope 仍为 `devices.write`
- 校验 rebind 请求：
  - 带 `X-Step-Up-Token`
  - body 为 `{ user_id: 'u_2', client_version: '0.3.0' }`
- 校验刷新后设备重新变成 `bound`

## 验证结果

在 `remote/remote-admin` 目录执行：

```bash
npm run typecheck
npm run test
npm run test:react-step-up
```

结果：

- `typecheck` 通过
- `test` 通过（27/27）
- `test:react-step-up` 通过（15/15）

## 当前浏览器级 step-up 覆盖面

现在已经覆盖：

- users revoke
- users restore
- devices disable
- devices unbind
- devices rebind
- sessions revoke

也就是说，admin 前端当前已经对主要 destructive 差异动作都有浏览器级 step-up 护栏。

## 剩余边界

- sessions 目前仍只覆盖 `revoke`，但该页本身也只有这一类 destructive 动作
- users / devices 的 failure / token_expired 仍然只对代表动作做了页面级回归；不过这些动作共享同一个 `useAdminStepUp` 主链路，因此当前已经能较好拦住接线回归
