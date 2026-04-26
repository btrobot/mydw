# 远端 Day X.3.1：Users Create 真实联调与浏览器冒烟

## 目标

验证 Day X.3 的 Users Create UI 不是只在测试桩里可用，而是能在真实本地运行时完成：

1. 登录 Remote Admin
2. 进入 Users 页面
3. 打开 Create user modal
4. 提交 `POST /admin/users`
5. 触发并完成 step-up password verify
6. 创建成功后刷新 list/detail
7. 刷新页面后按用户名再次查询到新用户

---

## 运行时环境

- Remote backend: `http://127.0.0.1:8100`
- Remote admin: `http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100`
- Admin account:
  - username: `admin`
  - password: `admin-secret`

本轮先做了两件收敛动作：

1. 重新执行 `npm --prefix remote/remote-admin run build:react`
2. 重新执行 admin bootstrap，确保账号存在且密码一致
3. 重启了 `8100` 上的 `uvicorn`，确保跑的是最新 backend 代码，而不是更早的旧进程

---

## 浏览器烟测结果

### 最终通过的真实冒烟用户名

- `smoke_user_20260426034736`

### 流程结果

- 登录成功
- Users 页打开成功
- Create modal 打开成功
- 首次 create 后进入 step-up verify
- 输入 admin 密码后 create 成功
- 成功提示出现
- 新用户自动成为选中详情
- 页面 reload 后，按用户名过滤仍能查到该用户

---

## API 侧二次核验

使用真实 `POST /admin/login` 拿到 token 后，再调用：

- `GET /admin/users?q=smoke_user_20260426034736`
- `GET /admin/users/u_3`

确认结果：

- username: `smoke_user_20260426034736`
- id: `u_3`
- display_name: `Smoke User`
- email: `smoke_user_20260426034736@example.com`
- tenant_id: `tenant_smoke`
- license_status: `active`
- entitlements: `dashboard:view`, `publish:run`

这说明：

- 不是前端假刷新
- 数据真实落到了 backend 持久层
- list/detail/search 都能从真实后端重新读回

---

## 证据文件

目录：

- `discss/artifacts/remote-users-create-smoke-2026-04-26/`

文件：

- `create-modal.png`
- `create-success.png`
- `create-reloaded-search.png`
- `result.json`
- `smoke-users-create.mjs`

---

## 视觉观察

从 `create-success.png` 可见：

- 成功提示位于右侧 detail 区域，位置合理
- 新创建用户已进入左侧列表并自动选中
- 详情面板字段完整回显
- edit/revoke/restore 区域没有被 create 流程破坏

---

## 额外说明

第一次真实烟测里：

- 创建动作本身已经成功
- 失败只发生在 reload 后的自动化断言 selector 过宽（命中了两个 `Users` 标题）

随后收窄 selector 后再次运行，整条真实 smoke 全绿。

因此本轮没有发现产品运行时 bug，发现并修复的是**冒烟脚本自身的断言选择器问题**。

---

## 当前判断

Day X.3 的 Users Create UI 已通过：

1. 真实 backend 联调
2. 真实浏览器冒烟
3. 页面 reload 后的二次查验
4. API 侧二次数据核验

可以把这条能力视为**本地运行时已打通**。
