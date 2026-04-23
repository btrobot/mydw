# Creative Domain Model Realignment Phase 3 Closeout / 作品域重整 Phase 3 收口

> Version: 1.0.0  
> Updated: 2026-04-23  
> Owner: Product / Domain Design / Codex  
> Status: Recorded closeout

> 目的：把 Creative Domain Model Realignment 的 **Phase 3** 从“3 个已完成实现 PR”收敛成一份正式 closeout，明确这一阶段已经完成的冻结真值落位、执行链路切换、表层语义收口，以及为什么现在可以正式退出 Phase 3 并进入 Phase 4 规划。

---

## 1. 一句话总结

> Phase 3 已完成 **版本采用值落位 + 发布包冻结真值落位 + publish/task execution 消费源切换 + 前端语义收口**：`CreativeVersion` 现在承接版本 adopted truth，`PublishPackage / PackageRecord` 现在承接 publish freeze truth，Task 页面明确退回执行 / 重试 / 诊断载体，Phase 4 才继续处理 legacy contract retirement。

---

## 2. 本阶段原始目标

- 让 `CreativeVersion` 成为版本结果与最终采用值的明确落点
- 让 `PublishPackage / PackageRecord` 成为发布冻结四件套与发布约束的明确落点
- 让 publish planning / publish execution / publish task 改为消费 version/package freeze truth
- 让 review / version / publish / task-diagnostics 表层叙事围绕“作品定义 / 版本采用值 / 发布冻结值”组织
- 保持 Task 为执行与诊断层，不再回收业务真值解释权
- 严格守住边界：**不在 Phase 3 内提前删除 legacy carriers，不在 Phase 3 内偷带 Phase 4 retirement**

关联文档：

- frozen PRD: `.omx/plans/prd-creative-domain-model-realignment.md`
- frozen test spec: `.omx/plans/test-spec-creative-domain-model-realignment.md`
- Phase 3 PR plan: `.omx/plans/prd-creative-domain-model-realignment-phase3-pr-plan.md`
- Phase 3 test spec: `.omx/plans/test-spec-creative-domain-model-realignment-phase3-pr-plan.md`
- Phase 2 closeout: `.omx/plans/closeout-creative-domain-model-realignment-phase2.md`

---

## 3. 实际交付结果

### 3.1 已完成

- **PR1：backend/domain freeze contract landing**
  - 提交：`5dd94af`
  - 标题：`Land explicit freeze contracts for version and publish package truth`
  - 结果：
    - `CreativeVersion` 明确承接版本 adopted truth / version result truth
    - `PackageRecord` 明确承接 publish package frozen truth
    - creative detail / version / publish contract 已能暴露 adopted/frozen fields，而不再只剩 ID 级别承接

- **PR2：publish execution cutover**
  - 提交：`59bf335`
  - 标题：`Cut publish execution over to version/package freeze truth`
  - 结果：
    - publish planner / publish snapshot / publish task execution 已切到 version/package freeze truth
    - task 执行载体继续保留，但来源已改为 freeze truth projection
    - task/source collection 不再充当 publish truth 的反向权威来源

- **PR3：frontend/evidence closeout**
  - 提交：`31b6215`
  - 标题：`Make frozen publish truth visible across creative surfaces`
  - 结果：
    - `CreativeDetail` / `VersionPanel` / publish surfaces 已明确区分：
      - 作品定义
      - 版本采用值
      - 发布包冻结值
      - 任务诊断入口
    - publish-pool / publish-cutover / task-diagnostics 文案与断言已对齐 freeze truth 叙事
    - E2E mocks 已补足 version adopted fields 与 package frozen fields，避免只用 task/package id 反推业务真值

### 3.2 未完成 / 明确不做

- 不在 Phase 3 内删除 legacy list/snapshot/public contract
- 不在 Phase 3 内完成 `video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids` 的正式 retirement
- 不在 Phase 3 内重写 scheduler/runtime 底座
- 不在 Phase 3 内移除 Task 诊断入口
- 不在 Phase 3 内把 Phase 4 的 public contract deprecation / deletion 偷带进来

### 3.3 与原计划相比的偏差

- **无实质 scope 偏差**
  - PR1 / PR2 / PR3 的落地顺序、边界与已批准的 Phase 3 PR plan 一致
- **PR3 采用“最小前端收口 + 证据强化”的方式完成**
  - 没有把 PR3 扩成新一轮 ownership 改造
  - 保持了 Phase 3 / Phase 4 边界清晰

---

## 4. 当前“系统真相”发生了什么变化

### 4.1 作品定义 / 版本结果 / 发布冻结的责任已经拆清

- `Creative` 继续承接作品定义：
  - brief
  - input orchestration
  - target duration
- `CreativeVersion` 现在承接版本结果与 adopted truth：
  - 当前版本最终采用的视频/封面/商品名/文案/实际时长
- `PublishPackage / PackageRecord` 现在承接 publish freeze truth：
  - 冻结后的四件套
  - 发布 profile / 平台约束

### 4.2 publish/task execution 的真值来源已经切换

- publish planner / publish snapshot 不再以 `source_task.*_ids` 作为主业务真值
- publish task 仍存在，但其执行输入现在来自 version/package freeze projection
- Task 不再承担“作品到底要发什么”的定义权，而只承担：
  - execution carrier
  - retry carrier
  - diagnostics carrier

