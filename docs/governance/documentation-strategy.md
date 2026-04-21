# 文档体系策略

> Updated: 2026-04-12
> Status: Active

本文档描述**当前**文档体系应该如何组织，而不是记录早期“准备新增哪些文档”的历史设想。

## 目标

仓库文档需要同时满足两件事：

1. 让 GitHub 读者能快速找到当前真相
2. 让 OMX / Codex 多 agent 工作流有清晰的共享定义与运行时边界

因此，当前策略是把仓库内容明确分成四类：

- `current` — 当前默认阅读入口与 canonical truth
- `working` — 仍有工程价值，但不是唯一真相
- `historical` — 历史规划、旧架构、归档材料
- `runtime` — 本地运行时、agent、session、导出/缓存产物

## 当前入口

默认阅读路径固定为：

1. `README.md`
2. `docs/README.md`
3. `docs/current-architecture-baseline.md`
4. `docs/current-runtime-truth.md`
5. `docs/epic-7-doc-authority-matrix.md`
6. `docs/dev-guide.md`

这条路径回答“项目现在是什么样”。

## 目录分层策略

### 1. 根层 `docs/`

只保留：

- current / canonical docs
- active engineering docs
- 治理类说明（如 generated artifact、runtime boundary）

### 2. `docs/archive/`

统一承接：

- stale architecture docs
- old planning docs
- exported reference snapshots
- 历史分析/设计材料

### 3. 平行文档树

- `design/` 可以保留，但默认按 **working / historical** 理解
- 原 `dev-docs/` 与 `backend/docs/` 已进一步并入 `docs/archive/` 子树
- archive 命名应保持单一，例如 `design/archive/`，不要同时存在 `archive/` 与 `archived/`

## 多 agent / runtime 边界

与文档体系直接相关的核心原则：

### 应视为共享 repo 资产

- `AGENTS.md`
- `.codex/agents/`
- `.codex/prompts/`
- `.codex/skills/`

### 应视为 runtime / local artifacts

- `.omc/`
- `.omx/`
- `.codex/` 下 history / sqlite / sessions / tmp / shell snapshots
- 本地 session / runtime 输出目录
- 本地 mirror 路径（如 `D:/`）

这些路径可以帮助本地工作流运行，但不应和主文档入口竞争。

## 维护原则

1. **入口稳定**：README 与 docs index 永远先回答“先读什么”。
2. **真相单一**：current docs 才是默认事实源；stale docs 必须显式降级。
3. **归档优先于混放**：旧文档优先进入 archive，而不是继续停留在 docs 根层伪装成当前文档。
4. **共享定义与运行时分离**：workflow 定义可以入库，运行时状态不应持续污染 repo surface。
5. **用测试守住边界**：repo hygiene tests 应覆盖 ignore 规则、tracked runtime artifacts、archive 命名与阅读路径。

## 文档更新时机

以下场景应同步更新文档：

- 改变仓库结构
- 调整 current docs 入口
- 增减 tracked generated artifacts
- 调整 multi-agent workflow 的共享定义与 runtime 边界
- 把 historical docs 迁入 archive

## 与其他文档的关系

- `docs/README.md`：文档导航首页
- `docs/doc-inventory-ledger.md`：当前分类台账
- `docs/runtime-local-artifact-policy.md`：runtime / local artifact 边界
- `docs/multi-agent-guide.md`：如何在当前仓库里使用多 agent 协作
- `docs/archive/reference/system-architecture.md`：历史架构长文，保留作 archive/reference 参考，不再作为当前默认入口
