---
name: ui-workflow
description: "UI 工作流 - 编排 UI 设计和前端实现"
argument-hint: "[页面名称或功能描述]"
user-invocable: true
allowed-tools: Agent, Read, Write, Glob, Grep, AskUserQuestion
---

# UI Workflow Skill

UI 设计和实现的完整工作流，编排 ui-designer 和 frontend-lead 协作。

## 触发方式

```
/ui-workflow 话题组管理页面
/ui-workflow 重构视频管理页面
/ui-workflow 新建商品详情页
```

## 工作流程

这个 skill 解决了子代理无法调用子代理的平台限制，通过主会话编排多个代理协作。

### Phase 1: UI 设计（ui-designer）

1. **调用 ui-designer 代理**（使用 `general-purpose` + 角色注入）
   - 分析需求，确定适用的布局模板（T1-T6）
   - 编写页面规范文档到 `docs/page-specs/`
   - 定义所有 UI 元素（搜索条件、表格列、操作按钮、表单字段）
   - 输出 Hard Check 计数

2. **设计审查检查点**
   - 页面规范是否完整？
   - 布局模板是否合适？
   - 与现有页面是否一致？

### Phase 2: 用户确认

使用 AskUserQuestion 让用户确认设计规范：
- 展示页面规范摘要
- 询问是否需要调整
- 如需调整，返回 Phase 1

### Phase 3: 前端实现（frontend-lead）

1. **调用 frontend-lead 代理**
   - 传递页面规范文档路径
   - 实现页面组件
   - 遵循 ProTable/PageContainer 模式
   - 实现所有交互逻辑

2. **实现验证**
   - TypeScript typecheck 通过
   - 所有 UI 元素已实现
   - 符合页面规范

### Phase 4: UI 一致性审查（ui-designer）

1. **再次调用 ui-designer 代理**进行设计审查
   - 对比实现与规范
   - 检查布局模板合规性
   - 检查元素计数是否匹配
   - 检查视觉一致性

2. **生成审查报告**
   - 合规项
   - 偏差项（高/中/低）
   - 结论：✅ 合规 / ⚠️ 轻微偏差 / ❌ 不合规

### Phase 5: 修复循环（如需要）

如果审查发现问题：
1. 调用 frontend-lead 修复问题
2. 返回 Phase 4 重新审查
3. 最多循环 2 次，之后上报用户

## 代理调用模式

由于平台限制（子代理无法调用子代理），本 skill 在主会话中运行，直接编排代理：

```typescript
// Phase 1: UI 设计
Agent({
  subagent_type: "general-purpose",
  description: "UI 设计规范",
  prompt: `You are the UI Designer for DewuGoJin project.
  
  [inject full role from .claude/agents/ui-designer.md]
  
  Task: ${userRequest}
  
  Output: Write page spec to docs/page-specs/${pageName}.md`
})

// Phase 3: 前端实现
Agent({
  subagent_type: "frontend-lead",
  description: "实现页面",
  prompt: `Implement the page based on the spec at docs/page-specs/${pageName}.md
  
  Follow ProTable patterns from existing pages.
  Ensure TypeScript typecheck passes.`
})

// Phase 4: 设计审查
Agent({
  subagent_type: "general-purpose",
  description: "UI 设计审查",
  prompt: `You are the UI Designer for DewuGoJin project.
  
  [inject full role from .claude/agents/ui-designer.md]
  
  Task: Review the implementation against the spec at docs/page-specs/${pageName}.md
  
  Output: Design review report`
})
```

## 输出

完成后更新 `production/session-state/active.md`：

```markdown
## 决策日志

### [日期] UI Workflow - ${pageName}
- **Phase 1**: 页面规范已编写 (docs/page-specs/${pageName}.md)
- **Phase 2**: 用户已确认设计
- **Phase 3**: 前端实现完成
- **Phase 4**: 设计审查通过 (✅ 合规)
- **状态**: 完成
```

## 示例

### 示例 1: 新建页面

```
用户: /ui-workflow 话题组管理页面

Skill 执行:
1. ui-designer: 编写 docs/page-specs/topic-group-list.md
2. 用户确认设计
3. frontend-lead: 实现 TopicGroupList.tsx
4. ui-designer: 审查实现 → ✅ 合规
5. 完成
```

### 示例 2: 重构现有页面

```
用户: /ui-workflow 重构视频管理页面

Skill 执行:
1. ui-designer: 分析现有实现，编写改进规范
2. 用户确认改进方案
3. frontend-lead: 重构 VideoList.tsx
4. ui-designer: 审查实现 → ⚠️ 轻微偏差（缺少批量操作）
5. frontend-lead: 修复偏差
6. ui-designer: 重新审查 → ✅ 合规
7. 完成
```

## 优势

1. **解决平台限制**: 主会话编排，绕过子代理嵌套限制
2. **完整设计流程**: 设计 → 确认 → 实现 → 审查
3. **质量保证**: ui-designer 参与设计和审查两个阶段
4. **可追溯**: 页面规范文档作为设计依据
5. **一致性**: 强制使用布局模板和设计审查

## 相关文件

- `.claude/agents/ui-designer.md` — UI Designer 角色定义
- `.claude/agents/frontend-lead.md` — Frontend Lead 角色定义
- `docs/ui-templates.md` — 布局模板定义
- `docs/page-specs/` — 页面规范文档目录
- `.claude/rules/ui-design-rules.md` — UI 设计规则
