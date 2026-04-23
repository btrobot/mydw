# 工作台相关页面可执行重构路线图

## 文档目标

这份路线图不是抽象建议，而是面向执行的重构方案。目标是：

1. 降低 Workbench 状态同步复杂度
2. 拆解 CreativeDetail 超级页面风险
3. 保留当前正确的产品方向：**以作品为中心**
4. 用小步可回滚的方式推进，而不是一次性推翻

---

## 当前问题归纳

### P0 问题

#### 1. Workbench 存在多状态源并存

当前同时有：

- URL search params
- ProTable 内部 form / request 状态
- React Query 数据状态

结果：

- preset / filter / sort / page 之间容易不同步
- 需要手动 `setFieldsValue`
- 需要 `request` 桥接 URL
- 甚至需要通过 `key={searchParams.toString()}` remount 兜底

#### 2. CreativeDetail 已接近超级页面

单页承载：

- 作品输入
- 素材编排
- 保存 / 提交合成
- 版本
- 审核
- 发布池
- 高级诊断
- AIClip 抽屉
- task diagnostics 跳转

结果：

- 阅读成本高
- 修改耦合高
- 很难继续稳定扩展

#### 3. 诊断信息可读，但行动性不足

现在偏“解释型信息展示”，还不够像“下一步该做什么”的操作台。

---

## 重构原则

1. **不推翻产品模型**
   - 继续坚持“作品为主对象”
   - 不退回“任务为中心”

2. **先收敛状态，再拆页面**
   - 先修地基，再拆房间

3. **每一步都可回滚**
   - 每个阶段都独立可上线
   - 避免大爆炸式重构

4. **先保证行为一致，再优化结构**
   - 先锁回归测试
   - 再改实现

---

## 目标架构

### 目标一：Workbench 单一状态源

希望最终变成：

- URL 是唯一可持久状态源
- 页面内部从 URL 派生查询参数
- 表单只是 URL 的投影，不再自己持有独立业务状态

即：

`URL -> parsed query state -> React Query request -> render`

而不是：

`URL <-> ProTable form <-> request callback <-> React Query`

### 目标二：CreativeDetail 分区清晰

希望最终拆成三个明确区块：

1. **创作输入区**
2. **版本 / 审核区**
3. **发布 / 诊断区**

不一定必须拆成真正路由，但至少要先拆成清晰容器与独立 view-model。

### 目标三：诊断区从“说明”升级为“行动建议”

诊断区域优先回答：

- 当前卡在哪
- 为什么卡住
- 下一步去哪里

---

## 分阶段执行方案

---

## Phase 0：锁行为，补测试

### 目标

在动结构前，把当前关键行为锁住。

### 要做的事

#### Workbench

补足以下回归测试：

- preset 左到右、右到左切换
- 从全部 -> preset -> 全部
- filter + preset 混用
- sort 改变后返回 preset
- page/pageSize 切换后状态恢复
- 从详情返回工作台时状态恢复

#### CreativeDetail

补足以下回归测试：

- 保存输入不影响版本/审核展示
- 打开高级诊断不影响主表单
- AIClip 抽屉开关不破坏 returnTo / taskId / diagnostics 参数
- 版本区、发布区、诊断区各自空态 / 错态

### 产出

- 更完整的 E2E 回归保护网

### 完成标准

- 现有主路径有稳定自动化测试
- 后续重构阶段出现行为偏差能被第一时间发现

---

## Phase 1：收敛 Workbench 查询状态

### 目标

去掉 Workbench 三套状态互相推的模式。

### 重构方向

抽一个显式的 workbench query state 层，例如：

- `parseWorkbenchQuery(searchParams)`
- `buildWorkbenchQuery(nextState)`
- `normalizeWorkbenchQuery(state)`
- `useWorkbenchQueryState()`

### 要做的事

#### 1. 定义统一状态对象

例如：

- `keyword`
- `status`
- `poolState`
- `preset`
- `sort`
- `page`
- `pageSize`
- `diagnostics`

把它作为唯一业务状态结构。

