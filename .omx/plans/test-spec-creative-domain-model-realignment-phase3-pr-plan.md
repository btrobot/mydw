# Test Spec: Creative Domain Model Realignment Phase 3 PR Decomposition

> Corresponding plan: `.omx/plans/prd-creative-domain-model-realignment-phase3-pr-plan.md`

---

## 1. Goal

验证 Phase 3 PR 计划满足冻结规划意图：

1. 每个 PR 都有明确变更范围
2. 每个 PR 都有明确测试方式
3. 每个 PR 都有明确回滚边界
4. 每个 PR 都有清晰依赖顺序
5. 整体序列完成 **version/publish freeze landing**
6. 整体序列不会回退到 Phase 2，也不会提前进入 Phase 4

---

## 2. Validation points

## 2.1 Global validation

- 所有 PR 必须可追溯到：
  - `.omx/plans/prd-creative-domain-model-realignment.md`
  - `.omx/plans/test-spec-creative-domain-model-realignment.md`
  - `.omx/plans/closeout-creative-domain-model-realignment-phase2.md`
- 所有 PR 必须显式包含：
  - goal
  - change scope
  - out-of-scope
  - test approach
  - rollback strategy
  - dependency / order
  - merge-safety note
- 整体序列必须显式说明：
  - `CreativeVersion` = adopted value / version result truth
  - `PublishPackage` = publish freeze truth
  - task = execution carrier / diagnostics surface
- 整体序列不得声称：
  - Phase 4 legacy retirement 已完成
  - task 仍然是作品定义权威来源

## 2.2 PR1 validation

- 仅覆盖 **backend/domain freeze contract landing**
- 必须明确落下：
  - version adopted values contract
  - publish package frozen values contract
  - API/schema/OpenAPI projection
- 不得吸收：
  - publish planner / task execution cutover
  - frontend review/version/publish surface 改造
  - legacy carrier retirement

## 2.3 PR2 validation

- 仅覆盖 **publish planning / publish-task execution cutover**
- 必须明确包括：
  - publish snapshot 从 freeze truth 构建
  - publish task 从 package/version truth 投影执行
  - task 退回 execution carrier
- 不得吸收：
  - 前端大规模语义改版
  - Phase 4 deprecation / removal
  - scheduler/runtime 全量重构

## 2.4 PR3 validation

- 仅覆盖 **frontend/evidence closeout**
- 必须明确包括：
  - review/version/publish surface 展示 adopted/frozen truth
  - diagnostics 与 publish package 的追溯关系
  - E2E/mocks/manual checklist 收口
- 必须明确避免：
  - 再次回到 task-first 叙事
  - 提前退役 legacy carriers
  - 重新打开 authoring semantics 改造

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
  - `follow future refactor`

### Phase-boundary review

- 确认文档明确区分：
  - **Phase 2 semantic-source cutover**
  - **Phase 3 freeze landing**
  - **Phase 4 legacy retirement**
- 若任一 PR 同时声称“冻结落地 + legacy 退役”，视为边界漂移

### Freeze-truth review

- 确认计划显式要求：
  - `CreativeVersion` 承接最终采用值
  - `PublishPackage` 承接发布冻结值
  - publish/task execution 消费 freeze truth
- 若计划仍允许：
  - `source_task.video_ids/...` 继续作为 publish freeze 主真相
  - task detail 继续充当最终业务定义源
  则视为不通过

### Proof-surface review

- 确认计划指向最小 must-cover surfaces：
  - `backend/models/__init__.py`
  - `backend/services/creative_version_service.py`
  - `backend/services/publish_planner_service.py`
  - `backend/services/task_service.py`
  - `frontend/src/features/creative/components/VersionPanel.tsx`
  - `frontend/e2e/creative-review/creative-review.spec.ts`
  - `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
  - `frontend/e2e/publish-pool/publish-pool.spec.ts`
  - `frontend/e2e/publish-cutover/publish-cutover.spec.ts`
  - `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`

---

## 4. Completion criteria

Phase 3 PR 计划仅在同时满足以下条件时可接受：

1. 每个 PR 都有独立 title / goal / scope / out-of-scope / test / rollback / dependency / merge-safety
2. PR1 完整承接 backend freeze contract landing
3. PR2 完整承接 publish execution 消费源切换
4. PR3 完整承接 frontend/evidence closeout
5. 整体序列明确把 task 降回 execution carrier
6. 整体序列明确禁止提前退休 legacy carriers
7. 计划可直接按顺序执行：**PR1 -> PR2 -> PR3**

---

## 5. Must-pass assertions for future execution

后续执行阶段至少应证明：

### 5.1 Backend / contract must-pass

1. `CreativeVersion` 可承接：
   - `actual_duration_seconds`
   - `final_product_name`
   - `final_copywriting_text`
   - 必要的最终封面/视频承接信息
2. `PublishPackage` 可承接：
   - frozen cover
   - frozen video
   - frozen product name
   - frozen copywriting
   - publish profile / constraints
3. API 可同时暴露 version truth 与 package truth

### 5.2 Execution must-pass

1. publish snapshot 以 version/package freeze truth 为主来源
2. publish task 是由 freeze truth 投影出来的执行载体
3. task diagnostics 仍可读，但不能替代 freeze truth

### 5.3 Frontend / E2E must-pass

1. `creative-review` 可见版本采用值
2. `creative-version-panel` 可区分：
   - creative definition
   - version result
   - publish package freeze
3. `publish-pool` / `publish-cutover` 可见 package freeze truth 与追溯关系
4. `task-diagnostics` 仍是诊断入口，而不是主业务说明页

---

## 6. Failure criteria

任一情况出现即视为 Phase 3 PR 计划不足：

1. PR1 没有结构化 version/package freeze contract
2. PR2 仍把 `source_task.*_ids` 当成 publish freeze 的主来源
3. PR3 仍要求用户通过 task 详情反推版本/发布真相
4. 任一 PR 把 Phase 4 legacy retirement 一并纳入
5. 任一 PR 没有清晰 rollback seam

---

## 7. One-line conclusion

> 这份 Phase 3 test spec 的核心不是证明“多了几个字段”，而是证明：Version 真正接住了最终采用值，PublishPackage 真正接住了发布冻结值，而 Task 真正退回到了执行与诊断层。
