# Current Project MVP Closeout Execution / 当前项目 MVP 收口执行记录

> Version: 1.0.0  
> Updated: 2026-04-22  
> Owner: Tech Lead / Codex  
> Status: Recorded execution

> 目的：按照 `docs/governance/inventory/current-project-mvp-closeout-checklist.md`，把当前项目的 MVP 收口执行结果逐项落成正式记录。  
> 这份文档回答的不是“理论上应该收什么”，而是：**这次到底已经收到了哪一步、证据在哪、还剩什么残留项。**

---

## 1. 执行结论

一句话结论：

> 当前项目已经从“能跑起来的 MVP”收口到“可以继续启动下一阶段开发的基线”，但 `.omx/plans` 中仍有一小批 pending-manual-review 计划文件保留在 active 区，作为已知残留项继续跟踪。

本轮判断：

| 收口项 | 状态 | 结论 |
| --- | --- | --- |
| A. 实现状态收口 | completed | 当前系统完成度、已完成/未完成、下一阶段 backlog 已能清楚说明 |
| B. 系统边界收口 | completed | Creative-first、task/publish/composition、local_ffmpeg V1 等关键边界已形成 current truth |
| C. 文档体系收口 | completed | current truth 入口、治理入口、archive 导航与 authority 分层已建立 |
| D. 验证基线收口 | completed | 最小可信回归基线已显式化并具备测试保护 |
| E. Planning / 历史产物收口 | mostly completed | active / archive 已显式分流，但仍有少量 pending review plans 保留 |
| F. 下一阶段决策收口 | completed | 下一阶段唯一主线、kickoff、PRD、test spec、execution breakdown 已成套存在 |

---

## 2. A：实现状态收口

### 状态

> **completed**

### 已执行到位的内容

- 当前系统已不再被描述为“单体 Electron 应用”，而是：
  - 本地 **Creative-first** 工作台（`frontend/` + `backend/`）
  - 远程授权控制平面（`remote/`）
- 当前项目已能清楚说明：
  - 哪些主链路已跑通
  - 哪些能力还处于“可运行但未完全产品化”
  - 哪些问题进入了 next-phase backlog

### 证据

- `docs/current/architecture.md`
- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-backlog.md`

### 当前结论

当前 MVP 已能稳定回答：

- 系统现在由哪些部分组成
- 主业务入口为什么已经是 Creative-first
- 下一阶段为什么不是继续讨论主路径，而是进入 UI/UX 稳定化收口

---

## 3. B：系统边界收口

### 状态

> **completed**

### 已执行到位的内容

- 本地工作台 vs remote 控制平面的职责边界已清楚
- CreativeWorkbench / CreativeDetail / Dashboard / auth shell 的页面职责已清楚
- task / publish / composition 语义已明确分层
- `local_ffmpeg V1` 已从“设想”收成“当前冻结能力”
- 本地 FFmpeg 与 `coze` 路径不再混写

### 证据

- `docs/current/architecture.md`
- `docs/current/runtime-truth.md`
- `docs/domains/tasks/task-management-domain-model.md`
- `docs/domains/tasks/task-semantics.md`
- `docs/domains/publishing/local-ffmpeg-composition.md`

### 当前结论

后续开发已经不应再把下面这些问题当作开放问题：

- 主路径是不是 Task-first
- `local_ffmpeg` 是不是还等同于更大的 composition 草案
- `CompositionPoller` 是否服务本地 FFmpeg

这些边界已经有 current truth。

---

## 4. C：文档体系收口

### 状态

> **completed**

### 已执行到位的内容

- `docs/` 根层已只保留默认入口
- `docs/current/architecture.md`、`docs/current/runtime-truth.md`、`docs/governance/authority-matrix.md`、`docs/governance/verification-baseline.md`、`docs/current/next-phase-kickoff.md` 已形成 current truth 主入口组
- `docs/governance/README.md` 已建立 Core / Policies / Inventory / Standards / Templates 分类
- `docs/archive/README.md` 及二级 README 已建立历史导航
- closeout / inventory / checklist 类文档已回收到 `docs/governance/inventory/`

### 证据

- `docs/README.md`
- `docs/governance/README.md`
- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/inventory/inventory-ledger.md`
- `docs/governance/inventory/post-mvp-doc-governance-closeout.md`
- `docs/archive/README.md`

