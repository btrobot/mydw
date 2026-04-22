# Creative Domain Model Realignment Test Spec（作品域重整 Test Spec）

> Version: 2.1.0  
> Updated: 2026-04-22  
> Owner: Product / Verification Design / Codex  
> Status: Phase 0 PR2 frozen normative artifact

> 本文档用于把配套验证设计冻结为 **Phase 0 PR2 的正式 Test Spec**。  
> 它回答：**领域模型重整后，要靠哪些验证证明“新主语义成立、旧合同受控迁移、主链路没有被破坏”。**

> PR2 invariant lines:
> - docs-only
> - No runtime behavior changes
> - Implementation is out of scope
> - Future implementation PRs must cite the frozen Phase 0 artifacts

## 0. 在启动包中的角色

本 test spec 与以下文档一起使用：

- PRD：`.omx/plans/prd-creative-domain-model-realignment.md`
- 上下文快照：`.omx/context/creative-domain-model-realignment-2026-04-22.md`
- 风格参考：`docs/governance/next-phase-test-spec.md`

规则：

1. 先锁 PRD，再锁 test spec。
2. 若迁移阶段、验证面或 authoritative source 定义有变化，先改本文档，再允许后续执行计划更新。
3. 本文档是 **Phase 0 PR2 的规范性来源**；后续实现 PR 不得绕过本文档重写验证口径。
4. 本文档负责定义“如何证明”，不负责定义“先做哪个 PR”。
5. 本轮产出为 docs-only planning artifact，不是实现指令；不得将本文档视为代码变更已获批准。
6. 本文档不得重写 PR1 已冻结的领域边界；若边界发生变化，必须先回到 PR1/PRD 更新。

## 1. 适用范围

本 test spec 只覆盖：

- Creative 域边界重整
- 输入快照到输入编排的迁移合同
- 作品/版本/发布包/Task 的职责重画
- 兼容期 legacy contract 的保留与退役门禁

不覆盖：

- remote 新能力扩展
- local_ffmpeg V2 的具体实现方案
- 非本次主线的 UI/UX 全量重做

## 2. 验证目标

要证明的不是“字段改名了”，而是：

1. Creative 真正接住了业务定义责任。
2. 输入层从“去重集合”升级为“可审计的编排结构”。
3. 版本层与发布冻结层承担了明确的最终值责任。
4. Task 保持执行/诊断语义，不再回收作品定义。
5. 迁移期间新旧合同可以共存，但 authoritative source 明确且可验证。

## 3. 当前基线证据（repo-grounded）

当前仓库已有这些基线，后续验证设计必须基于它们升级，而不是绕开它们：

### 3.1 现有 backend / contract 基线

- `backend/tests/test_creative_workflow_contract.py`
- `backend/tests/test_openapi_contract_parity.py`
- `backend/tests/test_creative_input_snapshot_contract.py`
- `backend/tests/test_creative_schema_contract.py`
- `backend/tests/test_creative_versioning.py`
- `backend/tests/test_creative_task_mapping.py`
- `backend/tests/test_composition_creative_writeback.py`

### 3.2 现有 frontend / E2E 基线

- `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/publish-pool/publish-pool.spec.ts`
- `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`

### 3.3 当前被旧语义锁定的验证点

以下现状需要被显式迁移，而不是默默失效：

- schema 对 `video_ids` 等字段保序去重：`backend/schemas/__init__.py:605-625`
- snapshot/hash 按 ID 集合稳定：`backend/services/creative_service.py:816-835`
- 测试把“重复 ID 去重且 hash 稳定”视为正确：`backend/tests/test_creative_input_snapshot_contract.py:168-245`
- `local_ffmpeg V1` 仅支持单视频：`backend/tests/test_task_creation_semantics.py:70-84`

## 4. 必须覆盖的验证结构

## 4.1 Layer A — 领域 contract 验证

必须证明：

1. `Creative` 持有作品层业务定义字段。
2. `CreativeInputItem` 能表达重复实例、顺序、role、trim。
3. `CreativeVersion` 持有实际结果与最终采用值。
4. `PublishPackage` 持有发布冻结值。
5. `Task` 只承载执行/调度/诊断/执行结果。

建议验证类型：

- backend schema contract test
- service-level contract test
- API parity / serialization test

## 4.2 Layer B — 迁移兼容验证

必须证明：

