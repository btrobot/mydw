# 远端 Day X.4.6：Users 真实 smoke 入口全收口

## 本 slice 做了什么

- 把之前散落在 artifact 目录里的 create / 单用户 update smoke，正式提升为 repo 内脚本：
  - `remote/remote-admin/scripts/smoke-users-create.mjs`
  - `remote/remote-admin/scripts/smoke-users-update.mjs`
- 给它们各自补了 launcher：
  - `run-smoke-users-create.mjs`
  - `run-smoke-users-update.mjs`
- 保留已有的 multi-user smoke launcher，并把三类入口统一收敛进 `package.json`

## 现在的正式入口

在 `remote/remote-admin/` 下可直接运行：

```bash
npm run smoke:users:create
npm run smoke:users:update
npm run smoke:users:update:multi
npm run smoke:users
```

含义分别是：

- `smoke:users:create`
  - create UI 真烟测
- `smoke:users:update`
  - create + direct update + sensitive update + revoke/restore 真烟测
- `smoke:users:update:multi`
  - 多用户编辑态隔离 / reset / 真实 update 真烟测
- `smoke:users`
  - 一次 build 后顺序跑完整 users 真实 smoke 套件
  - artifact 会拆成 `create / update / update-multi` 三个子目录
  - 会按 admin step-up verify 限流窗口自动插入等待，避免整套连跑时被 429 打断

## 配套收口

- `remote/remote-admin/README.md`
  - 现在已经列出完整 smoke 命令表
- `scripts/start-remote.bat`
  - 现在会直接打印完整 users smoke 入口

## 为什么这是最小风险

- 不改运行时
- 不扩产品合同
- 只是把已验证过的真实 smoke 能力从“零散脚本”提升为“稳定入口”
- 后续做 users 相关改动时，不需要再翻 artifact 目录找旧命令

## 验证

- `npm run smoke:users:create`
- `npm run smoke:users:update`
- `npm run smoke:users`

本次已实跑完整入口链路：

- 单独 create 入口通过
- 单独 update 入口通过
- 全量 `smoke:users` 套件通过
  - 证据目录：`discss/artifacts/remote-users-smoke-suite-2026-04-26-134949/`
  - 套件在 `update -> update-multi` 之间按默认 `5 次 / 60 秒` step-up 限流自动等待后继续执行