#### 2. URL 成为唯一持久状态源

所有以下行为都只做一件事：

- preset 点击
- sort 变化
- filter 提交
- 重置
- page 变化
- diagnostics 开关

统一改成：

- 计算 next state
- 写回 URL

而不是同时：

- 改 form
- 改 request
- 改 actionRef

#### 3. 把 ProTable 降级成纯展示表格

建议逐步减少对 `ProTable.request` 的依赖：

- 数据请求由外部 React Query 完成
- ProTable 只吃 `dataSource`
- 搜索区如有必要，单独控制提交动作

如果 ProTable 持续与架构冲突，允许后续替换成：

- 普通 `Card + Form + Table + Pagination`

### 产出

- `useWorkbenchQueryState` 或等价 query state 模块
- Workbench 不再依赖 request 回调桥接业务状态

### 完成标准

- 不再需要靠 remount 兜同步
- preset / filter / sort / page 全部通过统一状态链路工作
- 代码阅读时能明确指出“唯一状态源在哪里”

---

## Phase 2：拆 Workbench 页面结构

### 目标

把 Workbench 从“大组件”拆成若干职责清晰的块。

### 建议拆分

#### 1. `WorkbenchSummaryCard`

负责：

- 入口模式
- 基础 summary
- 运行诊断入口

#### 2. `WorkbenchFilterBar`

负责：

- 搜索
- 状态筛选
- 池状态筛选
- 应用 / 重置

#### 3. `WorkbenchPresetBar`

负责：

- 高频视角按钮
- preset 计数
- 当前选中态

#### 4. `WorkbenchTable`

负责：

- 列表展示
- sort
- pagination
- 行级跳转按钮

#### 5. `WorkbenchDiagnosticsDrawer`

负责：

- 运行态信息
- warning / retry
- 与主列表解耦

### 注意

这里的拆分不是为了“文件变多”，而是为了：

- 让每个区域有单独 props 边界
- 减少一个文件内上下文切换
- 后续可以单独测单个区域

### 完成标准

- `CreativeWorkbench.tsx` 只保留页面装配逻辑
- 大部分 UI 被下沉到独立组件

---

## Phase 3：拆 CreativeDetail 的 view-model 与区域职责

### 目标

不立刻改交互形态，先拆内部结构。

### 第一层拆分：按职责分 view-model

建议拆成：

#### 1. `useCreativeAuthoringModel`

负责：

- 表单初始化
- 校验
- 保存
- 提交合成前置逻辑

#### 2. `useCreativeVersionReviewModel`

负责：

- 当前版本
- 版本列表
- 审核摘要
- review drawer 打开关闭

#### 3. `useCreativePublishDiagnosticsModel`

负责：

- publish status
- schedule config
- pool items
- invalidated items
- shadow diff
- retry diagnostics

#### 4. `useCreativeNavigationState`

负责：

- `returnTo`
- `taskId`
- `tool`
- `diagnostics`

### 第二层拆分：按展示区块拆组件

建议拆成：

- `CreativeAuthoringSection`
- `CreativeVersionSection`
- `CreativePublishSection`
- `CreativeDiagnosticsDrawer`
- `CreativeAiClipDrawer`

### 完成标准

- `CreativeDetail.tsx` 不再同时持有所有请求与所有展示逻辑
- 单个区域修改不需要理解整页所有上下文

---

## Phase 4：把诊断区从“说明页”改成“行动面板”

### 目标

让诊断区更像操作支持，而不是领域说明集合。

### 改法

在诊断区顶部新增“当前建议动作”卡片。

例如：

- **待审核**
  - 建议：进入当前版本审核
- **版本未进入发布池**
  - 建议：先完成当前版本审核 / 提交合成
- **存在任务失败**
  - 建议：打开主执行诊断
- **发布侧版本不对齐**
  - 建议：查看发布池候选项与冻结值

### 表达顺序改成

1. 当前状态
2. 阻塞原因
3. 推荐动作
4. 底层诊断明细

### 完成标准

- 非开发用户不必先读完整说明文案，也能知道下一步动作

