# Archive Export Snapshots Index / 导出快照索引

`docs/archive/exports/` 保存的是**导出型项目说明、结构映射与历史快照**。

当前主要内容包括：

- 架构与数据流快照
- 风险与重构建议快照
- 数据模型与字段职责快照
- 前后端页面/API 映射快照
- 任务生命周期与端到端序列快照

适合：

- 回看某次导出/外部分析产物
- 快速获取一份历史结构快照

不适合：

- 当作当前真实接口/模型/页面边界

如果 archive export 与 current docs 冲突，优先相信：

- `docs/current/*`
- `docs/domains/*`
- 当前代码与测试
