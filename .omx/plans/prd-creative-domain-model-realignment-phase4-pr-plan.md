# Plan: Creative Domain Model Realignment Phase 4 Executable PR Plan

## Scope

把 **Creative Domain Model Realignment - Phase 4** 拆成可执行、可评审、可回滚的 implementation PR 序列。

本计划建立在以下已冻结/已完成材料之上：

- PRD：`.omx/plans/prd-creative-domain-model-realignment.md`
- test spec：`.omx/plans/test-spec-creative-domain-model-realignment.md`
- context snapshot：`.omx/context/creative-domain-model-realignment-2026-04-22.md`
- Phase 3 PR plan：`.omx/plans/prd-creative-domain-model-realignment-phase3-pr-plan.md`
- Phase 3 closeout：`.omx/plans/closeout-creative-domain-model-realignment-phase3.md`

Phase 4 的目标保持为原始 PRD 中定义的 **legacy contract retirement**：

- 旧 list/snapshot/public contract 不再承担主语义或主写入职责
- 旧 snapshot hash 不再作为 creative authoring 的 canonical hash
- `input_items` / version adopted truth / publish package freeze truth 继续作为唯一主线
- 允许保留受控的历史读取或迁移观察能力，但不允许继续保留“兼容名义下的长期双轨”

---

## Repo-grounded current snapshot

当前 repo 仍保留明显的 Phase 1/2 兼容残留，这些残留正是 Phase 4 的主要收口对象：

- `backend/schemas/__init__.py`
  - `CreativeCreateRequest` / `CreativeUpdateRequest` 仍保留 `video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids` compatibility fields
  - `CreativeDetailResponse` / `CreativeWorkbenchItemResponse` 仍暴露 `input_snapshot`
  - `CreativeInputSnapshotResponse` 仍暴露 legacy list + `snapshot_hash`
- `backend/services/creative_service.py`
  - `_build_input_snapshot_response()` 仍持续构建 compatibility snapshot
  - `_apply_input_snapshot()` 仍 dual-write：
    - `creative.input_video_ids / ... / input_snapshot_hash`
    - `creative_input_snapshots.*`
  - `_extract_legacy_input_snapshot()` 仍允许 fallback 到 legacy columns / snapshot row
  - eligibility / expected task inputs / submit path 仍显式消费 `input_snapshot`
  - `_build_snapshot_hash()` 仍以 legacy list carriers 组装 hash
- `backend/tests/test_creative_input_snapshot_contract.py`
  - 仍锁定 migration 031 / 032 存在
  - 仍锁定 dual-write sync
  - 仍锁定 legacy fallback read + recreate snapshot row
- `frontend/src/features/creative/creativeAuthoring.ts`
  - 当 `input_items` 为空时，仍会从 `input_snapshot` synthesize fallback authoring items
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
  - 默认仍构建 `input_snapshot` fallback
  - 页面仍展示“兼容 Snapshot Hash”
- `frontend/src/api/types.gen.ts`
  - 仍公开 `input_snapshot`、legacy list fields、`snapshot_hash`

这说明：

1. **主语义已经切换，但兼容承载层尚未退休**
2. **backend / frontend / generated SDK / tests 仍共同加固了 legacy carriers**
3. **Phase 4 不能只改一层；否则会留下“代码不再依赖，但 contract 与测试仍继续冻结旧语义”的漂移**

---

## Phase 4 global constraints

Phase 4 是 **legacy contract retirement**，不是：

- 不是重新打开作品 / 版本 / 发布包的领域边界讨论
- 不是重写 publish scheduler / task runtime
- 不是重新设计 AIClip authoring flow
- 不是顺手做新的 product UX 主线

Phase 4 必须同时满足以下约束：

