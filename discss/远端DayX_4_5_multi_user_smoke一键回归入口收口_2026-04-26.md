# 远端 Day X.4.5：multi-user smoke 一键回归入口收口

## 本 slice 做了什么

- 给 `remote-admin` 增加了一条正式 npm script：
  - `npm run smoke:users:update:multi`
- 新增一个轻量 launcher：
  - `remote/remote-admin/scripts/run-smoke-users-update-multi.mjs`
- 它会自动：
  1. 先跑 `build`
  2. 再跑 `build:react`
  3. 自动生成带时间戳的 artifact 目录
  4. 调起真实多用户 smoke 脚本
  5. 在成功后打印证据目录

## 入口收口结果

现在“Users Update 多用户真实冒烟”的推荐入口已经收敛成：

```bash
npm --prefix remote/remote-admin run smoke:users:update:multi
```

如果当前 shell 已经在 `remote/remote-admin/` 下，则可直接：

```bash
npm run smoke:users:update:multi
```

## 配套提示补齐

- `remote/remote-admin/README.md`
  - 补了 real smoke entry 章节
  - 补了 artifact 目录说明
  - 补了自定义 artifact 目录方式
- `scripts/start-remote.bat`
  - 启动完成后会直接提示这条 smoke 命令，避免以后忘记入口

## 为什么这是最小风险

- 不改运行时
- 不改 smoke 业务脚本本身的行为合同
- 只是把“手敲长命令 + 手动指定目录”收敛成固定入口
- 以后回归时不容易再跑错命令或忘记保存证据

## 验证

- `npm run smoke:users:update:multi`

结果：

- 能自动 build + build:react
- 能自动生成 timestamped artifact 目录
- 能跑通真实 multi-user users update smoke
- 能在结束后打印 evidence 路径

