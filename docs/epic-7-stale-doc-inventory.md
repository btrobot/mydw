# Epic 7 Stale Doc Inventory

> PR2 checked-in artifact  
> 目的：记录高可见度旧文档在 Epic 7 / PR2 中采取了什么动作。

| Document | Visibility | Action in PR2 | Current authoritative pointer |
|---|---|---|---|
| `README.md` | Highest | updated in place as project entrypoint; removed stale deep detail sections and fixed current reading path | `docs/current-architecture-baseline.md`, `docs/current-runtime-truth.md` |
| `docs/system-architecture.md` | High | marked stale / archival | `docs/current-architecture-baseline.md`, `docs/current-runtime-truth.md` |
| `docs/api-reference.md` | High | marked stale / archival | `/docs`, `/openapi.json`, current baseline docs |
| `docs/data-model.md` | High | marked stale / archival | `backend/models/__init__.py`, current baseline docs |

## Selection rule used in PR2

PR2 focuses on:

1. project entrypoint (`README.md`)
2. old architecture deep-dive (`docs/system-architecture.md`)
3. high-visibility reference docs that can easily be mistaken as current truth:
   - `docs/api-reference.md`
   - `docs/data-model.md`

Other older docs remain candidates for later cleanup, but these are the primary high-signal surfaces most likely to mislead readers first.

## 推荐阅读路径

1. `README.md`
2. `docs/current-architecture-baseline.md`
3. `docs/current-runtime-truth.md`
4. `docs/epic-7-doc-authority-matrix.md`