1. `input_items` 继续是 creative authoring 的唯一 canonical source
2. version adopted truth / publish package frozen truth 不得回退到 task-first 解释
3. legacy carriers 的退休必须 **先断主写入与主读取，再做物理删除**
4. destructive schema cleanup 只能放在最后，且必须建立在前序 PR 已证明没有 live dependency
5. 历史数据可读性必须有明确策略：要么前置 backfill，要么显式 one-way adapter；不能靠“希望没有老数据”过关
6. generated SDK / frontend / docs / tests 必须一起退休旧 contract，避免只退 backend 不退外围

---

## RALPLAN-DR Summary（deliberate）

### Principles

1. **Canonical-first**：Phase 4 只允许围绕 `input_items` 与 freeze truth 收口，不允许恢复 legacy field 的业务权威地位。
2. **Retire in stages**：先引入明确 canonical contract，再切断 dual-write/fallback，最后才做 destructive cleanup。
3. **Historical safety**：任何删除都必须先证明历史数据可读/可迁移/可审计。
4. **SDK/UI parity**：backend contract 退休与 frontend/generated type 收口必须同步推进。
5. **Evidence over intent**：Phase 4 完成的证明必须来自 migration tests、OpenAPI parity、E2E、search audit，而不是口头声明“现在没人用了”。

### Decision Drivers

1. **兼容残留仍被代码和测试共同加固**：不只是 schema 字段存在，service、frontend、generated SDK、tests 都还在消费它。
2. **这是高风险迁移**：涉及 public contract、历史数据、dual-write retirement、可能的 destructive schema cleanup。
3. **Phase 3 已明确完成 freeze truth landing**：因此 Phase 4 可以聚焦 retirement，而不需要再做 ownership 落位。

### Viable Options

- **Option A：2 PR - 一次性退休 contract + schema deletion**
  - Pro：
    - 交付最快
    - 叙事简单
  - Con：
    - public contract、generated SDK、frontend、migration cleanup 全部绑在一起
    - 任一历史数据或 fallback 漏洞都会让回滚面过大
    - 不符合“先断依赖、再删承载”的安全顺序

- **Option B：3 PR - canonical contract / runtime retirement / frontend+cleanup**
  - Pro：
    - 比 2 PR 更可控
    - 可先做 contract，再做逻辑退休
  - Con：
    - destructive schema deletion 仍容易被混进 frontend cleanup
    - docs/tests/physical deletion 仍有机会被压缩成最后一个过胖 PR

- **Option C：4 PR - canonical contract, dual-write retirement, frontend/SDK cleanup, physical cleanup+closeout（推荐）**
  - Pro：
    - 与当前 repo 的 fault lines 最匹配
    - 可以把“风险最大的 destructive deletion”单独放到最后
    - 每个 PR 都有清晰 rollback seam
  - Con：
    - 计划/评审成本略高
    - 需要纪律性地禁止 PR2 / PR3 偷带 PR4 删除动作

### Recommendation

选择 **Option C（4 PR）**。

核心张力是：

- Phase 4 必须真正退休 legacy carriers
- 但退休不能靠一次性大删，而必须按 **contract → logic → frontend/SDK → storage cleanup** 的顺序推进

### Pre-mortem（3 scenarios）

1. **历史数据读挂**
   - 场景：旧 creative 仍只依赖 `input_snapshot` / legacy columns，PR2/PR4 后详情页或提交流程读不到输入
   - 缓解：
     - 在 PR1/PR2 先建立 canonical projection/backfill 方案
     - 以旧 schema fixture 做 migration/integration 测试

2. **SDK / frontend 编译通过但运行叙事漂移**
   - 场景：backend 已去掉 `input_snapshot` 主语义，但 frontend 仍从 fallback synthesize input items 或展示“兼容 Snapshot Hash”
   - 缓解：
     - PR3 必须显式清掉 fallback authoring path
     - E2E 必须证明 creative surfaces 不再需要 legacy snapshot 叙事

3. **schema 删除过早导致回滚困难**
   - 场景：PR4 删除 `creative_items.input_*` / `creative_input_snapshots` 后，才发现某条诊断路径或迁移脚本仍依赖它
   - 缓解：
     - PR4 前必须完成 rg/search audit + targeted regression + historical fixtures
     - PR4 只在 PR1~PR3 证据完备后合入

