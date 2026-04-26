# 远端 Day X.4.1：Users Update / Revoke / Restore 真实联调与浏览器冒烟

## 目标

验证 Users CRUD 当前已落地能力不只是在 mock/harness 里可用，而是能在真实本地运行时打通以下链路：

1. 登录 Remote Admin
2. 创建一个临时 smoke 用户（保证样本自包含）
3. 直接保存低风险 Update（`display_name`）
4. 保存敏感 Update（`license_expires_at` + `entitlements`），并完成 step-up verify
5. 执行 `revoke user`，并完成 step-up verify
6. 执行 `restore user`，并完成 step-up verify
7. 页面 reload 后再次搜索该用户
8. 通过真实 admin API 二次核对最终数据

---

## 运行时环境

- Remote backend: `http://127.0.0.1:8100`
- Remote admin: `http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100`
- Admin account:
  - username: `admin`
  - password: `admin-secret`

为了保证命中最新代码，本轮先执行了：

1. `npm --prefix remote/remote-admin run build`
2. `npm --prefix remote/remote-admin run build:react`
3. `python remote/remote-backend/scripts/bootstrap_admin.py --migrate ...`
4. 重启 `127.0.0.1:8100` 上的 `uvicorn`

---

## 最终通过的 smoke 用户

- username: `smoke_update_20260426042846`
- user id: `u_7`

---

## 浏览器链路结果

### 1. Create seed user

- 打开 Create user modal 成功
- 输入用户名 / 初始密码 / 展示名 / 邮箱 / tenant / entitlements 成功
- 触发 step-up verify 成功
- 用户创建成功，list/detail 自动刷新

### 2. Direct update（无需 step-up）

- 把 `display_name` 从 `Smoke Update User` 改为 `Smoke Update User Edited`
- 点击 `Save changes` 后直接保存成功
- 未要求额外密码确认

### 3. Sensitive update（需要 step-up）

提交字段：

- `license_expires_at = 2026-12-31T00:00:00Z`
- `entitlements += support:read`

实际链路：

- 首次 `PATCH /admin/users/u_7` 触发后端 `step_up_required`
- 前端弹出 `Confirm password: Save user changes`
- 输入 admin 密码后拿到 step-up token
- 第二次 `PATCH /admin/users/u_7` 携带 `X-Step-Up-Token` 成功
- detail 区已显示新增 entitlement

### 4. Revoke / Restore

- `Revoke user` 触发 step-up verify 成功
- detail 区进入 `Current state: revoked`
- `Restore user` 再次走 step-up verify 成功
- detail 区回到 `Current state: active-or-readable`

### 5. Reload 后再查

- 页面 reload 后再次按用户名过滤
- 仍能搜索到该用户
- 页面仍显示更新后的 `display_name`

---

## API 二次核对

使用真实 `POST /admin/login` 获取 token 后，再调用：

- `GET /admin/users?q=smoke_update_20260426042846`
- `GET /admin/users/u_7`

最终核对结果：

- `username = smoke_update_20260426042846`
- `display_name = Smoke Update User Edited`
- `status = active`
- `license_status = active`
- `license_expires_at = 2026-12-31T00:00:00`
- `entitlements = ["dashboard:view", "publish:run", "support:read"]`

这说明：

- 不是前端假刷新
- sensitive update 的第二次 tokenized PATCH 真正落库
- revoke / restore 后最终状态可回到 active

---

## 网络证据（关键点）

真实 smoke 脚本记录了关键请求：

### Step-up verify

共发生 4 次，scope 都是：

- `users.write`

分别对应：

1. create
2. sensitive update
3. revoke
4. restore

### User PATCH

记录到 3 次：

1. 直接更新：
   - `{ "display_name": "Smoke Update User Edited" }`
2. 敏感更新首次尝试（无 step-up token）：
   - `{ "license_expires_at": "2026-12-31T00:00:00Z", "entitlements": [...] }`
3. 敏感更新第二次尝试（带 `X-Step-Up-Token`）：
   - 同上 payload，且 header 中存在 `X-Step-Up-Token`

### Revoke / Restore

- `POST /admin/users/u_7/revoke` 带 step-up token
- `POST /admin/users/u_7/restore` 带 step-up token

---

## Artifact 目录

目录：

- `discss/artifacts/remote-users-update-smoke-2026-04-26/`

文件：

- `smoke-users-update.mjs`
- `result.json`
- `create-success.png`
- `update-direct-success.png`
- `update-sensitive-success.png`
- `revoke-success.png`
- `restore-reloaded-search.png`

---

## 额外说明

本轮中途出现过一次 **冒烟脚本自身的误报**：

- 脚本最初把前端提交的 `2026-12-31T00:00:00Z`
- 与后端回传的 naive datetime `2026-12-31T00:00:00`

按“完全字符串相等”比较，导致假失败。

收窄为“前缀一致”后再次执行，整条链路通过。

因此这次发现并修复的是：

- **真实 smoke 脚本断言过严**

而不是 Users Update / Revoke / Restore 运行时回退。

---

## 当前判断

Users 当前主线能力已具备真实运行时证据：

1. Create
2. Update（direct + sensitive step-up）
3. Revoke
4. Restore
5. Reload 后可再次查询
6. API 二次核对一致

可以把这条 Users 治理主线视为：

- **本地真实联调已打通**
- **浏览器级最小冒烟已通过**
