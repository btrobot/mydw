# 验证基线（Verification Baseline）

> Version: 1.0.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把“下一阶段开发至少跑什么”收口成一份可执行清单，避免每次开发都靠个人记忆决定验证范围。

## 1. 这份文档负责什么

本文件定义 repo 级的**最小可信回归基线**，回答三个问题：

1. 日常开发至少跑什么
2. 触及 remote / 发布链路时至少补跑什么
3. 阶段发布前必须为绿的验证集合是什么

本文件**不**取代：

- `docs/guides/dev-guide.md` 的环境与启动说明
- `remote/remote-shared/docs/phase4-release-gate.md` 的 remote 发布细则
- 各 feature 自己的更细粒度专项测试

如果改动超出本页覆盖范围，仍然需要在本基线之上追加对应专项验证。

## 2. 使用原则

- **先跑最小可信集**：先确认主链路没断，再决定是否扩跑
- **改哪层，加哪层**：只改文档/启动协议，不必强拉 full E2E；触及 remote，就补 remote gate
- **基线不是上限**：本页列的是“至少跑什么”，不是“只能跑这些”
- **发布看分层，不看感觉**：阶段发布按“日常基线 + 发布基线”执行，不再靠个人经验临时拼命令

## 3. 日常开发必跑

> 适用：本地 frontend/backend 常规开发，目标是快速确认 auth 入口、Creative 主入口、publish/task 主链路与核心后端契约仍然可信。

### 3.1 Frontend 最小 E2E 基线

在 `frontend/` 目录运行：

```powershell
npm run test:e2e -- `
  e2e/auth-routing/auth-routing.spec.ts `
  e2e/creative-main-entry/creative-main-entry.spec.ts `
  e2e/publish-pool/publish-pool.spec.ts
```

覆盖意图：

- `auth-routing.spec.ts`：授权态 / 路由门禁 / grace shell
- `creative-main-entry.spec.ts`：`/` 与 `/login` 到 Creative workbench 的默认入口
- `publish-pool.spec.ts`：当前 Creative-first 下的发布池主链路

### 3.2 Backend 最小 pytest 基线

在 repo 根目录运行：

```powershell
pytest `
  backend/tests/test_auth_router_gates_pr3.py `
  backend/tests/test_creative_workflow_contract.py `
  backend/tests/test_local_ffmpeg_contract.py `
  backend/tests/test_openapi_contract_parity.py `
  -q
```

覆盖意图：

- `test_auth_router_gates_pr3.py`：本地 auth enforcement 与读写门禁
- `test_creative_workflow_contract.py`：Creative workflow submit 主契约
- `test_local_ffmpeg_contract.py`：local_ffmpeg V1 参数/契约边界
- `test_openapi_contract_parity.py`：前后端共享 API 契约没有明显漂移

### 3.3 文档 / 启动协议改动时补跑

如果这次改动涉及 `README.md`、`docs/current/*`、`docs/guides/*`、启动脚本或 launcher 协议，再补跑：

```powershell
pytest `
  backend/tests/test_backend_launcher_contract.py `
  backend/tests/test_startup_workflow_consistency.py `
  backend/tests/test_doc_truth_fixes.py `
  backend/tests/test_epic7_docs_baseline.py `
  -q
```

目的：保证入口文档、启动协议、当前真相与契约文档继续一致。

## 4. 触及 remote / 联调链路时必跑

> 适用：改动 remote-backend、remote-admin、本地 auth 对接、设备/会话治理、发布治理链路时。

### 4.1 Remote 最小 gate

在 repo 根目录运行：

```powershell
pytest `
  backend/tests/test_remote_phase0_bootstrap.py `
  backend/tests/test_remote_phase1_pr4_gate.py `
  backend/tests/test_remote_phase4_pr4_gate.py `
  -q

npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
```

覆盖意图：

- `test_remote_phase0_bootstrap.py`：remote 基础可启动 / bootstrap 资产仍在
- `test_remote_phase1_pr4_gate.py`：登录 / 生命周期 / admin 早期 gate 仍可组成最小闭环
- `test_remote_phase4_pr4_gate.py`：release-governance 资产与 workflow 仍然存在
- `remote-admin typecheck/build`：控制台基础可构建

### 4.2 需要更强 remote 信心时追加

如果改动直接触及 compatibility harness、release checklist、runbook、admin runtime 或 staging promotion 逻辑，直接转入第 5 节的“阶段发布必跑”。

## 5. 阶段发布必跑

> 适用：阶段收口、准备交接、准备发版、或者需要给下一阶段建立可信起跑线时。

阶段发布不是只跑一条命令，而是跑完下面整组：

### 5.1 先跑全部日常基线

必须先完成：

- 第 3 节全部内容
- 如果触及 remote，再完成第 4 节全部内容

### 5.2 Frontend 全量 E2E

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e
```

目的：把 auth / creative / ai-clip / publish / task 的完整前端回归跑一遍。

### 5.3 Remote Phase 4 release gate

在 repo 根目录按 `remote/README.md` 与 `remote/remote-shared/docs/phase4-release-gate.md` 执行：

```powershell
pytest backend/tests/test_remote_phase0_bootstrap.py backend/tests/test_remote_phase0_contract_freeze.py backend/tests/test_remote_phase0_compatibility_gate.py backend/tests/test_remote_phase1_pr1_login.py backend/tests/test_remote_phase1_pr2_lifecycle.py backend/tests/test_remote_phase1_pr3_admin.py backend/tests/test_remote_phase1_pr4_gate.py backend/tests/test_remote_phase2_pr1_control_backbone.py backend/tests/test_remote_phase2_pr2_admin_users.py backend/tests/test_remote_phase2_pr3_admin_devices.py backend/tests/test_remote_phase2_pr4_admin_sessions.py backend/tests/test_remote_phase2_pr5_supportability.py backend/tests/test_remote_phase2_pr5_gate.py backend/tests/test_remote_phase3_pr1_admin_rbac.py backend/tests/test_remote_phase3_pr2_dashboard_audit.py backend/tests/test_remote_phase3_pr3_operations_ux.py backend/tests/test_remote_phase3_pr4_gate.py backend/tests/test_remote_phase4_pr1_contract_hardening.py backend/tests/test_remote_phase4_pr2_runtime_reliability.py backend/tests/test_remote_phase4_pr4_gate.py backend/tests/test_remote_a0_pr1_operating_model.py backend/tests/test_remote_a0_pr2_env_discipline.py backend/tests/test_remote_a0_pr3_topology_health.py backend/tests/test_remote_a0_pr4_release_governance.py -q
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/build_phase0_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase0_gate.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```

另外必须人工完成：

- `remote/remote-shared/docs/staging-deploy-checklist.md`
- `remote/remote-shared/docs/staging-promotion-checklist.md`
- `remote/remote-shared/docs/rollback-runbook.md`
- `remote/remote-shared/docs/restore-recovery-runbook.md`
- `remote/remote-shared/docs/support-runbook.md`

## 6. 最小回归测试矩阵

| 层级 | 什么时候跑 | 命令 / 套件 | 目的 |
| --- | --- | --- | --- |
| Frontend 日常基线 | 本地前端 / 联调常规开发 | `auth-routing` + `creative-main-entry` + `publish-pool` | 保住入口、Creative 主工作台、发布池主链路 |
| Backend 日常基线 | 本地 backend / schema / workflow 常规开发 | `auth_router_gates` + `creative_workflow_contract` + `local_ffmpeg_contract` + `openapi_contract_parity` | 保住 auth、Creative、组合参数与 API 契约 |
| 文档 / 启动补充基线 | 改 README / docs / 启动脚本时 | `backend_launcher_contract` + `startup_workflow_consistency` + docs truth tests | 保住入口文档与启动协议一致 |
| Remote 最小 gate | 改 remote / 本地 auth 对接时 | remote phase0 + phase1 gate + phase4 gate + remote-admin build | 保住 remote 最小闭环 |
| 阶段发布基线 | 阶段收口 / 发版前 | 日常基线 + full frontend E2E + full remote phase4 release gate | 建立可交接、可发版的可信证据 |

## 7. 结论

如果只记一条规则：

> **平时先跑“日常开发必跑”；一旦触及 remote 或准备阶段发布，就在此基础上升级到对应 gate，而不是临时猜该跑什么。**
