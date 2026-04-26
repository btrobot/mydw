# 远端 Day X.4.2：Users filter state 差异回归

## 本 slice 做了什么

- 给 `remote/remote-admin/tests/step-up.react.test.mjs` 补了两条 users 浏览器级差异回归：
  - `active` 过滤下 revoke 后，目标行会从列表消失，详情区不会残留旧数据。
  - `revoked` 过滤下 restore 后，目标行会从列表消失；清空过滤后会重新出现。
- 同时把 users 测试里的状态过滤交互 helper 收敛为更稳定的 Ant Design 下拉项点击方式，避免命中隐藏的虚拟列表节点。

## 这次评估到的真实 UI 合同

- destructive 成功后，如果当前过滤条件已经把目标记录排除出列表，页面会进入：
  - `Users (0)`
  - `No users matched the current filters.`
  - `Select a user from the list to review authorization detail.`
- 这时详情面板已经被清空，所以原先依赖详情面板区域渲染的 success alert 不再可见。
- 因此，这个 slice 把浏览器级断言收口到 **“过滤后列表/详情状态是否正确”**，而不是强绑 success alert 文案。

## 为什么这样是最小风险

- 不改运行时组件合同，只补测试覆盖。
- 断言点直接对齐用户真正关心的风险：**过滤态下 destructive 之后不能残留 stale detail**。
- helper 只收敛到测试层，不影响生产代码。

## 验证

- `npm run build`
- `npm run lint`
- `node --test --test-concurrency=1 tests/step-up.react.test.mjs`

结果：`25/25` 通过。