---

## Phase 5：决定是否升级为分区 Tab / 子路由

### 目标

在结构拆开后，再决定是否需要更强的信息分层。

### 可选方案

#### 方案 A：保持单页，但分大区块

适合：

- 用户已经习惯当前单页
- 切换成本不想太高

#### 方案 B：详情页增加 Tab

例如：

- 创作输入
- 版本与审核
- 发布与诊断

适合：

- 页面继续膨胀
- 首屏信息量过大
- 不同角色只关心部分区域

#### 方案 C：子路由

例如：

- `/creative/:id/authoring`
- `/creative/:id/review`
- `/creative/:id/publish`

适合：

- 后续功能继续扩张
- 需要更强的权限、埋点、独立分享链接能力

### 建议

短期先不做子路由，优先完成前四个阶段。  
完成后再基于真实使用反馈判断要不要上 Tab / 子路由。

---

## 推荐实施顺序

### 最小可执行路径

1. **Phase 0**
   - 补测试
2. **Phase 1**
   - 收敛 Workbench 状态源
3. **Phase 2**
   - 拆 Workbench 结构
4. **Phase 3**
   - 拆 CreativeDetail view-model
5. **Phase 4**
   - 诊断升级为行动面板
6. **Phase 5**
   - 评估 Tab / 子路由

---

## 每阶段的风险控制

### Phase 1 风险

- URL 状态重构可能引入回归

控制方式：

- 先补 E2E
- 一次只改一个状态入口

### Phase 2 风险

- 组件拆分后 props 过多

控制方式：

- 先拆数据模型，再拆 UI 容器

### Phase 3 风险

- 详情页拆分过程中容易引入查询时序问题

控制方式：

- 先拆 hooks，不先拆视觉结构

### Phase 4 风险

- 过度“产品化”后丢掉底层信息

控制方式：

- 保留原诊断细节，只调整展示顺序

---

## 不建议现在做的事

以下事项目前不建议优先做：

### 1. 不建议先全面视觉重做

现在核心问题不是皮肤，而是结构。

### 2. 不建议一次性把 Workbench/Detail 全部重写

风险太高，且难以验证。

### 3. 不建议先引入新状态管理库

当前优先级是收敛状态模型，不是增加技术栈。

### 4. 不建议先把任务页重新抬成主入口

这会破坏已经做对的产品主轴。

---

## 预期收益

如果按这条路线走，预期会得到：

### 对用户

- 工作台行为更稳定
- 筛选 / preset / 返回状态更可信
- 详情页认知负担下降
- 诊断更接近“下一步建议”

### 对开发

- 更少的状态同步 bug
- 更低的页面修改耦合
- 更清晰的测试边界
- 后续加功能时风险更可控

---

## 最终建议

一句话建议：

> 不要推翻这套“作品为中心”的产品方向；应当在保留当前信息架构优势的前提下，优先收敛 Workbench 状态模型，再逐步拆解 CreativeDetail 的实现复杂度。

如果只能选一个最先做的动作：

> **先做 Phase 1：Workbench 状态源收敛。**

因为这是当前最容易继续放大 bug 的位置，也是后续所有优化的地基。

---

## 按 OMX 最佳实践如何执行这份 roadmap

这份 roadmap 不应作为一次性“大重构”执行。  
按 OMX 最佳实践，正确姿势是：

> **先用 `ralplan` 把每个 phase 切成独立 slice，再按规模选择 `ralph` 或 `team` 执行。**

### 总策略

#### 1. 一次只做一个 slice

不要直接说：

- “重构整个 workbench”
- “把 creative detail 全拆了”

而要拆成独立交付物，例如：

- Slice A：补测试，锁 Workbench / Detail 行为
- Slice B：收敛 Workbench 查询状态源
- Slice C：拆 Workbench 页面结构

每个 slice 都必须：

- 有明确范围
- 有明确验收标准
- 能单独提交 / 回滚

#### 2. 标准流程永远是：`ralplan -> ralph/team`

对于这种重构任务，不建议一上来直接 `ralph`。

