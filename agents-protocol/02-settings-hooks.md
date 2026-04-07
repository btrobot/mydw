# L1: Settings.json 配置与 Hooks 生命周期

## 1. settings.json 结构

CCGS 的 `.claude/settings.json` 是整个 agent 通信框架的配置中枢，定义了三大块:

### 1.1 Status Line (状态栏)

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash .claude/statusline.sh"
  }
}
```

状态栏脚本 `statusline.sh` 接收 JSON 输入 (包含 model、context_window、workspace 信息)，输出格式:

```
ctx: 45% | Claude 3.5 Sonnet | Production | Combat System > Melee > Hitboxes
```

四个段: 上下文使用率 | 模型名 | 项目阶段 | 当前工作面包屑

项目阶段自动检测逻辑:
- 有 `production/stage.txt` -> 读取显式阶段
- 否则根据项目产物推断: Concept -> Systems Design -> Technical Setup -> Pre-Production -> Production
- Production 及以上阶段会从 `active.md` 解析 `<!-- STATUS -->` 块显示面包屑

### 1.2 Permissions (权限控制)

```json
{
  "permissions": {
    "allow": [
      "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)",
      "Bash(git branch*)", "Bash(git rev-parse*)",
      "Bash(ls *)", "Bash(dir *)",
      "Bash(python -m json.tool*)", "Bash(python -m pytest*)"
    ],
    "deny": [
      "Bash(rm -rf *)", "Bash(git push --force*)",
      "Bash(git reset --hard*)", "Bash(git clean -f*)",
      "Bash(sudo *)", "Bash(chmod 777*)",
      "Bash(*>.env*)", "Bash(cat *.env*)",
      "Read(**/.env*)"
    ]
  }
}
```

权限设计原则:
- allow: 只开放只读 git 操作、目录列表、测试运行
- deny: 禁止破坏性操作 (强制推送、硬重置)、敏感文件访问 (.env)

### 1.3 Hooks (生命周期钩子)

这是 agent 通信的核心基础设施。

## 2. Hook 事件类型与触发时机

CCGS 注册了 6 类 hook 事件:

| 事件 | 触发时机 | Matcher | Hook 脚本 | 作用 |
|------|---------|---------|-----------|------|
| `SessionStart` | 会话启动 | `""` (全匹配) | `session-start.sh` | 加载项目上下文、恢复会话状态 |
| `SessionStart` | 会话启动 | `""` | `detect-ecommerce-gaps.sh` | 检测项目健康问题 |
| `PreToolUse` | 工具调用前 | `Bash(git commit*)` | `validate-ecommerce-commit.sh` | 提交前验证 |
| `PostToolUse` | 工具调用后 | `Write\|Edit` | `validate-schema-change.sh` | Schema 变更后提示 |
| `PreCompact` | 上下文压缩前 | `""` | `pre-compact.sh` | 保存状态到对话中 |
| `Stop` | 会话结束 | `""` | `session-stop.sh` | 归档状态、记录日志 |
| `SubagentStart` | 子 agent 启动 | `""` | `log-agent.sh` | 审计 agent 调用 |

## 3. 各 Hook 详细分析

### 3.1 session-start.sh (SessionStart)

**输入**: 无 stdin，直接执行
**输出**: stdout 内容作为会话初始上下文注入给 Claude

功能:
1. 显示当前 git 分支和最近 5 条提交
2. 检测最新 sprint 文件和 milestone 文件
3. 统计未关闭的 bug 数量
4. 扫描 src/ 中的 TODO/FIXME 数量
5. **关键**: 检测 `production/session-state/active.md` 是否存在，如果存在则预览前 20 行，提示 Claude 读取以恢复上下文

这是 agent 间"跨会话通信"的核心机制 -- 上一个会话的 agent 写入 active.md，下一个会话的 agent 通过此 hook 自动发现并恢复。

### 3.2 detect-ecommerce-gaps.sh (SessionStart)

**输入**: 无
**输出**: 项目健康检查报告

检查项:
1. Schema 修改后是否已生成 migration
2. API 实现与文档的比例 (源文件数 vs 文档数)
3. 环境文件 (.env) 是否配置
4. 数据库连接是否配置
5. 依赖是否已安装 (node_modules)

### 3.3 validate-ecommerce-commit.sh (PreToolUse)

**输入**: JSON stdin，包含 `tool_input.command`
**Matcher**: `Bash(git commit*)` -- 仅匹配 git commit 命令

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m 'feat: add user service'"
  }
}
```

