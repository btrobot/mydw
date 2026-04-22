# Creative Domain Model Realignment Phase 2 Closeout / 作品域重整 Phase 2 收口

> Version: 1.0.0  
> Updated: 2026-04-23  
> Owner: Product / Domain Design / Codex  
> Status: Recorded closeout

> 目的：把 Creative Domain Model Realignment 的 **Phase 2** 从“3 个已完成实现 PR”收敛成一份正式 closeout，明确这一阶段已经完成的语义切换、保留的兼容边界、验证证据，以及为什么现在可以正式退出 Phase 2 并进入 Phase 3 规划。

---

## 1. 一句话总结

> Phase 2 已完成 **语义源切换 + 主创作流切换 + 下游语义收口**：`CreativeInputItem + creative brief` 已成为作品创作的主语义源，legacy list/snapshot 已降级为兼容投影，review / version / publish / task-diagnostics 也已对齐到新的 creative-first 模型；但 **最终冻结真值与 publish-freeze ownership 仍明确留在 Phase 3**。

---

## 2. 本阶段原始目标

- 把作品创建/编辑主链路从 legacy `video_ids / copywriting_ids / ...` 迁到 **creative brief + input orchestration**
- 让 `CreativeInputItem` 成为 authoring / UI / API 的 **canonical semantic source**
- 将 legacy list/snapshot 语义降级为 **compatibility carrier / read-only projection**
- 让 workbench / detail / review / version / publish surfaces 描述新的 creative-first 语义
- 保持 task / diagnostics 为次级执行诊断位
- 将执行限制表述为 **capability limits**，而不是业务模型限制

关联文档：

- context snapshot: `.omx/context/creative-domain-model-realignment-2026-04-22.md`
- frozen PRD: `.omx/plans/prd-creative-domain-model-realignment.md`
- frozen test spec: `.omx/plans/test-spec-creative-domain-model-realignment.md`
- Phase 2 PR plan: `.omx/plans/prd-creative-domain-model-realignment-phase2-pr-plan.md`
- Phase 2 test spec: `.omx/plans/test-spec-creative-domain-model-realignment-phase2-pr-plan.md`

---

## 3. 实际交付结果

### 3.1 已完成

- **PR1：backend/API semantic-source gate**
  - 提交：`a2955bf`
  - 标题：`Make creative API reject legacy write semantics in Phase 2`
  - 结果：
    - API 写入语义已切换到 `input_items + brief fields`
    - legacy list/snapshot 仅保留兼容读回/投影角色
    - Phase 2 已显式拒绝继续把 legacy write semantics 当作权威写入口

- **PR2：workbench/detail 主创作流切换**
  - 提交：`d873662`
  - 标题：`Shift creative authoring to brief-led workbench/detail flow`
  - 结果：
    - workbench / detail 主链路已围绕作品 brief、素材编排、目标时长组织
    - 主页面不再以 legacy list 作为作者心智中心
    - diagnostics/task 保持可达，但下沉为次级位置

- **PR3：review/version/publish/task-diagnostics 语义收口**
  - 提交：`6007d8b`
  - 标题：`Clarify downstream creative semantics before Phase 3 publish-freeze work`
  - 结果：
    - version / review surfaces 已明确区分：
      - 作品定义
      - 版本结果
      - 发布侧承接语义
    - publish-pool / publish-cutover 文案已切到“发布侧候选 / 能力边界”语义
    - task surfaces 已进一步明确为执行诊断位
    - 相关 E2E 断言已补齐

### 3.2 未完成 / 明确不做

- 不在 Phase 2 内完成 `CreativeVersion / PublishPackage` 的最终冻结真值落位
- 不在 Phase 2 内让 task execution 只消费 publish-freeze truth
- 不在 Phase 2 内移除 compatibility carriers
- 不在 Phase 2 内做 publish-package ownership / freeze ownership 的最终迁移
- 不在 Phase 2 内做 runtime 执行引擎重构

### 3.3 与原计划相比的偏差

- **无实质 scope 偏差**
  - PR1 / PR2 / PR3 的边界与 Phase 2 PR plan 基本一致
- **PR3 采用“前端语义对齐 + 定向 E2E 锁定”的最小实现方式**
  - 没有把 PR3 扩成新的数据 ownership 改造
  - 保持了 Phase 2 / Phase 3 的边界清晰

---

## 4. 当前“系统真相”发生了什么变化

### 4.1 Authoring / API 真相变化

- Phase 2 之后，作品 authoring 的主语义源是：
  - `input_items`
  - `subject_product_*`
  - `main_copywriting_*`
  - `target_duration_seconds`
- legacy `video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids`
  - 仍存在
  - 但已经不是主 authoring truth
  - 仅作为兼容投影与读回 carrier 存活

### 4.2 前端主流程真相变化