### 当前结论

当前仓库已不再依赖“翻根层 + 翻历史长文”来判断谁说了算。  
文档入口层面的收口已达到下一阶段可用状态。

---

## 5. D：验证基线收口

### 状态

> **completed**

### 已执行到位的内容

- repo 级最小可信回归基线已显式定义
- frontend 最小 E2E、backend 最小 pytest、文档/启动协议补跑、remote 发布额外 gate 已分层说明
- 文档索引与高价值 current truth 说法已被 doc truth tests 锁住

### 证据

- `docs/governance/verification-baseline.md`
- `backend/tests/test_doc_truth_fixes.py`
- `backend/tests/test_epic7_docs_baseline.py`

### 当前结论

“以后继续开发至少跑什么”已经不再依赖个人记忆。  
当前最小验证基线已具备治理意义上的稳定性。

---

## 6. E：Planning / 历史产物收口

### 状态

> **mostly completed**

### 已执行到位的内容

- `.omx/plans` 已按 active / archive 显式分流
- 已被正式文档吸收的多批 planning 已进入 `.omx/plans/archive/`
- retention 规则已明文化
- inventory / closeout / ledger 已能说明 planning 与正式文档之间的关系

### 证据

- `docs/governance/policies/omx-plan-retention.md`
- `docs/governance/inventory/inventory-ledger.md`
- `.omx/plans/`
- `.omx/plans/archive/`

### 当前残留项

根据 `docs/governance/policies/omx-plan-retention.md`，下面这批文件仍保留在 `.omx/plans/` pending manual review：

- `prd-login-bs-alignment-pr-plan.md`
- `test-spec-login-bs-alignment-pr-plan.md`
- `prd-task-management-page-closeout.md`
- `test-spec-task-management-page-closeout.md`
- `prd-work-driven-creative-flow-refactor.md`
- `test-spec-work-driven-creative-flow-refactor.md`

### 当前结论

Planning 收口已经**足够支持下一阶段继续推进**，但还没有做到“active 区完全清爽”。  
因此，本项判定为 **mostly completed**，并把 pending review files 作为残留风险保留。

---

## 7. F：下一阶段决策收口

### 状态

> **completed**

### 已执行到位的内容

- 下一阶段唯一主线已明确：
  - **Creative-first 稳定化 / UI-UX 收口主线**
- kickoff / PRD / test spec / execution breakdown 已成套存在
- backlog 已压缩，未进入主线的事项不再与当前执行并列竞争

### 证据

- `docs/current/next-phase-kickoff.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/next-phase-backlog.md`

### 当前结论

当前项目已经不是“有很多可做方向但不知道先干什么”，而是已经有：

- 唯一主线
- 启动包
- 对应验证口径
- 对应执行分解

---

## 8. 残留风险 / Remaining risks

当前仍保留但不阻塞下一阶段启动的风险：

1. `.omx/plans` active 区还有少量 pending review 文件  
   - 影响：active / archive 边界还不够彻底  
   - 当前处理：继续按 retention 规则逐批处理

2. 一些 working / historical 材料仍有进一步吸收空间  
   - 影响：历史追溯时仍可能读到更多上下文  
   - 当前处理：优先保 current truth，不做全量同步

3. 下一阶段 UI/UX 主线仍需要在执行中继续补充路线绑定 truth  
   - 影响：部分页面/文案/状态反馈文档会在执行期继续细化  
   - 当前处理：按 kickoff + PRD + test spec + breakdown 继续推进

---

## 9. Exit decision / 退出结论

> 当前项目的 MVP 收口执行，已达到 **可以进入下一阶段持续开发** 的程度。  
> 本轮不再要求“全量补完所有历史文档”，而是确认当前项目已经拥有足够稳定的 current truth、验证基线、planning 分流与下一阶段启动包。

如果只记一句话：

> **这次执行真正完成的，是把当前项目从“能跑的 MVP”收成“可继续推进的基线”；未完成的少量 planning 残留，已被降级为可继续跟踪的后续项。**
