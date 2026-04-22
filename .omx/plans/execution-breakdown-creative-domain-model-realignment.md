# Creative Domain Model Realignment Execution Breakdown（作品域重整 Execution Breakdown）

> Version: 2.1.0  
> Updated: 2026-04-22  
> Owner: Product / Delivery Design / Codex  
> Status: Phase 0 PR3 frozen handoff artifact

> 本文档用于把 **Phase 0 PR1 + PR2** 冻结后的结果，收敛为 **Phase 0 PR3 的执行拆解与 handoff pack**。  
> 它回答：**后续实现 PR 应按什么顺序推进、每条实现线的出入口在哪里、以及如何回链到已冻结的 PRD / Test Spec。**

> PR3 invariant lines:
> - docs-only
> - No runtime behavior changes
> - Implementation is out of scope
> - Future implementation PRs must cite the frozen Phase 0 artifacts

## 0. 在启动包中的角色

本文件与以下冻结文档配套使用：

- PR1 领域真相：`.omx/plans/prd-creative-domain-model-realignment.md`
- PR2 验证真相：`.omx/plans/test-spec-creative-domain-model-realignment.md`
- PR 计划来源：`.omx/plans/prd-creative-domain-model-realignment-phase0-pr-plan.md`
- PR 计划验证来源：`.omx/plans/test-spec-creative-domain-model-realignment-phase0-pr-plan.md`
- 上下文快照：`.omx/context/creative-domain-model-realignment-2026-04-22.md`

使用规则：

1. 本文档只负责 **execution breakdown / traceability / handoff packaging**，不重写领域规则，也不重写验证规则。
2. 若发现缺失的领域边界、迁移门禁或验证口径，先回到 PR1 或 PR2 更新；不得在 PR3 补写。
3. 每个后续实现 PR 都必须显式引用本文档，以及对应的 PR1 / PR2 章节。
4. 本文档可以定义“先做什么、谁来验证、退出证明是什么”，但不能单独发明新的 pass/fail gate。
5. 本轮产出为 docs-only planning artifact，不是实现指令；不得将本文档视为代码变更已获批准。

## 1. 冻结来源总览（source-of-truth bundle）

### 1.1 PR1 负责冻结什么

后续实现必须以 PR1 的以下章节为领域真相来源：

- `§6 领域边界与推荐模型`
- `§7 关键业务不变量`
- `§9 分阶段迁移路径`
- `§10 验收标准（testable）`
- `§13 后续 staffing guidance`
- `§14 ADR（execution handoff contract）`

### 1.2 PR2 负责冻结什么

后续实现必须以 PR2 的以下章节为验证真相来源：

- `§4 必须覆盖的验证结构（Layer A-D）`
- `§5 Must-cover checks`
- `§6 与迁移阶段的映射`
- `§8 通过标准`
- `§9 失败标准`
- `§11 Staffing guidance`

### 1.3 PR3 只负责包装什么

PR3 只包装以下内容：

- 后续实现顺序
- 实现 PR 的 traceability 回链
- implementation-readiness checklist
- future implementation PR description requirements
- future `$ralph` / `$team` launch guidance

## 2. 执行模型（非规范新增，只做顺序包装）

推荐包装方式：

> **单主线推进 + 分阶段 implementation PR sequence**

原因不是新增规则，而是对 PR1 `§9 分阶段迁移路径` 与 PR2 `§6 与迁移阶段的映射` 做顺序包装：

1. 先引入并行模型与兼容回读，再切主语义；
2. 先切作品/编排主语义，再落版本/发布冻结；
3. 最后退役旧 snapshot/list contract。

## 3. 后续实现 PR sequence（execution-ready packaging）

