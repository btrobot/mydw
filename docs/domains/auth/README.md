# Auth Docs Index

> 作用：作为远程认证 / 本地授权门禁相关规范文档的入口。  
> 说明：Step 0 文档均为 **docs-only freeze artifacts**，不直接实现运行时代码。

## Step 0 / Frozen artifacts

- `docs/auth/remote-auth-api-contract-v1.md` — 远程认证 API 契约 v1（PR1）
- `docs/auth/examples/remote-auth-login.success.json` — 登录成功示例
- `docs/auth/examples/remote-auth-refresh.revoked.json` — refresh 被撤销示例
- `docs/auth/examples/remote-auth-me.device-mismatch.json` — 设备不匹配示例
- `docs/auth/local-auth-domain-model.md` — 本地 auth domain model 主索引（PR2）
- `docs/auth/local-auth-state-machine.md` — 本地 auth 状态机
- `docs/auth/machine-session-semantics.md` — machine-session 语义
- `docs/auth/local-auth-storage-model.md` — 本地持久化模型
- `docs/auth/client-transport-auth-model.md` — transport / auth propagation 模型
- `docs/auth/diagrams/local-auth-state-machine.mmd` — 状态机 Mermaid 图
- `docs/auth/offline-revoke-policy.md` — offline / revoke 策略（PR3）
- `docs/auth/background-auth-enforcement.md` — 后台执行面 auth enforcement（PR3）
- `docs/auth/observability-events.md` — auth 相关事件 taxonomy（PR3）
- `docs/auth/step0-handoff-pack.md` — Step 0 handoff 入口（PR4）
- `docs/auth/traceability-matrix.md` — Step 0 追踪矩阵（PR4）
- `docs/auth/implementation-readiness-checklist.md` — 实现前检查清单（PR4）
- `docs/auth/step0-final-summary.md` — Step 0 最终总结

## Usage rule

后续任何实现 PR：

1. 必须引用对应冻结文档
2. 不得在代码 PR 中隐式扩展本契约字段或错误语义
3. 如果契约需要变化，必须先补新的文档 PR，再进入实现

## Scope rule

本目录下 **Step 0** 文档当前已冻结两类内容：

### PR1 冻结内容
- 远程认证接口
- 请求 / 响应字段
- 错误语义
- 示例 payload
- 版本策略

### PR2 冻结内容
- 本地 auth state machine
- machine-session 语义
- secret / non-secret 持久化分层
- `SecretStore` 抽象要求
- transport / auth propagation model

### PR3 冻结内容
- offline / revoke policy
- refresh failure 分支 UX
- grace 模式允许 / 禁止动作
- router / service / scheduler / poller enforcement 覆盖矩阵
- auth 相关 observability taxonomy

### PR4 交付内容
- handoff index
- traceability matrix
- implementation readiness checklist

仍然**不冻结**：

- 新规范
- runtime implementation

## Implementation summaries

- `docs/auth/step2-final-summary.md` - Step 2 final summary for frontend auth shell / bootstrap / transport rollout
