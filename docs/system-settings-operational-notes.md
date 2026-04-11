# System Settings Operational Notes

> Phase 5 / PR4 收尾文档  
> 目标：给开发/运维一个单页说明，回答“哪些设置能改、改到哪里、何时生效、哪些还不支持”。

## 1. Truth boundary

系统设置分为两类：

- **startup-env**：启动期读取，权威来源是 `.env` / `backend/core/config.py`
- **runtime-config**：运行期真实可写，权威来源是 `data/system_config.json`

当前唯一批准进入 `runtime-config` 的字段只有：

- `material_base_path`

## 2. Per-field operational truth

| Field | Classification | Authoritative source | Operator action |
|---|---|---|---|
| `material_base_path` | `runtime-config` | `data/system_config.json`（缺失时回退到 startup-env） | 在 Settings 页保存，或直接维护该 JSON 文件 |
| `log_level` | `startup-env` | `.env` / `backend/core/config.py` | 修改启动期配置后重启 |
| `auto_backup` | `remove` / unsupported | 无真实 runtime source；兼容字段仅用于明确拒绝旧写请求 | 不要在 UI 或脚本中把它当作可编辑设置 |

## 3. Unsupported settings policy

- 未进入 truth matrix 的字段，不得在 UI 中伪装成“可保存设置”
- 旧调用方如果继续向 `PUT /api/system/config` 传入 `auto_backup` 或 `log_level`，后端会返回 400
- policy 要点：**明确失败，不能静默成功**

## 4. Runtime config file

- 路径：`data/system_config.json`
- 当前允许的 key：
  - `material_base_path`
- 生效规则：
  - 若文件存在且含值，则优先于 startup-env
  - 若文件不存在或字段缺失，则回退到 `backend/core/config.py`

## 5. Backup scope

- API：`POST /api/system/backup`
- 默认产物根目录：`data/backups/`
- 返回值 `backup_file` 指向：`data/backups/<timestamp>/manifest.json`

当前 manifest 可能列出：

- `database_snapshot`
- `runtime_config_snapshot`
- `log_snapshot`（仅 `include_logs=true` 且日志存在时）

当前明确不包含：

- 媒体文件
- 完整 restore/import 工作流
- 跨机器迁移保证

## 6. Frontend alignment contract

Settings 页面当前必须保持以下表达：

- 只暴露 `material_base_path` 为可编辑项
- 将 `log_level` 展示为只读启动期信息
- 明确 `auto_backup` 当前不支持运行时修改
- 明确 backup 是“最小真实备份产物”，并说明 manifest / `data/backups`

## 7. Change checklist

如果未来要扩展系统设置，先回答：

1. 新字段属于 `startup-env`、`runtime-config`、`read-only` 还是 `remove`？
2. 它的 authoritative source 是什么？
3. UI、API、docs 是否会同时更新？
4. 如果旧字段被废弃，是否提供“明确拒绝”而不是“假成功”？