推荐顺序：

- **先**：`$ralplan --interactive`
- **再**：
  - 单 lane / 中小 slice：`$ralph`
  - 多 lane / 可并行 slice：`$team`

#### 3. 每个 slice 完成后独立验证并提交

不要攒成一个超级分支里的超级提交。  
应当每个 slice：

1. 计划
2. 执行
3. 验证
4. 提交
5. 再进入下一个 slice

---

## OMX 下的推荐执行顺序

### Slice A：先补测试

这是第一步，不建议跳过。

目标：

- 给 Workbench / Detail 建立重构保护网
- 锁住 preset / filter / sort / returnTo / diagnostics / AIClip drawer 等关键路径

建议执行模式：

- 先 `ralplan`
- 再 `ralph`

原因：

- 这是单主线、强验证型任务
- 不需要太多并行 lane

### Slice B：收敛 Workbench 状态源

这是整个路线图里优先级最高的一步。

目标：

- 让 URL 成为唯一持久状态源
- 降低 ProTable form / request 与 React Query 的双向推状态

建议执行模式：

- 先 `ralplan`
- 再按计划复杂度选择：
  - 中等规模：`ralph`
  - 可拆 lane：`team`

通常建议优先考虑 `team`，因为它天然可拆为：

- query-state lane
- 页面接线 lane
- 测试 / 验证 lane

### Slice C：拆 Workbench 页面结构

这一步要在状态源收敛之后做，不建议倒序。

目标：

- 拆成 Summary / Filter / Preset / Table / Diagnostics 等独立块
- 页面主文件只保留装配逻辑

建议执行模式：

- 先 `ralplan`
- 再 `team`

原因：

- 非常适合拆分多个并行 lane
- 适合组件级职责边界收敛

---

## 在 ralplan 阶段必须要求输出的内容

每个 slice 的计划里，都应该明确写出：

### 1. 范围边界

- 改什么
- 不改什么

### 2. 风险点

- 哪些行为最容易回归

### 3. 验收标准

必须可测试，例如：

- preset 无回归
- returnTo 正常
- diagnostics 不破坏主流程
- typecheck / e2e 通过

### 4. 文件触点

明确会改哪些文件。

### 5. 执行建议

计划需要明确说明：

- 更适合 `ralph` 还是 `team`
- 如果是 `team`，需要几条 lane

---

## Slice A/B/C 的 OMX 指令清单

下面这组命令是“最小可执行版本”，可以直接作为实际落地模板使用。

### Slice A：测试补强

#### A1. 先做共识规划

```bash
$ralplan --interactive "为 creative workbench / detail 重构建立回归保护网。范围仅限补测试，不改产品行为。目标：锁住 preset、filter、sort、returnTo、detail diagnostics、AIClip drawer 等关键路径。要求输出 PRD、test spec、风险、文件触点、验收标准，以及推荐执行模式。"
```

#### A2. 批准后执行

```bash
$ralph "执行已批准的 Slice A：为 creative workbench / detail 补齐重构保护测试。只补测试，不做结构重构。"
```

#### A3. 完成标准

- 有新增 / 补足的自动化测试
- typecheck / e2e 通过
- 单独提交

---

### Slice B：Workbench 状态源收敛

#### B1. 先做共识规划

```bash
$ralplan --interactive "重构 CreativeWorkbench 的状态管理。目标：让 URL 成为唯一持久状态源，减少 ProTable form/request 与 React Query 的双向推状态；保持当前产品行为不变；不做视觉改版。要求输出 PRD、test spec、风险、文件触点、验收标准，以及推荐执行模式。"
```

#### B2. 如果计划判断适合单主线执行

```bash
$ralph "执行已批准的 Slice B：收敛 CreativeWorkbench 状态源。保持 preset/filter/sort/page/diagnostics/returnTo 行为一致。"
```

#### B3. 如果计划判断适合并行 lane 执行

```bash
$team 3:executor "执行已批准的 Slice B：收敛 CreativeWorkbench 状态源。建议 lane 为 query-state、页面接线、测试验证。"
```

