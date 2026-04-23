# Plan: Creative Domain Model Realignment Phase 3 Executable PR Plan

## Scope

把 **Creative Domain Model Realignment - Phase 3** 拆成可执行、可评审、可回滚的 implementation PR 序列。

本计划建立在已经冻结的上游规划与 Phase 2 收口之上：

- PRD：`.omx/plans/prd-creative-domain-model-realignment.md`
- test spec：`.omx/plans/test-spec-creative-domain-model-realignment.md`
- context snapshot：`.omx/context/creative-domain-model-realignment-2026-04-22.md`
- Phase 2 PR 计划：`.omx/plans/prd-creative-domain-model-realignment-phase2-pr-plan.md`
- Phase 2 收口：`.omx/plans/closeout-creative-domain-model-realignment-phase2.md`

Phase 3 的冻结目标保持为原始 PRD 中定义的边界：

- 让 `CreativeVersion` 成为 **最终采用值 / 版本结果真相层**
- 让 `PublishPackage`（当前 repo 中的 `PackageRecord`/发布冻结承接层）成为 **发布冻结真相层**
- 让 publish planning / publish execution **消费冻结真相**，而不是继续把 task/resource collection 当作业务定义源
- 保留必要兼容桥接，但**不**在本阶段做 Phase 4 的 legacy contract retirement

## Repo-grounded context snapshot

- `backend/models/__init__.py` 中：
  - `CreativeVersion` 目前只承载 `version_no / version_type / title / parent_version_id`
  - `PackageRecord` 目前只承载 `package_status / manifest_json`
  - 这意味着“版本最终值”和“发布冻结四件套”还没有结构化落在领域模型里
- `backend/services/creative_version_service.py` 当前只负责建版本和挂 `PackageRecord`，还没有“采用值落版 / 冻结值落包”的 helper
- `backend/services/publish_planner_service.py` 虽已存在 `PublishExecutionSnapshot`，但 `_build_snapshot_payload()` 仍主要冻结：
  - `source_task.video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids`
  - `execution_view`
  - 也就是**发布快照仍主要从 task 视角冻结**
- `backend/services/task_service.py` 的 `clone_as_publish_task()` 仍以 “preserve collection truth” 为目标，直接复制 task 资源集合，说明 publish task 仍带有较强的旧执行语义来源
- `backend/schemas/__init__.py` 中：
  - `CreativeVersionSummaryResponse` 仅暴露版本基础信息
  - `PackageRecordResponse` 仅暴露 `package_status / manifest_json`
  - 还不足以表达 version adopted values / publish package frozen values
- `frontend/src/features/creative/components/VersionPanel.tsx` 目前已经把 version/package/task 的展示关系讲清楚，但仍以“版本记录 + package_record_id”级别为主，未展示冻结四件套真值
- `frontend/e2e/utils/creativeReviewMocks.ts` 和 `frontend/e2e/publish-cutover/publish-cutover.spec.ts` 当前也仍以 `package_record_id`、task 细节、pool/snapshot 诊断为主要测试承接层

## Phase 3 global constraints

Phase 3 是 **version/publish freeze landing**，不是：

- 不是重复 Phase 2 的 semantic-source cutover
- 不是直接退役 `video_ids` / `copywriting_ids` / `cover_ids` / `audio_ids` 等 legacy carriers
- 不是一次性重写整个 task runtime / scheduler
- 不是让 task UI 消失；它仍然保留为执行诊断层

Phase 3 必须同时满足以下约束：

1. `CreativeVersion` 要承接 **版本实际结果 + 最终采用值**
2. `PublishPackage` 要承接 **发布冻结四件套 + 发布约束**
3. publish/task execution 只能把 task 当作 **执行载体**，不能继续把 task collections 当成最终业务真相
4. 兼容桥接可以保留，但必须是 **freeze truth -> execution carrier** 的单向投影
5. Phase 3 完成后，应为 Phase 4 的 legacy retirement 提供清晰 handoff，而不是把 Phase 4 偷带进来

