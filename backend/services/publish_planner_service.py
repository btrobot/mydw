"""
Creative Phase C publish planner bridge.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth_dependencies import require_active_service_session
from models import CreativeVersion, PublishExecutionSnapshot, PublishPoolItem, Task
from schemas.auth import LocalAuthSessionSummary
from services.publish_pool_service import PublishPoolService
from services.task_execution_semantics import resolve_publish_execution_view
from services.task_service import TaskService


@dataclass(frozen=True)
class PublishPlanningResult:
    pool_item_id: int
    snapshot_id: int
    task_id: int
    source_task_id: int


@dataclass(frozen=True)
class PublishPoolPreview:
    pool_item_id: int
    creative_item_id: int
    creative_version_id: int
    source_task_id: int
    account_id: int
    profile_id: int | None
    source_task_priority: int
    source_task_created_at: datetime
    source_task_kind: str | None


class PublishPlannerService:
    """Freezes publish truth from a pool candidate without cutting over scheduler selection."""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None) -> None:
        self.db = db
        self._auth_summary = auth_summary

    async def plan_publish_task(
        self,
        pool_item_id: int,
        *,
        source_task_id: int | None = None,
    ) -> PublishPlanningResult:
        await require_active_service_session(self.db, auth_summary=self._auth_summary)
        pool_service = PublishPoolService(self.db)
        task_service = TaskService(self.db, auth_summary=self._auth_summary)
        pool_item = await pool_service.lock_active_item(pool_item_id)

        try:
            source_task = await self._resolve_source_task(pool_item, source_task_id=source_task_id)
            resolved_profile = await task_service.resolve_profile(source_task)
            snapshot = PublishExecutionSnapshot(
                pool_item_id=pool_item.id,
                source_task_id=source_task.id,
                creative_item_id=pool_item.creative_item_id,
                creative_version_id=pool_item.creative_version_id,
                account_id=source_task.account_id,
                profile_id=resolved_profile.id if resolved_profile is not None else None,
                snapshot_json=json.dumps(
                    await self._build_snapshot_payload(
                        pool_item,
                        source_task,
                        profile=resolved_profile,
                    ),
                    ensure_ascii=False,
                ),
            )
            self.db.add(snapshot)
            await self.db.flush()

            publish_task = await task_service.clone_as_publish_task(
                source_task,
                creative_item_id=pool_item.creative_item_id,
                creative_version_id=pool_item.creative_version_id,
                profile_id=resolved_profile.id if resolved_profile is not None else None,
                batch_id=f"publish-pool:{pool_item.id}",
            )
            snapshot.task_id = publish_task.id
            await pool_service.attach_lock_to_task(pool_item.id, publish_task.id)
            await self.db.commit()

            return PublishPlanningResult(
                pool_item_id=pool_item.id,
                snapshot_id=snapshot.id,
                task_id=publish_task.id,
                source_task_id=source_task.id,
            )
        except Exception:
            await self.db.rollback()
            raise

    async def get_snapshot_for_task(self, task_id: int) -> PublishExecutionSnapshot | None:
        result = await self.db.execute(
            select(PublishExecutionSnapshot).where(PublishExecutionSnapshot.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def release_pool_lock_for_task(self, task_id: int, *, reason: str | None = None) -> int:
        released = await PublishPoolService(self.db).release_lock_for_task(task_id, reason=reason)
        if released:
            await self.db.commit()
        return released

    async def mark_publish_succeeded(self, task_id: int) -> bool:
        snapshot = await self.get_snapshot_for_task(task_id)
        if snapshot is None:
            return False

        await PublishPoolService(self.db).invalidate_pool_item(
            snapshot.pool_item_id,
            reason="published_successfully",
        )
        await self.db.commit()
        return True

    async def preview_next_pool_candidate(
        self,
        *,
        max_per_account_per_day: int | None = None,
    ) -> PublishPoolPreview | None:
        pool_items = await PublishPoolService(self.db).list_active_unlocked_items()
        task_service = TaskService(self.db, auth_summary=self._auth_summary)
        candidates: list[PublishPoolPreview] = []

        for pool_item in pool_items:
            try:
                source_task = await self._resolve_source_task(pool_item, source_task_id=None)
                profile = await task_service.resolve_profile(source_task)
            except ValueError:
                continue

            preview = PublishPoolPreview(
                pool_item_id=pool_item.id,
                creative_item_id=pool_item.creative_item_id,
                creative_version_id=pool_item.creative_version_id,
                source_task_id=source_task.id,
                account_id=source_task.account_id,
                profile_id=profile.id if profile is not None else None,
                source_task_priority=source_task.priority or 0,
                source_task_created_at=source_task.created_at,
                source_task_kind=source_task.task_kind,
            )
            candidates.append(preview)

        candidates.sort(
            key=lambda item: (
                -item.source_task_priority,
                item.source_task_created_at,
                item.pool_item_id,
            )
        )

        if max_per_account_per_day is None:
            return candidates[0] if candidates else None

        for candidate in candidates:
            if await task_service.check_account_daily_limit(candidate.account_id, max_per_account_per_day):
                continue
            return candidate
        return None

    async def _resolve_source_task(
        self,
        pool_item: PublishPoolItem,
        *,
        source_task_id: int | None,
    ) -> Task:
        if source_task_id is not None:
            task = await self._load_task_with_resources(source_task_id)
            self._validate_source_task(task, pool_item)
            return task

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.videos),
                selectinload(Task.copywritings),
                selectinload(Task.covers),
                selectinload(Task.audios),
                selectinload(Task.topics),
                selectinload(Task.account),
                selectinload(Task.profile),
            )
            .where(
                Task.creative_item_id == pool_item.creative_item_id,
                Task.creative_version_id == pool_item.creative_version_id,
            )
            .order_by(Task.id.desc())
        )
        candidates = list(result.scalars().all())
        if not candidates:
            raise ValueError("No source task is linked to the publish-pool item")

        valid_candidates: list[Task] = []
        for task in candidates:
            try:
                self._validate_source_task(task, pool_item)
            except ValueError:
                continue
            valid_candidates.append(task)

        if not valid_candidates:
            raise ValueError("No publishable source task is linked to the publish-pool item")

        preferred = next((task for task in valid_candidates if task.task_kind != "publish"), valid_candidates[0])
        return preferred

    @staticmethod
    def _validate_source_task(task: Task, pool_item: PublishPoolItem) -> None:
        if task.creative_item_id != pool_item.creative_item_id or task.creative_version_id != pool_item.creative_version_id:
            raise ValueError("Source task does not match the publish-pool candidate")
        resolve_publish_execution_view(task)

    async def _build_snapshot_payload(
        self,
        pool_item: PublishPoolItem,
        source_task: Task,
        *,
        profile,
    ) -> dict:
        version = await self._load_creative_version(pool_item.creative_version_id)
        package_record = version.package_records[0] if version.package_records else None
        creative = pool_item.creative_item
        execution_view = resolve_publish_execution_view(source_task)

        return {
            "pool_item": {
                "id": pool_item.id,
                "creative_item_id": pool_item.creative_item_id,
                "creative_version_id": pool_item.creative_version_id,
                "status": pool_item.status,
            },
            "creative_item": {
                "id": creative.id if creative is not None else pool_item.creative_item_id,
                "creative_no": creative.creative_no if creative is not None else None,
                "title": creative.title if creative is not None else None,
                "status": creative.status if creative is not None else None,
                "current_version_id": creative.current_version_id if creative is not None else None,
            },
            "creative_version": {
                "id": version.id,
                "version_no": version.version_no,
                "title": version.title,
                "parent_version_id": version.parent_version_id,
                "package_record_id": package_record.id if package_record is not None else None,
                "package_status": package_record.package_status if package_record is not None else None,
            },
            "account": {
                "id": source_task.account.id if source_task.account is not None else source_task.account_id,
                "account_id": source_task.account.account_id if source_task.account is not None else None,
                "account_name": source_task.account.account_name if source_task.account is not None else None,
                "status": source_task.account.status if source_task.account is not None else None,
            },
            "profile": (
                {
                    "id": profile.id,
                    "name": profile.name,
                    "composition_mode": profile.composition_mode,
                    "is_default": profile.is_default,
                }
                if profile is not None
                else None
            ),
            "source_task": {
                "id": source_task.id,
                "status": source_task.status,
                "task_kind": source_task.task_kind,
                "profile_id": source_task.profile_id,
                "name": source_task.name,
                "final_video_path": source_task.final_video_path,
                "video_ids": [video.id for video in source_task.videos or []],
                "copywriting_ids": [copywriting.id for copywriting in source_task.copywritings or []],
                "cover_ids": [cover.id for cover in source_task.covers or []],
                "audio_ids": [audio.id for audio in source_task.audios or []],
                "topic_ids": [topic.id for topic in source_task.topics or []],
            },
            "execution_view": {
                "video_path": execution_view.video_path,
                "content": execution_view.content,
                "cover_path": execution_view.cover_path,
                "topic": execution_view.topic,
            },
        }

    async def _load_task_with_resources(self, task_id: int) -> Task:
        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.videos),
                selectinload(Task.copywritings),
                selectinload(Task.covers),
                selectinload(Task.audios),
                selectinload(Task.topics),
                selectinload(Task.account),
                selectinload(Task.profile),
            )
            .where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise ValueError(f"Task {task_id} does not exist")
        return task

    async def _load_creative_version(self, creative_version_id: int) -> CreativeVersion:
        result = await self.db.execute(
            select(CreativeVersion)
            .options(selectinload(CreativeVersion.package_records))
            .where(CreativeVersion.id == creative_version_id)
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise ValueError(f"CreativeVersion {creative_version_id} does not exist")
        return version
