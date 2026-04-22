# PR-4 Slice A 收口门禁锁定与验证范围冻结收口件

> Version: 1.0.0
> Updated: 2026-04-22
> Owner: Tech Lead / Codex
> Status: Recorded slice closeout

> 目的：把 `PR-4 / Slice A：收口门禁锁定与验证范围冻结` 的实际交付、当前真相、验证结果与剩余风险落成一份正式收口件。  
> 这份文档回答的不是“Slice A 原本想做什么”，而是：**Slice A 最终实际锁定了哪些门禁、哪些文档成为执行 authority、哪些事情明确留给 Slice B / Slice C。**

---

## 1. 一句话总结

> Slice A 已把 `PR-4` 从“只在 execution breakdown 里占位的下一步”收口成“有正式 plan、有 OMX planning artifacts、有阶段 closeout gate、有最小修复政策、可直接交给 `$ralph` / `$team` 接手执行”的当前 authority。

---

## 2. 本 Slice 原始目标

- 把 PR-4 的 stage closeout gate 写清
- 冻结 PR-4 的验证范围与最小修复政策
- 让 PR-4 不再只是一个高层占位标题，而是可执行的 focused plan
- 同步正式 docs 与 OMX planning artifacts，使后续执行不再依赖聊天上下文

关联规划：

- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
- `.omx/plans/archive/prd-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/test-spec-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/slice-plan-pr4-regression-and-stage-closeout.md`

---

## 3. 实际交付结果

### 3.1 已完成

- **PR-4 正式计划已落盘**
  - 新增 `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
  - 明确写清：
    - 为什么 PR-4 是“阶段收口”而不是“继续扩张”
    - stage closeout gate 的构成
    - 最小修复政策
    - Slice A / B / C 的顺序与边界

- **OMX planning artifacts 已补齐**
  - `.omx/plans/archive/prd-pr4-regression-and-stage-closeout.md`
  - `.omx/plans/archive/test-spec-pr4-regression-and-stage-closeout.md`
  - `.omx/plans/archive/slice-plan-pr4-regression-and-stage-closeout.md`
  - 这意味着后续 `$ralph` / `$team` 执行时，不需要重新起草 PR-4 的 PRD、test spec、slice plan

- **阶段 closeout gate 已冻结**
  - `docs/governance/next-phase-test-spec.md` 已明确 PR-4 的通过口径：
    - backend / contract baseline
    - frontend typecheck / build
    - frontend stage closeout E2E suite
    - 手工主链路
    - closeout authority 文档

- **执行入口已同步**
  - `docs/governance/next-phase-execution-breakdown.md` 已从“PR-4 占位说明”升级为“带 planning 入口、验收口径、切片顺序”的执行入口
  - 当前已明确：
    - Slice A = 锁门禁
    - Slice B = 跑回归 / 吸收最小修复
    - Slice C = 正式 closeout / handoff

- **治理导航已同步**
  - `docs/governance/README.md` 已纳入 PR-4 planning 入口
  - `docs/governance/inventory/inventory-ledger.md` 已纳入 PR-4 规划工件

### 3.2 明确没做

- **没跑 backend / frontend 回归**
  - 这些属于 Slice B 的执行范围，不属于 Slice A

- **没产生 PR-4 整体 closeout**
  - PR-4 正式 closeout 文档属于 Slice C

- **没吸收任何代码修复**
  - Slice A 只锁门禁与文档 authority，不处理真实回归问题

- **没扩大验证范围**
  - 没把 PR-4 扩成新的 full-matrix regression engineering 项目

### 3.3 与原规划相比的偏差

- 偏差 1：**Slice A 的主要产出集中在正式 docs authority，而不是只停留在 `.omx/plans/`**
  - 原因：当前项目已经明确采用“formal docs 负责 current truth，`.omx/plans` 负责工作轨迹”的吸收规则

- 偏差 2：**为 Slice A 增补了正式 slice closeout**
  - 原因：PR-4 是阶段收口 PR；Slice A 本身就是“锁门禁”的治理动作，为后续执行留下正式收口件更利于接力

---

## 4. 当前系统真相发生了什么变化

### 4.1 PR-4 当前真相

- PR-4 不再是“后面再做的收尾 PR”这种模糊说法
- 当前已经有明确答案：
  - 要跑什么
  - 哪些测试是阶段 closeout gate
  - 什么修复允许吸收
  - 哪些事情明确不在 PR-4 做

### 4.2 验证真相

- `next-phase-test-spec` 现在不再把 PR-4 简写成“baseline + 手工链路”
- 当前阶段的最小阶段 gate 已被显式列成：
  - 2 个 backend / contract baseline
  - frontend typecheck / build
  - 14 个 stage closeout E2E specs
  - 手工主链路
  - 正式 closeout authority

### 4.3 文档 authority 真相

- 当前接手 PR-4 时，应先读：
  - `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
  - `docs/governance/next-phase-test-spec.md`
  - `docs/governance/next-phase-execution-breakdown.md`