验证逻辑:
1. Schema 变更时检查是否有对应 migration
2. DTO 变更时提醒更新测试
3. 新 Controller 文件提醒补充 API 文档
4. 检测安全敏感文件 (.env, jwt, secret, password, token)
5. 检测大文件 (>1MB)

**退出码**: 始终 exit 0 (仅警告，不阻断)。如果需要阻断，应 exit 2。

### 3.4 validate-schema-change.sh (PostToolUse)

**输入**: JSON stdin，包含 `tool_input.file_path` 和 `tool_output`
**Matcher**: `Write|Edit` -- 匹配文件写入/编辑操作

仅当修改的文件路径匹配 `packages/server/prisma/schema.prisma` 时触发，输出后续步骤提示:
1. 验证 schema: `npx prisma validate`
2. 生成 client: `npx prisma generate`
3. 创建 migration: `npx prisma migrate dev`

### 3.5 pre-compact.sh (PreCompact)

**输入**: 无
**输出**: 会话状态快照，注入到压缩前的对话中

这是上下文管理的关键 hook。在 Claude Code 压缩上下文之前:
1. 读取并输出 `active.md` 的内容 (截断到 100 行)
2. 列出所有未提交的文件变更 (unstaged/staged/untracked)
3. 扫描设计文档中的 WIP 标记 (TODO/WIP/PLACEHOLDER)
4. 记录压缩事件到 `compaction-log.txt`
5. 输出恢复指令

这确保了压缩后的摘要中包含关键状态信息，agent 可以从摘要中恢复工作上下文。

### 3.6 session-stop.sh (Stop)

**输入**: 无
**输出**: 无 (仅写文件)

会话结束时:
1. 将 `active.md` 内容归档到 `session-logs/session-log.md`
2. 删除 `active.md` (清理临时状态)
3. 记录最近 8 小时的 git 提交和未提交变更到日志

### 3.7 log-agent.sh (SubagentStart)

**输入**: JSON stdin，包含 `agent_name`

```json
{
  "agent_name": "game-designer",
  "model": "kimi-for-coding",
  "description": "Design the combat healing mechanic"
}
```

将 agent 调用记录追加到 `session-logs/agent-audit.log`:
```
20260407_143022 | Agent invoked: game-designer
```

这提供了 agent 调用的审计追踪，可用于分析协作模式和调试。

## 4. Hook 输入/输出 Schema 总结

| 事件 | 输入 | 输出效果 | 可阻断 |
|------|------|---------|--------|
| SessionStart | 无 stdin | stdout -> Claude 上下文 | 否 |
| PreToolUse | JSON (tool_name, tool_input) | stderr -> 警告; exit 2 -> 阻断 | 是 |
| PostToolUse | JSON (tool_name, tool_input, tool_output) | stderr -> 警告 | 否 |
| PreCompact | 无 stdin | stdout -> 压缩前对话 | 否 |
| Stop | 无 stdin | 无直接输出 | 否 |
| SubagentStart | JSON (agent_name, model, description) | 无直接输出 | 否 |

## 5. settings.local.json (个人覆盖)

CCGS 支持通过 `.claude/settings.local.json` 进行个人配置覆盖 (不提交到版本控制):
- 可扩展权限 (如开发时允许更多 Bash 命令)
- 可添加个人 hooks (如构建完成通知)
- 不会覆盖项目级 hooks，而是扩展

## 6. 对 DewuGoJin 的启示

DewuGoJin 当前的 hook 配置可参考 CCGS 的以下模式:
1. **SessionStart 双 hook 模式**: 一个加载上下文 + 一个健康检查
2. **PreToolUse 精确匹配**: 用 `Bash(git commit*)` 而非匹配所有 Bash 命令
3. **SubagentStart 审计**: 记录所有子 agent 调用，便于调试协作问题
4. **PreCompact 状态保存**: 压缩前自动 dump 状态，确保恢复能力
