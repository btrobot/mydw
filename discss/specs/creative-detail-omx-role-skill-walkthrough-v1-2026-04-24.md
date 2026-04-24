# 《CreativeDetail OMX 角色 + Skill 手把手流程 v1》

> 目标：把 CreativeDetail 的完整推进流程，从“谁负责什么”变成“具体先做什么、后做什么、每一步要产出什么”。  
> 方法：**skill 管流程，role 管产出。**

---

# 1. 先记住一句话

> **skill = 流程方法**  
> **role = 具体负责人**

所以在 OMX 里，最佳实践不是“只用一个 skill”或者“只用一个角色”，而是：

> **skill 管流程，role 管产出。**

---

# 2. CreativeDetail 的完整推荐流程

| 阶段 | 主 skill | 主 role | 目标 | 输出物 |
|---|---|---|---|---|
| 1 | `deep-interview` | `analyst` | 把页面边界说清楚 | 页面定位 / 职责 / 非职责 |
| 2 | `ui-ux-pro-max` | `designer` | 把交互结构设计出来 | 首屏骨架 / A-B-C-D-E / CTA |
| 3 | `plan` / `ralplan` | `planner` | 把方案变成切片计划 | P0 / P1 / Advanced 切片 |
| 4 | 无特定 skill，直接技术分析 | `architect` | 映射到组件 / 状态 / API | 技术改造方案 |
| 5 | 无特定 skill，直接实施 | `executor` | 按切片实现页面 | 代码与页面 |
| 6 | `visual-verdict` | `verifier` | 看图审结构和优先级 | 视觉验收结论 |
| 7 | 无特定 skill，完成验证 | `verifier` | 验行为 / 测试 / 规范一致性 | 最终完成证明 |

---

# 3. 先分清：什么时候用 skill，什么时候用 role

## 3.1 什么时候用 skill

当你要的是“流程”：

- 我该先做什么？
- 我该输出什么？
- 我该怎么推进？

比如：

- `deep-interview`
- `ui-ux-pro-max`
- `plan`
- `visual-verdict`

## 3.2 什么时候用 role

当你要的是“一个负责人”：

- 谁来像产品分析师一样想问题？
- 谁来像设计师一样做结构？
- 谁来像架构师一样做技术映射？
- 谁来写代码？

比如：

- `analyst`
- `designer`
- `planner`
- `architect`
- `executor`
- `verifier`

---

# 4. 手把手走一遍完整流程

下面按 CreativeDetail 来讲。

---

## Step 0：准备输入材料

在真正调用 skill / role 前，先把输入准备好。

### 当前已经有的输入

- `discss/specs/creative-detail-business-flow-v1-2026-04-24.md`
- `discss/specs/creative-detail-ab-current-definition-selected-spec-v1-2026-04-24.md`
- `discss/specs/creative-detail-page-spec-v1-2026-04-24.md`
- `discss/specs/creative-detail-omx-roles-workflow-v1-2026-04-24.md`

### 代码输入

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `useCreativeAuthoringModel`
- `useCreativeVersionReviewModel`
- `useCreativePublishDiagnosticsModel`

---

## Step 1：先用 `deep-interview`，不要上来改代码

### 为什么先它

因为如果页面语义还没稳，后面所有角色都会歪。

### 这个阶段谁负责

- skill：`deep-interview`
- role：`analyst`

### 你应该怎么下指令

```text
$deep-interview
围绕 CreativeDetail 页面做一次页面边界澄清。
不要写代码。
只回答：
1. 这页一句话定位
2. 这页负责什么 / 不负责什么
3. 用户第一任务是什么
4. A/B/C/D/E 应该怎么分层
5. 哪些内容不能抢占首屏
```

### 这个阶段要拿到什么

必须拿到这几个结论：

- CreativeDetail 是什么页
- 主任务是什么
- 哪些是主语义
- 哪些是次语义
- 哪些必须下沉

### 什么时候算完成

当你能一句话说出：

> CreativeDetail 是“定义作品页”，不是总控详情页。

如果这一句还不稳，**不要进入下一步**。

---

## Step 2：再用 `ui-ux-pro-max`，把页面交互做出来