### Expanded test plan

- **Unit**
  - creative orchestration projection/hash builder
  - legacy deprecation guards
  - migration helper / backfill helper
- **Integration**
  - old-row fixtures upgrade into canonical read model
  - create / patch / get / submit-composition 不再依赖 `input_snapshot`
  - OpenAPI / generated contract parity
- **E2E**
  - creative-workbench
  - creative-review
  - creative-version-panel
  - publish-pool
  - publish-cutover
  - task-diagnostics
- **Observability / audit**
  - repo-wide search audit：`input_snapshot|input_snapshot_hash|input_video_ids|CreativeInputSnapshot`
  - migration/retirement ledger or closeout evidence capturing what was removed and what remains

---

## ADR

### Decision

采用 **4-PR 的 Phase 4 序列**：

1. backend/contract：引入 canonical orchestration projection/hash，并把 legacy carriers 降为显式 deprecating compatibility surface
2. backend/runtime：退休 creative snapshot dual-write 与 fallback 逻辑
3. frontend/sdk：移除 creative surfaces 对 legacy snapshot 的消费与展示
4. backend/docs：完成物理 cleanup、测试退休、closeout 证据

### Drivers

- backend / frontend / tests / generated SDK 仍共同冻结 legacy carriers
- public contract retirement 与 physical deletion 风险不同，不应绑在一个 PR
- Phase 3 已收口 freeze truth，Phase 4 可以专注于 retirement discipline

### Alternatives considered

- **2 PR**：rejected，因为 contract retirement 与 destructive cleanup 耦合过高
- **3 PR**：rejected，因为 frontend/SDK cleanup 与 storage cleanup 仍容易相互污染

### Why chosen

该拆法最清楚地区分了：

- 哪些是 **新 canonical contract**
- 哪些是 **旧逻辑退休**
- 哪些是 **表层消费方退役**
- 哪些是 **最后的物理删除与收口证据**

### Consequences

- PR1 会成为 Phase 4 的硬门禁：没有明确 canonical orchestration projection/hash，就不能退休旧 contract
- PR2 必须先断 live dependency，不能提前删表删列
- PR3 必须证明 frontend/generated SDK 已不再依赖 legacy snapshot
- PR4 必须在 destructive cleanup 前做完 search audit、historical fixture、rollback seam 说明

### Follow-ups

- Phase 4 完成后，再决定是否需要单独做 post-retirement cleanup / docs archive pass
- 若历史数据规模或回填复杂度超预期，可在 PR1/PR2 之间插入单独 migration RFC，但不得跳过 gate

---

## Revised Phase 4 PR plan

### PR1 - backend(creative-phase4): land canonical orchestration projection/hash and deprecation gate
**Type:** implementation

**Goal**

把 creative authoring 的 canonical read contract 明确固定在 `input_items + input_profile_id + orchestration-derived metadata` 上，并把 legacy list/snapshot carriers 明确降级为 deprecating compatibility surface。

**Change scope**

- 在 creative read contract 中引入稳定的 canonical orchestration projection / hash（字段名在 PR1 固定），用于替代 `snapshot_hash` 的主语义地位
- 明确 `CreativeDetailResponse` / `CreativeWorkbenchItemResponse` 的 canonical input surface：
  - `input_items`
  - canonical profile reference
  - canonical orchestration-derived metadata
- 将 `input_snapshot` 与 legacy list fields 标注为：
  - deprecated / compatibility-only / read-only
  - 不再作为主 contract 叙事
- 更新 API doc / OpenAPI / generated schema annotations，使“谁是 canonical、谁是 compatibility”可从 contract 直接读出
- 如需过渡，可保留 `input_snapshot` response shape，但必须明确它是由 canonical input 机械投影得到，而非权威来源

**Explicitly out of scope**

- 退休 dual-write
- 删除 legacy columns / snapshot table
- frontend fallback cleanup
- physical schema deletion

