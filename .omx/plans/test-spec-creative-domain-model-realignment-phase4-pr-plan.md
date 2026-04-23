# Test Spec: Creative Domain Model Realignment Phase 4 PR Decomposition

> Corresponding plan: `.omx/plans/prd-creative-domain-model-realignment-phase4-pr-plan.md`

---

## 1. Goal

验证 Phase 4 PR 计划满足 legacy contract retirement 的规划意图：

1. 每个 PR 都有明确变更范围
2. 每个 PR 都有明确测试方式
3. 每个 PR 都有明确回滚边界
4. 每个 PR 都有明确依赖顺序
5. 整体序列完成 **legacy contract retirement**
6. 整体序列不会回退到 Phase 3 freeze truth，也不会把 destructive cleanup 提前到无证据状态

---

## 2. Validation points

## 2.1 Global validation

- 所有 PR 必须可追溯到：
  - `.omx/plans/prd-creative-domain-model-realignment.md`
  - `.omx/plans/test-spec-creative-domain-model-realignment.md`
  - `.omx/plans/closeout-creative-domain-model-realignment-phase3.md`
- 所有 PR 必须显式包含：
  - goal
  - change scope
  - out-of-scope
  - test approach
  - rollback strategy
  - dependency / order
  - merge-safety note
- 整体序列必须显式说明：
  - `input_items` 仍然是 creative authoring canonical source
  - version adopted truth / publish package frozen truth 不回退
  - legacy snapshot/list carriers 的退休按 `contract -> logic -> frontend/sdk -> storage cleanup` 顺序进行
- 整体序列不得声称：
  - “只要 frontend 不用了，backend storage 就可以直接删”
  - “Phase 4 顺手完成 runtime/product 新主线”

## 2.2 PR1 validation

- 仅覆盖 **canonical orchestration contract / deprecation gate**
- 必须明确落下：
  - canonical orchestration projection/hash
  - deprecated/compat-only status for legacy snapshot/list fields
  - OpenAPI / schema / SDK-visible documentation
- 不得吸收：
  - dual-write retirement
  - legacy fallback 删除
  - frontend fallback cleanup
  - physical schema deletion

## 2.3 PR2 validation

- 仅覆盖 **runtime dual-write/fallback retirement**
- 必须明确包括：
  - creative read/write/eligibility/submit path 不再 live-consume `input_snapshot`
  - 停止 legacy dual-write 或将其严格降级为 one-way compat projection
  - historical row handling / backfill strategy
- 不得吸收：
  - frontend page contract cleanup
  - generated SDK 主路径 cleanup
  - drop columns / drop tables

## 2.4 PR3 validation

- 仅覆盖 **frontend/generated SDK retirement**
- 必须明确包括：
  - creative surfaces 不再从 `input_snapshot` synthesize authoring state
  - 默认 UI 不再展示 compatibility snapshot hash narration
  - generated SDK / E2E / manual checklist 对齐 canonical contract
- 必须明确避免：
  - backend destructive cleanup
  - 新 product flow 扩张
  - 恢复 task-first 或 snapshot-first 叙事

## 2.5 PR4 validation

- 仅覆盖 **physical cleanup + closeout evidence**
- 必须明确包括：
  - drop legacy columns / indexes / snapshot table（若此前 PR 已证明无 live dependency）
  - replace/remove tests that still freeze dual-write/fallback behavior
  - Phase 4 closeout artifact
- 必须明确避免：
  - 新 runtime capability
  - 大范围 unrelated refactor
  - 在没有 search audit / historical fixture 证据时做删除

---

## 3. Review method

### Documentation review

- 检查每个 PR 段落是否都具备：
  - concrete scope
  - concrete tests
  - concrete rollback
  - concrete dependency
- 拒绝以下占位写法：
  - `TBD`
  - `later`
  - `implementation decides`
  - `delete if safe`

### Retirement-boundary review

- 确认文档明确区分：
  - **Phase 3 = freeze truth landing**
  - **Phase 4 = legacy contract retirement**
  - **post-Phase4 = optional cleanup / archive / follow-up**
- 若任一 PR 同时声称“runtime retirement + physical deletion + frontend rewrite”而没有清晰边界，视为 plan 过胖

### Historical-data review

- 确认计划显式要求：
  - 历史 row fixture
  - migration / backfill strategy
  - destructive cleanup 前的 safety proof
- 若计划允许：
  - 直接删除 `creative_input_snapshots`
  - 直接删除 `creative_items.input_*`
  - 但没有 historical-data handling
  则视为不通过

### SDK / frontend parity review

