# 当前规划对照表（规划文档 / Phase / PR / Commit / 状态）

> 生成时间：2026-04-18  
> 用途：帮助快速回答“我们正在实现的是哪个规划？”  
> 结论先行：**大主线是 Creative Progressive Rebuild；最近实际一直在执行的是其后续补出的 Frontend UI/UX Closeout（Phase E）规划。**

---

## 1. 先看总答案

当前项目里，最需要区分的是两层规划：

### A. 主线规划
- 文档：`.omx/plans/archive/prd-creative-progressive-rebuild-roadmap.md`
- 含义：把系统从 **Task-first** 渐进式迁移到 **Creative-first**
- 阶段：**Phase A ~ Phase D**

### B. 后续前端收口规划
- 文档：`.omx/plans/archive/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`
- 含义：在 A~D 主线跑通后，单独做一轮 **Frontend UI/UX 收口 + 技术栈最佳实践对齐**
- 阶段：**Phase E**

> 所以，最近你感觉一直在做的，其实主要是 **Phase E**，而不是重新回到 A/B/C/D。

---

## 2. 总体规划结构

| 层级 | 规划文档 | 目标 | 当前理解 |
|---|---|---|---|
| 主线 | `.omx/plans/archive/prd-creative-progressive-rebuild-roadmap.md` | 完成 Task-first -> Creative-first 的业务主线迁移 | 主线已完成到 D |
| 阶段拆分 | `.omx/plans/archive/prd-creative-progressive-rebuild-phase-a-pr-plan.md` ~ `phase-d-pr-plan.md` | 把 A/B/C/D 各阶段拆成可执行 PR | 已执行 |
| 前端收口 | `.omx/plans/archive/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md` | 用现有技术栈能力收口前端页面、职责、状态反馈、文案和布局 | 最近一直在执行 |

---

## 3. 主线规划（A ~ D）对照

### Phase A：Creative 骨架与工作台雏形

- 规划文档：`.omx/plans/archive/prd-creative-progressive-rebuild-phase-a-pr-plan.md`
- 目标：引入 Creative 域最小骨架、Workbench、Detail、Task 与 Creative 映射

| 项目 | 内容 |
|---|---|
| 代表性提交 | `a3b4207` Restore Phase A proof coverage for the creative workbench |
| 代表性提交 | `9ae7ece` Confirm the Phase A creative workbench frontend is ready for handoff |
| 代表性提交 | `5340f04` Close PR-3 proof gaps before Phase A sign-off |
| 代表性提交 | `e1561c6` Seal Phase 1 acceptance evidence before the rebuild advances |
| 当前状态 | 已完成 |

### Phase B：版本管理与人工检查闭环

- 规划文档：`.omx/plans/archive/prd-creative-progressive-rebuild-phase-b-pr-plan.md`
- 目标：稳定版本真相、审核闭环、composition 写回、版本历史与审核交互

| 项目 | 内容 |
|---|---|
| 代表性提交 | `3b80b9d` Enforce Creative review invariants before Phase B writeback |
| 代表性提交 | `e445eb5` Preserve creative review truth when composition callbacks write back results |
| 代表性提交 | `4bdb00d` Expose creative review history without collapsing task diagnostics into business truth |
| 代表性提交 | `964024f` Keep Phase B exit verification hermetic across local auth artifacts |
| 当前状态 | 已完成 |

### Phase C：发布池与调度器切换

- 规划文档：`.omx/plans/archive/prd-creative-progressive-rebuild-phase-c-pr-plan.md`
- 目标：建立 publish pool / snapshot，并把 scheduler 主候选源切到 pool

| 项目 | 内容 |
|---|---|
| 代表性提交 | `1208aab` Establish Creative publish-pool truth before scheduler cutover |
| 代表性提交 | `d266481` Bind publish execution to frozen pool snapshots before scheduler cutover |
| 代表性提交 | `e99adae` Cut scheduler over to publish-pool selection with kill switch and diagnostics |
| 代表性提交 | `dddbc48` Close Phase C with front-end publish-pool visibility and cutover diagnostics |
| 当前状态 | 已完成 |

### Phase D：AIClip 工作流化与主入口迁移

- 规划文档：`.omx/plans/archive/prd-creative-progressive-rebuild-phase-d-pr-plan.md`
- 目标：让 AIClip 进入作品工作流，并把默认主入口迁移到 Creative Workbench

| 项目 | 内容 |
|---|---|
| 代表性提交 | `40d0a7c` Route AI clip outputs through creative version workflow |
| 代表性提交 | `92d66a1` Enable AIClip workflow submission from Creative surfaces |
| 代表性提交 | `f60436a` Demote Task pages behind creative-first diagnostics flow |
| 代表性提交 | `f1d236b` Move daily entry onto Creative Workbench before Phase D closeout |
| 当前状态 | 已完成 |

---

## 4. 最近一直在做的规划：Phase E

### Phase E 的正式规划文档
- `.omx/plans/archive/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`

### Phase E 的正式目标
不是重做视觉，而是把前端页面按技术栈最佳实践收口：

