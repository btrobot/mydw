"""
Creative Phase C publish-pool domain service.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import CreativeItem, CreativeVersion, PublishPoolItem
from schemas import PublishPoolItemResponse, PublishPoolListResponse, PublishPoolStatus


class PublishPoolService:
    """Owns publish-pool invariants before scheduler cutover."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def activate_for_version(
        self,
        creative: CreativeItem,
        version: CreativeVersion,
    ) -> PublishPoolItem:
        if creative.current_version_id != version.id:
            raise ValueError("Only the current Creative version can enter the publish pool")

        await self.invalidate_for_creative(
            creative.id,
            reason="superseded_by_current_version",
            exclude_version_id=version.id,
        )

        pool_item = await self._get_by_version_id(version.id)
        if pool_item is None:
            pool_item = PublishPoolItem(
                creative_item_id=creative.id,
                creative_version_id=version.id,
                status=PublishPoolStatus.ACTIVE.value,
            )
            self.db.add(pool_item)
        else:
            pool_item.creative_item_id = creative.id
            pool_item.status = PublishPoolStatus.ACTIVE.value
            pool_item.invalidation_reason = None
            pool_item.invalidated_at = None
            pool_item.locked_at = None
            pool_item.locked_by_task_id = None

        await self.db.flush()
        logger.info(
            "publish_pool_entered creative_item_id={creative_item_id} creative_version_id={creative_version_id} pool_item_id={pool_item_id}",
            creative_item_id=creative.id,
            creative_version_id=version.id,
            pool_item_id=pool_item.id,
        )
        return pool_item

    async def invalidate_for_creative(
        self,
        creative_id: int,
        *,
        reason: str,
        exclude_version_id: int | None = None,
    ) -> int:
        result = await self.db.execute(
            select(PublishPoolItem).where(
                PublishPoolItem.creative_item_id == creative_id,
                PublishPoolItem.status == PublishPoolStatus.ACTIVE.value,
            )
        )
        pool_items = list(result.scalars().all())
        invalidated = 0
        now = datetime.now(UTC).replace(tzinfo=None)
        for item in pool_items:
            if exclude_version_id is not None and item.creative_version_id == exclude_version_id:
                continue
            item.status = PublishPoolStatus.INVALIDATED.value
            item.invalidation_reason = reason
            item.invalidated_at = now
            item.locked_at = None
            item.locked_by_task_id = None
            invalidated += 1

        if invalidated:
            await self.db.flush()
            for item in pool_items:
                if item.status != PublishPoolStatus.INVALIDATED.value:
                    continue
                logger.info(
                    "publish_pool_removed creative_item_id={creative_item_id} creative_version_id={creative_version_id} pool_item_id={pool_item_id} reason={reason}",
                    creative_item_id=item.creative_item_id,
                    creative_version_id=item.creative_version_id,
                    pool_item_id=item.id,
                    reason=item.invalidation_reason,
                )
        return invalidated

    async def get_pool_item(self, pool_item_id: int) -> Optional[PublishPoolItem]:
        result = await self.db.execute(
            select(PublishPoolItem)
            .where(PublishPoolItem.id == pool_item_id)
            .options(
                selectinload(PublishPoolItem.creative_item),
                selectinload(PublishPoolItem.creative_version),
            )
        )
        return result.scalars().first()

    async def list_active_unlocked_items(self) -> list[PublishPoolItem]:
        result = await self.db.execute(
            select(PublishPoolItem)
            .where(
                PublishPoolItem.status == PublishPoolStatus.ACTIVE.value,
                PublishPoolItem.locked_at.is_(None),
            )
            .options(
                selectinload(PublishPoolItem.creative_item),
                selectinload(PublishPoolItem.creative_version),
            )
            .order_by(PublishPoolItem.created_at.asc(), PublishPoolItem.id.asc())
        )
        return list(result.scalars().all())

    async def lock_active_item(self, pool_item_id: int) -> PublishPoolItem:
        pool_item = await self.get_pool_item(pool_item_id)
        if pool_item is None:
            raise ValueError(f"Publish pool item {pool_item_id} does not exist")
        if pool_item.status != PublishPoolStatus.ACTIVE.value:
            raise ValueError("Only active publish-pool items can be locked")
        if pool_item.creative_item is None or pool_item.creative_item.current_version_id != pool_item.creative_version_id:
            raise ValueError("Only the current Creative version can be planned from the publish pool")
        if pool_item.locked_at is not None:
            raise ValueError("Publish pool item is already locked")

        pool_item.locked_at = datetime.now(UTC).replace(tzinfo=None)
        pool_item.locked_by_task_id = None
        await self.db.flush()
        return pool_item

    async def attach_lock_to_task(self, pool_item_id: int, task_id: int) -> PublishPoolItem:
        pool_item = await self.get_pool_item(pool_item_id)
        if pool_item is None:
            raise ValueError(f"Publish pool item {pool_item_id} does not exist")
        if pool_item.locked_at is None:
            raise ValueError("Publish pool item must be locked before binding a task")

        pool_item.locked_by_task_id = task_id
        await self.db.flush()
        logger.info(
            "publish_pool_locked creative_item_id={creative_item_id} creative_version_id={creative_version_id} pool_item_id={pool_item_id} task_id={task_id}",
            creative_item_id=pool_item.creative_item_id,
            creative_version_id=pool_item.creative_version_id,
            pool_item_id=pool_item.id,
            task_id=task_id,
        )
        return pool_item

    async def release_lock_for_task(self, task_id: int, *, reason: str | None = None) -> int:
        result = await self.db.execute(
            select(PublishPoolItem).where(PublishPoolItem.locked_by_task_id == task_id)
        )
        pool_items = list(result.scalars().all())
        released = 0
        for item in pool_items:
            item.locked_at = None
            item.locked_by_task_id = None
            released += 1

        if released:
            await self.db.flush()
            for item in pool_items:
                logger.info(
                    "publish_pool_unlocked creative_item_id={creative_item_id} creative_version_id={creative_version_id} pool_item_id={pool_item_id} task_id={task_id} reason={reason}",
                    creative_item_id=item.creative_item_id,
                    creative_version_id=item.creative_version_id,
                    pool_item_id=item.id,
                    task_id=task_id,
                    reason=reason or "released",
                )
        return released

    async def invalidate_pool_item(self, pool_item_id: int, *, reason: str) -> PublishPoolItem:
        pool_item = await self.get_pool_item(pool_item_id)
        if pool_item is None:
            raise ValueError(f"Publish pool item {pool_item_id} does not exist")

        pool_item.status = PublishPoolStatus.INVALIDATED.value
        pool_item.invalidation_reason = reason
        pool_item.invalidated_at = datetime.now(UTC).replace(tzinfo=None)
        pool_item.locked_at = None
        pool_item.locked_by_task_id = None
        await self.db.flush()
        logger.info(
            "publish_pool_removed creative_item_id={creative_item_id} creative_version_id={creative_version_id} pool_item_id={pool_item_id} reason={reason}",
            creative_item_id=pool_item.creative_item_id,
            creative_version_id=pool_item.creative_version_id,
            pool_item_id=pool_item.id,
            reason=reason,
        )
        return pool_item

    async def list_pool_items(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        status: PublishPoolStatus | None = PublishPoolStatus.ACTIVE,
        creative_id: int | None = None,
    ) -> PublishPoolListResponse:
        filters = []
        if status is not None:
            filters.append(PublishPoolItem.status == status.value)
        if creative_id is not None:
            filters.append(PublishPoolItem.creative_item_id == creative_id)

        total_query = select(func.count()).select_from(PublishPoolItem)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        query = select(PublishPoolItem).options(
            selectinload(PublishPoolItem.creative_item),
        )
        if filters:
            query = query.where(*filters)
        query = query.order_by(PublishPoolItem.created_at.desc(), PublishPoolItem.id.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        items = [self.build_pool_item_response(item) for item in result.scalars().all()]
        return PublishPoolListResponse(total=total, items=items)

    @staticmethod
    def build_pool_item_response(pool_item: PublishPoolItem) -> PublishPoolItemResponse:
        creative = pool_item.creative_item
        return PublishPoolItemResponse(
            id=pool_item.id,
            creative_item_id=pool_item.creative_item_id,
            creative_version_id=pool_item.creative_version_id,
            status=pool_item.status,
            invalidation_reason=pool_item.invalidation_reason,
            invalidated_at=pool_item.invalidated_at,
            creative_no=creative.creative_no if creative else None,
            creative_title=creative.title if creative else None,
            creative_status=creative.status if creative else None,
            creative_current_version_id=creative.current_version_id if creative else None,
            created_at=pool_item.created_at,
            updated_at=pool_item.updated_at,
        )

    async def _get_by_version_id(self, creative_version_id: int) -> Optional[PublishPoolItem]:
        result = await self.db.execute(
            select(PublishPoolItem).where(PublishPoolItem.creative_version_id == creative_version_id)
        )
        return result.scalars().first()