#### B4. 完成标准

- 不再依赖多套状态互相推
- 不再依赖 remount 兜底同步作为核心机制
- preset / filter / sort / page / diagnostics / returnTo 全链路回归通过
- 单独提交

---

### Slice C：拆 Workbench 页面结构

#### C1. 先做共识规划

```bash
$ralplan --interactive "拆分 CreativeWorkbench 页面结构。目标：将页面拆为 SummaryCard / FilterBar / PresetBar / WorkbenchTable / DiagnosticsDrawer 等独立组件；不改变用户行为；要求输出 PRD、test spec、风险、文件触点、验收标准，以及推荐执行模式。"
```

#### C2. 批准后并行执行

```bash
$team 3:executor "执行已批准的 Slice C：拆分 CreativeWorkbench 页面结构。建议 lane 为 summary+filter/preset、table+pagination/row-actions、diagnostics+验证。"
```

#### C3. 完成标准

- `CreativeWorkbench.tsx` 只保留页面装配逻辑
- 主要 UI 被拆到职责清晰的子组件
- 用户行为与 URL 语义无回归
- 单独提交

---

## 最简推荐起手式

如果现在就要开始，建议直接从下面这个顺序启动：

### 第一步：只规划 Slice A 与 Slice B

```bash
$ralplan --interactive "为 workbench/detail 重构建立执行计划。先只规划 Slice A（测试补强）与 Slice B（Workbench 状态源收敛），不要扩到 CreativeDetail 拆分。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 第二步：先做 Slice A

```bash
$ralph "执行已批准的 Slice A：测试补强"
```

### 第三步：再细化 Slice B

```bash
$ralplan --interactive "规划并细化 Slice B：Workbench 状态源收敛。要求明确 URL 单一状态源方案与回归验证方案。"
```

### 第四步：按计划选择执行模式

适合单主线：

```bash
$ralph "执行已批准的 Slice B：Workbench 状态源收敛"
```

适合并行 lane：

```bash
$team 3:executor "执行已批准的 Slice B：Workbench 状态源收敛"
```

---

## 最终执行建议

一句话版本：

> 不要把这份 roadmap 当成一次性大修；应当按 slice 走 `ralplan`，批准后再用 `ralph` 或 `team` 执行，每个 slice 独立验证、独立提交。

如果只能选一个最值得先落地的动作：

> **先做 Slice A，然后马上推进 Slice B。**

因为测试保护网和 Workbench 状态收敛，是后续所有结构优化的共同地基。

---

## Slice D/E 的 OMX 指令清单

下面补充 CreativeDetail 重构与诊断行动化这两个后续 slice 的可执行命令。

### Slice D：拆 CreativeDetail 的 view-model

#### D1. 先做共识规划

```bash
$ralplan --interactive --deliberate "重构 CreativeDetail 内部结构。目标：拆分 authoring / version-review / publish-diagnostics / navigation state 的 view-model；保持当前页面对用户的整体信息架构不变；先不改成子路由。要求输出 PRD、test spec、风险、文件触点、验收标准，以及推荐执行模式。"
```

#### D2. 批准后并行执行

```bash
$team 4:executor "执行已批准的 Slice D：拆分 CreativeDetail 的 view-model。建议 lane 为 authoring model、version/review model、publish/diagnostics model、测试与整体验证。"
```

#### D3. 如果 team 执行后还需要单 owner 收口

```bash
$ralph "对已完成的 Slice D 进行收口、清理、最终验证与反回归修正。"
```

#### D4. 完成标准

- `CreativeDetail.tsx` 不再同时承载所有数据请求与所有展示逻辑
- authoring / version-review / publish-diagnostics / navigation state 至少完成一层 view-model 拆分
- 用户对页面的主流程认知不变
- 关键路径回归通过
- 单独提交

---

### Slice E：把诊断区升级为行动面板

#### E1. 先做共识规划

```bash
$ralplan --interactive "优化 creative detail / workbench diagnostics 的信息架构。目标：从解释型文案升级为行动建议型诊断面板，优先展示当前状态、阻塞原因、推荐动作；底层明细仍然保留。要求输出 PRD、test spec、风险、文件触点、验收标准，以及推荐执行模式。"
```

#### E2. 批准后执行

```bash
$ralph "执行已批准的 Slice E：把 diagnostics 从解释型展示升级为行动建议型面板，保持底层诊断明细可见。"
```

#### E3. 如果计划判断适合多 lane 并行

```bash
$team 3:executor "执行已批准的 Slice E：升级 diagnostics 为行动建议型面板。建议 lane 为信息架构/文案、UI 接线、测试验证。"
```

#### E4. 完成标准

- 诊断区顶部优先展示当前状态 / 阻塞原因 / 推荐动作
- 底层明细、对账、发布池、任务诊断信息仍可访问
- 不破坏现有主流程与跳转路径
- 用户可以不读完整说明文案也知道下一步去哪
- 单独提交

---

## A/B/C/D/E 的推荐推进顺序

如果完整按 roadmap 推，建议顺序为：

1. Slice A：测试补强
2. Slice B：Workbench 状态源收敛
3. Slice C：Workbench 页面结构拆分
4. Slice D：CreativeDetail view-model 拆分
5. Slice E：诊断行动化

### 推荐原因

- A/B 是地基
- C 是 Workbench 结构整理
- D 是 Detail 内部解耦
- E 是在结构稳定后做产品表达优化

---

## 完整起手模板（更新版）

如果现在要从头按 OMX 落地整套 roadmap，可按下面顺序执行：

### 第一步：先规划 A/B

```bash
$ralplan --interactive "为 workbench/detail 重构建立执行计划。先只规划 Slice A（测试补强）与 Slice B（Workbench 状态源收敛），不要扩到 CreativeDetail 拆分。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 第二步：执行 A