## RALPLAN-DR Summary

### Principles

1. Freeze truth 必须显式落在领域对象上，不能继续散落在 task/resource collections 里。
2. `CreativeVersion` 与 `PublishPackage` 必须分责：前者管“最终采用结果”，后者管“发布冻结真值”。
3. Task 在 Phase 3 后只能承接执行，不再承接作品业务定义。
4. 兼容桥接允许存在，但只能是从 freeze truth 向执行层投影，不能反向夺回权威。
5. 验证必须证明“冻结真相已经落地”，而不只是“文案换了”。

### Decision Drivers

1. 当前 repo 虽已有 version / package / publish snapshot 基础骨架，但关键 adopted/frozen values 仍未结构化落位。
2. `PublishExecutionSnapshot` 和 `clone_as_publish_task()` 仍然以 task collections 为主要冻结/复制来源，是最明显的 Phase 3 漂移点。
3. 前端 version/review/publish surface 已具备展示语义基础，适合在 backend freeze truth 落地后做收口，而无需再改回 authoring semantics。

### Viable Options

- **Option A：2 PR - backend freeze landing + frontend/execution follow-up**
  - Pro：
    - 交付路径最短
    - 文档叙事简单
  - Con：
    - 把“版本/发布冻结建模”和“执行消费切换”绑得过紧
    - 一旦 publish execution cutover 出问题，回滚面太大

- **Option B：3 PR - freeze contract, execution cutover, surface closeout（推荐）**
  - Pro：
    - 先锁定 version/package truth
    - 再单独切 publish/task execution 的消费来源
    - 最后做 UI/E2E/closeout 对齐，回滚清晰
  - Con：
    - 需要严格控制 PR2 不漂到 Phase 4
    - 需要在 PR1 就把 contract 设计得足够明确

- **Option C：4 PR - version truth、package truth、execution、frontend 各拆一条**
  - Pro：
    - 粒度最细
    - 适合强并行
  - Con：
    - 对当前 repo 实际复杂度来说偏碎
    - 计划/评审/合并成本高于收益

### Recommendation

选择 **Option B（3 PR）**。

核心张力是：

- Phase 3 必须真正把 freeze ownership 落地
- 但不能把 legacy retirement / runtime 重构一起吞进去

3 PR 的拆法最符合当前 fault lines：

1. 先把 **version/package contract** 锁死
2. 再把 **publish/task execution** 切到 freeze truth
3. 最后把 **review/version/publish UI 与验证证据** 对齐

## ADR

### Decision

采用 **3-PR 的 Phase 3 序列**：

1. backend/domain：`CreativeVersion` / `PublishPackage` 冻结契约落地
2. backend/runtime：publish planning / publish task 消费冻结真相
3. frontend/evidence：review/version/publish surface 对齐冻结真相并完成收口证据

### Drivers

- 当前 version/package 仍只有基础骨架，尚未承接最终值
- 当前 publish snapshot/task clone 仍以 task collection truth 为中心
- 前端已有 Phase 2 语义框架，适合在 freeze contract 落地后做低风险收口

### Alternatives considered

- **2 PR**： rejected，因为 contract landing 与 execution cutover 耦合过高
- **4 PR**： rejected，因为对当前代码面来说过度拆分

### Why chosen

该拆法最清楚地区分了：

- 领域真相落点
- 执行层消费来源
- 表层语义与验证证据

### Consequences

- PR1 会成为 Phase 3 的硬门禁：没有 adopted/frozen contract，就不允许后续 execution cutover
- PR2 必须把 publish/task execution 改成 **消费 freeze truth**，而不是继续复制 task collection truth
- PR3 必须证明 UI 与 E2E 已以版本/发布冻结为主叙事，但不进入 Phase 4 legacy retirement

### Follow-ups