**Likely files / artifacts**

- `backend/schemas/__init__.py`
- `backend/api/creative.py`
- `backend/services/creative_service.py`
- `backend/tests/test_creative_schema_contract.py`
- `backend/tests/test_creative_workflow_contract.py`
- `backend/tests/test_openapi_contract_parity.py`
- `frontend/src/api/types.gen.ts`（若 OpenAPI 生成产物需要随 contract 变化同步）

**Test approach**

- contract tests：
  - prove canonical orchestration surface exists and is documented
  - prove `input_snapshot` is no longer described as canonical
- OpenAPI parity / generated schema checks：
  - prove deprecation metadata and canonical descriptions are visible
- negative assertions：
  - no new schema text may describe `video_ids / ... / snapshot_hash` as canonical authoring semantics

**Rollback strategy**

- 回滚 canonical contract landing
- 保持 Phase 3 已完成的 freeze truth 与 execution cutover 不动
- 在 PR1 未稳定前，不允许进入 PR2

**Dependency / order**

- merge first

**Merge safety notes**

- PR1 必须建立新的 canonical contract；不能只是把旧 `input_snapshot` 换个描述继续沿用
- 若 code / OpenAPI 仍只能通过 `input_snapshot` 表达 creative input truth，则 PR1 不算完成

---

### PR2 - backend(creative-phase4): retire creative snapshot dual-write and legacy fallback logic
**Type:** implementation

**Goal**

把 creative authoring / eligibility / submit path 从 legacy snapshot dual-write 与 legacy fallback 中切出来，使 live runtime 只依赖 canonical orchestration source。

**Change scope**

- 重构 `CreativeService` 相关路径，使以下逻辑不再以 `input_snapshot` 为 live dependency：
  - eligibility projection
  - expected task inputs
  - submit composition
  - detail/list projection builder
- 退休或降级：
  - `_apply_input_snapshot()`
  - `_extract_legacy_input_snapshot()`
  - `_build_snapshot_hash()` 的 canonical 地位
- 停止对以下字段/表做 live dual-write（或将其限制为临时 one-way compat projection）：
  - `creative_items.input_video_ids / input_copywriting_ids / input_cover_ids / input_audio_ids / input_topic_ids / input_snapshot_hash`
  - `creative_input_snapshots`
- 建立历史数据 read / backfill / migration 方案，证明旧 row 不会在 PR2 后变成不可读

**Explicitly out of scope**

- frontend authoring fallback 删除
- generated SDK / page copy cleanup
- physical drop columns / drop table

**Likely files / artifacts**

- `backend/services/creative_service.py`
- `backend/models/__init__.py`（如需调整 ORM 字段使用策略）
- 新 migration / backfill helper（如需要）
- `backend/tests/test_creative_input_snapshot_contract.py`（拆分/替换为 retirement-oriented tests）
- `backend/tests/test_creative_workflow_contract.py`
- `backend/tests/test_composition_creative_writeback.py`
- `backend/tests/test_task_creation_semantics.py`

**Test approach**

- integration tests：
  - prove create / patch / get / submit-composition 不再依赖 legacy snapshot live state
- historical fixture tests：
  - prove old rows can still be upgraded/read through canonical path
- negative assertions：
  - prove no new/updated creative requires snapshot-row recreation to remain readable
- runtime regression：
  - publish / task mapping remains intact after legacy fallback retirement

**Rollback strategy**

- 独立回滚 runtime retirement
- 保留 PR1 canonical contract
- 若历史数据安全无法证明，禁止进入 PR3/PR4

**Dependency / order**

- depends on PR1
- merge second

**Merge safety notes**

- PR2 的核心是“断 live dependency”，不是“立刻做大删除”
- 若 `CreativeService` 仍必须先读 `input_snapshot` 才能组装 canonical authoring state，则 PR2 不算完成

---

### PR3 - frontend(creative-phase4): remove legacy snapshot fallback from creative surfaces and SDK usage
**Type:** implementation

**Goal**

