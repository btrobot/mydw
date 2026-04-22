# Current Project MVP Closeout Checklist / 当前项目 MVP 收口清单

> Version: 1.0.0  
> Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Active working checklist

> 目的：把“当前这个项目在 MVP 完成后到底要收口哪些东西”落成一份**可逐项检查**的清单。  
> 本文件不是通用模板，而是针对本仓库当前实际状态的项目级收口清单。

---

## 1. 使用方式

本清单服务的不是“全量补文档”，而是：

> **把当前项目从“能跑起来的 MVP”收成“能继续稳定开发的基线”。**

建议使用顺序：

1. 先按本清单做当前阶段收口
2. 再对照 `docs/governance/phase-transition-checklist.md` 判断是否能切阶段
3. 再进入 `docs/current/next-phase-kickoff.md` 启动下一阶段

相关入口：

- `docs/governance/post-mvp-closeout-sequence.md`
- `docs/governance/phase-transition-checklist.md`
- `docs/governance/inventory/post-mvp-doc-governance-closeout.md`

---

## 2. 收口项 A：实现状态收口

目标：先把“现在到底做到哪了”说清楚。

当前项目至少应检查：

```text
[ ] 已能一句话说明：当前系统已不是单体 Electron，而是本地 Creative-first 工作台 + remote 授权控制平面双系统
[ ] 已能说明：Creative-first 已是默认业务入口，而不是 Task-first
[ ] 已能说明：哪些主流程已跑通，哪些只算可运行但未完全产品化
[ ] 已能说明：哪些原计划内容本阶段未完成，已明确进入 backlog
[ ] 已有至少一份 closeout / summary / audit / report 说明“做了什么、没做什么、剩余风险是什么”
```

重点参考：

- `docs/current/architecture.md`
- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-backlog.md`

通过标准：

> 不重新翻大量聊天记录，也能回答“现在这个 MVP 已经能做什么，还不能稳定做什么”。

---

## 3. 收口项 B：系统边界收口

目标：把最容易误导后续开发的“当前有效边界”收清楚。

当前项目至少应检查：

```text
[ ] frontend / backend / remote 的当前职责边界已清楚
[ ] CreativeWorkbench / CreativeDetail / Dashboard / auth shell 的页面职责边界已清楚
[ ] task / publish / composition 的当前真实语义已清楚
[ ] local_ffmpeg V1 的能力边界已清楚，不再与更大设想混写
[ ] 哪些数据库/数据模型仍是草稿、哪些已成为运行时真实约束，已能说清
[ ] 明显过时的边界草稿，不再被当作当前 authoritative 输入
```

重点参考：

- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/domains/tasks/task-management-domain-model.md`
- `docs/domains/tasks/task-semantics.md`
- `docs/domains/publishing/local-ffmpeg-composition.md`

当前特别要守住的真相：

- **Creative-first** 已经是默认业务入口
- `local_ffmpeg V1` 是当前冻结能力，不是“未来更大 composition 面”的代称
- `CompositionPoller` 只服务 `coze`，不服务本地 FFmpeg

通过标准：

> 后续开发者不会再因为旧边界草稿，把当前系统理解成另一套实现。

---

## 4. 收口项 C：文档体系收口

目标：不是补全所有文档，而是建立一套能继续指导开发的 current truth 入口。

当前项目至少应检查：

```text
[ ] docs 根层只保留默认入口，不再堆放大量未分类 active 文档
[ ] 当前架构入口已明确：docs/current/architecture.md
[ ] 当前运行事实入口已明确：docs/current/runtime-truth.md
[ ] authority 入口已明确：docs/governance/authority-matrix.md
[ ] verification baseline 入口已明确：docs/governance/verification-baseline.md
[ ] next-phase 启动入口已明确：docs/current/next-phase-kickoff.md
[ ] 高可见度旧文档已被 stale / redirect / archive / inventory 分流
[ ] 每个高价值主题尽量只有一个当前 authoritative 入口
```

重点参考：