- Phase 3 完成后，可进入 Phase 4 legacy retirement PR planning
- Phase 4 再处理旧字段 public contract / snapshot hash / legacy carriers 的正式退役

## Revised Phase 3 PR plan

### PR1 - backend(creative-phase3): land adopted-value and publish-package freeze contracts
**Type:** implementation

**Goal**

把 `CreativeVersion` 与 `PublishPackage` 的 freeze truth 结构化落到 backend domain / schema / API contract：

- `CreativeVersion`：承接版本结果与最终采用值
- `PublishPackage`：承接发布冻结四件套与发布约束

**Change scope**

- 为 `CreativeVersion` 增加明确的结果/采用值承接字段或等价结构化 contract，例如：
  - `actual_duration_seconds`
  - `final_product_name`
  - `final_copywriting_text`
  - 以及必要的封面/视频结果承接信息
- 为 `PackageRecord`（或等价 publish package contract）增加明确冻结字段或结构化 manifest 约束，例如：
  - frozen cover/video/product-name/copywriting
  - publish profile / platform constraints / freeze metadata
- 在 service 层补齐：
  - version adopted value 写入/更新 helper
  - publish package freeze helper
  - creative detail / version / publish 相关 projection builder
- 更新 schema / OpenAPI / contract tests，使 API 能明确暴露：
  - version adopted truth
  - package frozen truth
- 为后续 PR2 提供稳定 contract，但暂不切 publish execution 消费逻辑

**Explicitly out of scope**

- publish planner / scheduler 行为切换
- `clone_as_publish_task()` 的执行来源切换
- 前端页面/交互大范围改造
- legacy carriers retirement

**Likely files / artifacts**

- `backend/models/__init__.py`
- 新 migration（creative phase 3 contract landing）
- `backend/schemas/__init__.py`
- `backend/services/creative_version_service.py`
- `backend/services/creative_service.py`
- `backend/api/creative.py`
- `backend/tests/test_creative_versioning.py`
- `backend/tests/test_creative_workflow_contract.py`
- `backend/tests/test_openapi_contract_parity.py`
- 任何新增 publish-package contract test 文件

**Test approach**

- backend model/service tests：
  - prove `CreativeVersion` 能承接 adopted values
  - prove `PackageRecord` 能承接 publish frozen values
- API/contract/OpenAPI tests：
  - creative detail / version summary / package projection 正确暴露新 contract
- migration/idempotency tests：
  - 新增字段/结构可平滑引入
- negative assertions：
  - 不能只保留 `package_record_id` 而没有 freeze payload

**Rollback strategy**

- 回滚 migration + model/schema/service contract landing
- 保留 Phase 2 creative-first 语义切换成果不动
- 若 contract 无法稳定，禁止进入 PR2 execution cutover

**Dependency / order**

- merge first

**Merge safety notes**

- 必须让 adopted/frozen truth 可被读取、验证、投影
- 不能把“继续依赖 task collection truth”伪装成 package contract 已完成
- 若 API 仍只暴露 `package_record_id` 级别信息，则 PR1 不算完成

---

### PR2 - backend(creative-phase3): cut publish planning and publish-task execution to freeze truth
**Type:** implementation

**Goal**

把 publish planning / publish task execution 的消费源从 task collection truth 切到 version/package freeze truth。

**Change scope**

- 改造 `PublishPlannerService`：
  - `_build_snapshot_payload()` 不再以 `source_task.video_ids/copywriting_ids/...` 为主真相
  - 改为优先冻结：
    - `CreativeVersion` 的 adopted values
    - `PublishPackage` 的 frozen values
    - 必要的 publish profile / platform constraints
- 改造 `TaskService.clone_as_publish_task()` 或等价桥接逻辑：
  - publish task 由 freeze truth 投影生成执行载体
  - task 仍可保留执行所需 resource relations，但其来源需明确为 package freeze projection
