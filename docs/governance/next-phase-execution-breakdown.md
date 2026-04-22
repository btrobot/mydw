# 下一阶段执行分解（Next-Phase Execution Breakdown）

> Version: 1.2.0 | Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Active planning artifact

> 本文件是下一阶段启动包中的**执行顺序**文档。  
> 它回答：**下一步先做什么、按什么 PR sequence 推进、每个 PR 出口在哪里。**

## 0. 在启动包中的角色

执行前先确认以下前提已经成立：

- `docs/governance/phase-transition-checklist.md` 已完成 Part A / Part B
- `docs/current/next-phase-kickoff.md` 已确认当前唯一主线
- `docs/governance/next-phase-prd.md` 已锁定范围与成功标准
- `docs/governance/next-phase-test-spec.md` 已锁定对应验证口径

使用规则：

1. 本文件只负责 **顺序与切片**，不单独决定范围或验证
2. 如果要调整 PR 顺序，先改本文件，再检查 PRD / test spec 是否仍成立
3. 每个 PR 完成后，都要同步更新相关 docs 与测试，而不是把收口留到最后一次性处理

## 1. 执行模型

执行方式选择：

> **单主线推进 + 多 PR sequence**

本阶段按一条主线拆成多个可验证 PR，而不是同时并行推进多个大方向。

## 2. PR Sequence

先给出一张总表，避免执行时只看到“PR 名称”看不到出口：

| PR | 目标 | 主要验证出口 | 需要同步更新 |
| --- | --- | --- | --- |
| PR-1 | Workbench 可管理性收口 | workbench 相关 E2E / 手工主链路 | kickoff（若边界变化）、PRD（若范围变化）、test spec（若验证面变化） |
| PR-2 | 业务层 / 诊断层分层 | creative-review / publish-pool / workbench 相关验证 | page spec / domain doc / test spec |
| PR-3 | 文案与四态统一 | targeted E2E + 手工四态核对 | 文案相关 spec / baseline / test spec |
| PR-4 | 回归补强与阶段收口 | baseline + full closeout gate | closeout / backlog / phase-transition checklist 对应收口产物 |

## PR-1 — Workbench 可管理性收口

> Status: Completed on 2026-04-22  
> Closeout: `docs/governance/inventory/pr1-workbench-manageability-closeout.md`

目标：

- 增加搜索 / 状态筛选 / 排序
- 明确列表视图的主操作与默认排序
- 必要时加入分页或等价的大列表控制

主要影响面：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- workbench 相关 hooks / query params / state
- `frontend/e2e/creative-workbench/*`

详细规划入口：

- `docs/governance/next-phase-pr1-workbench-manageability-plan.md`
- `.omx/plans/archive/prd-pr1-workbench-manageability.md`
- `.omx/plans/archive/test-spec-pr1-workbench-manageability.md`
- `.omx/plans/archive/slice-plan-pr1-workbench-manageability.md`

验收：

- 常见待处理内容可快速定位
- 不依赖手工滚列表找内容
- window-based 上限、当前只对窗口生效的语义、何时升级 server-side search planning 显式写入 UI / docs / tests
- 若引入了新的过滤/排序行为，需要同步更新 `docs/governance/next-phase-test-spec.md`

## PR-2 — 业务层 / 诊断层分层

目标：

- 默认业务视图只保留业务信息和主操作
- 把 scheduler / pool / shadow / kill-switch 诊断信息下沉到高级诊断层

详细规划入口：

- `docs/governance/next-phase-pr2-business-diagnostics-layering-plan.md`
- `.omx/plans/prd-pr2-business-diagnostics-layering.md`
- `.omx/plans/test-spec-pr2-business-diagnostics-layering.md`
- `.omx/plans/slice-plan-pr2-business-diagnostics-layering.md`

主要影响面：

- `CreativeWorkbench`
- `CreativeDetail`
- review / publish-pool 相关展示区块

验收：

- 默认工作台与详情页不再直接暴露过量 scheduler / pool / shadow diagnostics
- 研发仍可通过显式高级诊断入口拿到必要信息
- diagnostics 入口必须“一次显式操作可达”，不能退化成隐藏式信息
- 若改变默认业务层边界，需要同步更新相关 domain/page docs

## PR-3 — 文案与四态统一

目标：

- 统一关键页面文案
- 修复坏文案
- 核心页面统一 loading / success / empty / error 四态

主要影响面：

- auth 页面
- workbench / detail
- dashboard
- 共享 empty/error/loading components（如有）

验收：

- 主路径不再依赖说明性 Alert 解释页面角色
- 文案策略一致
- 若四态或 CTA 标准变化，需要同步更新 `docs/governance/next-phase-test-spec.md`

## PR-4 — 回归补强与阶段收口

目标：

- 补齐本主线新增测试
- 清理本阶段遗留边角
- 形成阶段完成说明

主要影响面：

- frontend E2E
- docs / closeout summary（如需要）

验收：

- 本阶段 test spec 覆盖的最小集合为绿
- 可以平滑进入下一条 P1 主线（AIClip 产品化）
- 产出至少一种 closeout / summary / audit / report，并能回填 `docs/governance/phase-transition-checklist.md` 的 Part A 收口语义

## 3. 不在本 sequence 首批处理的内容

以下事项保留在本阶段之后或并行低优先级处理：

- AIClip workflow 深度产品化
- root docs 实际 move/archive/delete 执行
- FastAPI / datetime deprecation cleanup
- runtime security / env warning cleanup

## 4. 退出条件

当以下条件满足时，可结束本主线并转入下一条：

1. Workbench 具备基础管理能力
2. 业务/诊断层完成分层
3. 核心页面四态与文案统一
4. 对应 baseline / E2E / 人工链路验证通过