### 为什么这一步最关键

因为你现在真正缺的不是代码，是：

- 首屏结构
- A/B/C/D/E 层次
- CTA 主次
- 当前定义 vs 当前入选 的表达方式

### 这个阶段谁负责

- skill：`ui-ux-pro-max`
- role：`designer`

### 推荐工作方式

这里最好是：

> **skill 提供设计方法，designer 产出 CreativeDetail 的具体页面结构。**

### 你应该怎么下指令

```text
使用 ui-ux-pro-max 的思路，为 CreativeDetail 输出交互骨架。
不要进入视觉细节，不要写代码。
只输出：
1. 首屏结构
2. A 当前定义区
3. B 当前入选区
4. C 候选池区
5. D 版本审核区
6. E 发布诊断区
7. 主 CTA / 次 CTA / 高级 CTA
8. loading / error / empty / readiness 状态
```

### 你希望 designer 交付什么

- 首屏线框
- 区块顺序
- 每块内容
- 每块动作
- 每块状态
- 不该出现在首屏的东西

### 这一步的通过标准

你看完后能回答：

- 用户 30 秒内看得懂这页干什么吗？
- A 和 B 区分清楚了吗？
- D/E 被压到后面了吗？

---

## Step 3：用 `plan` 或 `ralplan` 固化为实施计划

### 为什么要这一步

因为设计稿如果不变成切片计划，`executor` 又会乱冲。

### 这个阶段谁负责

- skill：`plan`
- 如果想更严谨：`ralplan`
- role：`planner`

### 你应该怎么下指令

```text
$plan
基于已经确定的 CreativeDetail 交互骨架，
输出一个实施计划：
1. 切片顺序
2. 每片目标
3. 每片明确不做什么
4. 验收标准
5. 哪些依赖现有 view-model
```

### 推荐切片

- Slice 1：A 当前定义区
- Slice 2：B 当前入选区
- Slice 3：C 候选池区
- Slice 4：D 版本与审核区
- Slice 5：E 发布与诊断区

### 这一步的通过标准

不能只是“要改页面”，而必须有：

- P0 是什么
- P1 是什么
- 先进什么，后进什么
- 每片完成怎么验收

---

## Step 4：让 `architect` 做技术映射

### 为什么不能让 designer 直接接 executor

因为中间还差一层：

> 交互结构如何落到代码结构上。

### 这个阶段谁负责

- role：`architect`

### 它负责什么

- 组件如何拆
- 哪些 model 继续保留
- 哪些逻辑下沉
- 哪些信息从首屏移走
- 页面状态如何组织

### 你应该怎么下指令

```text
请作为 architect，
基于已定的 CreativeDetail 交互规范和切片计划，
输出技术映射方案：
1. CreativeDetail.tsx 的新结构
2. 现有 view-model 如何分工
3. 哪些能力保留在首屏
4. 哪些能力改成 Drawer / 次区
5. Slice 1（A区）和 Slice 2（B区）分别怎么落地
```

### 这一步要拿到什么

- 组件树
- view-model 边界
- 数据流
- 改造顺序
- 风险点

### 什么时候算完成

当 `executor` 已经不需要再猜“结构应该怎么改”。

---

## Step 5：才轮到 `executor`

### 为什么现在才到它

因为现在它终于不需要再做产品 / 交互决策了。

### 这个阶段谁负责

- role：`executor`

### 它应该做什么

只做：

- 按切片实现
- 保持和规范一致
- 不重新发明页面结构

### 你应该怎么下指令

```text
请按 Slice 1 先实现 CreativeDetail 的 A 当前定义区。
要求：
1. 不碰 D/E 的首屏结构
2. 不重新定义页面主语义
3. 保持和已确认规范一致
4. 完成后给出变更文件、截图方式、验证结果
```

然后下一轮：

```text
请继续按 Slice 2 实现 B 当前入选区。
要求同上。
```

### 注意

不要一次说：

- “把整页做完”

要说：

- “只做 Slice 1”
- “再做 Slice 2”

---

## Step 6：用 `visual-verdict` 看图验收

### 为什么这个很重要

