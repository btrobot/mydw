"""
任务服务
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_, update
from sqlalchemy.orm import selectinload
from loguru import logger

from core.auth_dependencies import (
    require_active_service_session,
    require_grace_readonly_service_session,
)
from models import (
    CompositionJob,
    PublishExecutionSnapshot,
    PublishLog,
    PublishPoolItem,
    PublishProfile,
    Task,
    TaskAudio,
    TaskCopywriting,
    TaskCover,
    TaskTopic,
    TaskVideo,
)
from schemas.auth import LocalAuthSessionSummary
from utils.time import utc_day_start_naive, utc_now_naive


# 合法状态转换表
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "draft":      ["composing", "ready", "cancelled"],
    "composing":  ["ready", "failed", "cancelled"],
    "ready":      ["uploading", "cancelled"],
    "uploading":  ["uploaded", "failed", "cancelled"],
    "uploaded":   [],
    "failed":     ["composing", "ready", "draft", "cancelled"],
    "cancelled":  [],
}

# 终态集合（不可再转换）
TERMINAL_STATUSES = {"uploaded", "cancelled"}


class TaskDeleteConflictError(RuntimeError):
    """Raised when a task cannot be safely deleted because live references still depend on it."""


def validate_transition(current: str, target: str) -> bool:
    """校验状态转换是否合法"""
    return target in VALID_TRANSITIONS.get(current, [])


class TaskService:
    """任务服务"""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None):
        self.db = db
        self._auth_summary = auth_summary

    async def _require_active(self) -> LocalAuthSessionSummary:
        return await require_active_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )

    async def _require_grace_readonly(self) -> LocalAuthSessionSummary:
        return await require_grace_readonly_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )

    async def resolve_profile(self, task: Task) -> Optional[PublishProfile]:
        """
        解析任务关联的 PublishProfile。
        优先使用 task.profile_id，无则查 is_default=True 的档案。
        """
        await self._require_grace_readonly()
        if task.profile_id:
            result = await self.db.execute(
                select(PublishProfile).where(PublishProfile.id == task.profile_id)
            )
            profile = result.scalars().first()
            if profile:
                return profile
            logger.warning("任务 {} 关联的 profile_id={} 不存在，回退到默认档案", task.id, task.profile_id)

        result = await self.db.execute(
            select(PublishProfile).where(PublishProfile.is_default.is_(True)).limit(1)
        )
        return result.scalars().first()

    async def create_task(self, task_data: dict) -> Task:
        """创建单个任务"""
        await self._require_active()
        task = Task(**task_data)
        self.db.add(task)
        await self.db.commit()
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.topics),
                selectinload(Task.videos),
                selectinload(Task.copywritings),
                selectinload(Task.covers),
                selectinload(Task.audios),
                selectinload(Task.account),
            ).where(Task.id == task.id)
        )
        task = result.scalars().first()
        logger.info("创建任务: ID={}", task.id)
        return task

    async def create_tasks_batch(self, tasks_data: List[dict]) -> Tuple[int, List[Task]]:
        """批量创建任务"""
        await self._require_active()
        tasks = [Task(**data) for data in tasks_data]
        self.db.add_all(tasks)
        await self.db.commit()

        # 重新查询以预加载关系，避免 lazy loading MissingGreenlet
        task_ids = [task.id for task in tasks]
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.topics),
                selectinload(Task.videos),
                selectinload(Task.copywritings),
                selectinload(Task.covers),
                selectinload(Task.audios),
                selectinload(Task.account),
            ).where(Task.id.in_(task_ids))
        )
        loaded_tasks = result.scalars().all()

        logger.info("批量创建任务: {} 个", len(loaded_tasks))
        return len(loaded_tasks), list(loaded_tasks)

    async def clone_as_publish_task(
        self,
        source_task: Task,
        *,
        creative_item_id: int,
        creative_version_id: int,
        profile_id: int | None,
        batch_id: str | None = None,
    ) -> Task:
        """Clone a source task into a publish-task shell while preserving collection truth."""
        await self._require_active()
        hydrated_source = await self._load_task_with_resources(source_task.id)

        cloned_task = Task(
            account_id=hydrated_source.account_id,
            status="ready",
            priority=hydrated_source.priority,
            name=hydrated_source.name,
            composition_template=hydrated_source.composition_template,
            composition_params=hydrated_source.composition_params,
            final_video_path=hydrated_source.final_video_path,
            final_video_duration=hydrated_source.final_video_duration,
            final_video_size=hydrated_source.final_video_size,
            scheduled_time=hydrated_source.scheduled_time,
            profile_id=profile_id,
            batch_id=batch_id,
            creative_item_id=creative_item_id,
            creative_version_id=creative_version_id,
            task_kind="publish",
        )
        self.db.add(cloned_task)
        await self.db.flush()

        for order, video in enumerate(hydrated_source.videos or []):
            self.db.add(TaskVideo(task_id=cloned_task.id, video_id=video.id, sort_order=order))
        for order, copywriting in enumerate(hydrated_source.copywritings or []):
            self.db.add(TaskCopywriting(task_id=cloned_task.id, copywriting_id=copywriting.id, sort_order=order))
        for order, cover in enumerate(hydrated_source.covers or []):
            self.db.add(TaskCover(task_id=cloned_task.id, cover_id=cover.id, sort_order=order))
        for order, audio in enumerate(hydrated_source.audios or []):
            self.db.add(TaskAudio(task_id=cloned_task.id, audio_id=audio.id, sort_order=order))
        for topic in hydrated_source.topics or []:
            self.db.add(TaskTopic(task_id=cloned_task.id, topic_id=topic.id))

        await self.db.flush()
        logger.info(
            "created publish task: source_task_id={}, task_id={}, creative_item_id={}, creative_version_id={}",
            hydrated_source.id,
            cloned_task.id,
            creative_item_id,
            creative_version_id,
        )
        return await self._load_task_with_resources(cloned_task.id)

    async def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        await self._require_grace_readonly()
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def _load_task_with_resources(self, task_id: int) -> Task:
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.topics),
                selectinload(Task.videos),
                selectinload(Task.copywritings),
                selectinload(Task.covers),
                selectinload(Task.audios),
                selectinload(Task.account),
                selectinload(Task.profile),
            ).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise ValueError(f"Task {task_id} does not exist")
        return task

    async def get_tasks(
        self,
        status: Optional[str] = None,
        account_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[int, List[Task]]:
        """获取任务列表"""
        await self._require_grace_readonly()
        query = select(Task)

        if status:
            query = query.where(Task.status == status)
        if account_id:
            query = query.where(Task.account_id == account_id)

        # 获取总数
        count_query = select(func.count(Task.id))
        if status:
            count_query = count_query.where(Task.status == status)
        if account_id:
            count_query = count_query.where(Task.account_id == account_id)

        total = await self.db.execute(count_query)
        total_count = total.scalar()

        # 分页查询
        query = query.order_by(Task.priority.desc(), Task.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return total_count, list(tasks)

    async def update_task(self, task_id: int, update_data: dict) -> Optional[Task]:
        """更新任务"""
        await self._require_active()
        task = await self.get_task(task_id)
        if not task:
            return None

        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)

        task.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        await self._require_active()
        task = await self.get_task(task_id)
        if not task:
            return False

        await self._ensure_task_deletable(task.id)
        await self._delete_task_relations(task.id)
        await self.db.delete(task)
        await self.db.commit()
        return True

    async def delete_all_tasks(self, status: Optional[str] = None) -> int:
        """删除所有任务"""
        await self._require_active()
        query = select(Task)
        if status:
            query = query.where(Task.status == status)

        result = await self.db.execute(query)
        tasks = result.scalars().all()
        count = len(tasks)

        for task in tasks:
            await self._ensure_task_deletable(task.id)

        for task in tasks:
            await self._delete_task_relations(task.id)
            await self.db.delete(task)

        await self.db.commit()
        logger.info("删除任务: {} 个", count)
        return count

    async def _ensure_task_deletable(self, task_id: int) -> None:
        blocking_snapshot = (
            await self.db.execute(
                select(PublishExecutionSnapshot.id).where(
                    PublishExecutionSnapshot.source_task_id == task_id,
                    or_(
                        PublishExecutionSnapshot.task_id.is_(None),
                        PublishExecutionSnapshot.task_id != task_id,
                    ),
                )
            )
        ).scalars().first()

        if blocking_snapshot is not None:
            raise TaskDeleteConflictError(
                "该任务已被发布规划引用，请先删除对应的发布任务或取消发布规划后再删除。",
            )

    async def _delete_task_relations(self, task_id: int) -> None:
        """Delete task-owned association rows before deleting the task row."""
        await self.db.execute(
            update(PublishPoolItem)
            .where(PublishPoolItem.locked_by_task_id == task_id)
            .values(locked_at=None, locked_by_task_id=None)
        )

        await self.db.execute(
            delete(PublishExecutionSnapshot).where(PublishExecutionSnapshot.task_id == task_id)
        )

        for model in (
            TaskVideo,
            TaskCopywriting,
            TaskCover,
            TaskAudio,
            TaskTopic,
            PublishLog,
            CompositionJob,
        ):
            await self.db.execute(delete(model).where(model.task_id == task_id))

    async def get_next_ready_task(self, account_id: Optional[int] = None) -> Optional[Task]:
        """获取下一个待上传任务（ready 状态）"""
        query = select(Task).where(Task.status == "ready")

        if account_id:
            query = query.where(Task.account_id == account_id)

        query = query.order_by(Task.priority.desc(), Task.created_at)
        query = query.limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def mark_task_uploading(self, task_id: int) -> Optional[Task]:
        """标记任务为上传中"""
        return await self.update_task(task_id, {"status": "uploading"})

    async def mark_task_uploaded(self, task_id: int) -> Optional[Task]:
        """标记任务为已上传"""
        task = await self.update_task(task_id, {
            "status": "uploaded",
            "publish_time": utc_now_naive(),
            "error_msg": None,
        })

        if task:
            if task.account_id is not None:
                log = PublishLog(
                    task_id=task.id,
                    account_id=task.account_id,
                    status="uploaded",
                    message="发布成功",
                )
                self.db.add(log)
                await self.db.commit()

        return task

    async def mark_task_failed(self, task_id: int, error_msg: str) -> Optional[Task]:
        """标记任务为失败，记录失败时所处状态"""
        task = await self.get_task(task_id)
        if not task:
            return None

        failed_at_status = task.status
        task = await self.update_task(task_id, {
            "status": "failed",
            "error_msg": error_msg,
            "failed_at_status": failed_at_status,
        })

        if task:
            if task.account_id is not None:
                log = PublishLog(
                    task_id=task.id,
                    account_id=task.account_id,
                    status="failed",
                    message=error_msg,
                )
                self.db.add(log)
                await self.db.commit()

        return task

    async def cancel_task(self, task_id: int) -> Optional[Task]:
        """取消任务：非终态 → cancelled"""
        task = await self.get_task(task_id)
        if not task:
            return None

        if task.status in TERMINAL_STATUSES:
            logger.warning("任务 {} 已处于终态 {}，无法取消", task_id, task.status)
            return None

        task = await self.update_task(task_id, {"status": "cancelled"})
        logger.info("任务 {} 已取消，原状态={}", task_id, task.status if task else "unknown")
        return task

    async def get_task_stats(self) -> dict:
        """获取任务统计（7 状态）"""
        await self._require_grace_readonly()
        stats: dict = {}

        for status in ["draft", "composing", "ready", "uploading", "uploaded", "failed", "cancelled"]:
            result = await self.db.execute(
                select(func.count(Task.id)).where(Task.status == status)
            )
            stats[status] = result.scalar() or 0

        result = await self.db.execute(select(func.count(Task.id)))
        stats["total"] = result.scalar() or 0

        today_start = utc_day_start_naive()
        result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.status == "uploaded",
                Task.publish_time >= today_start,
            )
        )
        stats["today_uploaded"] = result.scalar() or 0

        return stats

    async def quick_retry(self, task_id: int) -> Optional[Task]:
        """快速重试：failed → failed_at_status 对应状态，retry_count += 1，清空 failed_at_status 和 error_msg"""
        await self._require_active()
        task = await self.get_task(task_id)
        if not task:
            return None

        if task.status != "failed":
            raise ValueError(f"任务当前状态为 {task.status}，不是 failed，无法快速重试")

        if not task.failed_at_status:
            raise ValueError("任务缺少 failed_at_status，无法快速重试")

        profile = await self.resolve_profile(task)
        max_retry = profile.max_retry_count if profile else 3
        if task.retry_count >= max_retry:
            raise ValueError(f"已达最大重试次数 {max_retry}，无法继续重试")

        target_status = task.failed_at_status
        task = await self.update_task(task_id, {
            "status": target_status,
            "retry_count": task.retry_count + 1,
            "failed_at_status": None,
            "error_msg": None,
        })
        logger.info("任务 {} 快速重试: 恢复至 {}，retry_count={}", task_id, target_status, task.retry_count if task else "?")
        return task

    async def edit_retry(self, task_id: int) -> Optional[Task]:
        """编辑重试：failed → draft，清空 failed_at_status 和 error_msg"""
        await self._require_active()
        task = await self.get_task(task_id)
        if not task:
            return None

        if task.status != "failed":
            raise ValueError(f"任务当前状态为 {task.status}，不是 failed，无法编辑重试")

        task = await self.update_task(task_id, {
            "status": "draft",
            "failed_at_status": None,
            "error_msg": None,
        })
        logger.info("任务 {} 编辑重试: 已重置为 draft", task_id)
        return task

    async def check_account_daily_limit(self, account_id: Optional[int], limit: int = 5) -> bool:
        """检查账号当日发布数是否达到上限"""
        if account_id is None:
            return False

        today_start = utc_day_start_naive()

        result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.account_id == account_id,
                Task.status == "uploaded",
                Task.publish_time >= today_start,
            )
        )
        count = result.scalar() or 0

        return count >= limit
