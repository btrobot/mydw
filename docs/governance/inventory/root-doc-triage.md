# 根层文档分诊表（Root Doc Triage）

> Version: 1.0.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active

> 目的：把仍停留在 `docs/` 根目录、但不属于 current entrypoint 的文档逐份分类，明确它们下一步应该保留、下沉、归档还是删除。

## 1. 范围说明

本表只处理 `docs/` 根目录下的**未归类文档**，不重复处理：

- `README.md`
- `docs/README.md`
- `docs/runtime-truth.md`（入口 alias）
- 已经位于 `docs/current/`、`docs/governance/`、`docs/guides/`、`docs/specs/`、`docs/domains/`、`docs/archive/` 的文档

本阶段先做**分类与去向收口**，不在这里直接执行大规模 move/delete。

## 2. 分诊规则

| 结果 | 含义 |
| --- | --- |
| 保留为 active domain doc | 仍有持续工程价值，但位置不该继续停在 `docs/` 根目录 |
| 下沉到 guide / governance / specs / domains | 内容有效，应该进入更明确的文档树 |
| archive | 主要保留为历史参考，不再作为当前工作入口 |
| 删除候选 | 只剩命令痕迹 / 临时产物 / 已被别处吸收 |

## 3. 当前根层文档去向表

| 文件 | 当前作用判断 | 当前引用 / 依赖 | 分诊结果 | 建议目标位置 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `docs/backup-scope.md` | system backup 最小真实范围说明 | `docs/domains/system/settings-truth-matrix.md` | 下沉到 domains | `docs/domains/system/backup-scope.md` | 属于系统运行/备份边界，不应留在根层 |
| `docs/chat-req.md` | 早期 PM 沟通需求输入 | `docs/specs/requirements-spec.md` | 下沉到 specs | `docs/specs/requirements-sources/chat-req.md` | 保留为 requirements source，不是当前产品真相 |
| `docs/coze-integration.md` | Coze 接入 draft 说明 | 无当前主入口引用 | archive | `docs/archive/reference/coze-integration.md` | 当前主链路已是 Creative + local/runtime workflow；该文档暂不应和 current docs 竞争 |
| `docs/dewu-page-structure.md` | 得物页面抓取/解析参考 | 无当前主入口引用 | 下沉到 domains | `docs/domains/products/dewu-page-structure.md` | 若继续维护解析链路，应成为 products/domain reference |
| `docs/domain-model-analysis.md` | 早期从 Task-first 向新模型迁移的分析稿 | 只被历史 planning 文档引用 | archive | `docs/archive/analysis/domain-model-analysis.md` | 当前架构已由 `docs/current/architecture.md` 与 Creative closeout 文档接管 |
| `docs/frontend-ui-issues-and-improvements.md` | 当前前端 UI/UX 问题盘点与改进建议 | `docs/README.md`、reports | 保留为 active domain doc | `docs/domains/creative/workbench-ui-issues.md` | 仍是下一阶段 backlog 的高价值输入 |
| `docs/frontend-ui-ux-closeout-final-summary.md` | 前端 UI/UX closeout 交付总结 | reports 引用 | archive | `docs/archive/history/frontend-ui-ux-closeout-final-summary.md` | 属于阶段收口证明，不应继续占据根层 |
| `docs/frontend-ui-ux-closeout-ralplan-command.md` | 一次性规划命令/提示词记录 | 无当前主入口引用 | 删除候选 | 删除，必要时保存在 `.omx/` 或 planning artifact | 不属于 repo 长期知识资产 |
| `docs/init-req.md` | 最初功能树 / 原始需求输入 | `docs/specs/requirements-spec.md`、`design/运行日志分析.md` | 下沉到 specs | `docs/specs/requirements-sources/init-req.md` | 保留为原始需求来源，不再伪装成当前规范 |
| `docs/manual-axios-exceptions.md` | generated client 例外登记表 | `docs/guides/openapi-generation-workflow.md` | 下沉到 governance | `docs/governance/manual-http-exceptions.md` | 本质上是工程治理规则 |
| `docs/schema-parity-checklist.md` | OpenAPI regeneration 前的 contract freeze 清单 | `docs/guides/openapi-generation-workflow.md` | 下沉到 governance | `docs/governance/schema-parity-checklist.md` | 更接近 API / generated artifact governance |

## 4. 压缩后的判断

从根层文档看，当前问题不是“文档不够多”，而是**文档角色混放**：

1. **requirements source** 还停在根层  
   - `init-req.md`
   - `chat-req.md`
2. **工程治理清单** 还停在根层  
   - `manual-axios-exceptions.md`
   - `schema-parity-checklist.md`
3. **专题 domain 说明** 还停在根层  
   - `backup-scope.md`
   - `dewu-page-structure.md`
   - `frontend-ui-issues-and-improvements.md`
4. **历史 closeout / analysis / command artifact** 仍然显眼  
   - `domain-model-analysis.md`
   - `frontend-ui-ux-closeout-final-summary.md`
   - `frontend-ui-ux-closeout-ralplan-command.md`
   - `coze-integration.md`

## 5. 推荐执行顺序

### Batch 1 — 低风险下沉

优先移动：

- `backup-scope.md`
- `manual-axios-exceptions.md`
- `schema-parity-checklist.md`
- `dewu-page-structure.md`

原因：这些文档仍有效，只是位置不对。

### Batch 2 — requirements source 收口

再处理：

- `init-req.md`
- `chat-req.md`

原因：它们仍被 `requirements-spec.md` 使用，但角色应明确为“原始输入”，而不是当前规范。

### Batch 3 — historical / delete 收口

最后处理：

- `domain-model-analysis.md`
- `frontend-ui-ux-closeout-final-summary.md`
- `coze-integration.md`
- `frontend-ui-ux-closeout-ralplan-command.md`

原因：这批文档需要结合引用关系和是否仍有 owner 再决定 archive 还是删除。

## 6. 结论

如果只记住一句话：

> `docs/` 根目录接下来不该继续承载“原始需求输入、治理清单、历史 closeout 和一次性命令记录”这几类内容；它们都已经有更合适的去处。
