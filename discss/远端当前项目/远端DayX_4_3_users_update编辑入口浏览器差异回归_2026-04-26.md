# 远端 Day X.4.3：Users Update 编辑入口浏览器差异回归

## 本 slice 做了什么

- 给 `remote/remote-admin/tests/step-up.react.test.mjs` 补了 Users Update 编辑入口的两条最小浏览器级差异回归：
  - `Reset` 会把未保存草稿恢复为当前选中用户的真实详情，不会误发 `PATCH`
  - 在多用户列表中切换选中项时，未保存草稿会被新选中用户的详情覆盖，不会把前一个用户的编辑态泄漏到下一个用户
- 为 users harness 增加了第二个用户样本，专门覆盖“列表选中切换 + 编辑表单同步”这类纯前端状态风险

## 这次锁住的真实风险

- 编辑入口最容易回归的不是 `PATCH` 合同本身，而是：
  - 草稿态没有被 `Reset` 正确回填
  - 切换列表选中项后，编辑表单残留前一条记录的脏数据
- 这类问题一旦回归，用户会误以为自己正在编辑 B，实际看到的是 A 的未保存输入，风险比普通文案问题更高

## 为什么这是最小风险做法

- 不改运行时实现，只补浏览器级回归保护
- 不扩 Users Update 字段面，只锁住当前编辑入口最核心的 UI 状态同步语义
- harness 扩展仅限测试层，对生产代码零侵入

## 验证

- `npm run build`
- `npm run lint`
- `node --test --test-concurrency=1 tests/step-up.react.test.mjs`

结果：`27/27` 通过。

