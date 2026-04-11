"""
Task legacy compatibility helpers.

Phase 6 / PR2:
- centralize residual reads of legacy Task FK columns
- keep compat behavior explicit while new runtime paths prefer relation tables
"""
from __future__ import annotations

from typing import Optional

from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Task, TaskCopywriting, TaskVideo, Video


async def resolve_primary_task_video(db: AsyncSession, task: Task) -> Optional[Video]:
    """
    Resolve a task's primary source video during the compatibility window.

    Preference order:
    1. ordered `task_videos` relation rows (authoritative source)
    2. legacy `tasks.video_id` fallback
    """
    relation_stmt = (
        select(Video)
        .join(TaskVideo, TaskVideo.video_id == Video.id)
        .where(TaskVideo.task_id == task.id)
        .order_by(TaskVideo.sort_order.asc(), TaskVideo.id.asc())
        .limit(1)
    )
    relation_video = (await db.execute(relation_stmt)).scalars().first()
    if relation_video:
        return relation_video

    if task.video_id:
        logger.debug("任务 {} 回退到 legacy tasks.video_id={}", task.id, task.video_id)
        legacy_stmt = select(Video).where(Video.id == task.video_id)
        return (await db.execute(legacy_stmt)).scalars().first()

    return None


async def count_tasks_referencing_video(db: AsyncSession, video_id: int) -> int:
    """Count distinct tasks referencing a video via relation tables or legacy fallback columns."""
    stmt = (
        select(func.count(func.distinct(Task.id)))
        .select_from(Task)
        .outerjoin(TaskVideo, TaskVideo.task_id == Task.id)
        .where(or_(Task.video_id == video_id, TaskVideo.video_id == video_id))
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def count_tasks_referencing_copywriting(db: AsyncSession, copywriting_id: int) -> int:
    """Count distinct tasks referencing a copywriting via relation tables or legacy fallback columns."""
    stmt = (
        select(func.count(func.distinct(Task.id)))
        .select_from(Task)
        .outerjoin(TaskCopywriting, TaskCopywriting.task_id == Task.id)
        .where(
            or_(
                Task.copywriting_id == copywriting_id,
                TaskCopywriting.copywriting_id == copywriting_id,
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0
