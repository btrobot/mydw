# Settings / System Capability Truth Matrix

> Phase 5 baseline, updated after PR4 cleanup  
> 目的：冻结系统设置相关能力的真相分类，并记录当前 repo 中 frontend / backend / docs 的一致答案。

## 分类说明

- **startup-env**：启动时由环境变量 / `backend/core/config.py` 决定，不在运行期写回
- **runtime-config**：本阶段批准进入真实运行期配置源的候选项
- **read-only**：只读信息/统计，不提供保存语义
- **remove**：当前不应继续暴露为“可配置项”
- **placeholder-capability**：功能入口存在，但当前能力并不真实完整；后续 PR 要么做真，要么降级

## Per-setting / capability matrix

| Capability / Field | Current surface | Current truth | Phase 5 classification | Notes |
|---|---|---|---|---|
| `material_base_path` | `GET/PUT /api/system/config`, `Settings` 页显示 | 已接入 file-backed runtime-config，真实持久化到 `data/system_config.json` | `runtime-config` | 当前唯一支持运行时修改的设置项 |
| `auto_backup` | `GET /api/system/config` 返回兼容字段；旧调用方仍可向 `PUT` 传参 | 兼容占位字段；返回值固定为 `false`，传入写请求会显式 400 | `remove` | 不在 UI 暴露为可编辑项，不允许伪装保存成功 |
| `log_level` | `GET /api/system/config`, Settings 只读信息 | 权威来源是 `backend/core/config.py` / `.env`，运行期仅只读展示 | `startup-env` | 如需修改，必须改启动期配置并重启 |
| 数据备份 | `POST /api/system/backup`, `Settings` 按钮 | 已生成最小真实备份：manifest + 可用 artifact 快照 | `runtime-capability` | 范围见 `docs/domains/system/backup-scope.md`；不是完整 restore 平台 |
| 素材统计 | `GET /api/system/material-stats`, MaterialOverview | 实时统计 DB 数据 | `read-only` | 已是只读能力，不应伪装成设置 |
| 系统日志 | `/api/system/logs` | DB / runtime log source | `read-only` | 可查看，不属于设置 |

## PR2 批准的 runtime-config 范围

仅批准以下项进入 Phase 5 / PR2 的真实 runtime config：

- `material_base_path`

其余项处理策略：

- `auto_backup` → 移除或显式标注未开放
- `log_level` → 明确保留为 `startup-env`

## PR2 precedence / fallback 规则

对于当前唯一被批准的 runtime-config 项：

- `material_base_path`
  - **优先级**：runtime config store > `backend/core/config.py` 的 `MATERIAL_BASE_PATH`
  - **fallback**：若 runtime store 中不存在该值，则回退到 startup-env

对于当前未批准为 runtime-config 的项：

- `log_level`
  - authoritative truth 仍是 startup-env（`backend/core/config.py` / `.env`）
- `auto_backup`
  - 当前不应作为运行时设置对外承诺

## 当前最小真实 backup 范围

`/api/system/backup` 当前明确：

- 会生成 manifest（`data/backups/<timestamp>/manifest.json`）
- 如 SQLite 数据库文件存在，会复制数据库快照
- 如 runtime config 文件存在，会复制 `data/system_config.json`
- 当 `include_logs=true` 且日志文件存在时，会复制应用日志
- 不包含媒体文件、完整 restore/import 流程、跨机器迁移保证

用户必须能从 UI/文档理解：

- “已经备份了什么”
- “还没有备份什么”
- `backup_file` 指向的是 manifest，而不是某个“万能恢复包”

## PR4 对齐要求

Phase 5 完成后当前答案是：

- frontend Settings 页面只展示真实能力 / 只读信息
- backend 不再对 unsupported setting 静默成功
- docs / backend / frontend 三处对 setting truth 一致
- 兼容遗留字段时，必须明确标注为只读/未开放，而不是继续伪装成可编辑能力
