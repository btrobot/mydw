# Backup Scope

> Phase 5 / PR3 minimal truthful backup scope

`/api/system/backup` 的目标不是“完整恢复平台”，而是提供**最小但真实**的系统快照能力。

## 当前备份包含

- 数据库快照（当 SQLite 文件存在时）
- 运行时配置快照（`data/system_config.json`）
- 备份元数据清单（manifest）
- 可选：应用日志快照（当 `include_logs=true` 时）

## 当前备份不包含

- 媒体文件
- 完整 restore / import 流程
- 跨机器迁移保证

## 返回值语义

`/api/system/backup` 返回的 `backup_file` 指向 manifest 文件路径。  
manifest 会说明：

- 备份时间
- artifact 所在目录（默认位于 `data/backups/<timestamp>/`）
- 有效系统配置
- 关键数据计数
- 实际包含的 artifact 路径

## 运维说明

- 默认备份目录：`data/backups/`
- manifest 默认文件名：`manifest.json`
- `runtime_config_snapshot` 仅在 `data/system_config.json` 存在时出现
- `database_snapshot` 仅在当前数据库是可复制的 SQLite 文件时出现
- `log_snapshot` 仅在 `include_logs=true` 且日志文件存在时出现
- 当前没有“一键 restore”；恢复时必须人工核对 manifest，再按 artifact 类型逐项处理

## 用户沟通要求

Settings 页面必须明确提示：

- 已经备份了什么
- 没有备份什么
- 当前备份适合“最小真实快照”，不等于完整恢复方案
