"""
Creative version helpers for Phase A / B.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models import CheckRecord, CreativeItem, CreativeVersion, PackageRecord
from schemas import (
    CheckRecordResponse,
    CreativeCurrentVersionResponse,
    CreativeVersionSummaryResponse,
)


class CreativeVersionService:
    """Helpers for creating and projecting Creative versions."""

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
        return await self._create_version(
            creative_item,
            title=title,
            version_type=version_type,
            package_status=package_status,
            version_no=1,
            parent_version_id=None,
            status_on_activate=None,
        )

    async def create_next_version(
        self,
        creative_item: CreativeItem,
        *,
        title: Optional[str] = None,
        version_type: str = "generated",
        package_status: str = "pending",
        status_on_activate: str = "WAITING_REVIEW",
    ) -> CreativeVersion:
        return await self._create_version(
            creative_item,
            title=title,
            version_type=version_type,
            package_status=package_status,
            version_no=creative_item.latest_version_no + 1,
            parent_version_id=creative_item.current_version_id,
            status_on_activate=status_on_activate,
        )

    async def _create_version(
        self,
        creative_item: CreativeItem,
        *,
        title: Optional[str],
        version_type: str,
        package_status: str,
        version_no: int,
        parent_version_id: Optional[int],
        status_on_activate: Optional[str],
    ) -> CreativeVersion:
        version = CreativeVersion(
            creative_item_id=creative_item.id,
            parent_version_id=parent_version_id,
            version_no=version_no,
            version_type=version_type,
            title=title,
        )
        self.db.add(version)
        await self.db.flush()

        package_record = PackageRecord(
            creative_version=version,
            package_status=package_status,
        )
        self.db.add(package_record)
        await self.db.flush()

        creative_item.current_version_id = version.id
        creative_item.latest_version_no = version.version_no
        if status_on_activate is not None:
            creative_item.status = status_on_activate
        return version

    @staticmethod
    def build_check_record_response(record: Optional[CheckRecord]) -> Optional[CheckRecordResponse]:
        if record is None:
            return None

        return CheckRecordResponse.model_validate(record)

    def build_version_summary_response(
        self,
        version: CreativeVersion,
        *,
        current_version_id: Optional[int],
    ) -> CreativeVersionSummaryResponse:
        package_record_id = None
        if version.package_records:
            package_record_id = version.package_records[0].id

        latest_check = None
        if version.check_records:
            latest_check = self.build_check_record_response(version.check_records[-1])

        return CreativeVersionSummaryResponse(
            id=version.id,
            creative_item_id=version.creative_item_id,
            parent_version_id=version.parent_version_id,
            version_no=version.version_no,
            version_type=version.version_type,
            title=version.title,
            package_record_id=package_record_id,
            is_current=version.id == current_version_id,
            latest_check=latest_check,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )

    def build_current_version_response(
        self,
        version: Optional[CreativeVersion],
    ) -> Optional[CreativeCurrentVersionResponse]:
        if version is None:
            return None

        package_record_id = None
        if version.package_records:
            package_record_id = version.package_records[0].id

        latest_check = None
        if version.check_records:
            latest_check = self.build_check_record_response(version.check_records[-1])

        return CreativeCurrentVersionResponse(
            id=version.id,
            version_no=version.version_no,
            title=version.title,
            parent_version_id=version.parent_version_id,
            package_record_id=package_record_id,
            latest_check=latest_check,
        )