- 对 publish pool / publish execution snapshot / task details 做必要 contract 对齐：
  - 让 snapshot 能追溯 package/version truth
  - 让 task diagnostics 说明“该 task 来源于哪个 publish package / frozen version”
- 补齐 publish planner / task semantics / runtime compatibility 测试

**Explicitly out of scope**

- 删除 task 诊断页面
- 大规模重写 scheduler/runtime
- 删除 legacy task collection relations
- Phase 4 的 legacy contract retirement

**Likely files / artifacts**

- `backend/services/publish_planner_service.py`
- `backend/services/task_service.py`
- `backend/services/task_execution_semantics.py`
- `backend/services/publish_pool_service.py`
- `backend/api/creative.py` / publish-related endpoints
- `backend/schemas/__init__.py`
- `backend/tests/test_task_creation_semantics.py`
- `backend/tests/test_work_driven_submit_idempotency.py`
- `backend/tests/test_composition_creative_writeback.py`
- 新增 publish planner / publish snapshot / publish task cutover tests

**Test approach**

- publish planner tests：
  - prove snapshot payload 以 version/package freeze truth 为主
- task execution bridge tests：
  - prove publish task 的执行资源来自 package freeze projection，而非 source task 反向夺权
- compatibility tests：
  - prove runtime 仍可执行
  - prove task diagnostics 仍可读
- regression tests：
  - publish pool / snapshot / task mapping 与 current creative version 保持可追溯关系

**Rollback strategy**

- 独立回滚 execution cutover，保留 PR1 已落地的 freeze contract
- 若 execution bridge 无法稳定，允许短期回退到旧执行桥接，但必须保留 Phase 3 contract，不得回退到 Phase 2 语义层

**Dependency / order**

- depends on PR1
- merge second

**Merge safety notes**

- 必须证明 publish execution 正在消费 freeze truth
- 若 snapshot payload 仍主要由 `source_task.*_ids` 组装，则 PR2 不算完成
- task 可以继续存在，但只能是 execution carrier，不能重新成为作品定义源

---

### PR3 - frontend(creative-phase3): align review/version/publish surfaces to frozen truth and close Phase 3 evidence
**Type:** implementation

**Goal**

让 review/version/publish/task-diagnostics 表层语义、E2E 与 closeout 证据对齐到 “version adopted truth + publish package frozen truth”。

**Change scope**

- 更新 creative detail / version panel / review 相关展示：
  - 明确显示版本最终采用值
  - 区分“当前作品定义”“当前版本结果”“当前发布冻结值”
- 更新 publish-pool / publish-cutover / diagnostics 展示：
  - 可见 package freeze truth
  - 可追溯 package -> publish task -> diagnostics 的关系
- 更新 E2E mocks / fixtures：
  - 不再只用 `package_record_id` + task detail 充当发布真相
  - mock 出明确的 version adopted values / package frozen values
- 补齐 targeted E2E/manual checklist，并形成 Phase 3 收口证据

**Explicitly out of scope**

- Phase 4 legacy field/public contract retirement
- authoring 主流程重做
- runtime scheduler 重构

**Likely files / artifacts**

