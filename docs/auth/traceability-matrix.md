# Step 0 Traceability Matrix（PR4）

> 说明：本矩阵只做映射，不新增规范。

---

## 1. PRD / Test Spec -> Frozen Docs -> Future Implementation

| Requirement / Test Area | Frozen Docs | Future Implementation Focus |
|---|---|---|
| Remote login / refresh / logout / me contract | `docs/auth/remote-auth-api-contract-v1.md` | `remote_auth_client`, `/api/auth/*` |
| Machine-session truth | `docs/auth/local-auth-domain-model.md`, `docs/auth/machine-session-semantics.md` | backend auth service / session APIs |
| Auth state set / transitions | `docs/auth/local-auth-state-machine.md` | backend session state handling + frontend auth UX |
| Secret / non-secret persistence split | `docs/auth/local-auth-storage-model.md` | `SecretStore`, session persistence layer |
| Renderer vs machine-session propagation model | `docs/auth/client-transport-auth-model.md` | frontend bootstrap, axios/generated client/SSE behavior |
| Offline / revoke / refresh-failure behavior | `docs/auth/offline-revoke-policy.md` | frontend locked/grace UX + backend auth decisions |
| Scheduler / poller auth behavior | `docs/auth/background-auth-enforcement.md` | scheduler + composition poller enforcement |
| Auth observability taxonomy | `docs/auth/observability-events.md` | loguru / SystemLog / assertions |

---

## 2. Step 0 PR mapping

| PR | Frozen Scope | Artifact Set |
|---|---|---|
| PR1 | Remote auth contract | remote-auth-api-contract + examples |
| PR2 | Local auth domain model | state machine + semantics + storage + transport |
| PR3 | Offline/revoke/background enforcement | policy + background enforcement + events |
| PR4 | Handoff / readiness / traceability | handoff pack + matrix + checklist |

---

## 3. Test Spec mapping

| Test Spec area | Frozen Doc Sources |
|---|---|
| Unit: auth state transitions | `local-auth-state-machine.md` |
| Unit: logout / machine session | `machine-session-semantics.md`, `local-auth-storage-model.md` |
| Integration: `/api/auth/*` semantics | `remote-auth-api-contract-v1.md`, `local-auth-domain-model.md` |
| Integration: protected route denial | `local-auth-domain-model.md`, `offline-revoke-policy.md` |
| Integration: scheduler / poller behavior | `background-auth-enforcement.md` |
| E2E: login / restore / locked / grace | `offline-revoke-policy.md`, `local-auth-state-machine.md` |
| Observability assertions | `observability-events.md` |

---

## 4. Rule for future PR authors

当实现 PR 涉及上表中的任一项时：

1. 必须引用对应 frozen doc
2. 若实现需要改变冻结规则，先补 docs PR
3. 不允许在代码 PR 中隐式扩展 Step 0 真相