- 确认计划显式要求：
  - generated SDK 随 contract 同步
  - creative frontend 不再依赖 snapshot fallback
  - 默认 UI 不再展示 compatibility snapshot hash 叙事
- 若 frontend 仍被允许“先不清理，后面再说”，则视为不通过

### Search-audit review

- 确认计划要求在 PR4 前执行 repo-wide search audit
- 若没有明确的 grep/rg 审计路径，就不能证明 destructive cleanup 安全

---

## 4. Completion criteria

Phase 4 PR 计划仅在同时满足以下条件时可接受：

1. 每个 PR 都有独立 title / goal / scope / out-of-scope / test / rollback / dependency / merge-safety
2. PR1 完整承接 canonical orchestration contract + deprecation gate
3. PR2 完整承接 dual-write/fallback retirement
4. PR3 完整承接 frontend/generated SDK cleanup
5. PR4 完整承接 physical cleanup + closeout
6. 整体序列明确要求 destructive cleanup 只能最后进行
7. 计划可直接按顺序执行：**PR1 -> PR2 -> PR3 -> PR4**

---

## 5. Must-pass assertions for future execution

### 5.1 Backend / contract must-pass

1. creative canonical input source = `input_items`（而不是 `input_snapshot`）
2. canonical orchestration hash/metadata 存在且可被读/验证
3. OpenAPI / schema 不再把 `video_ids / ... / snapshot_hash` 描述为 canonical authoring semantics
4. version/package freeze truth 不受 Phase 4 retirement 影响

### 5.2 Runtime / migration must-pass

1. create / patch / get / submit-composition 不再 live-consume `input_snapshot`
2. dual-write/fallback 退休后，旧 row 仍可被解释/升级/读取
3. destructive cleanup 前已有明确 search audit + historical fixture evidence
4. PR4 删除后，repo 中不存在活跃代码路径引用被删字段/表

### 5.3 Frontend / SDK must-pass

1. `creativeAuthoring` 不再从 `input_snapshot` synthesize input items
2. `CreativeDetail` 默认页面不再展示 compatibility snapshot hash
3. generated SDK / types 与 backend contract 同步
4. creative workbench / review / version / publish / task-diagnostics E2E 仍通过

### 5.4 Observability / audit must-pass

1. 需要至少一条 search-audit 证明：
   - `input_snapshot`
   - `input_snapshot_hash`
   - `input_video_ids / ...`
   - `CreativeInputSnapshot`
   的剩余引用符合当前阶段边界
2. Phase 4 closeout 必须记录：
   - retired what
   - intentionally kept what
   - why safe

---

## 6. Failure criteria

任一情况出现即视为 Phase 4 PR 计划不足：

1. PR1 没有建立明确 canonical orchestration contract
2. PR2 退休 dual-write 时仍允许 live path 依赖 `input_snapshot`
3. PR3 仍要求 creative frontend 从 snapshot fallback 反推主输入编排
4. PR4 在没有 historical-data proof / search audit 的情况下直接删表删列
5. 任一 PR 混入 freeze truth ownership 改造或 product 新主线
6. 任一 PR 没有清晰 rollback seam

---

## 7. Suggested verification coverage

### Backend baseline

```powershell
pytest `
  backend/tests/test_creative_schema_contract.py `
  backend/tests/test_creative_workflow_contract.py `
  backend/tests/test_openapi_contract_parity.py `
  backend/tests/test_creative_versioning.py `
  backend/tests/test_composition_creative_writeback.py `
  backend/tests/test_task_creation_semantics.py `
  -q
```

### Frontend targeted baseline

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e -- `
  e2e/creative-workbench/creative-workbench.spec.ts `
  e2e/creative-review/creative-review.spec.ts `
  e2e/creative-version-panel/creative-version-panel.spec.ts `
  e2e/publish-pool/publish-pool.spec.ts `
  e2e/publish-cutover/publish-cutover.spec.ts `
  e2e/task-diagnostics/task-diagnostics.spec.ts
```

### Build gate

```powershell
cd E:\ais\mydw\frontend
npm run typecheck
npm run build
```

### Search-audit gate

```powershell
rg -n "input_snapshot|input_snapshot_hash|input_video_ids|input_copywriting_ids|input_cover_ids|input_audio_ids|input_topic_ids|CreativeInputSnapshot" backend frontend
```

---

## 8. One-line conclusion

> 这份 Phase 4 test spec 的核心，不是证明“删掉了几个字段”，而是证明：repo 已经先完成 canonical 化、再完成逻辑退休、再完成 frontend/SDK 退役，最后才安全地做了物理删除与收口。
