# 下一阶段执行分解（Next-Phase Execution Breakdown）

> Version: 1.0.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active planning artifact

## 1. 执行模型

执行方式选择：

> **单主线推进 + 多 PR sequence**

本阶段按一条主线拆成多个可验证 PR，而不是同时并行推进多个大方向。

## 2. PR Sequence

## PR-1 — Workbench 可管理性收口

目标：

- 增加搜索 / 状态筛选 / 排序
- 明确列表视图的主操作与默认排序
- 必要时加入分页或等价的大列表控制

主要影响面：

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- workbench 相关 hooks / query params / state
- `frontend/e2e/creative-workbench/*`

验收：

- 常见待处理内容可快速定位
- 不依赖手工滚列表找内容

## PR-2 — 业务层 / 诊断层分层

目标：

- 默认业务视图只保留业务信息和主操作
- 把 scheduler / pool / shadow / kill-switch 诊断信息下沉到高级诊断层

主要影响面：

- `CreativeWorkbench`
- `CreativeDetail`
- review / publish-pool 相关展示区块

验收：

- 默认工作台与详情页不再带明显“验收台/诊断台”气质
- 研发仍可通过高级诊断入口拿到必要信息

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
