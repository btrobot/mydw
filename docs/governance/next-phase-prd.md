# 下一阶段 PRD（Next-Phase PRD）

> Version: 1.1.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active planning artifact

> 本文件是下一阶段启动包中的**范围与完成定义**文档。  
> 它回答：**为什么现在做、做到哪里算完成、什么明确不做。**

## 0. 在启动包中的角色

本文件要和以下文档一起使用：

- 入口：`docs/current/next-phase-kickoff.md`
- 阶段切换门禁：`docs/governance/phase-transition-checklist.md`
- 验证规格：`docs/governance/next-phase-test-spec.md`
- 执行分解：`docs/governance/next-phase-execution-breakdown.md`
- backlog 压缩入口：`docs/governance/next-phase-backlog.md`

使用规则：

1. 只有在 `phase-transition-checklist` 的 Part A / Part B 通过后，本 PRD 才视为当前有效主线
2. 如果目标、范围、非目标变了，先更新本 PRD，再决定 test spec / breakdown 是否需要改
3. 不允许跳过本 PRD，直接把 backlog 项混入执行主线

## 1. Phase 名称

**Creative-first 稳定化 / UI-UX 收口主线**

## 2. 背景

项目已经完成：

- Creative A~D 主线迁移
- auth Step 5
- 文档入口 / 启动协议 / 验证基线 / backlog 收口

但当前系统仍然停留在“功能可跑通、验证可闭环、界面仍有明显过渡态”的阶段。

最直接的开发摩擦集中在：

- Workbench 不够可管理
- 业务信息与诊断信息混放
- 文案、CTA、四态反馈不一致

## 3. 问题陈述

如果直接在当前状态继续扩功能，会遇到三个问题：

1. 主工作台的信息架构仍不稳定
2. 后续 feature 会继续叠加到过渡期 UI 上
3. 开发者虽然知道“现在是什么”，但还没有一个足够稳定的产品化工作面去承接下一阶段开发

## 4. 目标

下一阶段目标不是扩功能数量，而是完成以下收口：

1. 让 `CreativeWorkbench` 具备日常可管理能力
2. 把业务层与诊断层彻底分层
3. 统一关键页面文案、CTA 层级与 loading/empty/error/success 四态

## 5. 非目标

本阶段**不**以以下内容为主目标：

- 新业务域扩张
- remote 新大功能线
- Coze 深度接入落地
- 全量根层 docs 搬迁的最终执行
- 全量平台技术债一次性清零

## 6. 范围

### In scope

- `CreativeWorkbench`
- `CreativeDetail`
- 相关 dashboard / auth / diagnostics 边界
- 核心前端文案与状态反馈
- 为这条主线补齐必要 E2E / regression coverage

### Out of scope

- remote Phase 5+ 新规划
- AIClip 深度产品化（留到 P1）
- 大规模 docs 迁移执行
- 非本主线的广泛后端重构

## 7. 成功标准

达到以下标准即可视为本阶段完成：

1. Workbench 在常见内容规模下具备搜索 / 筛选 / 排序 / 分页或等价管理能力
2. 默认业务视图不再承担过量 scheduler / pool / shadow diagnostics
3. 核心页面四态一致，主要文案完成统一
4. 下一阶段继续做 AIClip 产品化或更多业务能力时，不再需要先修一轮信息架构

## 8. 风险

| 风险 | 表现 | 控制方式 |
| --- | --- | --- |
| 把阶段做成视觉重设计 | 范围失控 | 限定为 IA / UX 收口，不做大视觉重做 |
| 业务与诊断边界切得过猛 | 研发排障反而更难 | 保留高级诊断层，而不是删除诊断能力 |
| 一次改太多页面 | 回归成本高 | 按 PR sequence 拆开推进 |
| 文案统一时引入回归 | 文本/E2E 脆弱 | 用 targeted E2E + 文档/测试说明锁边界 |

## 9. 验收标准

- 可以从 `docs/current/next-phase-kickoff.md` 直接进入本阶段
- 有明确的 test spec
- 有明确的 PR 执行分解
- 本阶段结束后，Workbench / Detail 进入“稳定产品面”而不是“验收台”

## 10. 与执行/验证文档的对应关系

为了避免 PRD 只停留在“方向说明”，这里明确对应关系：

| PRD 目标 | 对应验证文档 | 对应执行文档 |
| --- | --- | --- |
| `CreativeWorkbench` 可管理性提升 | `docs/governance/next-phase-test-spec.md` 中的搜索 / 筛选 / 排序 / 分页验证 | `docs/governance/next-phase-execution-breakdown.md` 的 PR-1 |
| 业务层 / 诊断层分层 | `docs/governance/next-phase-test-spec.md` 中的默认业务层与高级诊断层验证 | `docs/governance/next-phase-execution-breakdown.md` 的 PR-2 |
| 文案与四态统一 | `docs/governance/next-phase-test-spec.md` 中的 CTA / 四态一致性验证 | `docs/governance/next-phase-execution-breakdown.md` 的 PR-3 |
| 阶段收口与回归补强 | `docs/governance/next-phase-test-spec.md` 的 baseline + 手工链路 | `docs/governance/next-phase-execution-breakdown.md` 的 PR-4 |

一句话：

> **PRD 负责锁范围，test spec 负责锁验证，execution breakdown 负责锁顺序。**
