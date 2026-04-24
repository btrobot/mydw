# 《CreativeDetail 在 OMX 里的角色分工与工作流建议 v1》

> 目标：把 CreativeDetail 从“容易做成总控页”拉回到“定义作品页”的正确流程  
> 结论：**这类页面不该由 `executor` 单独开干，而应由“分析 → 交互 → 实现 → 验收”串起来。**

---

## 1. 先说结论

对 CreativeDetail 这类页面，OMX 里最合适的分工是：

- **`deep-interview`**：澄清目标与边界
- **`ui-ux-pro-max` / `designer`**：做页面交互结构
- **`plan` / `ralplan` / `planner`**：固化规范与切片
- **`architect`**：把交互映射到状态模型、组件边界、数据流
- **`executor`**：按切片实现
- **`visual-verdict` + `verifier`**：截图验收 + 完成验证

一句话：

> **先让“设计角色”决定页面，再让“实现角色”写页面。**

---

## 2. CreativeDetail 适合的 OMX 角色分工

## 2.1 业务澄清层

### 角色 / skill
- `deep-interview`
- `analyst`

### 职责
- 搞清楚页面一句话定位
- 分清页面职责 / 非职责
- 确认用户第一任务
- 把“Creative / Material / Version / PublishPackage / Task”边界讲清楚

### 产出
- 页面定位
- 业务对象分工
- 主流程 / 次流程
- 验收口径

### 对 CreativeDetail 的具体作用
核心是锁定：

> **CreativeDetail = 定义一个作品，不是任务总控页。**

---

## 2.2 交互设计层

### 角色 / skill
- `ui-ux-pro-max`
- `designer`

### 职责
- 设计信息架构
- 设计首屏优先级
- 划分 A/B/C/D/E 区域
- 设计主 CTA / 次 CTA
- 设计空态 / 错态 / readiness / loading
- 设计低保真页面骨架

### 产出
- 页面交互规范
- 页面骨架
- 区块层级
- CTA 层级
- 页面状态定义

### 对 CreativeDetail 的具体作用
重点解决：

- A 当前定义区
- B 当前入选区
- C 候选池区
- D 版本与审核区
- E 发布与诊断区

并明确：

> **A+B 是主页面骨架，D/E 不能抢首屏主语义。**

---

## 2.3 方案收敛层

### 角色 / skill
- `plan`
- `ralplan`
- `planner`

### 职责
- 把讨论沉淀成正式规范
- 拆切片
- 定优先级
- 定实施顺序
- 定每片验收标准

### 产出
- 页面切片计划
- P0 / P1 / Advanced 优先级
- 每片范围与非范围
- 实施顺序

### 对 CreativeDetail 的具体作用
推荐切片：

- Slice 1：A 当前定义区
- Slice 2：B 当前入选区
- Slice 3：C 候选池区
- Slice 4：D 版本与审核区
- Slice 5：E 发布与诊断区

---

## 2.4 技术映射层

### 角色
- `architect`

### 职责
- 把交互方案映射成技术结构
- 定 view-model 边界
- 定数据依赖关系
- 定组件拆分
- 定哪些能力应该抽屉化 / 下沉

### 产出
- 组件分层方案
- 状态模型
- 接口映射
- 技术风险点

### 对 CreativeDetail 的具体作用
例如判断：

- `useCreativeAuthoringModel` 负责什么
- `useCreativeVersionReviewModel` 负责什么
- `useCreativePublishDiagnosticsModel` 是否应下沉
- `CreativeDetail.tsx` 如何从“并列堆叠”改为“主轴式结构”

---

## 2.5 实现层

### 角色
- `executor`

### 职责
- 按切片实现
- 保持与规范一致
- 不擅自重新定义页面语义
- 交付可运行页面

### 产出
- 页面代码
- 组件重构
- 状态联动
- 测试/验证结果

### 对 CreativeDetail 的具体要求
`executor` 不应该先决定“这页长什么样”，而应该只负责：

> **把已定好的 A+B/C/D/E 结构实现出来。**

---

## 2.6 验收层

### 角色 / skill
- `visual-verdict`
- `verifier`

### 职责
- 看截图验结构
- 看页面是否符合首屏优先级
- 看主任务有没有被抢走
- 看 CTA 是否清楚
- 看规范是否落地

### 产出
- 截图审稿意见
- 验收结论
- 差异清单

### 对 CreativeDetail 的具体作用
验收问题应该是：

