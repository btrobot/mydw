"""
Composition-to-Creative writeback orchestration for Phase B PR-B2.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models import CreativeItem, Task
from services.creative_version_service import CreativeVersionService
from utils.time import utc_now_naive


class CreativeGenerationService:
    """Keeps execution callbacks separate from Creative business writeback."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.version_service = CreativeVersionService(db)

    async def record_composition_success(self, task: Task) -> None:
        """Create and activate a reviewable Creative version for a mapped task.

        Legacy tasks without Creative mapping are intentionally no-ops so the
        existing composition execution chain remains backward compatible.
        """
        if task.creative_item_id is None:
            return

        creative = await self.db.get(CreativeItem, task.creative_item_id)
        if creative is None:
            return

        version = await self.version_service.create_next_version(
            creative,
            title=task.name or creative.title,
            version_type="generated",
            package_status="ready",
            status_on_activate="WAITING_REVIEW",
        )
        task.creative_version_id = version.id
        if task.task_kind is None:
            task.task_kind = "composition"
        creative.generation_error_msg = None
        creative.generation_failed_at = None
        creative.updated_at = utc_now_naive()
        await self.db.flush()

    async def record_composition_failure(self, task: Task, error_msg: str) -> None:
        """Record a Creative-side failure hint without changing review truth."""
        if task.creative_item_id is None:
            return

        creative = await self.db.get(CreativeItem, task.creative_item_id)
        if creative is None:
            return

        creative.generation_error_msg = error_msg
        creative.generation_failed_at = utc_now_naive()
        creative.updated_at = utc_now_naive()
        if task.task_kind is None:
            task.task_kind = "composition"
        await self.db.flush()
