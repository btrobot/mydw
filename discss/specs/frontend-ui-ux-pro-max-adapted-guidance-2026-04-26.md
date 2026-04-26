# 用 ui-ux-pro-max 重新校准当前项目 UI 方向（适配版）

> 日期：2026-04-26  
> 项目：`frontend/`  
> 目的：不是“盲信 skill 原始输出”，而是把它当成 UI 设计数据库，结合当前项目特点做二次解释。

---

## 1. 我已经怎么用这个 skill

已执行：

1. 全局设计系统检索  
   - 查询：`electron admin dashboard AI creative workflow content publishing operations professional dense`
2. 页面级设计系统检索  
   - `creative-workbench`
   - `ai-clip`
3. 补充检索  
   - `ux`
   - `react`
   - `web`
   - `style`
   - `color`
   - `typography`
   - `chart`

原始持久化输出已保存到：

- `discss/specs/ui-ux-pro-max-2026-04-26/design-system/dewu-creative-ops/MASTER.md`
- `discss/specs/ui-ux-pro-max-2026-04-26/design-system/dewu-creative-ops/pages/creative-workbench.md`
- `discss/specs/ui-ux-pro-max-2026-04-26/design-system/dewu-creative-ops/pages/ai-clip.md`

---

## 2. 先说结论：这个 skill 能用，但不能直接照抄

### 能用的部分

它对下面这些很有价值：

- 风格候选库
- 配色候选库
- 字体候选库
- 交互/可访问性规则
- React/Web 常见 UI 反模式提醒

### 不能直接照抄的部分

它的“整页模式匹配”有明显误判：

- 全局设计系统里出现了 `Newsletter / Content First`
- `creative-workbench` 被误配成 `Product Review/Ratings`
- `ai-clip` 被误配成 `Enterprise Gateway`

这些都**不符合当前项目业务形态**。

所以正确用法不是：

> “让 skill 决定我们的产品长什么样”

而是：

> “让 skill 提供候选设计语言，再由我们按项目业务去裁剪”

---

## 3. 当前项目真正的产品特点

结合代码结构、路由和近期 Slice 改造，当前项目更像：

### 产品类型

**桌面端内容运营工作台 / 创意生产控制台 / 发布运营后台**

不是：

- 消费型产品
- 营销落地页
- 轻量 SaaS 官网
- 评分类/社区型产品

### 主要用户任务

用户不是来“浏览”，而是来**持续处理任务**：

1. 看队列
2. 查异常
3. 选素材
4. 配工作流
5. 提交处理
6. 审核结果
7. 管发布与调度

### 页面特征

这个项目有 3 类页面：

1. **诊断/列表页**
   - Dashboard
   - TaskList
   - Material lists
   - Auth session admin

2. **策略/配置页**
   - Settings
   - ScheduleConfig
   - ProfileManagement

3. **工作流/创作页**
   - CreativeWorkbench
   - AIClip
   - CreativeDetail

其中第 3 类页面最决定“高级感”。

---

## 4. skill 里真正适合我们的方向

### 4.1 风格：采用 `Data-Dense Dashboard`，但要升级为 `Operational Studio`

skill 里最贴近我们的不是 newsletter，不是 playful，不是 gateway，而是：

- `Data-Dense Dashboard`

这个方向适合：

- 运营后台
- 队列管理
- 高信息密度
- 表格 + 指标 + 状态 + 筛选

但我们不能只做“密”，还要做“工作流感”。

所以建议把目标风格定义为：

> **Operational Studio（运营工作台风格）**  
> = Data-Dense Dashboard + Workflow Clarity + Calm Enterprise UI

它的关键词应该是：

- dense but readable
- operational
- queue-first
- workflow-aware
- diagnostic-friendly
- enterprise calm

---

### 4.2 配色：不用 raw 输出里的粉青体系，改用“信任蓝 + 状态色”

skill 原始落盘结果里出现的粉色/青色体系，不适合当前项目。

更适合当前项目的是它在 `color` 检索里给出的这些方向：

- `SaaS (General)`：蓝 + 橙
- `Analytics Dashboard`：蓝 + 琥珀
- `Financial Dashboard`：深色 + 绿（适合作为局部诊断色，不适合全站）

### 推荐适配版

