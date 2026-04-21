# Runtime / Local Artifact Policy

> 目的：明确哪些目录属于项目的**运行时/本地 agent 资产**，哪些才是团队应优先阅读和维护的项目文档。  
> 本文档不重写当前架构或运行真相；它只定义 **文档体系边界** 与 **后续治理策略**。

## Boundary rule

以下目录/路径默认**不属于项目主文档入口**：

- `.codex/`
- `.omx/`
- `.omc/`
- 本地 session / runtime 输出目录（仓库中不再保留 `production/`）

它们可能包含：

- agent prompts / skills / config
- orchestration state / plans / logs / context snapshots
- 导出型研究材料
- 会话产物 / session state
- 本地数据库、日志、shell snapshots、历史记录

这些内容对 agent/runtime 运维或历史回溯可能有价值，但不应和 `README.md`、`docs/README.md`、`docs/current/architecture.md`、`docs/current/runtime-truth.md` 竞争“先读什么”的位置。

## Current repo reality

当前仓库里，这些运行时/本地资产里有一部分已经被提交：

- `.codex/` 中既有 prompts / skills / agents，也有 logs、sqlite、history、sessions、snapshots
- `.omx/` 中既有 plans/context，也有 runtime state、logs、notepad、metrics
- `.omc/` 中主要是 Claude/OMC 会话与 mission 运行状态（session、state、project-memory 等）

这意味着：

1. 它们目前已经是 repo 内容的一部分；
2. 但它们仍应按 **runtime/local artifacts** 理解，而不是按产品文档理解；
3. 后续整理应先明确 policy，再决定哪些继续保留、哪些改为 ignore、哪些仅保留模板。

## What `.gitignore` already signals

当前 `.gitignore` 已经部分表达了这种边界：

- `production/` 目录已不再保留在仓库中；如本地运行仍需产生日志/会话输出，应视作本地 runtime 输出并被 Git 忽略
- `.omx/` 默认忽略
- `.omc/` 默认忽略（当前若有已跟踪文件，需单独清理 tracked exceptions）
- `.codex/*` 默认忽略，但对 `agents/`、`skills/`、`prompts/` 做了例外放行

这说明仓库已经隐含存在一个 policy：

- **工具定义 / prompts / skills** 可以被视为较 durable 的 repo 资产
- **logs / sessions / sqlite / runtime state** 更偏本地或瞬态资产

但这个策略目前还没有在项目文档中显式写清楚，这就是本文件存在的原因。

## Recommended reading behavior

当你在仓库里看到这些目录时，应按下面方式理解：

### `.codex/`
- 主要是 Codex 本地 agent/runtime 资产
- `agents/`、`prompts/`、`skills/` 可视作工作流/agent 定义
- `history.jsonl`、`logs_*.sqlite`、`sessions/`、`shell_snapshots/` 不应被当作项目文档阅读入口

### `.omx/`
- 主要是 OMX orchestration/runtime 资产
- `plans/`、`context/` 可能帮助理解历史执行路径
- `plans/archive/` 用于存放已被 `docs/` 正式文档吸收的历史 planning artifacts
- `state/`、`logs/`、`notepad.md`、`metrics.json` 不应被当作当前产品文档真相

### `.omc/`
- 主要是 OMC/Claude runtime 资产
- 常见内容包括 `sessions/`、`state/`、`project-memory.json`
- 这些内容用于会话/调度状态，不应被当作项目文档阅读入口

### `docs/archive/exports/`
- 导出型参考材料 / snapshots
- 这些内容已经从根目录移入 `docs/archive/exports/`
- 可以作为补充资料，但不应自动被当作 current authoritative docs

### Local runtime output directories
- 仓库中已不再保留 `production/`
- 如本地工作流仍需要会话日志、状态快照或类似输出，应把它们视为 **local runtime output**，不属于 repo surface
- 旧的 `production/session-*` 语义现在仅作为历史上下文存在于 archive 文档中

### `D:` mirror paths
- 当前它们更像由本地 `MATERIAL_BASE_PATH` 默认值派生出来的本地目录镜像
- 在现有配置仍默认指向 `D:/系统/桌面/得物剪辑/待上传数据` 的前提下，不应把“目录存在”本身当成仓库结构真相
- 当前治理目标是：**不让这些路径被 Git 跟踪，也不让它们出现在项目主文档入口中**

## Claude Code retirement note

仓库当前已迁移到 **OMX + Codex surfaces**（`AGENTS.md`, `.codex/skills/`, `.codex/prompts/`, `.omx/plans/` 等），不再把旧的 Claude Code 工作区作为活跃工作流目录。

如在历史文档中仍看到 Claude Code 或旧工作区引用，应按**历史上下文**理解，而不是当前执行面。

## Future policy direction / 后续策略

后续建议把这些目录再分成三类治理：

1. **Keep committed**
   - 确实需要 repo 共享的 agent definitions / prompts / skills / templates
2. **Keep committed but clearly non-primary**
   - 导出型参考材料、少量示例/模板、计划产物
3. **Prefer ignore or template-only**
   - logs
   - sqlite/db state
   - session histories
   - shell snapshots
   - transient runtime state

## Immediate rule for current cleanup work

在当前这轮目录/文档整理中：

- 不把 `.codex/`、`.omx/`、`.omc/`、本地 runtime 输出目录当作项目主文档簇
- 先在导航和 inventory 中标明它们的 runtime/local 属性
- `.omx/plans/` 只保留仍直接驱动开发的计划文件；已被正式文档吸收的计划下沉到 `.omx/plans/archive/`
- 是否进一步移动、瘦身、ignore 化，放到后续专门的 policy/cleanup PR 决定