- `docs/README.md`
- `docs/governance/README.md`
- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/inventory/inventory-ledger.md`
- `docs/archive/README.md`

通过标准：

> 新开发者先读入口文档，而不是先在历史资料堆里猜“谁说了算”。

---

## 5. 收口项 D：验证基线收口

目标：把“以后继续开发至少要跑什么”固定下来。

当前项目至少应检查：

```text
[ ] 已有 repo 级最小可信回归基线文档
[ ] frontend 最小 E2E 基线已固定
[ ] backend 最小 pytest 基线已固定
[ ] 文档 / 启动协议变更时补跑的验证已固定
[ ] remote / 阶段发布额外 gate 已固定
[ ] 团队已不再依赖个人记忆决定最低验证范围
```

当前最小可信回归入口：

- `docs/governance/verification-baseline.md`

当前特别要保护的链路：

- auth route gates
- Creative main entry
- publish pool 主链路
- creative workflow contract
- local_ffmpeg contract
- OpenAPI / shared contract parity

通过标准：

> 以后任何继续开发，都不能在不自知的情况下打穿当前最小验证基线。

---

## 6. 收口项 E：Planning / 历史产物收口

目标：不要让下一阶段继续背着上一阶段的全部施工现场。

当前项目至少应检查：

```text
[ ] next-phase PRD / test spec / execution breakdown 仍在 active 区，且继续服务当前主线
[ ] 已被正式文档吸收的 planning，已逐步移出 active 区
[ ] `.omx/plans` 已明确分 active / archive
[ ] inventory / retention 文档已说明这些 planning 的去向规则
[ ] closeout / audit / issue / summary 类产物已尽量进入 docs/governance/inventory/ 或 archive，而不是散落根层
[ ] 明显一次性、低复用价值的材料，已归档或删除
```

重点参考：

- `docs/governance/policies/omx-plan-retention.md`
- `docs/governance/inventory/inventory-ledger.md`
- `docs/governance/inventory/post-mvp-doc-governance-closeout.md`
- `.omx/plans/`

通过标准：

> 你不需要继续把上一阶段所有 plans 都背在脑子里，仍然能知道当前 active 计划是什么、历史 planning 去哪里找。

---

## 7. 收口项 F：下一阶段决策收口

目标：收口不是只回顾历史，还要形成下一阶段启动条件。

当前项目至少应检查：

```text
[ ] 已能判断：当前阶段是否已经收尾到“能做决定”
[ ] 已能判断：下一阶段有且只有一条主线
[ ] 已明确：不属于主线的事项进入 backlog，而不是并行混入执行
[ ] 已形成 kickoff / PRD / test spec / execution breakdown 启动包
[ ] 已能说明：为什么当前先做 Creative-first 稳定化 / UI-UX 收口，而不是别的
[ ] 已能说明：这一主线依赖哪些 current truth 必须先准
```

当前项目的主线入口：

- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/next-phase-backlog.md`

通过标准：

> 当前项目不是停留在“有一堆能跑的东西”，而是已经知道下一阶段从哪里正式开始。

---

## 8. 不属于本轮收口的事情

下面这些事不应作为“收口完成”的前置条件：

```text
[ ] 不要求把所有旧文档都补齐
[ ] 不要求把所有数据库草稿都升级成正式设计
[ ] 不要求把所有历史边界文档逐份同步
[ ] 不要求一次性清空全部 backlog / TODO / 技术债
[ ] 不要求同时启动多个下一阶段方向
```

一句话：

> **收口的目标是形成可继续开发的基线，不是一次性把整个历史世界整理成完美状态。**

---

## 9. 本项目“收口完成”的判断问题

如果下面这些问题都能不依赖大量历史材料而回答出来，说明当前项目已经基本收口完成：

```text
[ ] 现在系统能做什么？
[ ] 当前主流程边界是什么？
[ ] 哪几份文档是当前真相？
[ ] 哪些旧文档已经不能继续指导开发？
[ ] 日常最小验证基线是什么？
[ ] 当前 active planning / archive planning 怎么区分？
[ ] 下一阶段唯一主线是什么？
[ ] 从哪份 kickoff 文档开始继续开发？
```

---

## 10. 一句话结论

> 对当前这个项目来说，MVP 后收口不是“再做一遍全局整理”，而是把 **实现状态、系统边界、文档入口、验证基线、planning 去向、下一阶段主线** 六件事收实。