- **Primary**：`#2563EB` 或更接近当前 Ant Design 主蓝
- **Secondary**：`#3B82F6`
- **Success**：`#16A34A`
- **Warning**：`#D97706`
- **Error**：`#DC2626`
- **Surface**：`#FFFFFF`
- **Page background**：`#F8FAFC` 或当前轻灰布局底
- **Text primary**：`#0F172A`
- **Text secondary**：`#475569`

### 设计原则

- 全站保持**浅色工作台**
- 深色只用于：
  - 诊断抽屉
  - 日志区
  - 只读技术信息块
- 不建议把整站切成炫酷暗黑风

---

### 4.3 字体：优先 `Inter` / `IBM Plex Sans`，不要走 playful 路线

skill 检索里最适合我们的是：

1. `Inter`
2. `IBM Plex Sans`
3. `Lexend + Source Sans 3`（次优）

### 推荐顺序

- **第一选择：Inter**
  - 最稳
  - 最中性
  - 最适合管理后台
  - 与 Ant Design 气质兼容

- **第二选择：IBM Plex Sans**
  - 更有“系统工具 / 专业控制台”气质
  - 很适合数据、状态、操作型产品

### 不建议

- Fredoka / Nunito 这类偏 playful 字体
- 过强“品牌感”的标题字体

因为这个项目核心不是“情绪表达”，而是“操作可靠感”。

---

## 5. skill 给我们的关键 UX 提醒（这部分很有价值）

从 `ux / web / react` 检索里，最值得立刻吸收的是：

### 5.1 不能只靠颜色表达状态

现在这种项目里最危险的 UI 问题不是“不够漂亮”，而是：

- 成功/失败只看颜色
- 风险状态不够明确
- 错误只在顶部提示

应改为：

- 颜色 + 图标
- 颜色 + 标签文字
- 颜色 + 明确动作建议

---

### 5.2 标题层级必须稳定

这个项目页面层级已经开始统一 `PageHeader`，这是对的。  
下一步要继续保证：

- 页面标题 = 一级入口语义
- Section 标题 = 二级任务区
- 卡片标题 = 局部模块语义

不能出现：

- 只是视觉变大，但语义层级混乱

---

### 5.3 Drawer / Modal / Table / Form 的焦点与键盘路径要统一

skill 的 `web` 检索提醒是对的：

- 只靠 `onClick` 不够
- 焦点态不能丢
- destructive action 必须 confirm
- 表单错误最好靠近字段

这对你项目尤其重要，因为你有大量：

- Modal
- Drawer
- 表格行操作
- 批量操作
- 配置表单

---

### 5.4 长列表最终要考虑虚拟化

React 检索里最 relevant 的一条是：

> 列表数据量超过 100 时考虑虚拟化

这对：

- TaskList
- CreativeWorkbench
- Material lists

都成立。

这不是马上第一优先级，但应作为后续性能/UI 联动项。

---

## 6. 适合当前项目的 UI 战略，不适合当前项目的 UI 战略

## 6.1 适合

### A. Calm Enterprise

特点：

- 稳定
- 专业
- 清楚
- 不卖弄
- 可持续扩展

### B. Operational Studio

特点：

- 强工作流感
- 主操作明确
- 诊断信息有稳定落点
- 内容区是“处理区”不是“宣传区”

### C. Dense but breathable

特点：

- 信息密度高
- 但扫描负担低
- 靠分区和层级，不靠大段解释

---

## 6.2 不适合

### A. 过度营销化

不适合：

- Hero 式大标题
- 大面积展示图
- 强 CTA 落地页语言

### B. 过度 playful / AI 炫技感

不适合：

- 粉紫渐变
- 霓虹科技风
- 巨大动效
- 强视觉噪音

### C. 纯 BI 风

也不适合只做成纯报表系统。

因为你项目不是只看数据，它还有：

- 选素材
- 提工作流
- 审核
- 生成
- 发布

所以它不是纯 dashboard，而是 **dashboard + workflow studio**。

---

## 7. 这意味着接下来 UI 不该怎么做

### 不该继续只做：

- 每页加 `PageHeader`
- 每页加 `InlineNotice`
- 横向平推更多页面

这只能解决“统一”，不能解决“高级感”。

### 应该开始做：

1. **内部结构组件**
   - `PageSectionCard`
   - `FilterBar`
   - `DangerZoneCard`
   - `InspectorPanel`
   - `MetricStrip`