很多页面“功能是对的，感觉却不对”，就是因为没人做视觉结构验收。

### 这个阶段谁负责

- skill：`visual-verdict`
- role：`verifier`

### 你应该怎么下指令

```text
$visual-verdict
请基于 CreativeDetail 交互规范，
审查当前页面截图：
1. 首屏主任务是否清楚
2. A 当前定义区是否成立
3. B 当前入选区是否成立
4. D/E 是否抢了首屏
5. CTA 主次是否清楚
```

### 这一步看什么

不是看像不像设计稿，而是看：

- 页面主语义成立了吗
- 首屏优先级对了吗
- A/B 的区分真的看得出来吗

---

## Step 7：最后用 `verifier` 做完成验证

### 为什么还要最后一层

因为截图过了，不等于实现逻辑和状态都对。

### 这个阶段谁负责

- role：`verifier`

### 它负责什么

- 核对实现是否符合规范
- 核对状态是否可用
- 核对 CTA 行为是否正确
- 核对 readiness 提示是否合理
- 核对代码 / 测试 / 页面行为

### 你应该怎么下指令

```text
请作为 verifier，
检查 CreativeDetail 当前实现是否满足：
1. A/B 主骨架成立
2. 提交条件可解释
3. loading/error/empty/readiness 状态正确
4. 与已保存的规格文档一致
5. 还有哪些未完成项
```

---

# 5. 什么时候用 `team`

## 不要一开始就用

因为一开始最容易乱。

### 什么时候适合 `team`

当以下条件成立时：

- 页面语义已经锁定
- 交互骨架已经确定
- 切片计划已经写好
- 只是要并行推进

### 这时可以这么分

- `designer`：看结构和局部优化
- `architect`：看技术映射
- `executor`：实现
- `verifier`：验收

### 什么时候不适合

如果还在争：

- 这页到底是什么页
- 首屏该看什么
- 哪块该主、哪块该次

那就**不要 team**。

---

# 6. 最常见的错误流程

## 错误流程 1

`executor` → `executor` → `executor`

后果：

- 越改越像旧页面
- 一直在修补，不是在设计

## 错误流程 2

`designer` 和 `executor` 同时开干，但没有规范

后果：

- 一边设计一边实现
- 最后都说自己理解对

## 错误流程 3

跳过 `architect`

后果：

- 交互方案看着对
- 代码改造落地很痛苦
- 页面结构重新塌回并列堆叠

---

# 7. 对当前项目，最实用的“现在开始”版本

其实现在已经做完前半段一部分了。

## 已经有的产物

- 业务流程分析
- A+B 规范
- OMX 角色分工建议
- 页面规范模板

所以现在**不用从 Step 1 重来**，而是从这里开始最合适：

### 现在的推荐顺序

1. `ui-ux-pro-max` / `designer`
   - 补出 **CreativeDetail A+B 首屏低保真骨架**
2. `architect`
   - 输出 **CreativeDetail.tsx 改造映射方案**
3. `executor`
   - 实现 **Slice 1：A 当前定义区**
4. `visual-verdict`
   - 看图验收
5. `executor`
   - 实现 **Slice 2：B 当前入选区**
6. `visual-verdict` + `verifier`
   - 再验收

---

# 8. 以后可以直接这么用

如果想让我按这个流程带着走，可以直接一句话这样说：

```text
按 CreativeDetail 的 OMX 工作流来。
先用 designer / ui-ux-pro-max 给我出 A+B 首屏低保真骨架，
再用 architect 给我出技术映射，
确认后再让 executor 做 Slice 1。
```

这句话就够了。

---

# 9. 超短版本

## CreativeDetail 的标准跑法

1. `deep-interview` / `analyst`：定边界  
2. `ui-ux-pro-max` / `designer`：定交互  
3. `plan` / `planner`：定切片  
4. `architect`：定技术结构  
5. `executor`：按片实现  
6. `visual-verdict` / `verifier`：截图验收与完成验证

---

如果需要，下一步可以继续补：

**《CreativeDetail 的 OMX 执行剧本 v1》**  
把上面这些角色，进一步写成可直接照抄执行的任务清单。
