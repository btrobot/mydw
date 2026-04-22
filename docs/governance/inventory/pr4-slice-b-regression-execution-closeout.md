# PR-4 Slice B 回归执行、最小修复与证据沉淀收口件

> Version: 1.0.0
> Updated: 2026-04-22
> Owner: Tech Lead / Codex
> Status: Recorded slice closeout

> 目的：把 `PR-4 / Slice B：回归执行、最小修复与证据沉淀` 的实际交付、当前真相、验证证据与残留风险落成一份正式收口件。  
> 这份文档回答的不是“Slice B 理论上要跑什么”，而是：**这次真实跑 gate 时哪里失败了、实际吸收了什么最小修复、现在有哪些证据已经沉淀完成、哪些事情明确留给 Slice C。**

---

## 1. 一句话总结

> Slice B 已经把 PR-4 的自动化 closeout gate 真正跑通，并以最小修复方式把 `frontend` 的 Playwright 脚本绑定到正式配置文件；当前自动化证据已经足够证明阶段基线可重复执行，但 PR-4 的最终退出说明与手工门禁归口仍留给 Slice C。

---

## 2. 本 Slice 原始目标

- 运行 PR-4 已锁定的 stage closeout gate
- 如出现失败，只吸收通过 gate 所必需的最小修复
- 把验证结果沉淀为后续可引用的正式证据

关联 authority：

- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/inventory/pr4-slice-a-gate-lock-closeout.md`

---

## 3. 实际交付结果

### 3.1 初始失败被定位清楚

- backend / contract baseline 首次即通过
- frontend `npm run typecheck` 与 `npm run build` 首次即通过
- frontend stage closeout E2E 首次失败，核心报错为：
  - `page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL`

根因不是业务页面 truth 回退，而是：

- Playwright 配置位于 `frontend/e2e/playwright.config.ts`
- 但 `frontend/package.json` 里的 `test:e2e*` 脚本调用的是裸 `playwright test`
- 结果是 stage closeout suite 执行时没有加载正式配置，`BASE_URL` 为空，导致所有 `page.goto()` 目标 URL 失效

### 3.2 已吸收的最小修复

只修改了一个文件：

- `frontend/package.json`

实际修复：

- `test:e2e` 改为 `playwright test --config e2e/playwright.config.ts`
- `test:e2e:ui` 改为 `playwright test --config e2e/playwright.config.ts --ui`
- `test:e2e:headed` 改为 `playwright test --config e2e/playwright.config.ts --project=chromium-headed`
- `test:e2e:report` 改为 `playwright show-report reports`

这次修复保持在 PR-4 Slice B 的最小修复政策之内：

- 没改业务实现
- 没改测试语义
- 没扩充验证面
- 只修正了导致 gate 无法按既定 authority 执行的脚本绑定问题

### 3.3 已沉淀的证据

- 现在 `frontend/package.json` 中的 `npm run test:e2e*` 已成为 PR-4 自动化 gate 的正式执行入口
- stage closeout suite 已经能在当前仓库状态下被重复跑通
- `reports` 也已与 Playwright 报告查看命令对齐，避免继续依赖默认路径猜测

---

## 4. 明确没做什么

- **没有吸收更大范围修复**
  - 没有因为这次 gate 失败而顺手改 `playwright.config.ts`、测试内容、页面行为或额外环境逻辑

- **没有重开 PR-4 的阶段边界讨论**
  - Slice B 只处理“如何把既定 gate 跑通”，不回退到重新定义 gate

- **没有形成 PR-4 最终阶段退出 authority**
  - 这仍属于 Slice C 的职责

- **没有单独新增一轮手工 gate 记录**
  - 本 Slice 已完成自动化 gate 与最小修复证据沉淀；最终阶段退出时的手工核对与正式放行说明，留给 Slice C 一并归口

---

## 5. 当前真相发生了什么变化

### 5.1 自动化 gate 的执行真相已更清晰

- PR-4 现在不只是“理论上应该能跑”
- 当前已经有真实证据证明：
  - backend / contract baseline 可通过
  - frontend typecheck / build 可通过
  - frontend stage closeout E2E suite 可通过

### 5.2 frontend E2E 的正式入口已被纠正

- 当前应通过 `npm run test:e2e` 这组脚本来跑 PR-4 closeout suite
- 不应再把是否加载 `frontend/e2e/playwright.config.ts` 配置，寄托于“裸 `playwright test` 是否刚好生效”这种偶然路径

### 5.3 哪些旧理解不再成立

- “E2E 全挂说明业务面大面积回退” —— **不成立**
- “需要重开一轮前端诊断/环境设计讨论” —— **不成立**
- “Slice B 必须吸收更大的环境规范化改动才能继续” —— **不成立**

---

## 6. 验证与证据

### 6.1 最小 smoke 复跑

- 命令：
  - `npm run test:e2e -- e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- 结果：
  - **PASS（8 passed）**

