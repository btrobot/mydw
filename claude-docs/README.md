# claude-docs 文档索引

> 创建日期：2026-04-25  
> 目的：记录从 oh-my-codex (OMX) 切换到 Claude Code 时的项目评估与工作指南

---

## 文档列表

| 文档 | 用途 |
|------|------|
| [project-health.md](./project-health.md) | 项目整体健康评估（评分、关键发现、切换建议） |
| [architecture-for-claude.md](./architecture-for-claude.md) | 针对 Claude Code 工作方式的架构指南（踩坑预警、权威来源） |
| [dev-workflow.md](./dev-workflow.md) | 日常开发工作流（OMX vs Claude Code 对照、标准流程、Lore commit） |
| [tech-debt-roadmap.md](./tech-debt-roadmap.md) | 技术债清单与优先级 Roadmap |
| [creative-detail-analysis.md](./creative-detail-analysis.md) | CreativeDetail 交互设计分析（设计意图、实现差距、解决方案） |
| [creative-detail-user-confirmation.md](./creative-detail-user-confirmation.md) | CreativeDetail 用户确认纪要（实时生效、A/B/C 三区、废弃 legacy editor） |
| [creative-detail-redesign-proposal.md](./creative-detail-redesign-proposal.md) | CreativeDetail 精简设计方案（Tab 切换、实时生效、删除 D/E） |
| [creative-detail-implementation-plan.md](./creative-detail-implementation-plan.md) | CreativeDetail 精简重构实现计划（Phase 1-3、文件变更、测试策略） |

## 与现有文档的关系

这个目录**不取代** `docs/current/`——那里是代码库的权威架构文档。  
`claude-docs/` 是**工具迁移层**：专门回答"换成 Claude Code 之后怎么工作"这个问题。

权威阅读顺序：
1. `CLAUDE.md`（根）— 项目命令和顶层约定
2. `claude-docs/architecture-for-claude.md` — Claude Code 工作时的关键注意事项
3. `docs/current/architecture.md` — 完整系统架构
4. `docs/current/runtime-truth.md` — 运行时事实
