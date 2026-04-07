# L3: 协作协议、委派规则与冲突解决

## 1. 核心协作原则

CCGS 定义了 5 条不可违反的协调规则 (coordination-rules.md):

1. **垂直委派**: 领导层 -> 部门层 -> 专家层，复杂决策不跳级
2. **水平协商**: 同级 agent 可互相咨询，但不能做跨域绑定决策
3. **冲突升级**: 两个 agent 分歧时，升级到共同上级；无共同上级则升级到对应 director
4. **变更传播**: 设计变更影响多个域时，由 `producer` 协调传播
5. **禁止单方面跨域修改**: agent 不得修改其指定目录之外的文件，除非获得显式委派

## 2. 三种协作协议模板

CCGS 为三类 agent 定义了标准化的协作协议模板，嵌入到每个 agent 的定义文件中。

### 2.1 Leadership Agent Protocol (领导层协议)

适用于: creative-director, technical-director, producer

核心流程:

```
1. 理解完整上下文
   - 提问以理解各方视角
   - 审查相关文档 (pillars, constraints, prior decisions)
   - 识别真正的利害关系

2. 框定决策
   - 清晰陈述核心问题
   - 解释为什么这个决策重要
   - 识别评估标准

3. 呈现 2-3 个战略选项
   - 每个选项: 具体含义、服务/牺牲的目标、下游后果、风险、缓解策略
   - 使用 AskUserQuestion 工具捕获决策

4. 给出明确推荐
   - "我推荐选项 X，因为..."
   - 承认接受的权衡
   - 明确: "这是你的决定"

5. 支持用户决策
   - 文档化决策 (ADR)
   - 级联到受影响部门
   - 设定验证标准
```

关键特征:
- **用户是最终决策者**，agent 只是顾问
- 必须呈现多个选项，不能只给一个方案
- 决策后必须文档化并传播

### 2.2 Design Agent Protocol (设计层协议)

适用于: game-designer, art-director, narrative-director 等设计类 agent

核心流程:

```
1. 提问优先 (Question-First)
   - 核心目标是什么?
   - 约束条件是什么?
   - 有参考案例吗?
   - 与项目支柱的关系?

2. 呈现 2-4 个选项并说明理由
   - 每个选项的优缺点
   - 引用设计理论 (MDA, SDT, Bartle 等)
   - 给出推荐但明确让用户决定

3. 基于用户选择起草
   - 逐节迭代 (展示一节、获取反馈、修改)
   - 遇到歧义时提问而非假设

4. 获得批准后才写入文件
   - 展示完整草稿或摘要
   - 明确询问: "可以写入 [filepath] 吗?"
   - 等待 "yes" 才使用 Write/Edit 工具
```

### 2.3 Implementation Agent Protocol (实现层协议)

适用于: lead-programmer, gameplay-programmer 等实现类 agent

核心流程:

```
1. 阅读设计文档
   - 识别已明确 vs 模糊的部分
   - 标记潜在实现挑战

2. 提出架构问题
   - "这应该是静态工具类还是场景节点?"
   - "数据应该放在哪里?"
   - "设计文档没有指定 [边界情况]，应该怎么处理?"

3. 先提出架构方案再实现
   - 展示类结构、文件组织、数据流
   - 解释为什么推荐这种方案
   - 突出权衡

4. 透明地实现
   - 遇到规格歧义时停下来问
   - rules/hooks 标记问题时修复并解释
   - 偏离设计文档时明确指出

5. 写入文件前获得批准
   - 展示代码或详细摘要
   - 列出所有受影响的文件
   - 等待确认

6. 提供后续步骤
   - "要写测试吗?"
   - "可以运行 /code-review 验证"
   - "我注意到 [潜在改进]，要重构吗?"
```

## 3. AskUserQuestion 工具的使用规范

CCGS 定义了 "Explain -> Capture" 模式来使用 AskUserQuestion 工具:

1. **先解释**: 在对话文本中写完整分析 (选项、权衡、推荐)
2. **再捕获**: 调用 AskUserQuestion 用简洁标签呈现选项

使用场景:
- 战略决策点 (领导层)
- 设计选择 (设计层)
- 架构问题 (实现层)
- 后续步骤选择

不使用场景:
- 开放式探索性问题
- 单一确认 ("可以写入文件吗?")
- 作为 Task 子 agent 运行时 (工具可能不可用)

格式规范:
- 标签: 1-5 个词
- 描述: 1 句话，包含关键权衡
- 推荐选项加 "(Recommended)" 后缀
- 一次最多批量 4 个独立问题

## 4. 跨域通信协议

### 4.1 设计变更通知

当设计文档变更时，game-designer 必须通知:
- lead-programmer (实现影响)
- qa-lead (测试计划更新)
- producer (排期影响)
- 相关专家 agent

### 4.2 架构变更通知

当 ADR 创建或修改时，technical-director 必须通知:
- lead-programmer (代码变更)
- 所有受影响的专家程序员
- qa-lead (测试策略可能变化)
- producer (排期影响)

### 4.3 资产标准变更通知

当美术规范变更时，art-director 必须通知:
- technical-artist (管线变更)
- 所有受影响的内容创作者
- devops-engineer (如果影响构建管线)

## 5. 审查工作流 (Review Workflow)

CCGS 定义了四级审查签核:

| 变更类型 | 审查者 |
|---------|--------|
| 代码变更 | 相关部门 lead agent |
| 设计变更 | game-designer + creative-director |
| 架构变更 | technical-director |
| 跨域变更 | producer |

## 6. 反模式 (Anti-Patterns)

CCGS 明确列出了 5 个必须避免的反模式:

1. **绕过层级**: 专家 agent 不经 lead 直接做决策
2. **跨域实现**: agent 修改其指定目录之外的文件
3. **影子决策**: 口头约定不文档化，导致矛盾
4. **巨型任务**: 分配给 agent 的任务超过 1-3 天工作量
5. **假设性实现**: 规格模糊时猜测而非提问

## 7. Handoff 机制

CCGS 的 agent 间 handoff 通过以下方式实现:

### 7.1 Task 工具 (直接委派)

```
主 agent 使用 Task 工具启动子 agent:
- subagent_type: "game-designer"
- prompt: 包含完整上下文 (设计文档路径、相关代码、约束条件)
- 子 agent 在独立上下文窗口中运行
- 返回结果摘要给主 agent
```

### 7.2 文件系统 (间接通信)

```
Agent A 写入设计文档 -> Agent B 读取设计文档
Agent A 更新 active.md -> Agent B 从 active.md 恢复上下文
Agent A 写入 ADR -> Agent B 参考 ADR 做实现决策
```

### 7.3 Skills 编排 (流水线)

```
/team-combat 技能:
Phase 1: game-designer 输出设计文档
Phase 2: gameplay-programmer 读取设计文档，输出架构方案
Phase 3: 多个 agent 并行实现
Phase 4: 集成
Phase 5: qa-tester 验证
Phase 6: 汇总报告
```

## 8. 对 DewuGoJin 的启示

1. **三种协议模板**: DewuGoJin 可直接复用 Leadership/Design/Implementation 三种协议模板
2. **Question -> Options -> Decision -> Draft -> Approval**: 这个流程应作为所有 agent 的标准交互模式
3. **AskUserQuestion 的 Explain -> Capture 模式**: 结构化决策 UI 提升用户体验
4. **跨域通知机制**: 变更传播需要显式定义，不能依赖 agent 自觉
5. **反模式清单**: 在 agent 定义中明确列出禁止行为，比只说"应该做什么"更有效
