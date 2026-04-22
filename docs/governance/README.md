# Governance Docs Index / 治理文档导航

> 目的：给 `docs/governance/` 目录一个稳定的分类入口，避免治理文档都堆在同一层后难以判断“先看什么、去哪找、哪些是高频入口”。

## 1. 目录分类

当前 `docs/governance/` 分成 5 类：

| 分类 | 路径 | 适合放什么 |
| --- | --- | --- |
| Core | `docs/governance/*.md` | 高频治理入口、阶段切换、next-phase 启动相关文档 |
| Policies | `docs/governance/policies/` | 规则、保留策略、runtime/generated artifact 边界 |
| Inventory | `docs/governance/inventory/` | 盘点台账、分诊表、历史版本/过时文档清单 |
| Standards | `docs/governance/standards/` | 文档体系策略、检查清单、协作规范、标准说明 |
| Templates | `docs/governance/templates/` | 可复制使用的阶段收尾/选线模板 |

一句话：

> **Core 负责入口，Policies 负责规则，Inventory 负责盘点，Standards 负责方法，Templates 负责复用。**

---

## 2. Core：高频治理入口

这些文档仍保留在 `docs/governance/` 根层，因为它们是高频入口，不适合再继续下沉：

- `docs/governance/authority-matrix.md`
- `docs/governance/verification-baseline.md`
- `docs/governance/post-mvp-development-model.md`
- `docs/governance/phase-transition-checklist.md`
- `docs/governance/post-mvp-closeout-sequence.md`
- `docs/governance/omx-to-formal-doc-absorption-rules.md`
- `docs/governance/next-phase-backlog.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`
- `docs/governance/next-phase-pr1-workbench-manageability-plan.md`
- `docs/governance/next-phase-pr2-business-diagnostics-layering-plan.md`
- `docs/governance/next-phase-pr3-copy-and-state-unification-plan.md`

推荐理解：

- 想知道治理规则入口：先看 `authority-matrix.md`
- 想知道验证底线：看 `verification-baseline.md`
- 想知道 MVP 后如何推进：看 `post-mvp-development-model.md`
- 想知道阶段切换怎么做：看 `phase-transition-checklist.md`
- 想知道 `.omx` 工作文档何时吸收到正式 docs：看 `omx-to-formal-doc-absorption-rules.md`
- 想知道下一阶段怎么启动：看 `next-phase-*` 一组文档
- 想知道 PR-1 怎么具体切片：看 `next-phase-pr1-workbench-manageability-plan.md`
- 想知道 PR-2 如何做业务层 / 诊断层分层：看 `next-phase-pr2-business-diagnostics-layering-plan.md`
- 想知道 PR-3 如何统一文案、CTA 与四态：看 `next-phase-pr3-copy-and-state-unification-plan.md`

### next-phase 文档的最小阅读顺序

如果你现在要接手“下一阶段主线”，不要在 root 里来回猜，直接按下面顺序：

1. `docs/current/next-phase-kickoff.md`：当前唯一主线是什么
2. `docs/governance/next-phase-prd.md`：这一阶段到底做什么
3. `docs/governance/next-phase-test-spec.md`：做到什么才算通过
4. `docs/governance/next-phase-execution-breakdown.md`：按什么 PR 顺序推进
5. `docs/governance/next-phase-pr1-workbench-manageability-plan.md`
6. `docs/governance/next-phase-pr2-business-diagnostics-layering-plan.md`

当前 PR-2 的正式口径应以 `docs/` 为准，核心事实是：

- 默认业务面不再混排 diagnostics
- diagnostics 必须通过显式入口打开
- 打开状态应支持 URL 恢复，便于 deep-link、refresh 与 E2E 稳定复现

---

## 3. Policies：规则与边界

路径：

- `docs/governance/policies/generated-artifact-policy.md`
- `docs/governance/policies/manual-http-exceptions.md`
- `docs/governance/policies/runtime-local-artifact-policy.md`
- `docs/governance/policies/omx-plan-retention.md`

适合放：

- generated artifact 追踪策略
- runtime / local artifact 边界
- `.omx/plans` active / archive 分流

不适合再放在根层的原因：

- 这些文档重要，但属于**规则手册**，不是每日最高频入口

---

## 4. Inventory：盘点、分诊、清单

路径：

