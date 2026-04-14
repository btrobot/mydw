# 本地 Auth Domain Model（Step 0 PR2）

> 状态：Frozen for Step 0 PR2  
> 作用：冻结本地授权域模型，作为后续 backend / frontend / background execution 实现的共同真相。  
> 关联：
> - `docs/auth/remote-auth-api-contract-v1.md`
> - `.omx/plans/prd-remote-auth.md`
> - `.omx/plans/test-spec-remote-auth.md`

---

## 1. Purpose

本文档冻结 **local auth domain model**，明确以下内容：

1. 三层真相模型
2. 本地 auth state machine
3. machine-session 语义
4. secret / non-secret persistence split
5. `SecretStore` 抽象要求
6. client transport / auth propagation model

本文档**不定义**：

- 远程 API 契约字段
- offline / revoke / expired 的后台执行策略
- scheduler / poller 的 stop / pause 规则
- 任何运行时代码

这些内容分别由：

- PR1 契约文档
- PR3 offline / revoke enforcement 文档

继续冻结。

---

## 2. Three-layer truth model

本地授权体系分为三层：

### 2.1 Remote truth

远程认证后端提供的真相，包括：

- user identity
- tenant / license / entitlement
- token validity
- device binding result
- revoke / disabled / minimum version gate
- optional offline grace fields

它是：

> **授权真相源**

但不是最终本地执行门禁本身。

### 2.2 Local machine-session truth

本地 FastAPI 维护 machine-session，并以此作为：

> **本地执行门禁真相**

用于控制：

- 本地 API 是否可用
- 高风险本地操作是否允许执行
- 后台任务是否允许启动
- 当前授权状态对 UI 应如何呈现

### 2.3 Renderer UX state

前端只负责：

- 展示登录状态
- 展示被锁定原因
- 在启动时探测本地 `/api/auth/session`
- 根据本地授权状态决定 UI 是否进入 login / dashboard / locked 页面

前端不是长期 bearer token 真相源。

---

## 3. Domain model summary

PR2 冻结的本地 auth 域由以下规范文档组成：

- `docs/auth/local-auth-state-machine.md`
- `docs/auth/machine-session-semantics.md`
- `docs/auth/local-auth-storage-model.md`
- `docs/auth/client-transport-auth-model.md`

推荐实现时以本文为入口，再逐项引用子文档。

---

## 4. Design principles frozen in PR2

1. **Local FastAPI machine-session is the v1 auth truth**
2. **Renderer does not hold long-lived bearer tokens as the primary auth model**
3. **Refresh token must not be stored as plaintext in SQLite**
4. **Single-machine single-active remote user** 是 v1 默认机器语义
5. **Secret storage and non-secret state are different persistence classes**

---

## 5. Implementation boundary

PR2 只冻结模型，不产生运行时代码承诺。

明确 out of scope：

- `SecretStore` 的具体实现
- 数据库 schema / migration
- FastAPI auth router / service / dependency stubs
- axios / generated client / SSE 的代码改造
- Electron preload / IPC 认证实现

---

## 6. Review checklist

- [ ] 三层真相模型定义清楚
- [ ] 本地 state machine 已冻结
- [ ] machine-session 语义已冻结
- [ ] persistence split 已冻结
- [ ] `SecretStore` 抽象要求已冻结
- [ ] transport/auth propagation 模型已冻结
- [ ] 无占位词
