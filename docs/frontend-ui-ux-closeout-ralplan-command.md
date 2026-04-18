# Frontend UI/UX Closeout Ralplan Command

以下命令可直接复制执行：

```text
$ralplan: 把 frontend 作为一个单独阶段做“UI/UX 收口 + 技术栈最佳实践对齐”规划。
目标不是重做视觉，而是按技术栈最佳实践收口当前界面：
- 优先复用 Ant Design / ProComponents / React Router / React Query 的现成能力
- 不新增技术栈已经提供的基础组件
- 只抽业务域组件，不抽通用 UI 壳组件
- 统一信息架构、页面布局模式、状态反馈、文案语言
- 统一 workbench / detail / dashboard / task diagnostics 的职责边界
- 把业务信息与高级诊断信息分层
- 输出可执行 PR 计划，每个 PR 都要有变更范围、组件策略、验收标准、测试方式
```

## 推荐用途

适用于下一阶段前端收口规划，重点解决：

- Creative-first 界面的信息架构收口
- 页面布局与交互模式统一
- antd / procomponents 组件复用策略
- loading / empty / error / success 四态统一
- 中英文文案统一
- AIClip / review / diagnostics 的层次化表达

## 期望产出

建议本轮 `ralplan` 最终输出：

1. 一份 **Phase E / Frontend UI-UX Closeout** PR 计划
2. 每个 PR 的：
   - 文件范围
   - 组件复用策略
   - 页面边界
   - 验收标准
   - 测试方式
