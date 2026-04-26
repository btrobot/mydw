# Claude Code 开发工作流

> 从 oh-my-codex (OMX) 切换到 Claude Code 的工作方式指南  
> 更新：2026-04-25

---

## 核心原则变化

| OMX 模式 | Claude Code 等价方式 |
|----------|---------------------|
| `$ralplan` — 生成计划文档后审批 | `EnterPlanMode` — 在对话中探索 + 等待用户审批 |
| `$team` — 并行多 agent 执行 | Claude Code 自身并行工具调用；复杂任务用 Agent 工具 |
| `$ralph` — 持续单 owner 完成循环 | 对话内持续工作；Task 工具跟踪进度 |
| `$deep-interview` — 澄清需求 | 直接对话提问 |
| 自动提交（approved slice → auto-commit） | **不自动提交**，完成后明确请求 `/commit` |
| Role prompt（executor/debugger/architect） | Claude Code 内置，无需 prompt 切换 |

**最重要的变化**：Claude Code 不会在没有指令的情况下提交代码或推送分支。
所有破坏性操作（push、reset、drop migration）都会先确认。

---

## 日常开发启动

### 方式一：纯前端开发（最常用）

```bash
# 终端 1 — 启动后端
cd backend
python -m uvicorn main:app --reload --port 8000

# 终端 2 — 启动前端 Vite 开发服务器
cd frontend
npm run dev
# 浏览器访问 http://localhost:5173
```

### 方式二：完整 Electron 桌面调试

```bash
cd frontend
npm run dev:electron
# 自动启动 Electron + 管理 backend 生命周期
```

### 方式三：一键脚本（Windows）

```bat
dev.bat          # 启动全部
scripts/stop-all.bat  # 停止全部
scripts/status-all.bat  # 查看运行状态
```

---

## 常见任务的标准流程

### 添加后端 API 端点

1. 在 `backend/api/<domain>.py` 添加路由
2. 在 `backend/services/<domain>_service.py` 添加业务逻辑
3. 如需新 schema，在 `backend/schemas/<domain>.py` 定义
4. 运行测试：`pytest backend/tests/test_<domain>_api.py`
5. 重新生成前端 SDK：
   ```bash
   cd frontend && npm run generated:regenerate
   ```
6. 更新 `docs/current/runtime-truth.md`（如有新 API surface）

### 修改数据库 schema

1. 创建新迁移文件 `backend/migrations/028_<intent>.py`
   ```python
   async def run_migration(engine: AsyncEngine) -> None:
       async with engine.connect() as conn:
           result = await conn.execute(text("PRAGMA table_info(<table>)"))
           if "<new_col>" not in [r[1] for r in result]:
               await conn.execute(text("ALTER TABLE <table> ADD COLUMN ..."))
           await conn.commit()
   ```
2. 在迁移运行器中注册
3. 测试：重启 backend，确认迁移无错误日志
4. 运行相关测试

### 修改前端组件

1. 先读目标文件，理解现有模式（特别是大文件如 `CreativeDetail.tsx`）
2. 如果改动影响 API 调用，检查对应 hook（`src/hooks/`）
3. 运行 typecheck：`cd frontend && npm run typecheck`
4. 跑相关 E2E 套件：`npm run test:e2e -- e2e/<feature>/`

### 修改后端 + 前端（全栈改动）

1. 先改后端（路由 + schema）
2. 重新生成 SDK：`cd frontend && npm run generated:regenerate`
3. 改前端调用
4. 跑两侧测试
5. 跑 contract parity 测试：`pytest backend/tests/test_openapi_contract_parity.py`

---

## 提交规范（Lore Protocol）

这个项目使用 Lore 提交协议，保留自 OMX 时期，在 Claude Code 中继续执行。

### 格式

```
<意图行：说明为什么改，不是改了什么>

<正文：背景叙述 — 约束、方案选择理由>

Constraint: <外部约束>
Rejected: <考虑过但放弃的方案> | <原因>
Confidence: <low|medium|high>
Scope-risk: <narrow|moderate|broad>
Directive: <对未来修改者的警告>
Tested: <验证了什么>
Not-tested: <已知未覆盖的>
```

### 关键规则

- **第一行说 why，不说 what**（diff 已经说明 what）
- Trailer 按需使用，不要为了格式而填
- `Rejected:` 防止未来重踏覆辙
- `Directive:` 给未来维护者的警告（"不要在没有检查 Y 的情况下修改 X"）

### 示例

```
Guard invalid timing edits before creative payloads drift

CreativeDetail timing fields were being validated only at submit,
allowing stale values to accumulate during multi-step authoring.
Moving validation to field-change handlers prevents silent drift.

Constraint: Backend rejects timing mismatches with 422; frontend must surface early
Rejected: Validate only on submit | Allows UX confusion when multiple fields stale
Confidence: high
Scope-risk: narrow
Directive: Do not remove field-level validation without re-testing submit flow
Tested: Unit — timing guard logic; E2E — creative authoring flow
Not-tested: Concurrent edits from two windows
```

---

## 分支与 PR 策略

当前分支：`feat/no-ralph`（正在进行的 CreativeDetail 改造）

**日常工作节奏：**
1. 功能实现 + 验证完成后，请求 `/commit`
2. 单个完整功能点合并一次提交（保持 diff 可 review）
3. 非紧急的跨域重构走独立 branch + PR

**不要做的事：**
- 不要 force push main
- 不要跳过 pre-commit hooks（`--no-verify`）
- 不要在 PR 合并前把 discss/ 清空（工作日志需要保留到 closeout）

---

## discss/ 工作日志规范

```
discss/
  ├── specs/          ← 跨域规范/样板/模板文档
  ├── prd-*.md        ← 功能需求文档
  ├── test-spec-*.md  ← 测试规格（与 PRD 配对）
  ├── ralplan-*.md    ← 执行计划（可多版本迭代）
  ├── closeout-*.md   ← 阶段 closeout 记录
  └── *.md            ← 分析/讨论/积压文档
```

**文件命名约定**：`<type>-<domain>-<feature>-<YYYY-MM-DD>.md`

Claude Code 不会自动维护这些文件。如果你想要 Claude 生成 PRD 或执行计划，
明确告诉它写到 `discss/` 对应位置即可。

---

## 与 Claude Code 协作的最佳实践

### 给 Claude 清晰的上下文

- 说明当前在哪个功能/修复上工作
- 如果涉及大文件（creative_service / CreativeDetail），先说"先读文件"
- 引用 discss/ 里的 PRD 或 ralplan 时，直接给文件路径

### 让 Claude 验证再宣布完成

Claude Code 会在声明完成前验证（读回修改的文件、跑测试）。
如果 Claude 没有主动验证，可以说："先跑相关测试再告诉我结果"。

### 复杂任务用 Plan Mode

对于涉及多文件的功能，用 `/plan` 先对齐思路，审批后再实现。
这替代了 OMX 的 `$ralplan` 环节。

### 保持 diff 小

每次请求 Claude 做一件事，完成后再做下一件。
大 diff = 难 review = 难回滚。