- Workbench 已成为 creative-first 主入口
- Detail 已围绕“作品 brief 与素材编排”展开
- 当前版本不再被表达成“任务拼装结果说明页”，而是“作品定义派生出的版本结果”
- Review 结论不再暗示“任务定义被批准”，而是“版本结果被批准”

### 4.3 下游语义真相变化

- publish-pool / publish-cutover 不再被表达成“业务模型本身不成立”
- 当前不支持的组合，被明确表述为：
  - 当前执行引擎能力未覆盖
  - 当前发布承接存在能力边界
- task list / task detail / diagnostics 不再承担业务定义主语义，只承担执行诊断角色

### 4.4 当前仍未变化的真相

- `CreativeVersion` / `PublishPackage` 还不是最终唯一冻结真值
- task execution 尚未切换为只消费 publish-freeze truth
- compatibility projection 尚未退休

---

## 5. 验证总结

### 5.1 PR1 / PR2 / PR3 关键验证结果

- PR1：后端/API semantic-source gate 已落地
- PR2：frontend main authoring flow 已切换到 brief-led semantics
- PR3：downstream semantic alignment 已落地，且未越界到 Phase 3

### 5.2 最新 closeout 证据（以 PR3 收口为准）

- `frontend npm run typecheck` → PASS
- `frontend npm run build` → PASS
- Playwright Chromium 定向回归 → PASS（10 tests）
  - `e2e/creative-review/creative-review.spec.ts`
  - `e2e/creative-version-panel/creative-version-panel.spec.ts`
  - `e2e/publish-pool/publish-pool.spec.ts`
  - `e2e/publish-cutover/publish-cutover.spec.ts`
  - `e2e/task-diagnostics/task-diagnostics.spec.ts`
- frontend TS / LSP diagnostics → 0 errors

### 5.3 本阶段的验收结论

- Phase 2 的目标是 **semantic-source cutover**
- 不是 publish-freeze landing
- 按这个定义，Phase 2 已达成验收门槛

---

## 6. 文档吸收情况

- [x] Phase 2 PR plan 已执行完成
- [x] Phase 2 test spec 已被实现结果回链验证
- [x] Phase 2 closeout 已正式记录到 `.omx/plans/`
- [ ] 暂未将本轮 closeout 吸收到更高可见度的 `docs/` 正式文档

当前不吸收到 `docs/` 的原因：

- 本轮首先收的是 **phase implementation truth**
- 当前最直接的 authority 仍是 `.omx/plans/` 这一组 phase planning / closeout 文档
- 待 Phase 3 主线明确后，再决定是否做更高层 current-truth 文档吸收

---

## 7. Remaining risks / Residual risks

1. **Phase 3 ownership 迁移尚未开始**
   - 影响：代码与文档中仍会短期并存“semantic source 已切换”与“freeze truth 尚未落位”的双层状态
   - 当前处理：通过 PR3 文案与 closeout 明确这不是未完成 bug，而是故意保留的 phase boundary

2. **compatibility carriers 仍可能被误用为新实现入口**
   - 影响：后续实现若偷懒，可能再次把 legacy projection 当主语义使用
   - 当前处理：PR1 已在 API 侧建立写入门禁；Phase 3 仍需继续做退休与真值收束

3. **引擎能力限制与业务模型限制仍可能被重新混淆**
   - 影响：后续产品/实现文案可能重新把执行能力问题解释成业务定义无效
   - 当前处理：PR3 已把相关表述拉回 capability-limit framing，但后续仍需在 Phase 3 保持一致

---

## 8. Backlog / Handoff

Phase 2 结束后，下一阶段焦点不再是“semantic-source cutover”，而是：

- `CreativeVersion / PublishPackage` 的冻结真值落位
- publish-freeze ownership 明确化
- task execution 与 publish truth 的单向消费关系
- compatibility carriers 的有计划退休

推荐后续入口：

1. 先做 **Phase 3 PR planning**
2. 所有后续实现 PR 必须继续引用：
   - `.omx/plans/prd-creative-domain-model-realignment.md`
   - `.omx/plans/test-spec-creative-domain-model-realignment.md`
   - `.omx/plans/closeout-creative-domain-model-realignment-phase2.md`

---

## 9. Exit decision / Phase 2 退出结论

> **Creative Domain Model Realignment 的 Phase 2 可以视为已正式收口。**

原因不是“作品域已经彻底重构完成”，而是：

- semantic source 已切换完成
- 主创作流已切换完成
- 下游 review / version / publish / diagnostics 语义已完成对齐
- compatibility 仍被明确控制在保留边界内
- 没有把 Phase 3 的 publish-freeze ownership 迁移偷带进来

因此，当前状态已经满足：

> **退出 Phase 2，进入 Phase 3 规划 / 选主线。**

