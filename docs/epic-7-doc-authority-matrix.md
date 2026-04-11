# Epic 7 文档 Authority Matrix

> 目的：明确当前高可见度文档各自负责什么，避免多个文档同时自称 authoritative。

| 文档 | 角色 | 是否 authoritative | 负责内容 | 备注 |
|---|---|---|---|---|
| `docs/current-architecture-baseline.md` | 架构总入口 / entrypoint | 是 | 当前系统的高层结构、边界、推荐阅读路径 | 面向 onboarding / 快速建模 |
| `docs/current-runtime-truth.md` | 运行事实清单 | 是 | 当前代码已证明的 runtime truth / canonical source 列表 | 不负责完整架构导览 |
| `docs/runtime-truth.md` | 轻量入口 / entrypoint alias | 否 | 指向 `current-runtime-truth.md` 与 baseline | 不应与 canonical 内容竞争 |
| `docs/system-architecture.md` | 旧的全面架构说明 | 否（PR1 后） | 当前仅作 legacy comprehensive reference | PR2 必须决定 rewrite 还是 stale/archival |
| `docs/api-reference.md` | 旧 API 参考 | 否（PR2 后） | 历史性参考；不再承诺逐端点始终同步 | 当前 API truth 以 `/docs` / `/openapi.json` 为准 |
| `docs/data-model.md` | 旧数据模型字典 | 否（PR2 后） | 历史性参考；不再承诺字段/关系始终同步 | 当前模型 truth 以 `backend/models/__init__.py` 为准 |
| `README.md` | 项目入口 | 是（项目入口层面） | 项目简介、快速开始、当前推荐阅读入口 | 不承担完整事实清单职责 |

## 当前规则

1. **找当前系统长什么样** → 先看 `current-architecture-baseline.md`
2. **找当前代码真实行为** → 看 `current-runtime-truth.md`
3. **找历史长文架构说明** → `system-architecture.md` 只作参考，不是默认 truth source
4. `runtime-truth.md` 如果存在，只允许做入口，不允许复制出第二份 competing truth