- `docs/governance/inventory/inventory-ledger.md`
- `docs/governance/inventory/current-project-mvp-closeout-checklist.md`
- `docs/governance/inventory/current-project-mvp-closeout-execution.md`
- `docs/governance/inventory/current-project-phase-transition-decision.md`
- `docs/governance/inventory/pr1-workbench-manageability-closeout.md`
- `docs/governance/inventory/pr2-business-diagnostics-layering-closeout.md`
- `docs/governance/inventory/post-mvp-doc-governance-closeout.md`
- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/inventory/epic-7-docs-parity-checklist.md`
- `docs/governance/inventory/epic-7-stale-doc-inventory.md`
- `docs/governance/inventory/epic-7-version-inventory.md`

适合放：

- 文档盘点台账
- 当前项目收口清单 / project closeout checklist
- 当前项目收口执行记录 / project closeout execution record
- 当前项目阶段切换决议 / project phase transition decision
- PR-1 Workbench 可管理性收口正式件 / PR closeout record
- PR-2 业务层 / 诊断层分层正式件 / PR closeout record
- 正式收口件 / closeout record
- 根层文档分诊与去向表
- 特定阶段/批次的清单、inventory、parity check

规则：

> **凡是“盘一次、列一张表、给清单”的文档，默认先考虑进 Inventory。**

---

## 5. Standards：方法、规范、协作说明

路径：

- `docs/governance/standards/ai-doc-system-spec.md`
- `docs/governance/standards/coding-standards.md`
- `docs/governance/standards/doc-checklist.md`
- `docs/governance/standards/docs-directory-placement-rules.md`
- `docs/governance/standards/documentation-strategy.md`
- `docs/governance/standards/domains-architecture-governance-boundary.md`
- `docs/governance/standards/multi-agent-guide.md`
- `docs/governance/standards/schema-parity-checklist.md`

适合放：

- 文档体系策略
- 编码与文档检查标准
- 多 agent 协作说明
- 偏“长期方法论”的说明文档

规则：

> **凡是“描述应该怎么做”的长期方法文档，默认先考虑进 Standards。**

---

## 6. Templates：可复用模板

路径：

- `docs/governance/templates/phase-closeout-template.md`
- `docs/governance/templates/next-phase-mainline-selection-template.md`

适合放：

- 阶段收尾模板
- 下一阶段选线模板
- 后续可复制使用的治理模板

---

## 7. 如何判断新文档放哪类

可以用下面的简单判断：

### 问题 1：它是不是高频入口？

如果是，优先考虑留在 root `docs/governance/`。

### 问题 2：它是不是规则/边界？

如果是，放 `policies/`。

### 问题 3：它是不是盘点/清单/分诊？

如果是，放 `inventory/`。

### 问题 4：它是不是长期方法/规范？

如果是，放 `standards/`。

### 问题 5：它是不是可复制复用的模板？

如果是，放 `templates/`。

---

## 8. 当前收口原则

这次分类遵循两个原则：

1. **高频入口留在根层**
2. **低频但重要的规则/台账/标准下沉到子目录**

也就是说：

> **不是把所有文档都塞进子目录，而是先把“应当分类的”分开，把“应当直达的”保留在入口层。**

---

## 9. 推荐阅读路径

如果你是第一次进入治理文档，建议按下面顺序：

1. `docs/governance/README.md`
2. `docs/governance/authority-matrix.md`
3. `docs/governance/verification-baseline.md`
4. `docs/governance/post-mvp-development-model.md`
5. `docs/governance/phase-transition-checklist.md`
6. `docs/current/next-phase-kickoff.md`

如果你要找具体规则，再进入：

- `docs/governance/policies/`
- `docs/governance/inventory/`
- `docs/governance/standards/`
- `docs/governance/templates/`

---

## 10. 按场景的阅读顺序

不同问题，不应该从同一个文档开始读。

### 场景 A：我想知道治理入口和当前规则边界

按下面顺序：

1. `docs/governance/README.md`
2. `docs/governance/authority-matrix.md`
3. `docs/governance/verification-baseline.md`

适合：

- 新接手项目的人
- 想知道 governance 文档“谁说了算”的人

### 场景 B：我想知道 MVP 后怎么继续推进

按下面顺序：

1. `docs/governance/post-mvp-development-model.md`
2. `docs/governance/phase-transition-checklist.md`
3. `docs/governance/post-mvp-closeout-sequence.md`
4. `docs/current/next-phase-kickoff.md`

适合：

- 想讨论“下一阶段怎么开始”的人
- 想做阶段收尾 / 选线 / 启动包的人

这 4 份核心文档的关系，可以压缩理解成下面这张阅读地图：

```text
post-mvp-development-model
  = 为什么 MVP 后必须先进入治理节奏
              ↓
post-mvp-closeout-sequence
  = 正确顺序：收尾 → 选线 → 定向收口 → 启动
              ↓
phase-transition-checklist
  = 真正切阶段前，怎么逐项检查能不能切
              ↓
current/next-phase-kickoff
  = 已经能切之后，下一阶段从哪里正式开始
