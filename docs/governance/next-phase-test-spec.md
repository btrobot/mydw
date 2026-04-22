# 下一阶段 Test Spec（Next-Phase Test Spec）

> Version: 1.2.0 | Updated: 2026-04-22
> Owner: Tech Lead / Codex  
> Status: Active planning artifact

> 本文件是下一阶段启动包中的**完成证明**文档。  
> 它回答：**这条主线做完以后，要靠什么验证才能算真的完成。**

## 0. 在启动包中的角色

本文件与以下文档一起构成启动包：

- 入口：`docs/current/next-phase-kickoff.md`
- 范围定义：`docs/governance/next-phase-prd.md`
- 执行顺序：`docs/governance/next-phase-execution-breakdown.md`
- 当前验证总基线：`docs/governance/verification-baseline.md`

使用规则：

1. kickoff 确认主线后，先读 PRD，再用本文件锁验证口径
2. 若新增/删减验证面，必须先改本文件，再允许执行顺序继续推进
3. 若某项工作无法映射到本文件中的通过标准，应先判断它是不是误入主线

## 1. 适用范围

本 test spec 只覆盖：

- Creative-first 稳定化 / UI-UX 收口主线

不覆盖：

- remote 新能力扩展
- AIClip 深度产品化的后续阶段

## 2. 验证目标

要证明的不是“页面变漂亮了”，而是：

1. Workbench 变得更可管理
2. 业务层与诊断层完成分层
3. 核心页面状态反馈和文案更加一致
4. 现有 Creative-first 主链路没有回归

## 3. 自动化验证分层

## 3.1 必跑 backend / contract baseline

```powershell
pytest `
  backend/tests/test_creative_workflow_contract.py `
  backend/tests/test_openapi_contract_parity.py `
  -q
```

目的：

- 保住 Creative workflow 主契约
- 保住前后端 API 形状没有明显漂移

## 3.2 必跑 frontend E2E baseline

```powershell
cd E:\ais\mydw\frontend
npm run test:e2e -- `
  e2e/auth-routing/auth-routing.spec.ts `
  e2e/creative-main-entry/creative-main-entry.spec.ts `
  e2e/creative-workbench/creative-workbench.spec.ts `
  e2e/creative-review/creative-review.spec.ts `
  e2e/publish-pool/publish-pool.spec.ts
```

目的：

- 保住 auth 入口、Creative 默认入口、workbench、detail/review、publish-pool 主链路

## 3.3 文案 / IA / 状态反馈专项验证

新增或补强的自动化测试应重点覆盖：

- 搜索 / 筛选 / 排序 / 分页
- workbench window-based guardrail 是否显式说明“当前只对已加载窗口生效”与“何时升级 server-side search planning”
- 默认业务层是否隐藏高级诊断信息
- diagnostics 是否仍然通过显式入口可达，且不会把失败伪装成空态
- diagnostics 打开状态是否支持 URL 恢复 / deep-link / refresh 后保持一致
- error / empty / loading / success 四态
- 关键 CTA 文案与导航命名

当前 **PR-3** 的最小 targeted suite 应至少覆盖：

- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-error-ux/auth-status-live-state.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/e2e/creative-main-entry/creative-main-entry.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/creative-review/creative-review.spec.ts`
- `frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`
- `frontend/e2e/dashboard/dashboard-state.spec.ts`

PR-3 对应的专项口径应明确证明：

- auth/login shell 的用户可读文案已稳定，不再暴露假的 support / forgot CTA
- auth live refresh 的 loading / error 已显式可断言
- creative workbench / detail / version panel 的主文案、主 CTA 与当前版本语义已稳定
- Dashboard 仍是 diagnostics surface，但失败不再伪装成 empty / placeholder

建议主要落点：

- `frontend/e2e/creative-workbench/`
- `frontend/e2e/creative-review/`
- `frontend/e2e/publish-pool/`
- `frontend/e2e/publish-cutover/`
- `frontend/e2e/task-diagnostics/`
- `frontend/e2e/creative-version-panel/`
- baseline 依赖 `frontend/e2e/creative-main-entry/` 与 `frontend/e2e/auth-routing/`

当前 PR-2 的最小 targeted suite 应至少覆盖：

- `creative-workbench`
- `creative-review`
- `publish-pool`
- `publish-cutover`
- `task-diagnostics`
- `creative-version-panel`

## 3.4 与 PR Sequence 的映射

| PR | 必须证明什么 | 最小验证 |
| --- | --- | --- |
| PR-1 — Workbench 可管理性收口 | 列表可定位、可筛选、可排序、可控规模，且 window-based 限制与升级条件显式化 | workbench E2E + 必要手工链路 |
| PR-2 — 业务层 / 诊断层分层 | 默认业务视图不再承担过量诊断信息；diagnostics 默认隐藏、通过显式入口可达，且打开状态应可稳定恢复 | creative-workbench / creative-review / publish-pool / publish-cutover / task-diagnostics / creative-version-panel targeted E2E + creative-main-entry / auth-routing baseline |
| PR-3 — 文案与四态统一 | CTA、文案、loading/empty/error/success 四态一致，且 diagnostics failure 不再伪装成 empty/default | `npm run typecheck` + `npm run build` + auth/bootstrap/login/auth shell/routing/error UX/creative main entry/workbench/review/version panel/dashboard targeted E2E + 手工核对 |
| PR-4 — 回归补强与阶段收口 | 新主线被 regression baseline 接住 | backend/contract baseline + frontend baseline + 手工链路 |

## 4. 手工验证链路

每个阶段收口前至少人工确认：

1. 从 `/` 进入 `CreativeWorkbench`
2. 能快速定位待处理内容
3. 默认先看到业务统计、筛选、列表，而不是 runtime / scheduler / shadow / kill-switch 诊断正文
4. 从 workbench 进入 detail 时，默认看到的是业务概览、作品输入、当前版本、当前有效审核结论
5. 通过“查看运行诊断”/“查看高级诊断”能够一跳进入 diagnostics 层，并且 refresh 后仍保持同一打开状态
6. auth grace / error / normal 状态下，主页面反馈一致

## 5. 通过标准

视为通过，需要同时满足：

- 自动化 baseline 绿
- 新增 UI/UX 相关 E2E 绿
- 人工主链路核对通过
- PR-2 相关页面满足“默认隐藏 diagnostics + 显式可达 + refresh 可恢复”
- 无新增“必须靠 Alert 解释页面职责”的过渡态设计

## 6. 失败标准

以下任一情况，视为未通过：

- Workbench 增加了功能但仍然难以管理
- 默认页面继续暴露过量诊断信息
- diagnostics 入口存在但不显式、不可一跳到达，或 refresh / deep-link 后状态丢失
- 文案统一后引入明显信息回退
- Creative-first 主入口 / detail / publish-pool 回归

## 7. 与启动包的关系

本文件不负责定义“做什么”，那是 `docs/governance/next-phase-prd.md` 的职责。  
本文件也不负责定义“先做哪个 PR”，那是 `docs/governance/next-phase-execution-breakdown.md` 的职责。

如果出现以下任一情况，应先停下来修文档，而不是直接继续开发：

- kickoff 已调整主线，但本文件还沿用旧验证口径
- PRD 已扩大/缩小范围，但本文件没有同步
- execution breakdown 新增了 PR，但本文件没有对应的验证落点
