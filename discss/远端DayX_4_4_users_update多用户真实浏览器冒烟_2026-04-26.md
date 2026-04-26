# 远端 Day X.4.4：Users Update 多用户真实浏览器冒烟

## 本 slice 做了什么

- 新增一个可复用的真实浏览器冒烟脚本：
  - `remote/remote-admin/scripts/smoke-users-update-multi.mjs`
- 这个脚本直接连本地运行中的 remote backend + remote admin 静态入口，覆盖 Users Update 的多用户真实交互：
  1. 登录 Remote Admin
  2. 通过 UI 创建两条唯一 smoke 用户
  3. 在同一过滤结果下切换 A / B 两个用户
  4. 验证未保存草稿不会从 A 泄漏到 B
  5. 验证 `Reset` 不会误发 `PATCH`
  6. 在 B 上跑一次 direct update
  7. 在 B 上跑一次 sensitive update + step-up verify + retry
  8. 最后再用真实 API 校验 A 未被误改、B 已按预期更新

## 产出证据

- 运行 artifact 目录：
  - `discss/artifacts/remote-users-update-multi-smoke-2026-04-26/`
- 关键文件：
  - `result.json`
  - `filtered-two-users.png`
  - `switch-isolation-clean-b.png`
  - `reset-restored-a.png`
  - `update-direct-b.png`
  - `update-sensitive-b.png`

## 本次真实冒烟结论

本次实跑通过，验证了 3 个最关键的多用户编辑风险点：

1. **切换用户不会串草稿**
   - 在 A 上输入未保存脏数据后切到 B，B 的编辑表单仍然显示自己的真实详情
   - 切换过程中 `PATCH` 计数保持 `0`
2. **Reset 不会误提交**
   - 在 A 上再次制造脏数据后点击 `Reset`，表单恢复到真实详情
   - `PATCH` 计数仍然保持 `0`
3. **真实 update 流程可继续成立**
   - B 的 display name direct update 成功
   - B 的 entitlements + license expiry sensitive update 命中 step-up，并在 verify 后成功重试
   - API 回查确认 A 保持原值，B 按预期更新

## 关键实跑结果摘录

- 真实创建用户：
  - `u_8 / smoke_multi_update_20260426051545_a`
  - `u_9 / smoke_multi_update_20260426051545_b`
- 关键计数：
  - `patchCountBeforeSwitch = 0`
  - `patchCountAfterSwitchToB = 0`
  - `patchCountAfterReset = 0`
- 真实 API 最终状态：
  - A：
    - `display_name = Smoke Multi User A`
    - `entitlements = ["dashboard:view"]`
  - B：
    - `display_name = Smoke Multi User B Edited`
    - `license_status = active`
    - `license_expires_at = 2026-12-31T00:00:00`
    - `entitlements = ["dashboard:view", "publish:run", "support:read"]`

## 验证命令

- `npm run build`
- `npm run lint`
- `node remote/remote-admin/scripts/smoke-users-update-multi.mjs discss/artifacts/remote-users-update-multi-smoke-2026-04-26`

## 风险判断

这是一个最小风险增强：

- 不改运行时实现
- 只新增可复用 smoke 脚本和实跑证据
- 重点锁住“多用户编辑态串数据”这一类最容易被忽略、但真实风险很高的前端交互问题

