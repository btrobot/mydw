# 远端 Day 5.9：admin step-up 最小 React 级交互测试记录

## 本次目标

在 `remote/remote-admin` 上补一组**最小但真实可交互**的 step-up 前端测试，覆盖：

- destructive 按钮点击后 modal 打开；
- verify 成功后继续 destructive 请求，并带上 `X-Step-Up-Token`；
- verify 失败时 modal 保持打开并展示错误；
- verify 返回 `token_expired` 时跳回登录页并展示会话过期提示。

## 这次采用的测试策略

因为 `remote/remote-admin` 当前没有单独引入 Testing Library / jsdom，这次没有新增依赖，而是复用了仓库里已有的 Playwright 运行时（来自 `frontend/node_modules/playwright`），做了一组最小浏览器级交互测试。

这样做的好处是：

- 不改现有运行时代码；
- 不新增 remote-admin 自己的测试依赖；
- 覆盖的是接近真实用户路径的交互链路，而不是只测纯函数。

## 新增内容

### 1. 新脚本

文件：`remote/remote-admin/package.json`

新增：

```json
"test:react-step-up": "npm run build:react && node --test tests/step-up.react.test.mjs"
```

### 2. 新测试文件

文件：`remote/remote-admin/tests/step-up.react.test.mjs`

测试方式：

- 先构建 `dist-react`
- 在 Node 里启动一个最小静态文件服务器
- 用 Playwright 打开 `react-index.html#/users`
- 拦截 `http://127.0.0.1:8100/admin/**` 请求，模拟：
  - `/admin/session`
  - `/admin/users`
  - `/admin/users/u_1`
  - `/admin/step-up/password/verify`
  - `/admin/users/u_1/revoke`

## 覆盖的 4 个场景

### 场景 1：点击 revoke 会先打开 password confirm modal

- 进入 users 页
- 点击 `Revoke user`
- 断言 `Confirm password: Revoke user` modal 出现

### 场景 2：verify 成功后继续 destructive 请求

- 输入密码并确认
- 断言 verify 请求 body 为：
  - `password`
  - `scope: users.write`
- 断言 revoke 请求 header 带：
  - `Authorization`
  - `X-Step-Up-Token: admin_step_up_1`
- 断言页面出现成功提示，并刷新为 revoked 状态

### 场景 3：verify 失败时 modal 不关闭

- verify 返回 `invalid_credentials`
- 页面展示 `Incorrect password. Please retry.`
- revoke 请求不会发出

### 场景 4：verify 返回 token_expired 时跳回登录页

- verify 返回 `token_expired`
- 页面跳到 `#/login`
- 展示 `Your admin session expired. Please sign in again.`
- revoke 请求不会发出

## 验证命令

在 `remote/remote-admin` 目录执行：

```bash
npm run typecheck
npm run test
npm run test:react-step-up
```

结果：

- `typecheck` 通过
- `test` 通过（27/27）
- `test:react-step-up` 通过（4/4）

## 当前价值

这一步之后，admin step-up 前端链路不再只是：

- auth client contract test 覆盖；

而是补到了：

- 页面级按钮点击；
- modal 交互；
- verify 成功/失败；
- session 过期跳转；
- destructive 请求 header 透传。

也就是说，Day 5.8 的接线已经有了最小可运行的 UI 回归护栏。

## 剩余边界

- 当前 React 级交互测试先只覆盖了 `users revoke` 这一条代表性链路；
- `devices` / `sessions` 还没有各自补同等级浏览器交互测试；
- 当前测试复用了 workspace 里的 Playwright 安装，后续如果希望 remote-admin 完全独立运行测试，可以再评估是否把浏览器测试依赖内聚到该子项目。
