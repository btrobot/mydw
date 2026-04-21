# Archive Docs Index / 历史归档导航

> 目的：给 `docs/archive/` 一个稳定入口，回答“这些历史资料怎么分层、先去哪找、哪些只是归档参考而不是 current truth”。

## 1. 使用原则

`docs/archive/` 保存的是：

- 历史参考
- 已退出主线的 planning / analysis / closeout 文档
- 导出型快照与探索性材料

它**不是当前真相入口**。

默认阅读顺序仍然是：

1. `README.md`
2. `docs/README.md`
3. `docs/current/architecture.md`
4. `docs/current/runtime-truth.md`

只有当你明确需要：

- 查历史方案
- 对照旧设计
- 回看阶段收口
- 做考古 / 审计 / 追溯

再进入 `docs/archive/`。

---

## 2. Archive 二级分类

`docs/archive/` 当前按二级目录分成 9 类：

| 分类 | 路径 | 保存什么 |
| --- | --- | --- |
| Reference | `docs/archive/reference/` | 旧架构长文、旧 API / data model / 接入参考 |
| Planning | `docs/archive/planning/` | 已退出主线的 sprint / phase / breakdown / plan 文档 |
| Analysis | `docs/archive/analysis/` | 早期分析稿、ER 设计、领域诊断、操作分析 |
| History | `docs/archive/history/` | closeout summary、roadmap、gap list、阶段性历史证明 |
| Dev Docs | `docs/archive/dev-docs/` | 探索性开发笔记、登录自动化与局部 closeout 探索材料 |
| Backend Docs | `docs/archive/backend-docs/` | 局部 backend 设计说明与状态文档 |
| Exports | `docs/archive/exports/` | 导出型项目说明、结构映射、历史快照 |
| Examples | `docs/archive/examples/` | 示例型实现说明、历史 task breakdown 示例 |
| Private | `docs/archive/private/` | 私有/内部评审材料的归档副本 |

一句话：

> **reference 看旧事实，planning 看旧计划，analysis 看旧判断，history 看阶段收口；其余目录承接特殊来源的历史材料。**

---

## 3. 从哪里开始找

### 如果你要看旧架构 / 旧接口 / 旧数据模型

先看：

- `docs/archive/reference/README.md`

### 如果你要追溯早期阶段规划

先看：

- `docs/archive/planning/README.md`

### 如果你要理解早期分析过程

先看：

- `docs/archive/analysis/README.md`

### 如果你要看某阶段如何收口

先看：

- `docs/archive/history/README.md`

### 如果你要找特殊来源资料

按来源进入：

- `docs/archive/dev-docs/README.md`
- `docs/archive/backend-docs/README.md`
- `docs/archive/exports/README.md`
- `docs/archive/examples/README.md`
- `docs/archive/private/README.md`

---

## 4. 与 current docs 的边界

读 archive 时，默认要带着下面这个判断：

1. 这份文档是不是**仍然 authoritative**？  
   - 通常不是。
2. 它是不是只提供**历史上下文 / 演进线索 / 旧方案证据**？  
   - 通常是。
3. 如果它和 current docs 冲突，应该信谁？  
   - 先信 `docs/current/*`、`docs/domains/*`、`docs/governance/*` 的当前文档体系。

---

## 5. 当前维护约定

后续如果还有文档需要进入 archive，优先先判断它属于哪一类：

- 旧事实参考 → `reference/`
- 旧计划 → `planning/`
- 旧分析 / 旧设计判断 → `analysis/`
- 阶段收口 / 历史证明 → `history/`
- 特殊来源材料 → 对应专用子目录

不要把新的 historical 文档继续平铺在 `docs/archive/` 根层。

一句话：

> **archive 也要有入口，但它的入口是“怎么考古”，不是“现在该信什么”。**