```bash
$ralph "执行已批准的 Slice A：测试补强"
```

### 第三步：细化并执行 B

```bash
$ralplan --interactive "规划并细化 Slice B：Workbench 状态源收敛。要求明确 URL 单一状态源方案与回归验证方案。"
```

按计划选择其一：

```bash
$ralph "执行已批准的 Slice B：Workbench 状态源收敛"
```

或

```bash
$team 3:executor "执行已批准的 Slice B：Workbench 状态源收敛"
```

### 第四步：规划并执行 C

```bash
$ralplan --interactive "拆分 CreativeWorkbench 页面结构。目标：将页面拆为 SummaryCard / FilterBar / PresetBar / WorkbenchTable / DiagnosticsDrawer 等独立组件；不改变用户行为；要求输出 PRD、test spec、风险、文件触点、验收标准，以及推荐执行模式。"
```

```bash
$team 3:executor "执行已批准的 Slice C：拆分 CreativeWorkbench 页面结构。"
```

### 第五步：规划并执行 D

```bash
$ralplan --interactive --deliberate "重构 CreativeDetail 内部结构。目标：拆分 authoring / version-review / publish-diagnostics / navigation state 的 view-model；保持整体信息架构不变。"
```

```bash
$team 4:executor "执行已批准的 Slice D：拆分 CreativeDetail 的 view-model。"
```

### 第六步：规划并执行 E

```bash
$ralplan --interactive "优化 creative detail / workbench diagnostics 的信息架构。目标：从解释型文案升级为行动建议型诊断面板。"
```

按计划选择其一：

```bash
$ralph "执行已批准的 Slice E：升级 diagnostics 为行动建议型面板"
```

或

```bash
$team 3:executor "执行已批准的 Slice E：升级 diagnostics 为行动建议型面板"
```

---

## Roadmap 总收口状态（2026-04-23）

本 roadmap 已按 A/B/C/D/E 五个 slice 完成阶段性收口。对应总收口文档见：

- `discss/workbench-detail-refactor-plan-closeout-2026-04-23.md`

### PR / commit 与计划映射

