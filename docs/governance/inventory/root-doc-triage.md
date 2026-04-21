# 根层文档分诊表 / 去向盘点表（Root Doc Triage）

> Version: 2.1.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把仍然停留在 `docs/` 根目录、但不属于默认入口的文档逐份分类，明确它们应该下沉、归档、删除，还是暂时保留。

---

## 1. 范围说明

本表只处理 `docs/` 根目录下的**未归类文档**，不重复处理：

- `README.md`
- `docs/README.md`
- `docs/runtime-truth.md`（入口 alias）
- 已经位于 `docs/current/`、`docs/domains/`、`docs/governance/`、`docs/guides/`、`docs/specs/`、`docs/archive/` 的文档

本轮先做**去向盘点与分类收口**，再按批次执行 move/archive/delete。

---

## 2. 判定规则：先四分法，再补充树

根层文档先按下面顺序判断：

1. 能不能进入 `docs/current/`
2. 能不能进入 `docs/domains/`
3. 能不能进入 `docs/governance/`
4. 能不能进入 `docs/guides/`

如果四分法都不适合，再判断是否应该进入：

- `docs/specs/`（需求来源 / requirements source / supporting spec）
- `docs/archive/`（历史资料）
- 删除候选（一次性命令记录、临时产物、已被其他文档吸收）

一句话：

> **优先按 current / domains / governance / guides 四分法收口；放不进去的，再走 specs / archive / delete。**

---

## 3. Batch 1 已完成：低风险下沉

本批已完成的移动：

| 原路径 | 新路径 | 结果 |
| --- | --- | --- |
| `docs/backup-scope.md` | `docs/domains/system/backup-scope.md` | 已下沉到 domains |
| `docs/dewu-page-structure.md` | `docs/domains/products/dewu-page-structure.md` | 已下沉到 domains |
| `docs/manual-axios-exceptions.md` | `docs/governance/policies/manual-http-exceptions.md` | 已下沉到 governance/policies |
| `docs/schema-parity-checklist.md` | `docs/governance/standards/schema-parity-checklist.md` | 已下沉到 governance/standards |

这些文档已不再占据 `docs/` 根目录。

---

## 4. 当前 docs 根目录待分流文档

当前仍在根层、需要继续处理的文档：

- `docs/chat-req.md`
- `docs/coze-integration.md`
- `docs/domain-model-analysis.md`
- `docs/frontend-ui-issues-and-improvements.md`
- `docs/frontend-ui-ux-closeout-final-summary.md`
- `docs/frontend-ui-ux-closeout-ralplan-command.md`
- `docs/init-req.md`

---

## 5. 当前待处理去向盘点表

| 文件 | 当前角色判断 | 四分法第一判断 | 分诊结果 | 建议目标位置 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `docs/chat-req.md` | 早期 PM 沟通需求输入 | 四分法都不适合 | 下沉到 supporting specs | `docs/specs/requirements-sources/chat-req.md` | 保留为 requirements source，不是当前产品真相 |
| `docs/coze-integration.md` | Coze 接入 draft 说明 | 四分法都不适合 | archive | `docs/archive/reference/coze-integration.md` | 当前主链路已不是 Coze integration 主线，不应继续与 current docs 竞争 |
| `docs/domain-model-analysis.md` | 早期领域迁移分析稿 | 四分法都不适合 | archive | `docs/archive/analysis/domain-model-analysis.md` | 当前架构已由 `docs/current/architecture.md` 等文档接管 |
| `docs/frontend-ui-issues-and-improvements.md` | 当前前端 UI/UX 问题盘点与改进建议 | `domains/` | 下沉到 domains | `docs/domains/creative/workbench-ui-issues.md` | 仍是下一阶段 backlog 的高价值输入，但不应停留在根层 |
| `docs/frontend-ui-ux-closeout-final-summary.md` | UI/UX closeout 交付总结 | 四分法都不适合 | archive | `docs/archive/history/frontend-ui-ux-closeout-final-summary.md` | 属于阶段收口证明，不应继续占据根层 |
| `docs/frontend-ui-ux-closeout-ralplan-command.md` | 一次性 ralplan 命令记录 | 四分法都不适合 | 删除候选 | 删除；如需保留，转入 `.omx/` 或 planning artifact | 不属于 repo 长期知识资产 |
| `docs/init-req.md` | 最初需求树 / 原始输入 | 四分法都不适合 | 下沉到 supporting specs | `docs/specs/requirements-sources/init-req.md` | 保留为 requirements source，不再伪装成当前规范 |

---

## 6. 按目标目录聚合

### 6.1 进入 `docs/domains/`

- `docs/frontend-ui-issues-and-improvements.md`

### 6.2 进入 `docs/specs/`

- `docs/chat-req.md`
- `docs/init-req.md`

### 6.3 进入 `docs/archive/`

- `docs/coze-integration.md`
- `docs/domain-model-analysis.md`
- `docs/frontend-ui-ux-closeout-final-summary.md`

### 6.4 删除候选

- `docs/frontend-ui-ux-closeout-ralplan-command.md`

---

## 7. 当前结论

从根层文档看，当前剩余问题已经收敛为三类：

1. requirements source 还停在根层  
   - `docs/init-req.md`
   - `docs/chat-req.md`
2. 领域问题盘点还停在根层  
   - `docs/frontend-ui-issues-and-improvements.md`
3. 历史 closeout / analysis / command artifact 仍然显眼  
   - `docs/domain-model-analysis.md`
   - `docs/frontend-ui-ux-closeout-final-summary.md`
   - `docs/frontend-ui-ux-closeout-ralplan-command.md`
   - `docs/coze-integration.md`

---

## 8. 推荐执行顺序

### Batch 1：低风险下沉

已完成。

### Batch 2：requirements source + 剩余 active doc 收口

下一批建议处理：

- `init-req.md`
- `chat-req.md`
- `frontend-ui-issues-and-improvements.md`

### Batch 3：historical / delete 收口

最后处理：

- `domain-model-analysis.md`
- `frontend-ui-ux-closeout-final-summary.md`
- `coze-integration.md`
- `frontend-ui-ux-closeout-ralplan-command.md`

原因：这批文档需要结合引用关系与 owner 决定 archive 还是删除。

---

## 9. 一句话结论

> Batch 1 已经把低风险可下沉文档移出 `docs/` 根目录；接下来根层主要剩 requirements source、一个 active 领域盘点、以及几份历史收口/命令类文档。

