# Offline / Revoke Policy（Step 0 PR3）

> 状态：Frozen  
> 作用：冻结本地授权系统在 online / grace / expired / revoked / device mismatch 情况下的用户可见行为与执行策略。

---

## 1. Purpose

本文档冻结：

- offline vs revoke policy
- refresh failure 分支行为
- grace 模式允许 / 禁止动作

本文档**不定义**：

- 新 API 字段
- 新 auth 状态
- persistence / transport 新规则
- 任何运行时代码

这些已由：

- `docs/auth/remote-auth-api-contract-v1.md`
- `docs/auth/local-auth-domain-model.md`

冻结。

---

## 2. Policy precedence

v1 冻结以下优先级：

1. `revoked`
2. `device_mismatch`
3. `expired`
4. `authenticated_grace`
5. `authenticated_active`

说明：

- 远程明确撤销 / 禁用 / 设备不匹配的结果，优先级高于离线宽限
- grace 不是兜底“继续正常工作”模式，而是受限模式

---

## 3. Canonical policy table

| 场景 | 目标状态 | 页面行为 | 数据读取 | 高风险写操作 | 新后台任务 | 进行中后台任务 |
|---|---|---|---|---|---|---|
| 未登录 | `unauthenticated` | 登录页 | 否 | 否 | 否 | 否 |
| 正常在线授权 | `authenticated_active` | 正常 dashboard | 是 | 是（按授权） | 是 | 是 |
| 启动时离线且在 grace 内 | `authenticated_grace` | 进入受限模式 dashboard | 是（仅现有本地数据） | 否 | 否 | 否 |
| 运行中掉线且仍在 grace 内 | `authenticated_grace` | 保留当前页并提示受限模式 | 是（只读/低风险） | 否 | 否 | 按后台冻结规则执行 |
| refresh 失败且 grace 已失效 | `expired` | 锁定页 / 重新登录 | 否 | 否 | 否 | 否 |
| 远程明确 revoke / disabled | `revoked` | 锁定页 | 否 | 否 | 否 | 立即停止或进入安全停机流程 |
| 远程明确 device mismatch | `device_mismatch` | 设备不匹配锁定页 | 否 | 否 | 否 | 立即停止或进入安全停机流程 |

---

## 4. Refresh failure behavior

## 4.1 Network failure and grace still valid

当 refresh 失败原因是网络不可达，且本机仍处于 grace 窗口内：

- 本地状态进入 `authenticated_grace`
- 保留当前页面
- 显示持续横幅：`离线宽限中`
- 禁止启动新的高风险动作：
  - 发布
  - 提交合成
  - 账号自动化连接
  - 素材变更

## 4.2 Network failure and grace expired

当 refresh 失败原因是网络不可达，且本机已超出 grace：

- 本地状态进入 `expired`
- 切换到锁定页
- 要求重新联网登录
- 停止或拒绝所有后台执行

## 4.3 Remote deny / revoke / disabled

当 refresh 失败原因来自远程明确拒绝：

- `401/403` 对应远程 auth error
- `revoked`
- `disabled`

则：

- 本地不得进入 grace
- 必须进入 `revoked`
- 切换到锁定页
- 停止或拒绝所有后台执行

## 4.4 Device mismatch

当 refresh 或 `/me` 校验返回设备不匹配：

- 本地进入 `device_mismatch`
- 切换到设备不匹配锁定页
- 必须重新登录或重新绑定
- 不允许继续本地核心功能

---

## 5. Grace mode allowed / forbidden actions

## 5.1 Allowed in grace

v1 grace 模式允许：

- 进入 dashboard
- 查看现有本地数据
- 查看日志
- 查看授权状态
- 执行重新登录 / 重试校验

## 5.2 Forbidden in grace

v1 grace 模式禁止：

- 启动发布
- 提交合成
- 启动账号自动化登录/连接
- 修改高风险业务数据
- 启动新的后台任务

说明：

grace 不是“降级后的正常在线态”，而是：

> **受限模式**

---

## 6. UX expectations

| 状态 | 推荐页面/提示 |
|---|---|
| `authenticated_active` | 正常 dashboard |
| `authenticated_grace` | dashboard + 持续横幅 + 高风险按钮禁用 |
| `expired` | 锁定页或登录页（要求重新认证） |
| `revoked` | 授权失效锁定页 |
| `device_mismatch` | 设备不匹配锁定页 |

---

## 7. Review checklist

- [ ] revoke 优先级高于 grace
- [ ] refresh failure 分支全部冻结
- [ ] grace 模式允许 / 禁止动作已冻结
- [ ] 页面行为已冻结
- [ ] 无占位词

