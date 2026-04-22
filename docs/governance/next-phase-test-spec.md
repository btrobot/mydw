# 下一阶段 Test Spec（Next-Phase Test Spec）

> Version: 1.1.0 | Updated: 2026-04-21  
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
- error / empty / loading / success 四态
- 关键 CTA 文案与导航命名

建议主要落点：

- `frontend/e2e/creative-workbench/`
- `frontend/e2e/creative-review/`
- 如有必要补充 `frontend/e2e/dashboard/` 或 `auth-*` 现有 suite

## 3.4 与 PR Sequence 的映射

| PR | 必须证明什么 | 最小验证 |
| --- | --- | --- |
| PR-1 — Workbench 可管理性收口 | 列表可定位、可筛选、可排序、可控规模，且 window-based 限制与升级条件显式化 | workbench E2E + 必要手工链路 |
| PR-2 — 业务层 / 诊断层分层 | 默认业务视图不再承担过量诊断信息，且 diagnostics 仍然显式可达 | creative-workbench / creative-review / publish-pool / publish-cutover / task-diagnostics 相关 E2E |
| PR-3 — 文案与四态统一 | CTA、文案、loading/empty/error/success 四态一致 | 相关页面 targeted E2E + 手工核对 |
| PR-4 — 回归补强与阶段收口 | 新主线被 regression baseline 接住 | backend/contract baseline + frontend baseline + 手工链路 |

## 4. 手工验证链路

每个阶段收口前至少人工确认：

1. 从 `/` 进入 `CreativeWorkbench`
2. 能快速定位待处理内容
3. 从 workbench 进入 detail 时，默认看到的是业务信息而不是工程诊断
4. auth grace / error / normal 状态下，主页面反馈一致

## 5. 通过标准

视为通过，需要同时满足：

- 自动化 baseline 绿
- 新增 UI/UX 相关 E2E 绿
- 人工主链路核对通过
- 无新增“必须靠 Alert 解释页面职责”的过渡态设计

## 6. 失败标准

以下任一情况，视为未通过：

- Workbench 增加了功能但仍然难以管理
- 默认页面继续暴露过量诊断信息
- 文案统一后引入明显信息回退
- Creative-first 主入口 / detail / publish-pool 回归

## 7. 与启动包的关系

本文件不负责定义“做什么”，那是 `docs/governance/next-phase-prd.md` 的职责。  
本文件也不负责定义“先做哪个 PR”，那是 `docs/governance/next-phase-execution-breakdown.md` 的职责。

如果出现以下任一情况，应先停下来修文档，而不是直接继续开发：

- kickoff 已调整主线，但本文件还沿用旧验证口径
- PRD 已扩大/缩小范围，但本文件没有同步
- execution breakdown 新增了 PR，但本文件没有对应的验证落点
