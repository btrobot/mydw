"""
Creative Phase A service helpers.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import CreativeItem, CreativeVersion, Task
from schemas import (
    CreativeDetailResponse,
    CreativeWorkbenchItemResponse,
    CreativeWorkbenchListResponse,
)
from services.creative_version_service import CreativeVersionService


class CreativeService:
    """Minimal Creative workbench/detail service for Phase A."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.version_service = CreativeVersionService(db)

    async def list_creatives(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> CreativeWorkbenchListResponse:
        total_result = await self.db.execute(select(func.count()).select_from(CreativeItem))
        total = total_result.scalar() or 0

        result = await self.db.execute(
            select(CreativeItem)
            .order_by(CreativeItem.updated_at.desc(), CreativeItem.id.desc())
            .offset(skip)
            .limit(limit)
        )
        items = [
            CreativeWorkbenchItemResponse(
                id=item.id,
                creative_no=item.creative_no,
                title=item.title,
                status=item.status,
                current_version_id=item.current_version_id,
                updated_at=item.updated_at,
            )
            for item in result.scalars().all()
        ]
        return CreativeWorkbenchListResponse(total=total, items=items)

    async def get_creative_detail(self, creative_id: int) -> Optional[CreativeDetailResponse]:
        creative = await self._load_creative_detail(creative_id)
        if creative is None:
            return None
        return self._build_creative_detail_response(creative)

    async def attach_task_to_creative_sample(
        self,
        task_id: int,
        *,
        creative_no: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Task:
        task = await self.db.get(Task, task_id)
        if task is None:
            raise ValueError(f"Task {task_id} does not exist")

        if task.creative_item_id is not None or task.creative_version_id is not None:
            if task.creative_item_id is None or task.creative_version_id is None:
                raise ValueError("Task creative mapping is partially populated and cannot be auto-fixed in Phase A")
            return task

        creative = CreativeItem(
            creative_no=creative_no or f"CR-{task.id:06d}",
            title=title or task.name or f"Task {task.id}",
            status="PENDING_INPUT",
            latest_version_no=1,
        )
        self.db.add(creative)
        await self.db.flush()

        version = await self.version_service.create_initial_version(
            creative,
            title=creative.title,
        )

        task.creative_item_id = creative.id
        task.creative_version_id = version.id
        if task.task_kind is None:
            task.task_kind = "composition"

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def _load_creative_detail(self, creative_id: int) -> Optional[CreativeItem]:
        result = await self.db.execute(
            select(CreativeItem)
            .where(CreativeItem.id == creative_id)
            .options(
                selectinload(CreativeItem.current_version).selectinload(CreativeVersion.package_records),
                selectinload(CreativeItem.tasks),
            )
        )
        return result.scalars().first()

    def _build_creative_detail_response(self, creative: CreativeItem) -> CreativeDetailResponse:
        linked_task_ids = sorted(task.id for task in creative.tasks)
        current_version = self.version_service.build_current_version_response(creative.current_version)

        return CreativeDetailResponse(
            id=creative.id,
            creative_no=creative.creative_no,
            title=creative.title,
            status=creative.status,
            current_version_id=creative.current_version_id,
            current_version=current_version,
            linked_task_ids=linked_task_ids,
            updated_at=creative.updated_at,
        )