| Slice | 计划文件 | commit / PR 语义 | 收口状态 |
| --- | --- | --- | --- |
| Slice A：测试补强 | `.omx/plans/prd-workbench-slice-ab-2026-04-23.md` | `5babe1e` 锁定 Workbench query / preset / route 行为 | 已完成 |
| Slice B：Workbench 状态源收敛 | `.omx/plans/prd-workbench-slice-ab-2026-04-23.md` | `f02889d` URL canonical query state | 已完成 |
| Slice C：Workbench 页面结构拆分 | `.omx/plans/prd-workbench-slice-c-2026-04-23.md` | `65d119a` 拆 SummaryCard / PresetBar / WorkbenchTable / DiagnosticsDrawer | 已完成 |
| Slice D：CreativeDetail view-model 拆分 | `.omx/plans/prd-creative-detail-slice-d-2026-04-23.md` | `71cd132` 拆 authoring / version-review / publish-diagnostics / navigation state | 已完成 |
| Slice E：diagnostics 行动面板 | `.omx/plans/prd-creative-diagnostics-action-panel-2026-04-23.md` | `fe0d052` 增加 Workbench / Detail 推荐行动面板 | 已完成 |

### 总结论

这个 roadmap 的主目标已经达成：

- Workbench 状态源已收敛到 URL canonical query state。
- 高频 preset / filter / sort / pagination / detail return / diagnostics route chrome 已由 E2E 锁定。
- Workbench 已完成第一轮结构拆分，父页面仍是唯一 canonical query state owner。
- CreativeDetail 已完成第一轮 view-model 拆分，核心行为归属清晰。
- Diagnostics 已从解释型文案升级为“推荐行动 + 原始证据”的信息架构。
- Workbench `diagnostics=runtime` 与 Detail `diagnostics=advanced` 语义保持不变。
- Diagnostics drawer 不触发 submit composition。

### 关闭边界

本 roadmap 到此关闭，不继续在本计划内扩展：

- 不做 CreativeDetail tab/subroute。
- 不在 diagnostics drawer 内增加 submit / publish 等强业务 mutation。
- 不新增后端 diagnostics API。
- 不新增状态管理依赖。
- 不继续重写 Workbench table 技术栈。

这些如后续确有必要，应作为新计划单独评估。

### 后续方向

下一阶段应回到业务能力闭环，而不是继续结构重构：

1. 发布链路 / 发布池真实能力补齐。
2. CreativeDetail 主创作区体验优化。
3. AIClip 与作品版本链路进一步闭环。
4. 仅当单页结构再次出现明确维护或使用痛点时，再评估 tab/subroute。

---

## 后续 ADP UI System Adoption 收口状态（2026-04-24）

Workbench / Detail 结构收口后，已继续执行一轮独立的 ADP UI System Adoption 计划，用于充分复用 Ant Design Pro / ProComponents，而不破坏前述 Workbench 状态边界。

对应总收口文档：

- `discss/adp-ui-system-adoption-closeout-2026-04-24.md`
- `.omx/plans/prd-adp-ui-system-adoption-2026-04-23.md`

### 与本 roadmap 的关系

ADP adoption 是本 roadmap 的后续 UI 系统化阶段，不改变本 roadmap 的核心结论：

- Workbench URL 仍是 canonical query state。
- Workbench 父组件仍是唯一 query state owner。
- ProTable 仍是受控展示与交互壳，不重新接管 Workbench request/query。
- Detail diagnostics 与 Workbench diagnostics 的 URL 语义保持不变。
- Diagnostics drawer 不新增 submit composition。

### 已完成的 ADP 后续动作

- ProLayout 已接入 shell，并通过 HashRouter / auth / mobile parity gate。
- CreativeDetail 只读信息已迁移到 ProDescriptions。
- CheckDrawer 已迁移到 DrawerForm。
- ListPageLayout 已评估并删除无用 wrapper。
- StatisticCard / ProCard、TaskCreate StepsForm 均完成 assessment，并在收益不足时明确 no-op。

因此，本 roadmap 与后续 ADP UI System Adoption 均已阶段性关闭。后续应优先推进业务闭环，而不是继续扩大 UI 重构范围。