- 用户 30 秒内知道这是定义作品页吗？
- 当前定义和当前入选区分清楚了吗？
- 版本/诊断有没有抢首屏？

---

# 3. OMX 里最推荐的两种工作流

## 3.1 轻量单人流（最适合现在）

适合：你和我先把事做对，不急着并行大干。

### 推荐顺序
1. `deep-interview`
2. `ui-ux-pro-max`
3. `plan`
4. `architect`
5. `executor`
6. `visual-verdict`

### 适用原因
- 先稳住页面语义
- 再稳住交互结构
- 最后才进入代码

这是目前最适合 CreativeDetail 的方式。

---

## 3.2 团队并行流（适合 OMX runtime 下正式推进）

适合：规范已稳定，要加速实施。

### 推荐分工
- Lane 1：`designer` / `ui-ux-pro-max`
- Lane 2：`architect`
- Lane 3：`executor`
- Lane 4：`visual-verdict` / `verifier`

### 工作方式
- 设计 lane 出交互结构
- 架构 lane 做技术映射
- 实现 lane 只认规范做代码
- 验收 lane 用截图和行为验证回压

### 注意
前提是：

> **页面语义已经锁定。**

如果没锁定就并行，通常会更乱。

---

# 4. 对 CreativeDetail 的推荐职责归属

## 最终主责建议

### 页面定义主责
- `deep-interview` + `analyst`

### 页面交互主责
- `ui-ux-pro-max` + `designer`

### 页面结构与数据流主责
- `architect`

### 页面代码落地主责
- `executor`

### 页面验收主责
- `visual-verdict` + `verifier`

---

# 5. 不推荐的做法

## 不推荐 1
直接让 `executor` 从现有页面开始“优化一下”

### 问题
- 会继续沿着旧结构修补
- 很容易把页面越修越像总控页

---

## 不推荐 2
先把版本区、诊断区、发布区都保留在首屏，再想办法“弱化”

### 问题
- 语义还是乱
- 首屏还是会被抢

---

## 不推荐 3
没有交互规范就直接改 UI

### 问题
- 你只能凭感觉说“不对”
- 很难客观验收

---

# 6. CreativeDetail 的推荐推进顺序

## Phase 1：先定页面
使用：
- `deep-interview`
- `ui-ux-pro-max`
- `plan`

目标：
- 锁定页面定位
- 锁定 A/B/C/D/E
- 锁定首屏

## Phase 2：再定实现
使用：
- `architect`

目标：
- 定组件边界
- 定 view-model 分层
- 定下沉策略

## Phase 3：只做 P0
使用：
- `executor`

目标：
- 只实现 A+B

## Phase 4：看图验收
使用：
- `visual-verdict`
- `verifier`

目标：
- 看主语义是否成立
- 看页面是否终于像“定义作品页”

## Phase 5：再补 P1 / Advanced
使用：
- `executor`
- `verifier`

目标：
- 补 C
- 再补 D/E

---

# 7. 如果把它对应到真实团队

OMX 组合 | 现实团队角色
---|---
`deep-interview` / `analyst` | 产品经理 / 业务分析
`ui-ux-pro-max` / `designer` | UX / 产品设计师
`architect` | 前端负责人 / 技术负责人
`executor` | 前端工程师
`visual-verdict` / `verifier` | 设计评审 + QA/UAT

所以 OMX 其实能模拟一个比较完整的页面协作链路。

---

# 8. 对你当前情况的直接建议

如果只给一个最实用建议：

> **先不要再让实现角色主导 CreativeDetail。**  
> **先让“交互设计角色”把页面定型，再让“技术角色”映射，再实现。**

具体到当前页面，推荐下一步就是：

1. 用 `ui-ux-pro-max` / `designer` 把 **A+B 首屏骨架**定死
2. 用 `architect` 把它映射到 `CreativeDetail.tsx` 的改造方案
3. 再让 `executor` 开始改代码
4. 改完后用 `visual-verdict` 看图验收

---

# 9. 一句话版本

## 在 OMX 里，CreativeDetail 最适合的协作方式是：

> **`deep-interview` 定边界，`ui-ux-pro-max`/`designer` 定交互，`architect` 定结构，`executor` 做实现，`visual-verdict`/`verifier` 做验收。**

如果你要，我下一步可以直接继续给你出：

**《CreativeDetail 的 OMX 执行剧本 v1》**  
也就是把上面这些角色，直接写成一套你可以照着跑的执行顺序。