| 实现 PR | 目标 | change scope（包装后范围） | primary verification owner | exit proof（必须回链的冻结来源） |
| --- | --- | --- | --- | --- |
| IP1 — Parallel model introduction | 引入 `CreativeInputItem / CreativeVersion / PublishPackage` 的并行模型入口，并保留 legacy 回读与受控双写 | backend schema / service / serialization 的增量引入；不得提前把旧 carrier 直接删掉 | `test-engineer` | PR1 `§9 Phase 1` 退出条件 + PR2 `§4.1` / `§4.2` / `§5.1` / `§5.2` / `§6 Phase 1` |
| IP2 — Semantic-source cutover | 把 authoring / UI / API 主语义切到编排模型，旧列表字段降级为 compatibility carrier | API surface、Workbench / Detail / Review / Publish 主链路语义切换；不得把旧字段继续当 canonical semantic source | `test-engineer` | PR1 `§9 Phase 2` 退出条件 + PR2 `§4.3` / `§5.3` / `§8` / `§9` |
| IP3 — Version and publish freeze landing | 让版本层与发布包接住最终值与四件套冻结 | version result、publish freeze、Task 读取冻结结果执行；不得把最终值责任重新落回 Task 或 Material | `verifier` | PR1 `§6.4` / `§6.5` / `§6.6` + `§9 Phase 3` + PR2 `§4.1` / `§5.1` / `§5.3` / `§5.4` / `§6 Phase 3` |
| IP4 — Legacy contract retirement | 退役旧 `video_ids` / snapshot hash 主合同，完成 orchestration hash 切换 | deprecation、compatibility 收口、旧写语义退役；不得保留“无限期双轨” | `verifier` | PR1 `§9 Phase 4` + PR2 `§4.2` / `§5.2` / `§6 Phase 4` / `§8` / `§9` |

说明：

- 上表的顺序来自 PR1 `§9 分阶段迁移路径`，不是 PR3 自行发明。
- 上表的 exit proof 只打包 PR1 / PR2 已写明的退出条件、验证层次与 fail gate。
- 若某条实现 PR 发现必须改动上游边界或 gate，流程应回到 PR1 / PR2，而不是修改本表掩盖偏差。

## 4. Traceability matrix（PR1 / PR2 -> 后续实现线）

| handoff item | PR1 source | PR2 source | 默认实现线 |
| --- | --- | --- | --- |
| `Material / Creative / CreativeInputItem / CreativeVersion / PublishPackage / Task` 责任分层 | PR1 `§6` | PR2 `§4.1` / `§5.1` | IP1 / IP3 |
| 顺序、重复实例、role、trim 的编排表达 | PR1 `§6.3` / `§7.1-§7.3` | PR2 `§4.1` / `§5.1.2` / `§5.2.4` | IP1 / IP2 |
| `target_duration_seconds` vs `actual_duration_seconds` vs `Task.final_video_duration` 的层次区分 | PR1 `§6.4-§6.6` / `§7.4-§7.6` | PR2 `§5.1.1` / `§5.1.3` / `§5.1.5` | IP1 / IP3 |
| 商品名 / 文案的来源值、采用值、版本值、发布冻结值分层 | PR1 `§7.7` / `§6.4` / `§6.5` | PR2 `§4.1` / `§5.1.1` / `§5.1.3` / `§5.1.4` | IP3 |
| legacy 双轨的允许范围、切主语义阶段、退役阶段 | PR1 `§9 Phase 1-4` | PR2 `§4.2` / `§6` / `§8` / `§9` | IP1 / IP2 / IP4 |
| Phase 2+ 不得继续把旧列表字段当 canonical semantic source | PR1 `§9 Phase 2` | PR2 `§4.2.5` / `§8.6` / `§9.6` | IP2 / IP4 |
| 执行层限制必须表述为 capability limit，而不是业务模型限制 | PR1 `§11 风险与缓解` / `§12 具体验证建议` | PR2 `§4.4` / `§5.4` / `§8.4` / `§9.5` | IP2 / IP3 |
| future staffing / sign-off / evidence closeout | PR1 `§13` | PR2 `§11` | 全部实现 PR |