1. 兼容期 legacy list/snapshot 字段仍可回读。
2. 新旧载体双写/映射关系可解释、可审计。
3. authoritative source 已切到新编排模型时，旧字段仅作为 compatibility carrier。
4. 旧“去重 + hash 稳定”合同被明确标注为：
   - phase-scoped
   - 可退役
   - 不再代表最终设计目标
5. **Phase 2+ fail gate**：任何新 authoring/UI/API surface 若仍把旧列表字段作为 canonical semantic source，视为未通过。

建议验证类型：

- backward-compat contract tests
- migration snapshot parity tests
- deprecation warning / docs parity checks

## 4.3 Layer C — 前端主语义验证

必须证明：

1. workbench/detail/review/version/publish 页面展示的是新作品语义，而不是旧素材篮语义。
2. 重复素材/编排顺序/最终采用值在 UI 上有可见表达或明确约束。
3. diagnostics 入口保留，但不得重新夺回主业务语义。

建议主要落点：

- `frontend/e2e/creative-workbench/`
- `frontend/e2e/creative-review/`
- `frontend/e2e/creative-version-panel/`
- `frontend/e2e/publish-pool/`
- `frontend/e2e/publish-cutover/`
- `frontend/e2e/task-diagnostics/`

## 4.4 Layer D — 执行层约束验证

必须证明：

1. 执行层限制被表述为“当前能力限制”，而不是“业务模型限制”。
2. `local_ffmpeg V1` 的单视频限制在兼容期内仍被正确守住。
3. 当编排模型先于执行层上线时，错误提示/约束文案与 contract 一致。

建议验证类型：

- task semantics tests
- manual negative-path verification
- targeted UI/E2E assertion for unsupported execution combinations

## 5. Must-cover checks（最小通过清单）

### 5.1 Backend / contract must-cover

至少应存在或补强以下验证：

1. **Creative brief contract**
   - `subject_product_*`
   - `main_copywriting_*`
   - `target_duration_seconds`
2. **CreativeInputItem contract**
   - 重复素材实例不去重
   - 顺序稳定
   - role/trim 独立
3. **CreativeVersion contract**
   - `actual_duration_seconds`
   - `final_product_name`
   - `final_copywriting_text`
4. **PublishPackage contract**
   - 冻结四件套与 publish profile/constraints
5. **Task mapping contract**
   - `final_video_duration` 为执行结果
   - Task 不再充当作品定义源

### 5.2 Migration must-cover

1. 旧 `video_ids`/`topic_ids` 等字段的兼容回读
2. 新旧 carrier 同步策略的 phase-specific 证明
3. 从旧 snapshot hash 到新 orchestration hash 的迁移口径
4. 明确一条测试证明：
   - 在新模型阶段，重复实例不会被 schema 自动吞掉

### 5.3 Frontend / E2E must-cover

1. `creative-main-entry`：Creative 仍是默认主入口
2. `creative-workbench`：列表/详情入口体现作品主语义
3. `creative-review`：审核对象围绕 version/result 而非 task 参数
4. `creative-version-panel`：可区分版本结果与作品定义
5. `publish-pool` / `publish-cutover`：最终冻结值可见且可追溯
6. `task-diagnostics`：Task 仍可用于诊断，但不伪装成业务主视图

### 5.4 Manual must-cover

至少人工核对：

1. 从主入口进入 Workbench 时，默认看到作品对象而非素材列表快照语义
2. 作品详情能区分：
   - 当前作品定义
   - 当前版本结果
   - 当前发布冻结值（若已形成）
3. 遇到执行层不支持的编排组合时，系统明确提示是执行层限制，而不是作品层不合法
4. diagnostics 入口仍显式可达，且刷新后状态可恢复

## 6. 与迁移阶段的映射

| 阶段 | 必须证明什么 | 最小验证建议 |
| --- | --- | --- |
| Phase 0 — 共识锁定 | PRD/test spec/ADR 一致，边界与口径稳定 | 文档审阅 + evidence trace |
| Phase 1 — 模型并行引入 | 新模型可建立，legacy 可回读，双写范围受控 | backend contract + migration parity |
| Phase 2 — 主语义切换 | UI/API 主流程转向编排模型；旧列表字段降级为 compatibility carrier only | targeted E2E + API parity + semantic-source assertions |
| Phase 3 — 版本/发布冻结落地 | 版本与发布包承接最终值 | version/publish contract + review/publish E2E |
| Phase 4 — 旧合同退役 | 去重集合合同不再是主验证口径；legacy carrier 不再承担新写入职责 | deprecation tests + full regression |

