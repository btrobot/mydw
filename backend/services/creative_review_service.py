"""
Creative review invariants and review-write authority for Phase B.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import CheckRecord, CreativeItem, CreativeVersion
from schemas import CreativeReviewConclusion


@dataclass
class CreativeReviewError(Exception):
    message: str
    status_code: int

    def __str__(self) -> str:
        return self.message


class CreativeReviewService:
    """Owns Creative review invariants and business-status writes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def approve(
        self,
        creative_id: int,
        *,
        version_id: int,
        note: str | None = None,
    ) -> tuple[CreativeItem, CheckRecord]:
        return await self._record_review(
            creative_id,
            version_id=version_id,
            conclusion=CreativeReviewConclusion.APPROVED,
            note=note,
        )

    async def rework(
        self,
        creative_id: int,
        *,
        version_id: int,
        rework_type: str | None,
        note: str | None = None,
    ) -> tuple[CreativeItem, CheckRecord]:
        return await self._record_review(
            creative_id,
            version_id=version_id,
            conclusion=CreativeReviewConclusion.REWORK_REQUIRED,
            rework_type=rework_type,
            note=note,
        )

    async def reject(
        self,
        creative_id: int,
        *,
        version_id: int,
        note: str | None = None,
    ) -> tuple[CreativeItem, CheckRecord]:
        return await self._record_review(
            creative_id,
            version_id=version_id,
            conclusion=CreativeReviewConclusion.REJECTED,
            note=note,
        )

    async def _record_review(
        self,
        creative_id: int,
        *,
        version_id: int,
        conclusion: CreativeReviewConclusion,
        rework_type: str | None = None,
        note: str | None = None,
    ) -> tuple[CreativeItem, CheckRecord]:
        creative = await self._load_creative(creative_id)
        if creative is None:
            raise CreativeReviewError("作品不存在", 404)

        version = next((item for item in creative.versions if item.id == version_id), None)
        if version is None:
            raise CreativeReviewError("版本不存在", 404)

        if creative.current_version_id != version.id:
            raise CreativeReviewError("仅当前版本允许执行 review", 409)

        if conclusion == CreativeReviewConclusion.REWORK_REQUIRED and not rework_type:
            raise CreativeReviewError("REWORK_REQUIRED 必须携带 rework_type", 400)

        check = CheckRecord(
            creative_item=creative,
            creative_version=version,
            conclusion=conclusion.value,
            rework_type=rework_type,
            note=note,
        )
        self.db.add(check)
        creative.status = conclusion.value
        await self.db.flush()
        return creative, check

    async def _load_creative(self, creative_id: int) -> CreativeItem | None:
        result = await self.db.execute(
            select(CreativeItem)
            .where(CreativeItem.id == creative_id)
            .options(
                selectinload(CreativeItem.current_version),
                selectinload(CreativeItem.versions).selectinload(CreativeVersion.check_records),
            )
        )
        return result.scalars().first()
