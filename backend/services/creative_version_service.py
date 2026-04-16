"""
Creative version helpers for Phase A.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models import CreativeItem, CreativeVersion, PackageRecord
from schemas import CreativeCurrentVersionResponse


class CreativeVersionService:
    """Phase A helpers for creating and projecting Creative versions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_initial_version(
        self,
        creative_item: CreativeItem,
        *,
        title: Optional[str] = None,
        version_type: str = "generated",
        package_status: str = "pending",
    ) -> CreativeVersion:
        version = CreativeVersion(
            creative_item_id=creative_item.id,
            version_no=1,
            version_type=version_type,
            title=title,
        )
        self.db.add(version)
        await self.db.flush()

        package_record = PackageRecord(
            creative_version_id=version.id,
            package_status=package_status,
        )
        self.db.add(package_record)
        await self.db.flush()

        creative_item.current_version_id = version.id
        creative_item.latest_version_no = version.version_no
        return version

    @staticmethod
    def build_current_version_response(
        version: Optional[CreativeVersion],
    ) -> Optional[CreativeCurrentVersionResponse]:
        if version is None:
            return None

        package_record_id = None
        if version.package_records:
            package_record_id = version.package_records[0].id

        return CreativeCurrentVersionResponse(
            id=version.id,
            version_no=version.version_no,
            title=version.title,
            package_record_id=package_record_id,
        )
