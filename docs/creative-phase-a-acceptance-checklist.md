# Phase 1 / 阶段 A 验收清单

- 范围：Creative Progressive Rebuild Phase 1（阶段 A）
- 对照计划：`.omx/plans/prd-creative-progressive-rebuild-phase-a-pr-plan.md`
- 对照 test-spec：`.omx/plans/test-spec-creative-progressive-rebuild-roadmap.md`
- 结论：已达到阶段 A 自动化验收门槛，可正式收口

## 验收结论

- [x] PR-1：Creative 数据骨架与 Task 契约扩展完成
- [x] PR-2：Creative 最小 API 与 Task 映射读通完成
- [x] PR-3：Creative Workbench / Detail 前端骨架并存接入完成
- [x] PR-4：阶段 A 联调收口与回归证明完成

## 阶段 A 门槛核对

### 1. 数据与契约
- [x] `CreativeItem` / `CreativeVersion` / `PackageRecord` 最小骨架已落地
- [x] `Task` 已完成 `creative_item_id` / `creative_version_id` / `task_kind` 扩展
- [x] 旧 Task API 保持兼容增强，无破坏式变更

### 2. 后端能力
- [x] `backend/api/creative.py` 提供最小列表 / 详情接口
- [x] `backend/services/creative_service.py` 与 `creative_version_service.py` 已读通
- [x] 至少一条 Task 可映射到 Creative
- [x] Task / Publish / Auth 旧基线未回归

### 3. 前端能力
- [x] `/creative/workbench` 可访问
- [x] `/creative/:id` 可访问
- [x] `frontend/src/App.tsx` 与 `frontend/src/components/Layout.tsx` 完成并存接入
- [x] `TaskList / TaskDetail / /ai-clip` 仍保持旧入口与诊断定位

## 自动化证据

### Backend
- [x] `backend/tests/test_creative_api.py`
- [x] `backend/tests/test_creative_task_mapping.py`
- [x] `backend/tests/test_creative_schema_contract.py`
- [x] `backend/tests/test_openapi_contract_parity.py`
- [x] `backend/tests/test_task_creation_semantics.py`
- [x] `backend/tests/test_publish_service_semantics.py`
- [x] `backend/tests/test_auth_runtime_scheduler_pr5.py`
- [x] `backend/tests/test_task_assemble.py`

### Frontend
- [x] `cd frontend && npm run api:generate`
- [x] `cd frontend && npm run generated:check`
- [x] `cd frontend && npm run typecheck`
- [x] `cd frontend && npm run build`
- [x] `cd frontend && npm exec playwright test --config e2e/playwright.config.ts e2e/creative-workbench/creative-workbench.spec.ts`
- [x] `cd frontend && npm exec playwright test --config e2e/playwright.config.ts e2e/login/login.spec.ts`
- [x] `cd frontend && npm exec playwright test --config e2e/playwright.config.ts e2e/auth-routing/auth-routing.spec.ts`
- [x] `cd frontend && npm exec playwright test --config e2e/playwright.config.ts e2e/auth-shell/auth-shell.spec.ts`

## 最小人工验收链路

- [x] 打开作品工作台
- [x] 进入作品详情
- [x] 返回 TaskList / TaskDetail 诊断视图
- [x] 打开 `/ai-clip` 并确认入口未断
- [x] 未出现阶段 B/C/D 能力误渗入阶段 A

## 本次收口涉及文件

- `backend/tests/test_auth_runtime_scheduler_pr5.py`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/src/api/core/serverSentEvents.gen.ts`
- `docs/creative-phase-a-acceptance-checklist.md`
