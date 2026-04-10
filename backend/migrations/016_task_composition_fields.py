"""
迁移 016 — Task 表增加视频合成相关字段

变更：
  - 新增 source_video_ids (TEXT) — JSON array，原始视频片段列表
  - 新增 composition_template (VARCHAR(64)) — 合成模板名称
  - 新增 composition_params (TEXT) — JSON，合成参数
  - 新增 composition_job_id (INTEGER) — 关联的合成任务 ID
  - 新增 final_video_path (VARCHAR(512)) — 成品视频路径
  - 新增 final_video_duration (INTEGER) — 成品视频时长（秒）
  - 新增 final_video_size (INTEGER) — 成品视频大小（字节）
  - 新增 scheduled_time (DATETIME) — 计划上传时间
  - 新增 retry_count (INTEGER DEFAULT 0) — 重试次数
  - 新增 dewu_video_id (VARCHAR(128)) — 得物平台视频 ID
  - 新增 dewu_video_url (VARCHAR(512)) — 得物视频链接
  - 新增 name (VARCHAR(256)) — 任务名称
  - 新增 description (TEXT) — 任务描述
  - 迁移现有数据：video_id → source_video_ids (JSON array)
  - 迁移现有数据：status 映射（pending→ready, running→uploading, success→uploaded）

设计原则：幂等 — 字段已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 检查字段是否已存在
        columns = (
            await conn.exec_driver_sql(
                "PRAGMA table_info(tasks)"
            )
        ).fetchall()

        existing_columns = {col[1] for col in columns}

        # 新增字段列表
        new_columns = {
            'name': "ALTER TABLE tasks ADD COLUMN name VARCHAR(256)",
            'description': "ALTER TABLE tasks ADD COLUMN description TEXT",
            'source_video_ids': "ALTER TABLE tasks ADD COLUMN source_video_ids TEXT",
            'composition_template': "ALTER TABLE tasks ADD COLUMN composition_template VARCHAR(64)",
            'composition_params': "ALTER TABLE tasks ADD COLUMN composition_params TEXT",
            'composition_job_id': "ALTER TABLE tasks ADD COLUMN composition_job_id INTEGER",
            'final_video_path': "ALTER TABLE tasks ADD COLUMN final_video_path VARCHAR(512)",
            'final_video_duration': "ALTER TABLE tasks ADD COLUMN final_video_duration INTEGER",
            'final_video_size': "ALTER TABLE tasks ADD COLUMN final_video_size INTEGER",
            'scheduled_time': "ALTER TABLE tasks ADD COLUMN scheduled_time DATETIME",
            'retry_count': "ALTER TABLE tasks ADD COLUMN retry_count INTEGER DEFAULT 0",
            'dewu_video_id': "ALTER TABLE tasks ADD COLUMN dewu_video_id VARCHAR(128)",
            'dewu_video_url': "ALTER TABLE tasks ADD COLUMN dewu_video_url VARCHAR(512)",
        }

        # 添加缺失的字段
        added_count = 0
        for col_name, sql in new_columns.items():
            if col_name not in existing_columns:
                await conn.exec_driver_sql(sql)
                logger.info(f"迁移 016: 添加字段 tasks.{col_name}")
                added_count += 1

        if added_count == 0:
            logger.debug("迁移 016: 所有字段已存在，跳过添加")

        # 数据迁移：video_id → source_video_ids
        if 'source_video_ids' in new_columns and 'source_video_ids' not in existing_columns:
            # 将现有的 video_id 转换为 JSON 数组
            await conn.exec_driver_sql("""
                UPDATE tasks
                SET source_video_ids = json_array(video_id)
                WHERE video_id IS NOT NULL AND (source_video_ids IS NULL OR source_video_ids = '')
            """)
            logger.info("迁移 016: 数据迁移 video_id → source_video_ids 完成")

        # 数据迁移：status 映射
        # 旧状态: pending/running/success/failed/paused
        # 新状态: draft/composing/ready/uploading/uploaded/failed/cancelled
        status_mapping = {
            'pending': 'ready',      # 待发布 → 待上传（假设已有视频）
            'running': 'uploading',  # 发布中 → 上传中
            'success': 'uploaded',   # 已发布 → 已上传
            'failed': 'failed',      # 失败 → 失败
            'paused': 'draft',       # 已暂停 → 草稿
        }

        for old_status, new_status in status_mapping.items():
            result = await conn.exec_driver_sql(
                f"UPDATE tasks SET status = '{new_status}' WHERE status = '{old_status}'"
            )
            if result.rowcount > 0:
                logger.info(f"迁移 016: 状态迁移 {old_status} → {new_status} ({result.rowcount} 条)")

        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_time ON tasks (scheduled_time)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_composition_job_id ON tasks (composition_job_id)",
        ]

        for idx_sql in indexes:
            await conn.exec_driver_sql(idx_sql)

        logger.info("迁移 016: 索引创建完成")

    logger.info("迁移 016 完成")