## 5. 实现 lane packaging（供 future `$ralph` / `$team` 使用）

以下 lane 只是把 PR1 `§13` 与 PR2 `§11` 的分工建议整理成可执行展示：

### 5.1 单 owner `$ralph` follow-up

- implementation lane：`executor`
  - 负责当前 phase 的 backend / API / frontend 变更落地
- evidence lane：`test-engineer` + `verifier`
  - 负责 suite mapping、manual checklist、evidence closeout
- final sign-off lane：`architect`
  - 负责确认没有越界重写 PR1 / PR2

### 5.2 并行 `$team` follow-up

- lane A：`executor`（backend contract / migration）
- lane B：`executor`（frontend semantics / publish surfaces）
- lane C：`test-engineer`（verification matrix / manual scripts）
- lane D：`verifier`（evidence package / phase-exit closeout）
- final sign-off：`architect`

说明：

- lane 角色来自 PR1 `§13` 与 PR2 `§11`，PR3 只做归并展示。
- 若某 phase 规模较小，可合并 lane；但 architect sign-off 不可省略。

## 6. Implementation-readiness checklist

后续实现 PR 在开工前至少自检：

- [ ] 已阅读 PR1：`.omx/plans/prd-creative-domain-model-realignment.md`
- [ ] 已阅读 PR2：`.omx/plans/test-spec-creative-domain-model-realignment.md`
- [ ] 已阅读本文档：`.omx/plans/execution-breakdown-creative-domain-model-realignment.md`
- [ ] 已明确当前工作属于 `IP1 / IP2 / IP3 / IP4` 中的哪一条
- [ ] 已列出会引用的 PR1 / PR2 具体章节
- [ ] 已明确 change scope 与 out-of-scope，不把 phase 邻近内容偷偷并入
- [ ] 已明确 primary verification owner
- [ ] 已明确 exit proof 对应哪条 phase exit / pass-fail gate
- [ ] 若需要改 frozen rule，已先停止实现 PR，回到 PR1 或 PR2 发 docs PR

## 7. Future implementation PR description requirements

后续实现 PR 的描述至少应包含：

1. **Phase / sequence item**
   - 明确写出本 PR 对应 `IP1 / IP2 / IP3 / IP4`
2. **Frozen source citations**
   - 至少引用 1 个 PR1 章节 + 1 个 PR2 章节
3. **Change scope**
   - 说明这次只实现哪一层，不实现哪一层
4. **Verification owner**
   - 说明谁负责主验证：`test-engineer` 或 `verifier`
5. **Exit proof**
   - 说明要对齐的 phase exit / pass-fail gate
6. **Rollback / compatibility note**
   - 说明若回滚，本 PR 影响哪一段兼容策略或哪一段主语义切换
7. **Frozen-rule check**
   - 明确声明：本 PR 未重写 frozen rule；若需要重写，将先发 docs PR

## 8. Launch guidance（仅供后续，不代表当前执行）

### 8.1 Ralph launch hint

适合单 owner、阶段清晰、需要严格证据闭环时：

- `$ralph 实现 creative-domain IP1`
- `$ralph 实现 creative-domain IP2`
- `$ralph 实现 creative-domain IP3`
- `$ralph 实现 creative-domain IP4`

### 8.2 Team launch hint

适合 backend / frontend / verification 可以并行时：

- `$team 4 "implement creative domain model realignment with backend, frontend, verification, and architect lanes"`

使用前提：

- 先在 PR 描述中引用 PR1 / PR2 / PR3 的具体章节；
- 不得把 launch hint 当成新的领域规则或验证规则来源。

## 9. 一句话结论

> PR3 的职责不是再定义“作品域应该怎么做”，而是把 PR1 的领域真相与 PR2 的验证真相，包装成一个可直接启动后续实现 PR 的 execution-ready handoff pack。