```

如果只记一句话：

> **model 讲为什么，sequence 讲顺序，checklist 讲门槛，kickoff 讲起点。**

### 场景 B1：我想直接接手当前 next-phase / PR-2

先回到前面的“next-phase 文档的最小阅读顺序”，按那条主线读。

补充说明：

- `docs/` 负责 current truth / 正式指导口径
- `.omx/plans/` 负责 ralplan / ralph 的工作过程产物
- 当两边都存在同主题文档时，后续开发应先读 `docs/`，再回到 `.omx/plans/` 看切片细节与执行轨迹

### 场景 C：我想找具体规则

直接进入：

- `docs/governance/policies/`

优先看：

- `generated-artifact-policy.md`
- `runtime-local-artifact-policy.md`
- `omx-plan-retention.md`

### 场景 D：我想做盘点 / 分诊 / 清查

直接进入：

- `docs/governance/inventory/`

优先看：

- `inventory-ledger.md`
- `root-doc-triage.md`
- 各类 `epic-*inventory/checklist.md`

### 场景 E：我想知道长期规范 / 方法

直接进入：

- `docs/governance/standards/`

优先看：

- `documentation-strategy.md`
- `doc-checklist.md`
- `docs-directory-placement-rules.md`
- `domains-architecture-governance-boundary.md`
- `multi-agent-guide.md`
- `schema-parity-checklist.md`

### 场景 F：我想直接复用模板

直接进入：

- `docs/governance/templates/`

优先看：

- `phase-closeout-template.md`
- `next-phase-mainline-selection-template.md`

---

## 11. 新文档落点规则

以后新增治理文档时，优先按下面规则放置，而不是先随手丢到 root：

### 11.1 应该留在 root 的文档

满足任一条件，才考虑留在 `docs/governance/` 根层：

- 它是高频入口文档
- 它是阶段切换的直接入口
- 它会在 `docs/README.md` 的推荐路径中高频出现
- 它需要被人“一眼看到”，不适合再点进子目录

典型例子：

- `authority-matrix.md`
- `verification-baseline.md`
- `phase-transition-checklist.md`
- `post-mvp-development-model.md`
- `next-phase-*`

### 11.2 应该放进 `policies/` 的文档

满足下面特征时，放 `policies/`：

- 描述规则、保留策略、边界条件
- 更像“制度说明”而不是“阅读入口”
- 需要长期存在，但不是最高频打开

关键词提示：

- policy
- retention
- boundary
- artifact
- rule

### 11.3 应该放进 `inventory/` 的文档

满足下面特征时，放 `inventory/`：

- 以盘点、表格、清单、分诊为主
- 主要作用是“列出现状”而不是“解释长期规则”
- 常和 triage / stale / version / parity / ledger 相关

关键词提示：

- inventory
- ledger
- triage
- checklist
- stale
- version
- parity

### 11.4 应该放进 `standards/` 的文档

满足下面特征时，放 `standards/`：

- 描述“应该怎么做”
- 是长期方法、规范、协作方式
- 对新老阶段都适用，不只服务某一轮收口

关键词提示：

- standard
- strategy
- guide
- checklist
- spec

### 11.5 应该放进 `templates/` 的文档

满足下面特征时，放 `templates/`：

- 主要价值是复用
- 读者通常会复制后填写
- 文档本身是一个“骨架”而不是事实说明

关键词提示：

- template
- starter
- skeleton

---

## 12. 命名与维护约定

为了避免 governance 目录再次变乱，新增文档时建议遵守：

1. **先决定分类，再命名**
2. 不要把 inventory / policy / standard 混在一个文件名和一个文档里
3. 如果一个文档已经从“入口”退化为“规则手册”或“历史盘点”，应考虑下沉
4. 如果一个文档开始变成团队高频入口，才考虑提升到 root
5. 每次新增 governance 文档后，都检查是否需要更新：
   - `docs/governance/README.md`
   - `docs/README.md`
   - 相关 doc-truth tests

一句话：

> **先分类，再落点；先入口，后细则；不要让 root 再次变成杂物堆。**

---

## 13. 文档放置决策表（5 秒判断版）

如果你只是想快速判断“这份新文档到底该放哪”，直接用这张表：

| 如果这份文档主要是…… | 放这里 |
| --- | --- |
| 高频入口 / 阶段切换入口 / 推荐阅读路径中的高频文档 | `docs/governance/` root |
| 规则 / 边界 / retention / artifact policy | `docs/governance/policies/` |
| 盘点 / triage / ledger / stale/version/parity checklist | `docs/governance/inventory/` |
| 长期规范 / strategy / guide / checklist / system spec | `docs/governance/standards/` |
| 可复制复用的模板 / skeleton / starter | `docs/governance/templates/` |

如果还是拿不准，就按下面顺序问自己：

1. 它是不是每周都会被高频打开的治理入口？  
   - 是：优先考虑 root
2. 它是不是在定义“规则”而不是“现状”？  
   - 是：优先考虑 `policies/`
3. 它是不是在列清单、台账、盘点结果？  
   - 是：优先考虑 `inventory/`
4. 它是不是在描述长期方法或标准做法？  
   - 是：优先考虑 `standards/`
5. 它是不是拿来复制后填写的？  
   - 是：优先考虑 `templates/`

一句话速记：

> **入口放 root，规则进 policies，盘点进 inventory，规范进 standards，复用进 templates。**