2. **工作流页面模板**
   - Workbench layout
   - AI processing layout
   - Detail + side diagnostics layout

3. **状态表达系统**
   - inline state
   - section empty
   - blocking error
   - recoverable warning
   - action recommendation

---

## 8. 现在如果真的用这个 skill 来指导下一步，最应该打哪里

### 第一优先级

- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`

原因：

- 它最像“产品主战场”
- 它最能体现工作台质感
- 它最能决定用户是否觉得这套前端“高级”

### 第二优先级

- `frontend/src/pages/AIClip.tsx`

原因：

- 它现在更像“包了一层说明文案的工具页”
- 还没形成真正的流程结构感

### 第三优先级

- `frontend/src/features/creative/pages/CreativeDetail.tsx`

原因：

- 复杂度最高
- 最后打更稳

---

## 9. 用 skill 之后，我给这个项目的最终 UI 定位

### 一句话定位

> **不是“漂亮后台”，而是“创意生产运营工作台”**

### 更准确的风格定义

> **Calm Enterprise + Operational Studio + Data-Dense Dashboard**

拆开说就是：

- 页面壳层统一
- 内部结构明确
- 信息密度高但不拥堵
- 强调流程、状态、动作，而不是装饰

---

## 10. 后续如何继续正确使用 ui-ux-pro-max

建议以后别再直接问它“给我整个设计系统”，而是按页面类型拆开问。

### 对这个项目更有效的用法

#### 用法 A：查风格基线

```bash
python .codex/skills/ui-ux-pro-max/scripts/search.py "enterprise operational dashboard content workflow" --domain style -n 5
```

#### 用法 B：查配色候选

```bash
python .codex/skills/ui-ux-pro-max/scripts/search.py "saas dashboard enterprise" --domain color -n 5
```

#### 用法 C：查字体候选

```bash
python .codex/skills/ui-ux-pro-max/scripts/search.py "professional modern neutral enterprise dashboard" --domain typography -n 5
```

#### 用法 D：查工作流页交互规则

```bash
python .codex/skills/ui-ux-pro-max/scripts/search.py "keyboard focus modal drawer table form" --domain web -n 8
```

#### 用法 E：查 React/长列表风险

```bash
python .codex/skills/ui-ux-pro-max/scripts/search.py "react antd dashboard tables drawers workflow performance" --stack react
```

---

## 11. 给 AI 提要求时，应该怎么说

下面这类 prompt 比“做漂亮一点”有效得多：

### Prompt 模板

> 请把这个页面改造成“Calm Enterprise + Operational Studio”风格的管理后台页面。  
> 目标不是营销感，而是高密度、可扫描、可操作的工作台体验。  
>  
> 要求：  
> 1. 页面顶部有稳定的 PageHeader，明确页面任务，而不是只放标题。  
> 2. 主操作放在页头或区块头，不要把主按钮埋进表格工具栏。  
> 3. 页面内部按任务分区，用 2~4 个稳定 section，而不是长页面堆叠。  
> 4. 状态表达不要只靠颜色，要有标签/图标/动作建议。  
> 5. 保持信息密度高，但用卡片、边界、留白、标题层级来降低扫描成本。  
> 6. 不要使用营销化 hero、大渐变、夸张动效、playful 字体。  
> 7. 风格优先参考 enterprise dashboard / operational console / workflow studio。  
> 8. 技术栈是 React + Ant Design，优先复用现有组件，不引入新依赖。  

---

## 12. 当前最重要的判断

### 是不是该用这个 skill？

**是，应该用。**

### 但怎么用？

**把它当“设计参考数据库”，不要当“自动生成正确答案的设计总监”。**

### 对当前项目最重要的价值是什么？

不是直接给你一套完美视觉稿，而是帮助我们：

- 校准风格方向
- 避开明显不适合的风格
- 明确接下来该打“工作台内部结构”，而不是继续只包页面外壳

---

## 13. 基于这次 skill 结果，我建议的下一步

下一步不是继续横向推更多页面，而是：

1. 先抽 2~4 个内部结构组件
2. 用它们重做 `CreativeWorkbench`
3. 再把 `AIClip` 改成真正的流程页

这才是从“统一”走向“真正变好看、变高级”的关键转折点。