- `frontend/src/features/creative/components/VersionPanel.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- creative review/publish related components under `frontend/src/features/creative/`
- `frontend/e2e/utils/creativeReviewMocks.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/publish-pool/publish-pool.spec.ts`
- `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`
- Phase 3 closeout doc（后续执行阶段产出）

**Test approach**

- targeted E2E：
  - review/version/publish surfaces show adopted/frozen truth
  - diagnostics 仍可达，但不伪装成业务真相页
- frontend typecheck + build
- manual checklist：
  - 用户可区分 creative definition / version result / publish package freeze
  - publish failure / task diagnostics 可追溯回 package freeze

**Rollback strategy**

- 独立回滚 UI/E2E 对齐层
- 保留 backend freeze contract 与 execution cutover
- 若前端语义无法稳定，禁止声称 Phase 3 closeout 完成

**Dependency / order**

- depends on PR2
- merge third

**Merge safety notes**

- 需要证明 UI 讲述的是 freeze truth，而不是 task-first 诊断故事
- 若前端仍需要用户从 task 详情反推发布真相，则 PR3 不算完成
- PR3 完成后可以进入 Phase 3 closeout / Phase 4 planning，但仍不得提前删除 legacy carriers

## Available-Agent-Types Roster

- `architect`：把关 version/package/task 分责、冻结契约与 Phase 3/4 边界
- `executor`：落实 backend contract、publish execution cutover、frontend 对齐
- `test-engineer`：设计 contract tests / E2E / manual checklist
- `verifier`：收集 closeout 证据，确认 Phase 3 exit criteria 满足

## Ralph follow-up staffing guidance

- `$ralph` 单 owner 路径建议：
  - `architect`（high）：PR1/PR2 的领域边界守门
  - `executor`（high）：主导实现
  - `test-engineer`（medium）：定义 Phase 3 验证矩阵
  - `verifier`（high）：每个 PR 合并前后做证据核验

建议按顺序执行：

1. PR1 freeze contract
2. PR2 execution cutover
3. PR3 surface + evidence closeout

## Team follow-up staffing guidance

- `$team` 并行路径建议：
  - lane A — `executor`（high）：backend model/schema/service/migration contract
  - lane B — `executor`（high）：publish planner / task bridge / publish snapshot cutover
  - lane C — `executor`（medium）+ `test-engineer`（medium）：frontend E2E mock/surface 对齐
  - lane D — `architect`（high）+ `verifier`（high）：phase-boundary 审核与 closeout evidence

## Suggested reasoning by lane

- PR1 backend freeze contract：`high`
- PR2 publish execution cutover：`high`
- PR3 frontend/evidence alignment：`medium`
- verification / closeout：`high`

## Team launch hints

- Ralph：
  - `$ralph 实现 creative-domain phase3 PR1`
  - `$ralph 实现 creative-domain phase3 PR2`
  - `$ralph 实现 creative-domain phase3 PR3`
- Team：
  - `$team 4 "deliver creative-domain phase3 freeze contract, execution cutover, and closeout evidence"`

## Team verification path

团队执行结束前，至少要证明：

1. backend contract 证据：
   - `CreativeVersion` 已承接 adopted values
   - `PublishPackage` 已承接 frozen values
2. execution evidence：
   - publish snapshot / publish task 明确消费 freeze truth
   - task 仅为 execution carrier
3. frontend evidence：
   - review/version/publish surfaces 可见 adopted/frozen truth
   - diagnostics 可追溯但不夺回主语义
4. phase-boundary evidence：
   - 未提前退休 legacy carriers
   - 未把 Phase 4 偷带进来

## Verification path

建议 Phase 3 执行期间至少覆盖：

### Backend baseline

```powershell
pytest `
  backend/tests/test_creative_versioning.py `
  backend/tests/test_creative_workflow_contract.py `
  backend/tests/test_openapi_contract_parity.py `
  backend/tests/test_task_creation_semantics.py `
  backend/tests/test_work_driven_submit_idempotency.py `
  backend/tests/test_composition_creative_writeback.py `
  -q
```

### Frontend targeted baseline

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e -- `
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

## PR description requirements

每个 Phase 3 PR 描述都应显式包含：

1. 对应 Phase：`Creative Domain Model Realignment / Phase 3`
2. 对应 PR：`PR1` / `PR2` / `PR3`
3. 本 PR 的 freeze boundary：
   - landed what
   - explicitly not landing what
4. 测试方式：
   - automated
   - manual
5. rollback seam
6. 对 Phase 4 的 handoff 影响

## One-line conclusion

> Phase 3 最合理的执行方式，不是继续围绕 task/resource collection 解释发布，而是先把 `CreativeVersion` 与 `PublishPackage` 的冻结真相落下，再让 publish execution 和前端语义围绕这层真相收口。