- `.omx/plans/prd|test-spec|slice-plan-pr4-...` 提供本地执行工件，但正式指导口径仍以 `docs/` 为准

### 4.4 哪些旧理解不再成立

- “PR-4 只是最后再跑一轮 baseline” —— **不再成立**
- “PR-4 可以顺手清一批历史遗留” —— **不再成立**
- “等真的开始执行再决定门禁” —— **不再成立**

---

## 5. 验证总结

### 5.1 文档完整性验证

- `git diff --check` —— **PASS**
- 本轮新增/修改中文文档 UTF-8 回读 —— **PASS**

### 5.2 结构 / 执行边界复核

- 结论：**通过**
- 复核口径：
  - PR-4 已从占位转为可执行计划
  - Slice A 没有越界跑进 Slice B 的回归执行
  - Slice A 没有把 PR-4 扩成新的 feature / cleanup 工程

### 5.3 Slice A 对应提交

- `076895f` — `Lock the PR-4 closeout gate before stage exit`

---

## 6. 影响文件

正式 docs：

- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`
- `docs/governance/inventory/inventory-ledger.md`

本地 OMX 工件：

- `.omx/plans/archive/prd-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/test-spec-pr4-regression-and-stage-closeout.md`
- `.omx/plans/archive/slice-plan-pr4-regression-and-stage-closeout.md`

---

## 7. Remaining risks / Residual risks

1. **Slice A 只锁了门禁，还没证明门禁能跑通**
   - 影响：当前已经能执行，但还不能宣称 PR-4 完成
   - 当前处理：进入 Slice B 跑回归并吸收最小修复

2. **closeout authority 还未形成整 PR 最终件**
   - 影响：当前 authority 足以启动执行，但还不足以完成阶段退出
   - 当前处理：保留到 Slice C

3. **OMX planning artifacts 仍是本地执行工件**
   - 影响：正式阅读仍必须以 `docs/` 为准
   - 当前处理：已在 Slice A 明确这层 authority 边界

---

## 8. Backlog handoff

建议后续继续回答的问题：

- stage closeout gate 实际跑下来会暴露哪些最小必要修复？
- 哪些失败是 gate 失败项，哪些只是可接受 residual risks？
- PR-4 的正式 closeout authority 应如何回填到阶段切换语义？

推荐下一入口：

> **PR-4 Slice B：回归执行、最小修复与证据沉淀**

原因：

- Slice A 已经把“做什么 / 不做什么 / 怎么证明”锁清
- 下一步最自然的工作不再是继续写规划，而是实际跑 gate 并生成证据

---

## 9. Exit decision / Slice A 退出结论

> **PR-4 Slice A 可以视为已正式收口。**  
> 它已经把 PR-4 的门禁、范围、工件、执行入口与 authority 边界都接住了；后续不应再把 Slice A 当成“还在讨论阶段 gate”的开放问题，而应基于这份收口件直接进入 Slice B 执行。
