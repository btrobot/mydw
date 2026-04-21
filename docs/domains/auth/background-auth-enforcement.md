# Background Auth Enforcement（Step 0 PR3）

> 状态：Frozen  
> 作用：冻结 router / service / scheduler / poller 的授权门禁覆盖面，以及 publish scheduler / composition poller 的行为。

---

## 1. Purpose

PR3 的重点之一是：

> 不只冻结“前台 API 要鉴权”，还要冻结后台执行面的授权门禁。

本文档冻结：

- auth enforcement coverage matrix
- publish scheduler 规则
- composition poller 规则

---

## 2. Coverage matrix

| Layer | Must be protected | Why |
|---|---|---|
| Router | yes | 防止未授权直接请求本地 API |
| Service | yes | 防止未来内部调用绕过 router gate |
| Scheduler start/pause/resume | yes | 防止后台执行在未授权状态下启动 |
| Publish loop per iteration | yes | 防止运行中授权状态变化后继续取任务 |
| Composition poller start/stop | yes | 防止 composing 任务在撤销后继续轮询远程 |
| Composition poller per iteration | yes | 防止远程授权变化后继续消费远程合成结果 |

---

## 3. Publish scheduler enforcement

## 3.1 When state becomes `revoked` / `device_mismatch` / `expired`

冻结规则：

- `TaskScheduler` 立即 `stop`
- 不再启动任何新任务
- 若当前存在 in-flight publish task：
  - 不在浏览器动作不可预测中间态强制硬杀
  - 允许运行到当前 publish 安全检查点
  - 到达安全检查点后，将任务标记为 `failed`
  - 失败原因固定写 auth reason

### Canonical auth reasons

- `remote_auth_revoked`
- `remote_auth_expired`
- `remote_auth_device_mismatch`

## 3.2 When state becomes `authenticated_grace`

冻结规则：

- `TaskScheduler` 进入 `pause`
- 不启动任何新任务
- 若当前没有 in-flight task，则保持暂停
- 若当前有 in-flight task，则允许其运行到下一个安全检查点后暂停
- 不再取下一条任务

---

## 4. Composition poller enforcement

## 4.1 When state becomes `revoked` / `device_mismatch` / `expired`

冻结规则：

- `CompositionPoller` 立即 `stop`
- 不再查询远程 composing 任务状态
- 当前 composing 的 `Task/CompositionJob` 保持原状态
- 不伪造 success / failed
- 授权恢复后才允许显式恢复轮询

## 4.2 When state becomes `authenticated_grace`

冻结规则：

- `CompositionPoller` 进入 `pause`
- 暂停轮询
- composing 状态保持不变
- 恢复为 `authenticated_active` 后再恢复轮询

---

## 5. Why PR3 freezes these rules

如果这部分不在 Step 0 冻结，后续实现阶段就会重新争论：

- revoke 时到底 stop 还是 pause
- in-flight publish task 是立即失败还是等安全检查点
- composing 任务状态要不要在 poller stop 时被改写

PR3 明确这些行为，避免 Step 1+ 代码 PR 出现策略漂移。

---

## 6. Review checklist

- [ ] router / service / scheduler / poller 覆盖矩阵完整
- [ ] publish scheduler 在 revoke / expired / grace 下行为完整
- [ ] composition poller 在 revoke / expired / grace 下行为完整
- [ ] auth failure reason 已冻结
- [ ] 无占位词

