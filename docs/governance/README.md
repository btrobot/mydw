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
- `docs/governance/next-phase-backlog.md`
- `docs/governance/next-phase-prd.md`
- `docs/governance/next-phase-test-spec.md`
- `docs/governance/next-phase-execution-breakdown.md`

推荐理解：

- 想知道治理规则入口：先看 `authority-matrix.md`
- 想知道验证底线：看 `verification-baseline.md`
- 想知道 MVP 后如何推进：看 `post-mvp-development-model.md`
- 想知道阶段切换怎么做：看 `phase-transition-checklist.md`
- 想知道下一阶段怎么启动：看 `next-phase-*` 一组文档

---

## 3. Policies：规则与边界

路径：

- `docs/governance/policies/generated-artifact-policy.md`
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
- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/inventory/epic-7-docs-parity-checklist.md`
- `docs/governance/inventory/epic-7-stale-doc-inventory.md`
- `docs/governance/inventory/epic-7-version-inventory.md`

适合放：

- 文档盘点台账
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
- `docs/governance/standards/documentation-strategy.md`
- `docs/governance/standards/multi-agent-guide.md`

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