让 creative frontend surfaces 与 generated SDK 不再依赖 legacy snapshot contract，并移除默认 UI 中的 compatibility narration。

**Change scope**

- 更新 `creativeAuthoring.ts`：
  - `getCreativeAuthoringInputItems()` 不再从 `input_snapshot` synthesize fallback authoring items
- 更新 `CreativeDetail.tsx` / related creative surfaces：
  - 不再把 `input_snapshot` 作为默认主展示块
  - 移除默认界面的“兼容 Snapshot Hash”叙事
- 更新 generated API types / hooks / types alias：
  - creative surfaces 默认消费 canonical orchestration contract
- 补齐 E2E / manual checklist：
  - creative detail/workbench/review/version/publish/task-diagnostics 在无 legacy snapshot 叙事下仍成立

**Explicitly out of scope**

- 删除 backend schema 物理字段
- drop legacy tables / columns
- scheduler/runtime 重构

**Likely files / artifacts**

- `frontend/src/features/creative/creativeAuthoring.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/types/creative.ts`
- `frontend/src/api/types.gen.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/publish-pool/publish-pool.spec.ts`
- `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`

**Test approach**

- targeted E2E：
  - authoring/detail no longer require snapshot fallback
  - version/publish/task-diagnostics still narrate from canonical truth + freeze truth
- frontend typecheck + build
- generated SDK parity check（若 repo 当前生成流程要求）
- search audit：
  - creative frontend default path no longer references `snapshot_hash` / `input_snapshot` as primary UI semantics

**Rollback strategy**

- 独立回滚 frontend/SDK cleanup
- 保留 PR1/PR2 backend retirement work
- 若 frontend 仍存在 hidden dependency，则禁止进入 PR4 destructive cleanup

**Dependency / order**

- depends on PR2
- merge third

**Merge safety notes**

- PR3 必须证明 creative frontend 可在不依赖 legacy snapshot fallback 的情况下工作
- 若页面仍需从 `input_snapshot` 反推主输入编排，则 PR3 不算完成

---

### PR4 - backend(creative-phase4): remove legacy snapshot storage/contracts and record Phase 4 closeout
**Type:** implementation

**Goal**

在 PR1~PR3 已证明无 live dependency 的前提下，完成 legacy snapshot storage / tests / docs 的物理退休，并形成 Phase 4 closeout 证据。

**Change scope**

- 删除或正式退休以下承载层：
  - `creative_items.input_video_ids / input_copywriting_ids / input_cover_ids / input_audio_ids / input_topic_ids / input_snapshot_hash`
  - `ix_creative_items_input_snapshot_hash`
  - `creative_input_snapshots`
  - `ix_creative_input_snapshots_snapshot_hash`
- 删除/替换仍以 dual-write/fallback 为成功定义的测试与文档
- 补充 Phase 4 closeout 文档，明确：
  - 哪些 contract 已退休
  - 哪些历史读取策略仍保留
  - 哪些搜索/验证证据证明无活跃依赖

**Explicitly out of scope**

- 新 product flow
- 新 runtime capability
- 重新设计 creative domain

**Likely files / artifacts**

- 新 migration（drop legacy creative snapshot carriers）
- `backend/models/__init__.py`
- `backend/tests/test_creative_input_snapshot_contract.py`（删除或替换）
- `backend/tests/test_creative_schema_contract.py`
- `backend/tests/test_openapi_contract_parity.py`
- `.omx/plans/closeout-creative-domain-model-realignment-phase4.md`

**Test approach**

- migration tests：
  - prove destructive cleanup is idempotent
  - prove upgraded DB remains readable/usable
- search audit：
  - no live code path depends on removed fields/tables
- regression baseline：
  - creative create/get/update/submit + version/publish surfaces remain green
- closeout evidence：
  - rg/search proof + automated suites + UTF-8/readback on closeout doc

**Rollback strategy**