- 优先复用 `Ant Design / ProComponents / React Router / React Query`
- 不新造技术栈已有的基础组件
- 只抽业务域组件，不抽通用 UI 壳组件
- 统一 workbench / detail / dashboard / task diagnostics 的职责边界
- 统一文案、状态反馈、布局模式
- 把业务信息与高级诊断信息分层

### Phase E 原始 PR 计划

| PR | 计划目标 | 状态 |
|---|---|---|
| PR-E1 | 信息架构 / 导航命名 / 文案基线收口 | 已完成 |
| PR-E2 | Workbench 工作台能力与 ProTable 对齐 | 已完成 |
| PR-E3 | Detail / Dashboard / Task diagnostics 职责分层收口 | 已完成 |
| PR-E4 | 统一页面四态反馈 + Auth 产品化表达 | 已完成 |
| PR-E5 | AIClip workflow 产品化收尾 + 响应式基线整修 | 已完成 |

---

## 5. Phase E：PR 到 commit 的对应关系

> 说明：正式计划里只有 `PR-E1 ~ PR-E5`。  
> 后面你提到的 “PR-E6”，**不在最初正式计划中**，更像是 Phase E 剩余收口改动的追加 closeout。

| PR | 含义 | 主要对应提交 | 当前状态 |
|---|---|---|---|
| PR-E1 | IA / 导航命名 / 文案基线 | `ef7b0d7` Make the workbench and auth entry read like the product path | 已完成 |
| PR-E2 | Workbench table-first / ProTable / 搜索筛选排序分页 | 无单独特别清晰的独立标题提交；其结果已体现在后续 workbench 收口提交中 | 已完成 |
| PR-E3 | Detail / Dashboard / Task diagnostics 分层 | `c8038cd` Clarify creative detail vs diagnostics surfaces | 已完成 |
| PR-E4 | 四态反馈 / Auth 产品化 / 失败态显式化 | `1f0aaab` Make Phase E closeout surface explicit auth and workbench failure states | 已完成 |
| PR-E5 | AIClip workflow 产品化 + 响应式整修 | `d115836` Make the AIClip flow readable as a product workflow on smaller screens | 已完成 |
| 非正式尾声 | 剩余 Phase E / 前端收口改动 | `1f0aaab` 也可视为这轮剩余 closeout 的最终落点 | 已完成 |

---

## 6. 为什么会觉得自己“迷失了”

主要有三个原因：

### 6.1 规划层级很多
你不是只在跟一个 PR 打交道，而是在同时面对：

- 总路线图（roadmap）
- 阶段计划（A/B/C/D）
- 前端收口计划（E）
- 每个阶段内部 PR
- 每个 PR 的实现 / 验收 / commit / 文档收口

### 6.2 Phase E 是在主线之后追加出来的
A~D 是“业务主线重构”；
E 是“前端界面收口”。

所以在心理上，E 像是“第二条线”，但它实际上是：

- **主线完成后的前端收尾规划**

### 6.3 “PR-E6”不是最初正式计划里的编号
正式计划文件里只有：

- `PR-E1`
- `PR-E2`
- `PR-E3`
- `PR-E4`
- `PR-E5`

你后面说“PR-E6”，我们实际对齐到的是：

- **剩余 Phase E / 前端收口改动**
- 它更像 **Phase E tail closeout**，不是原始计划里单独存在的正式条目

---

## 7. 现在最准确的理解

如果只保留一句话：

> **我们的大主线规划是 `Creative Progressive Rebuild`，而最近一直在执行的具体规划，是它后续补出来的 `Frontend UI/UX Closeout (Phase E)`。**

再拆开说：

- **A~D**：业务重构主线
- **E**：前端收口主线
- 你最近反复推进和提交的，主要是 **E**
- 当前 Phase E 也已经基本完成

---

## 8. 当前状态快照

| 维度 | 状态 |
|---|---|
| Creative Progressive Rebuild 主线（A~D） | 已完成 |
| Frontend UI/UX Closeout（Phase E） | 已基本完成 |
| Phase E 正式规划 PR 数 | 5 个（E1 ~ E5） |
| “PR-E6” | 非最初正式计划条目，更像追加 closeout |
| 当前建议 | 不要再按“我是不是还在做 A/B/C/D”去理解，而应把当前视为：**主线完成后，Phase E 前端收口已到尾声** |

---

## 9. 相关文档

- `.omx/plans/archive/prd-creative-progressive-rebuild-roadmap.md`
- `.omx/plans/archive/prd-creative-progressive-rebuild-phase-a-pr-plan.md`
- `.omx/plans/archive/prd-creative-progressive-rebuild-phase-b-pr-plan.md`
- `.omx/plans/archive/prd-creative-progressive-rebuild-phase-c-pr-plan.md`
- `.omx/plans/archive/prd-creative-progressive-rebuild-phase-d-pr-plan.md`
- `.omx/plans/archive/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`
- `reports/creative-rebuild-plan-and-dev-history-2026-04-18.md`
