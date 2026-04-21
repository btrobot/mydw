# Implementation Readiness Checklist（PR4）

> 作用：供 Step 1+ 的实现 PR 作者在开工前自检。  
> 说明：本清单不新增规范，只确认是否已引用 Step 0 冻结文档。

---

## 1. Before coding

- [ ] 已确认当前工作项属于哪个实现主题
- [ ] 已阅读 `.omx/plans/prd-remote-auth.md`
- [ ] 已阅读 `.omx/plans/test-spec-remote-auth.md`
- [ ] 已阅读 `docs/auth/step0-handoff-pack.md`
- [ ] 已从 `docs/auth/traceability-matrix.md` 找到对应 frozen docs

---

## 2. If your work touches remote auth contract

- [ ] 已引用 `docs/auth/remote-auth-api-contract-v1.md`
- [ ] 未在代码 PR 中新增 contract 字段 / 错误码

## 3. If your work touches local auth session / state

- [ ] 已引用 `docs/auth/local-auth-domain-model.md`
- [ ] 已引用 `docs/auth/local-auth-state-machine.md`
- [ ] 已引用 `docs/auth/machine-session-semantics.md`

## 4. If your work touches persistence / token storage

- [ ] 已引用 `docs/auth/local-auth-storage-model.md`
- [ ] 明确区分 secret 与 non-secret state
- [ ] 未把 refresh token 设计成明文落 SQLite

## 5. If your work touches frontend API propagation / SSE

- [ ] 已引用 `docs/auth/client-transport-auth-model.md`
- [ ] 未把 renderer 改成长期 bearer 真相源
- [ ] 未把 SSE 留成绕过 machine-session 的特殊洞口

## 6. If your work touches offline / revoke / grace UX

- [ ] 已引用 `docs/auth/offline-revoke-policy.md`
- [ ] 未在代码 PR 中改写 grace / revoke / expired 规则

## 7. If your work touches scheduler / poller

- [ ] 已引用 `docs/auth/background-auth-enforcement.md`
- [ ] 已引用 `docs/auth/observability-events.md`
- [ ] 未在代码 PR 中改写 stop / pause / fail 语义

---

## 8. If you need to change a frozen rule

- [ ] 已停止当前实现改动
- [ ] 已先创建新的 docs PR 更新 Step 0 真相
- [ ] 未在代码 PR 中直接修改冻结规则

