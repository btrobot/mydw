# 远端 Day X.3：Users Create UI 最小前端落地

## 本轮目标

在 `remote-admin` 的 Users 页面补上最小风险的 Create UI，不重写现有 master-detail 结构，只在页头增加 `Create user` 入口，并复用现有：

- `users.write`
- step-up verify
- list/detail refresh
- token expired 跳转登录

---

## 本轮落地范围

### 1. 前端 client 合同

新增：

- `AdminUserCreateRequest`
- `createAdminUser(accessToken, payload, stepUpToken?)`

并补上 `422 {"detail": [...]}` 的错误细节透传，让 create modal 能把后端字段错误回填到表单。

### 2. Users 页 create modal

新增页头按钮：

- `Create user`

打开 modal 后支持输入：

- Username
- Initial password
- Display name
- Email
- Tenant ID
- License status
- License expiry
- Entitlements

### 3. 交互策略

采用“**先 create，后按需 step-up retry**”：

1. 首次直接调用 `POST /admin/users`
2. 若后端返回 `step_up_required / invalid / expired`
3. 再弹 password verify modal
4. 带 `X-Step-Up-Token` 重试 create

这与现有 users update 的敏感字段策略一致，风险最小。

### 4. 成功后的行为

创建成功后：

1. 关闭 create modal
2. 刷新 users list
3. 拉取新用户 detail
4. 自动选中新用户
5. 展示成功提示：

`User created. The list and detail panel were refreshed from the backend.`

---

## 改动文件

- `remote/remote-admin/src/features/auth/auth-client.ts`
- `remote/remote-admin/src/pages/users/UsersPage.tsx`
- `remote/remote-admin/tests/react-contract.test.mjs`
- `remote/remote-admin/tests/step-up.react.test.mjs`
- `remote/remote-shared/docs/remote-admin-platform-ui-spec-v1.md`

---

## 关键实现决策

### 决策 1：不预先弹 step-up

原因：

- 后端已经把 create 定义为受保护写操作
- 前端沿用“后端要求时再 verify”的成熟模式即可
- 避免把 Users create 变成一条新的前端特判分支

### 决策 2：不把 create form 塞进右侧 detail panel

原因：

- 右侧已经承担 selected user 的 detail/edit/revoke/restore
- 再混入 create 会让“新增”和“编辑现有”状态互相污染
- modal 改动更小，更容易回归

### 决策 3：422 直接回填表单字段

原因：

- 后端 duplicate username 已收敛为 validation-style 422
- 前端不需要引入新的 error code 语义
- 可以直接映射 `detail[].loc[-1]` 到表单字段

---

## 验证

### 已通过

```bash
npm run typecheck
npm test
npm run build:react
node --test --test-concurrency=1 --test-name-pattern "users page opens a create-user modal|users create retries with step-up token|users create surfaces backend 422 validation details|users create token expiry redirects back to login" tests/step-up.react.test.mjs
node --test --test-concurrency=1 --test-name-pattern "users" tests/step-up.react.test.mjs
```

结果：

- `typecheck` 通过
- `react-contract` 18/18 通过
- `users` React 级回归子集 11/11 通过

---

## 仍未做

### 1. 未回跑整份 `test:react-step-up`

原因不是失败，而是整份浏览器级回归非常慢，包含 Users / Devices / Sessions 全量场景；本轮已改动范围只在 Users create，因此先跑了：

- create 新增场景
- users 全量子集

### 2. 还没做浏览器真实后端联调

当前验证是：

- contract + React/browser harness

还未做：

- 接真实 backend 的手工创建用户联调

---

## 当前判断

Day X.3 已经达到“**最小可上线前端 baseline**”：

- 有真实 create 入口
- 有 step-up retry
- 有 422 表单错误回填
- 有创建后 list/detail refresh
- 没破坏既有 users revoke/restore/update 流程
