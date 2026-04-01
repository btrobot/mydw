# 协调规则

多 Agent 协作的核心规则，确保各 Agent 高效协作、避免冲突。

---

## 1. 垂直委托规则

### 层级结构

```
用户 (Product Owner)
  └── Project Manager (PM)
        └── Tech Lead
              ├── Frontend Lead
              ├── Backend Lead
              ├── QA Lead
              └── DevOps Engineer
                    └── 各 Developer
```

### 委托原则

1. **任务分配**: PM 分配任务给 Tech Lead，Tech Lead 分配给 Lead，Lead 分配给 Developer
2. **决策上移**: 复杂决策必须逐层上报，不能跳级
3. **报告下沉**: 结果逐层汇报，最终到 PM

### 禁止行为

- ❌ Developer 直接接受用户分配的任务（除非简单任务）
- ❌ Developer 自己做跨域架构决策
- ❌ 跳过 Lead 直接向 Tech Lead 汇报（除非升级情况）

---

## 2. 水平协作规则

### 协作关系

| Agent | 协作对象 | 协作内容 |
|-------|---------|---------|
| Frontend Lead | Backend Lead | API 契约、类型定义、数据流 |
| Backend Lead | QA Lead | 测试用例、验收标准、Mock 数据 |
| Automation Dev | Backend Lead | API 端点、Webhook 定义 |
| QA Lead | DevOps | CI/CD 集成、测试自动化 |
| Tech Lead | Security Expert | 安全架构、漏洞修复 |

### 协作原则

1. **协商范围**: 可以讨论、提出建议
2. **决定权限**: 不能替对方做决定
3. **文档记录**: 协作结果必须文档化

### 示例

```
Frontend Lead: "我建议 API 返回分页数据，不是全量返回"
Backend Lead: "分页会增加复杂度，但可以接受"
Backend Lead: "我来实现分页功能，你那边更新类型定义"
```

---

## 3. 冲突升级规则

### 升级路径

| 冲突类型 | 升级目标 | 说明 |
|----------|----------|------|
| 技术架构 | Tech Lead | API 设计、数据库 Schema、系统边界 |
| 代码质量 | Tech Lead | 评审不通过、重构争议 |
| 功能设计 | Project Manager | 需求不清、优先级争议 |
| 安全问题 | Security Expert | 发现安全漏洞、敏感数据处理 |
| 测试标准 | QA Lead | 测试覆盖率、验收标准 |
| 资源冲突 | Project Manager | 同一 Developer 被多方争抢 |
| 无法达成共识 | Project Manager | 水平协商失败 |

### 升级格式

```markdown
## 升级报告

### 冲突描述
[清晰描述冲突]

### 各方观点
- **Agent A**: [观点和理由]
- **Agent B**: [观点和理由]

### 影响评估
- [对项目的影响]

### 建议
[升级者建议的解决方案]

### 请求
[需要上级做什么]
```

---

## 4. 变更传播规则

### 触发条件

当变更影响多个域时必须执行：

- API 契约变更
- 共享数据类型变更
- 跨域功能依赖
- 配置文件变更

### 传播流程

```
1. 发起变更 → 通知 PM
2. PM 评估影响 → 确定受影响方
3. PM 协调各方 → 确认变更方案
4. 各方实现 → 完成时间表
5. PM 跟踪 → 确认全部完成
```

### 变更通知模板

```markdown
## 变更通知

### 变更描述
[变更内容]

### 影响范围
- [ ] Frontend Lead
- [ ] Backend Lead
- [ ] QA Lead
- [ ] DevOps

### 时间表
- 方案确认: [日期]
- 实现完成: [日期]
- 测试通过: [日期]

### 状态
- [ ] Frontend: 待确认
- [ ] Backend: 待确认
- [ ] QA: 待确认
```

---

## 5. 跨域变更禁止

### 默认禁止

除非获得明确授权，否则：

| 禁止 | 说明 |
|------|------|
| Frontend → Backend | 不能修改 API 路由、服务层代码 |
| Backend → Frontend | 不能修改 React 组件、状态管理 |
| Developer → 跨域 | Developer 只能修改自己负责的文件 |
| QA → 实现代码 | QA 只能修改测试文件 |

### 申请授权

如需跨域修改，必须：

1. 向目标域 Lead 提出申请
2. 说明修改原因和范围
3. 获得书面确认
4. 在变更说明中注明授权来源

---

## 6. 决策规则

### 决策类型

| 类型 | 决策者 | 说明 |
|------|--------|------|
| 产品决策 | 用户 | 功能范围、优先级 |
| 技术架构 | Tech Lead | 系统设计、API 契约 |
| 实现细节 | Lead/Developer | 具体实现方式 |
| 安全决策 | Security Expert | 安全措施 |
| 测试标准 | QA Lead | 测试覆盖率要求 |

### 决策流程

```
1. Question (问询) → 理解问题本质
2. Options (选项) → 提出 2-3 个方案
3. Analysis (分析) → 分析各方案利弊
4. Decision (决策) → 决策者选择
5. Document (文档) → 写入决策日志
```

### 决策文档化

所有重要决策写入 `production/session-state/active.md`：

```markdown
## 决策日志

### [日期] [决策标题]
- **问题**: [需要决策的问题]
- **选项**:
  - A: [方案A]
  - B: [方案B]
- **决策**: [选择的方案]
- **理由**: [决策原因]
- **影响**: [对项目的影响]
- **决策者**: [谁做的决定]
```

---

## 7. 状态管理规则

### Session State 文件

位置: `production/session-state/active.md`

### 更新时机

| 时机 | 更新内容 |
|------|----------|
| Sprint 开始 | Sprint 目标、任务分配 |
| 任务开始 | 当前任务、负责人 |
| 任务完成 | 标记完成、记录结果 |
| 决策做出 | 写入决策日志 |
| 风险出现 | 记录风险和应对 |
| Sprint 结束 | 总结、准备下一 Sprint |

### 状态块格式

```markdown
<!-- STATUS -->
Epic: [当前 Epic]
Feature: [当前 Feature]
Task: [当前任务]
Owner: [当前负责人]
<!-- /STATUS -->
```

---

## 8. 验收规则

### 代码验收

1. **自检**: Developer 完成自检
2. **Lead 审查**: Lead 代码审查
3. **测试验证**: Test Engineer 测试
4. **安全扫描**: Security Expert 安全检查
5. **PM 确认**: PM 确认交付

### 功能验收

1. **符合设计**: 与设计文档一致
2. **测试通过**: 所有测试用例通过
3. **无安全问题**: 安全扫描通过
4. **代码规范**: 符合项目规范

---

## 违规处理

| 违规 | 处理 |
|------|------|
| 跳过层级 | PM 纠正并记录 |
| 跨域变更 | 回滚并重新协调 |
| 未文档化 | 要求补充文档 |
| 不升级冲突 | PM 介入解决 |
