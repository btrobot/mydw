# Step 0 Handoff Pack（PR4）

> 状态：Frozen handoff artifact  
> 作用：为 Step 1+ 的实现 PR 提供统一入口。  
> 说明：本文档**不引入新规则**，只汇总已冻结的 Step 0 产物。

---

## 1. Purpose

Step 0 已完成以下冻结：

- PR1：远程认证 API 契约
- PR2：本地 auth domain model
- PR3：offline / revoke / background enforcement

PR4 的职责是：

1. 给实现者一个单一入口
2. 告诉实现者应该引用哪些文档
3. 告诉实现者哪些内容不能在代码 PR 中擅自修改

---

## 2. Canonical Step 0 artifacts

### PR1 — Remote contract freeze

- `docs/auth/remote-auth-api-contract-v1.md`
- `docs/auth/examples/remote-auth-login.success.json`
- `docs/auth/examples/remote-auth-refresh.revoked.json`
- `docs/auth/examples/remote-auth-me.device-mismatch.json`

### PR2 — Local auth domain model freeze

- `docs/auth/local-auth-domain-model.md`
- `docs/auth/local-auth-state-machine.md`
- `docs/auth/machine-session-semantics.md`
- `docs/auth/local-auth-storage-model.md`
- `docs/auth/client-transport-auth-model.md`
- `docs/auth/diagrams/local-auth-state-machine.mmd`

### PR3 — Enforcement / policy freeze

- `docs/auth/offline-revoke-policy.md`
- `docs/auth/background-auth-enforcement.md`
- `docs/auth/observability-events.md`

### Planning artifacts

- `.omx/plans/prd-remote-auth.md`
- `.omx/plans/test-spec-remote-auth.md`
- `.omx/plans/prd-remote-auth-step0-pr-plan.md`
- `.omx/plans/test-spec-remote-auth-step0-pr-plan.md`

---

## 3. How Step 1+ implementation should consume Step 0

## 3.1 For backend auth foundation work

必须至少引用：

- `docs/auth/remote-auth-api-contract-v1.md`
- `docs/auth/local-auth-domain-model.md`
- `docs/auth/local-auth-storage-model.md`
- `docs/auth/offline-revoke-policy.md`
- `docs/auth/background-auth-enforcement.md`

## 3.2 For frontend login / session UX work

必须至少引用：

- `docs/auth/local-auth-domain-model.md`
- `docs/auth/local-auth-state-machine.md`
- `docs/auth/machine-session-semantics.md`
- `docs/auth/client-transport-auth-model.md`
- `docs/auth/offline-revoke-policy.md`

## 3.3 For scheduler / poller enforcement work

必须至少引用：

- `docs/auth/background-auth-enforcement.md`
- `docs/auth/offline-revoke-policy.md`
- `docs/auth/observability-events.md`

## 3.4 For test work

必须至少引用：

- `.omx/plans/test-spec-remote-auth.md`
- `docs/auth/traceability-matrix.md`

---

## 4. What future code PRs must not do

后续代码 PR **不得**：

1. 隐式新增远程 auth 字段
2. 隐式新增本地 auth 状态
3. 改写 machine-session 语义
4. 把 refresh token 改成明文落 SQLite
5. 把 renderer 改成长期 bearer 真相源
6. 修改 revoke / grace / expired 行为而不先更新 Step 0 文档

如果需要改这些内容，必须先补新的 docs PR。

---

## 5. Suggested implementation entry order

建议 Step 1+ 按以下顺序消费 Step 0：

1. backend auth foundation
2. frontend login shell / session bootstrap
3. router protection
4. service + scheduler/poller enforcement
5. refresh / device binding / observability completion

---

## 6. Non-goals of PR4

PR4 不做：

- 新字段定义
- 新状态定义
- 新 persistence 规则
- 新 transport 规则
- 新 offline / revoke 行为
- 任何实现代码