### 6.2 全量自动化 gate 复跑

- backend：
  - `pytest backend/tests/test_creative_workflow_contract.py backend/tests/test_openapi_contract_parity.py -q`
  - **PASS（13 passed）**

- frontend build gate：
  - `npm run typecheck`
  - **PASS**
  - `npm run build`
  - **PASS**

- frontend stage closeout suite：
  - 通过 `npm run test:e2e -- ...` 执行 14 个 stage closeout specs
  - Playwright 输出：
    - `Running 122 tests using 4 workers`
  - 最终结果：
    - **PASS（exit code 0）**

- 静态诊断：
  - `lsp_diagnostics_directory(frontend, strategy="tsc")`
  - **PASS（0 errors, 0 warnings）**

### 6.3 复核结论

- Debugger lane 的额外建议是：可考虑对 `frontend/e2e/playwright.config.ts` 做 env 归一化
- 但当前观测到的 gate 失败，已经被 package script 的配置绑定修正解决
- Architect 复核结论：**APPROVED**
- ai-slop-cleaner 针对 `frontend/package.json` 做 changed-files-only 审查后结论：**无需进一步简化**

### 6.4 已观察到但当前不阻断的现象

- E2E 执行期间出现多条 Vite proxy `ECONNREFUSED 127.0.0.1:8000` 日志
- 但当前 suite 退出码为 `0`，目标 specs 全部通过
- 因此当前把它记为 **非阻断噪音**，而不是 Slice B 的失败项

---

## 7. 影响文件

代码/配置：

- `frontend/package.json`

文档：

- `docs/governance/inventory/pr4-slice-b-regression-execution-closeout.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/README.md`
- `docs/governance/inventory/inventory-ledger.md`

---

## 8. Remaining risks / Residual risks

1. **直接裸跑 `playwright test` 仍可能绕过正式 config**
   - 影响：如果后续有人不通过 `package.json` 脚本而直接调用 Playwright CLI，仍有再次偏离当前 gate 入口的风险
   - 当前处理：把 `npm run test:e2e*` 固化为正式执行入口，并在本收口件中显式记录

2. **proxy 噪音仍存在**
   - 影响：当前不阻断，但可能掩盖未来真正的预览/代理问题
   - 当前处理：先记为 residual risk，不在 Slice B 扩 scope 处理

3. **PR-4 仍未正式退出**
   - 影响：虽然自动化 gate 已绿，但阶段退出 authority 还没有最终落盘
   - 当前处理：进入 Slice C，形成 PR-4 正式 closeout 与阶段 handoff

---

## 9. Handoff to Slice C

下一步不应重复讨论 Slice B 是否还要继续扩修，而应直接回答：

- PR-4 为什么现在可以进入正式阶段收口？
- 自动化 gate 与先前 PR-1 / PR-3 closeout 如何串成一个正式退出说明？
- 哪些 residual risks 被接受，哪些必须显式写入阶段 handoff？

推荐下一入口：

- `docs/governance/inventory/pr4-slice-b-regression-execution-closeout.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/next-phase-pr4-regression-and-stage-closeout-plan.md`

---

## 10. Exit decision / Slice B 退出结论

> **PR-4 Slice B 可以视为已正式收口。**  
> 它已经把自动化回归执行、最小修复与证据沉淀这三件事接住了；后续不应再把 Slice B 当成“还在找失败原因”的开放问题，而应基于这份收口件进入 Slice C，把 PR-4 的最终退出 authority 写完整。