### 4.3 前端叙事已经从 task-first 诊断故事切回 freeze truth

- `CreativeDetail` 讲的是作品定义、版本结果、发布冻结值之间的关系
- `VersionPanel` 讲的是：
  - 版本采用值
  - 发布包冻结值
- `publish-pool` / `publish-cutover` 讲的是 package freeze 与 package -> version -> task 的追溯关系
- `task-diagnostics` 保留可达性，但不再伪装成业务真值页

### 4.4 当前仍未变化的真相

- legacy carriers 仍在
- 旧 public contract 仍需在 Phase 4 决定 deprecate / delete 节奏
- Task 仍是必要运行时对象，但只应保留执行和诊断叙事

---

## 5. 验证总结

### 5.1 Phase 3 主验证证据

- `frontend npm run test:e2e -- e2e/creative-review/creative-review.spec.ts e2e/creative-version-panel/creative-version-panel.spec.ts e2e/publish-pool/publish-pool.spec.ts e2e/publish-cutover/publish-cutover.spec.ts e2e/task-diagnostics/task-diagnostics.spec.ts` → PASS（20 tests）
- `frontend npm run typecheck` → PASS
- `frontend npm run build` → PASS
- `frontend` TS / LSP diagnostics → 0 errors

### 5.2 本轮 closeout 追加的新鲜证据

- `frontend npm run test:e2e -- e2e/publish-cutover/publish-cutover.spec.ts` → PASS（2 tests）
- `frontend npm run build` → PASS
- stale Ralph hook 清理后二次核验：
  - `state_get_status(mode="ralph") => {"statuses":{}}`
  - `state_list_active() => {"active_modes":[]}`

### 5.3 验收结论

- Phase 3 的目标是 **freeze truth landing + execution cutover + surface closeout**
- 不是 legacy retirement
- 按这个定义，Phase 3 已达到退出门槛

---

## 6. 文档吸收情况

- [x] Phase 3 closeout 已正式记录到 `.omx/plans/`
- [x] 已同步更新 Creative 高可见度总结文档，补充当前真相附录
- [ ] frozen PRD / test spec 本轮未改写
- [ ] Phase 4 planning 文档尚未生成

当前不改写 frozen PRD / test spec 的原因：

- 它们仍然是有效的规范性来源
- 本轮收口的职责是记录“实现结果与阶段退出结论”，不是重写规范边界
- Phase 4 若改变 retirement 策略，应新增 Phase 4 planning artifact，而不是回写 Phase 0 的 frozen normative docs

---

## 7. Remaining risks / Residual risks

1. **legacy contract 仍可能被误用为当前真值**
   - 影响：后续实现可能再次从 task/source collection 反推发布真值
   - 当前处理：Phase 3 已把 truth source 明确迁到 version/package；Phase 4 仍需正式 retirement

2. **Task 诊断叙事可能再次上浮成业务叙事**
   - 影响：后续页面若偷懒，可能重新让用户从 task detail 反推业务定义
   - 当前处理：PR3 已显式把 task 降级为 execution/retry/diagnostics carrier

3. **Phase 4 边界可能被扩大成“顺手重构一切”**
   - 影响：legacy deletion、runtime cleanup、API deprecation 可能混成一次高风险大改
   - 当前处理：本 closeout 明确要求 Phase 4 继续保持以 retirement 为中心的最小切片

4. **OMX stop hook 曾被残留 Ralph state 干扰**
   - 影响：收口过程中可能出现“实际已结束但 hook 仍提示 active”的误报
   - 当前处理：已清理历史与当前 session 的残留 `ralph-state.json`，当前状态已回到 inactive

---

## 8. Backlog / Handoff

Phase 3 结束后，下一阶段焦点不再是“freeze truth 有没有落位”，而是：

- 旧 list/snapshot/public contract 的 retirement 策略
- API / schema / frontend 对 legacy carriers 的正式 deprecate/delete 节奏
- 删除 task-first 反向解释路径
- 保留必要兼容读取，但禁止继续作为新写入口或新叙事来源

推荐后续入口：

1. 先做 **Phase 4 PR planning**
2. 所有后续实现 PR 必须继续引用：
   - `.omx/plans/prd-creative-domain-model-realignment.md`
   - `.omx/plans/test-spec-creative-domain-model-realignment.md`
   - `.omx/plans/closeout-creative-domain-model-realignment-phase2.md`
   - `.omx/plans/closeout-creative-domain-model-realignment-phase3.md`

---

## 9. Exit decision / Phase 3 退出结论

> **Creative Domain Model Realignment 的 Phase 3 可以视为已正式收口。**

原因不是“所有历史 contract 都已删除”，而是：

- `CreativeVersion` 已接住 adopted truth
- `PublishPackage / PackageRecord` 已接住 publish freeze truth
- publish/task execution 已切到 freeze truth 消费路径
- review/version/publish/task-diagnostics 表层语义已完成对齐
- 没有把 Phase 4 retirement 偷带进 Phase 3

因此，当前状态已经满足：

> **退出 Phase 3，进入 Phase 4 规划。**
