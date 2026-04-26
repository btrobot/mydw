# 项目健康评估

> 评估日期：2026-04-25  
> 评估者：Claude Code（基于代码库静态分析 + git 历史 + 文档审读）  
> 项目：DewuGoJin — 多账号内容管理桌面工具

---

## 总体结论

**健康评分：8.4 / 10 — 健康，有少量已知技术债**

项目整体结构清晰、测试体系成熟、文档治理规范。主要的弱点是两个已知的大文件
（`creative_service.py` / `CreativeDetail.tsx`）和 OMX 框架带来的认知开销——这两点
在切换到 Claude Code 工作流后可以逐步改善。

---

## 分项评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 后端架构 | 8.5 | 分层清晰；单一超大服务层可接受但需监控 |
| 前端架构 | 8.0 | 组件划分合理；CreativeDetail 在主动重构中 |
| 测试覆盖 | 8.5 | 94 个后端测试文件，22 个 E2E 套件；Auth 高度成熟 |
| 数据库/迁移 | 8.0 | 27 条自定义迁移全部落地；自定义模式需文档化 |
| 文档质量 | 9.0 | current/ 文档权威清晰；discss/ 工作日志组织有序 |
| 技术债 | 8.0 | 债务已知且在外部 roadmap 追踪，无隐性债 |
| 依赖健康 | 9.0 | 全部主要依赖版本当前，无已知漏洞 |
| Git 纪律 | 9.0 | 386 条 Lore 格式提交，intent-first 风格一致 |

---

## 关键发现

### 1. 优势

**测试体系成熟**  
后端 94 个测试文件，按域划分：Auth (14)、Creative (5)、Publishing (7)、Composition (3)、
Remote (23)、Governance (6)。`test_openapi_contract_parity.py`（26 KB）在 CI 层面
锁住了前后端 API 契约一致性，是防止漂移的核心保障。

**文档权威链清晰**  
`docs/current/` 是一级权威；`docs/archive/` 是历史参考；`discss/` 是工作日志。
三层不混用，新读者不会迷失。

**Generated Artifact 治理到位**  
`frontend/src/api/` 完全由 OpenAPI 生成，`npm run generated:check` 在 CI 中守门，
杜绝了手改生成代码这类低级错误。

**Lore Commit 执行一致**  
386 条提交均遵循 intent-first 格式，Constraint/Rejected/Directive/Tested 
trailers 覆盖关键决策，git blame 可直接追溯设计背景。

### 2. 已知问题

**creative_service.py — 3,254 行**  
位置：`backend/services/creative_service.py`  
包含：workbench 列表、详情、创建、更新、投稿、版本管理、review 流  
风险：调试定位慢，测试边界模糊，认知负担高  
状态：已在 discss/ 的 ralplan 文档中追踪，切片方案存在

**CreativeDetail.tsx — 2,228 行**  
位置：`frontend/src/features/creative/pages/CreativeDetail.tsx`  
包含：展示模式、创作流、投稿、错误恢复  
状态：P0 gap closure ralplan 已在 2026-04-25 生成（三版），主动重构中

**自定义迁移模式无文档**  
位置：`backend/migrations/`（27 个文件，`async def run_migration(engine)` 模式）  
无 README，无模板，无 rollback 说明  
影响：新开发者写迁移时容易踩坑

### 3. OMX 框架遗留影响

切换到 Claude Code 后需注意以下 OMX 遗产：

- `AGENTS.md`（412 行）：OMX 编排契约，其中的 **Lore Commit 协议** 和**工作协议**部分
  值得保留；模型路由、`$ralplan`/`$team` 等 OMX 专有语法在 Claude Code 中不适用
- `.omx/`（173 KB）：工作计划、采访记录、上下文缓存——可作为背景参考，不需迁移
- `discss/`（32 个文件）：健康的工作日志，继续维护即可
- `.codex/`（约 1.8 GB）：会话历史 + 插件缓存，可安全清理节省磁盘

---

## 切换 Claude Code 的评估

**适合切换的理由：**
- 代码库本身质量良好，不依赖 OMX 才能工作
- 测试体系完备，切换不会导致回归风险
- 文档层次清晰，新工作流可直接复用
- Lore Commit 协议与 Claude Code 工作方式兼容（只是 commit 格式规范，不是工具依赖）

**切换后需要调整的习惯：**
- OMX 的 `$ralplan` / `$team` 模式 → 改用 Claude Code 的 `EnterPlanMode` + 并行 Agent
- OMX 的 `$ralph` 持续完成模式 → 改用 Claude Code 的 Task 跟踪 + 手动确认重要决策
- OMX 的角色 prompt（executor/debugger/architect）→ Claude Code 自身具备这些能力，无需独立 prompt
- OMX 的自动提交逻辑 → Claude Code 不会自动提交，需显式请求

**建议保留的 AGENTS.md 内容：**  
Lore Commit 协议（格式 + trailer 词汇表）可迁移到根 `CLAUDE.md` 继续执行。