## 7. 推荐验证命令（planning recommendation）

以下为后续执行阶段建议的验证入口，不代表当前已执行：

### Backend baseline

```powershell
pytest `
  backend/tests/test_creative_workflow_contract.py `
  backend/tests/test_openapi_contract_parity.py `
  backend/tests/test_creative_input_snapshot_contract.py `
  backend/tests/test_creative_schema_contract.py `
  backend/tests/test_creative_task_mapping.py `
  backend/tests/test_creative_versioning.py `
  backend/tests/test_composition_creative_writeback.py `
  backend/tests/test_task_creation_semantics.py `
  -q
```

### Frontend targeted baseline

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e -- `
  e2e/auth-routing/auth-routing.spec.ts `
  e2e/creative-main-entry/creative-main-entry.spec.ts `
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

## 8. 通过标准

视为通过，必须同时满足：

1. 新领域模型的边界与不变量有对应自动化或人工验证项。
2. 迁移兼容与 authoritative source 切换有明确验证。
3. 前端主链路仍保持 Creative-first，不回退为 Task-first。
4. 执行层限制与业务模型边界未被混淆。
5. 每个迁移阶段都有明确的进入/退出验证口径。
6. Phase 2+ 不存在把旧列表字段继续当 canonical semantic source 的新增 surface。

## 9. 失败标准

以下任一情况视为未通过：

1. 新模型存在，但 UI/API 仍以旧集合快照为真实主语义。
2. 重复素材实例仍被 schema/service 默默去重。
3. 版本层与发布冻结层没有接住最终采用值。
4. Task 再次承担作品定义责任。
5. 执行层单视频限制被错误写成作品层规则。
6. Phase 2+ 仍允许旧列表字段作为新入口、新接口、新文档里的 canonical semantic source。

## 10. Verification recommendations

建议后续实现遵循：

1. **先 contract，后 UI**：先把 schema/service/serialization contract 锁住，再推动前端主语义切换。
2. **先 migration，后 deprecation**：先验证双轨兼容，再退役旧快照合同。
3. **每阶段都留手工链路**：因为“语义是否清晰”不能只靠自动化断言。
4. **证据要分层收集**：
   - contract log
   - API payload diff
   - E2E evidence
   - manual checklist

## 11. Staffing guidance（供 future $ralph / $team handoff）

本轮不进入 handoff 执行，但冻结未来验证编制建议如下：

### Available-Agent-Types Roster

- `architect`：验证仍在证明目标模型，而不是加固旧语义
- `executor`：补齐 backend/frontend 缺失测试与迁移支撑
- `test-engineer`：维护验证矩阵、suite mapping、manual checklist
- `verifier`：收集证据并做阶段退出审查

### Ralph verification guidance

- `test-engineer`（medium）：主导 test plan、suite mapping、manual checklist
- `executor`（high）：补齐 backend/frontend 缺失测试与迁移支撑
- `architect`（high）：确认测试仍在验证“目标模型”，不是在加固旧语义
- `verifier`（high）：收集最终通过证据并做阶段退出审查

### Team verification guidance

若走 `$team`：

- lane 1：`executor`（high）— backend contract/migration tests
- lane 2：`executor`（high）— frontend E2E/semantic assertions
- lane 3：`test-engineer`（medium）— verification matrix/manual scripts
- lane 4：`architect`（high）— final sign-off against PRD/test spec

### Team verification path

Team 必须在结束前提交：

1. backend 证据包：contract/migration/version/writeback suites 通过；
2. frontend 证据包：creative-main-entry/workbench/review/version/publish/task-diagnostics targeted E2E 通过；
3. manual 证据包：语义分层、执行层限制提示、diagnostics 可达性核对完成；
4. architect sign-off：确认 Phase N 的 semantic-source gate 成立；
5. verifier closeout：确认 evidence 对齐 PRD + test spec，且无 Phase 2+ semantic drift。

建议 launch hint（仅供后续）：

- `$team 4 "deliver creative domain model realignment with contract, e2e, and verification lanes"`

## 12. 一句话结论

> 这份 test spec 的核心不是证明“字段换了”，而是证明：Creative 真正接住了业务定义，输入真正升级成编排，Version/PublishPackage 真正承接了最终值，而 Task 真正退回执行层。