- PR4 only merges after PR1~PR3 evidence is fresh
- if deletion introduces unexpected dependency, revert PR4 independently and restore previous compat storage layer from canonical source/backups
- do not couple PR4 with unrelated refactors

**Dependency / order**

- depends on PR3
- merge fourth

**Merge safety notes**

- PR4 是 destructive cleanup；没有 fresh search audit + migration evidence 就不允许合入
- 若 repo 中仍存在活跃代码或 frontend contract 消费被删除字段，则 PR4 不算完成

---

## Available-Agent-Types Roster

- `architect`：把关 retirement boundary、historical-data safety、Phase 4 / post-Phase4 边界
- `executor`：落实 backend contract、runtime retirement、frontend cleanup、migration cleanup
- `test-engineer`：设计 migration fixtures、OpenAPI parity、E2E、search-audit gates
- `verifier`：收集 closeout 证据，确认 destructive cleanup 前后的 claim 都有证明

## Ralph follow-up staffing guidance

- `$ralph` 单 owner 路径建议：
  - `architect`（high）：PR1/PR4 边界与 deletion gate 守门
  - `executor`（high）：主导 PR1~PR4 实施
  - `test-engineer`（high）：设计 deliberate-mode 验证矩阵
  - `verifier`（high）：每个 PR 合并前后核验证据

建议按顺序执行：

1. PR1 canonical contract / deprecation gate
2. PR2 dual-write + fallback retirement
3. PR3 frontend/SDK cleanup
4. PR4 physical cleanup + Phase 4 closeout

## Team follow-up staffing guidance

- `$team` 并行路径建议：
  - lane A — `executor`（high）：backend contract / OpenAPI / canonical projection
  - lane B — `executor`（high）：creative runtime retirement / migration helpers
  - lane C — `executor`（medium）+ `test-engineer`（high）：frontend/generated SDK/E2E cleanup
  - lane D — `architect`（high）+ `verifier`（high）：historical-data audit、deletion gate、closeout evidence

## Suggested reasoning by lane

- PR1 canonical contract / deprecation：`high`
- PR2 runtime retirement / historical safety：`high`
- PR3 frontend/SDK cleanup：`medium`
- PR4 destructive cleanup / closeout：`high`

## Team launch hints

- Ralph：
  - `$ralph 实现 creative-domain phase4 PR1`
  - `$ralph 实现 creative-domain phase4 PR2`
  - `$ralph 实现 creative-domain phase4 PR3`
  - `$ralph 实现 creative-domain phase4 PR4`
- Team：
  - `$team 4 "deliver creative-domain phase4 legacy contract retirement with canonical contract, runtime retirement, frontend cleanup, and storage closeout"`

## Team verification path

团队执行结束前，至少要证明：

1. **contract evidence**
   - canonical orchestration contract 已固定
   - legacy snapshot/list fields 已降级为 deprecated/compat-only 或被移除
2. **runtime evidence**
   - create / patch / get / submit-composition 不再依赖 `input_snapshot` live path
   - version/package freeze truth 不受 retirement 影响
3. **frontend evidence**
   - creative surfaces 不再依赖 snapshot fallback
   - generated SDK 与 backend contract 同步
4. **deletion evidence**
   - rg/search audit 证明 repo 不再消费被删除字段/表
   - migration / historical fixture 证明 destructive cleanup 安全

## Verification path

建议 Phase 4 执行期间至少覆盖：

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

## PR description requirements

每个 Phase 4 PR 描述都应显式包含：

1. 对应 Phase：`Creative Domain Model Realignment / Phase 4`
2. 对应 PR：`PR1` / `PR2` / `PR3` / `PR4`
3. 本 PR 的 retirement boundary：
   - retired what
   - explicitly not retiring what
4. historical-data handling
5. test approach
6. rollback seam
7. 对后续 PR 的 gating implication

## One-line conclusion

> Phase 4 最合理的执行方式，不是“一次性大删旧字段”，而是先固定 canonical orchestration contract，再退休 dual-write/fallback，再清理 frontend/SDK，最后在证据完备时做物理删除与收口。
