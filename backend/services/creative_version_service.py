"""
Creative version helpers for Phase A / B / Phase 3 PR1.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CheckRecord, CreativeItem, CreativeVersion, PackageRecord
from schemas import (
    CheckRecordResponse,
    CreativeCurrentVersionResponse,
    CreativeVersionSummaryResponse,
    PackageRecordResponse,
)
from services.publish_pool_service import PublishPoolService
from utils.time import utc_now_naive

_UNSET = object()


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
            final_product_name=creative_item.subject_product_name_snapshot,
            final_copywriting_text=creative_item.main_copywriting_text,
        )
        self.db.add(version)
        await self.db.flush()

        package_record = PackageRecord(
            creative_version=version,
            package_status=package_status,
            publish_profile_id=creative_item.input_profile_id,
            frozen_duration_seconds=creative_item.target_duration_seconds,
            frozen_product_name=creative_item.subject_product_name_snapshot,
            frozen_copywriting_text=creative_item.main_copywriting_text,
        )
        self.db.add(package_record)
        await self.db.flush()

        creative_item.current_version_id = version.id
        creative_item.latest_version_no = version.version_no
        if status_on_activate is not None:
            creative_item.status = status_on_activate
        if parent_version_id is not None:
            await PublishPoolService(self.db).invalidate_for_creative(
                creative_item.id,
                reason="superseded_by_new_version",
            )
        return version

    @staticmethod
    def build_package_record_response(record: Optional[PackageRecord]) -> Optional[PackageRecordResponse]:
        if record is None:
            return None
        return PackageRecordResponse.model_validate(record)

    @staticmethod
    def _primary_package_record(version: CreativeVersion) -> Optional[PackageRecord]:
        if not version.package_records:
            return None
        return version.package_records[0]

    async def get_or_create_package_record(self, version: CreativeVersion) -> PackageRecord:
        package_record = (
            await self.db.execute(
                select(PackageRecord).where(PackageRecord.creative_version_id == version.id)
            )
        ).scalar_one_or_none()
        if package_record is not None:
            return package_record

        package_record = PackageRecord(
            creative_version_id=version.id,
            package_status="pending",
        )
        self.db.add(package_record)
        await self.db.flush()
        return package_record

    async def sync_version_result(
        self,
        version: CreativeVersion,
        *,
        actual_duration_seconds: Optional[int] | object = _UNSET,
        final_video_path: Optional[str] | object = _UNSET,
        final_product_name: Optional[str] | object = _UNSET,
        final_copywriting_text: Optional[str] | object = _UNSET,
    ) -> CreativeVersion:
        if actual_duration_seconds is not _UNSET:
            version.actual_duration_seconds = actual_duration_seconds
        if final_video_path is not _UNSET:
            version.final_video_path = final_video_path
        if final_product_name is not _UNSET:
            version.final_product_name = final_product_name
        if final_copywriting_text is not _UNSET:
            version.final_copywriting_text = final_copywriting_text
        version.updated_at = utc_now_naive()
        await self.db.flush()
        return version

    async def sync_publish_package(
        self,
        version: CreativeVersion,
        *,
        package_status: Optional[str] | object = _UNSET,
        publish_profile_id: Optional[int] | object = _UNSET,
        frozen_video_path: Optional[str] | object = _UNSET,
        frozen_cover_path: Optional[str] | object = _UNSET,
        frozen_duration_seconds: Optional[int] | object = _UNSET,
        frozen_product_name: Optional[str] | object = _UNSET,
        frozen_copywriting_text: Optional[str] | object = _UNSET,
        manifest_payload: Optional[dict[str, Any]] = None,
        manifest_json: Optional[str] = None,
    ) -> PackageRecord:
        package_record = await self.get_or_create_package_record(version)
        if package_status is not _UNSET:
            package_record.package_status = package_status
        if publish_profile_id is not _UNSET:
            package_record.publish_profile_id = publish_profile_id
        if frozen_video_path is not _UNSET:
            package_record.frozen_video_path = frozen_video_path
        if frozen_cover_path is not _UNSET:
            package_record.frozen_cover_path = frozen_cover_path
        if frozen_duration_seconds is not _UNSET:
            package_record.frozen_duration_seconds = frozen_duration_seconds
        if frozen_product_name is not _UNSET:
            package_record.frozen_product_name = frozen_product_name
        if frozen_copywriting_text is not _UNSET:
            package_record.frozen_copywriting_text = frozen_copywriting_text
        if manifest_payload is not None:
            package_record.manifest_json = json.dumps(
                manifest_payload,
                ensure_ascii=False,
                sort_keys=True,
            )
        elif manifest_json is not None:
            package_record.manifest_json = manifest_json
        package_record.updated_at = utc_now_naive()
        await self.db.flush()
        return package_record

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
        package_record = self._primary_package_record(version)
        package_record_id = package_record.id if package_record is not None else None

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
            actual_duration_seconds=version.actual_duration_seconds,
            final_video_path=version.final_video_path,
            final_product_name=version.final_product_name,
            final_copywriting_text=version.final_copywriting_text,
            package_record_id=package_record_id,
            package_record=self.build_package_record_response(package_record),
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

        package_record = self._primary_package_record(version)
        package_record_id = package_record.id if package_record is not None else None

        latest_check = None
        if version.check_records:
            latest_check = self.build_check_record_response(version.check_records[-1])

        return CreativeCurrentVersionResponse(
            id=version.id,
            version_no=version.version_no,
            title=version.title,
            parent_version_id=version.parent_version_id,
            actual_duration_seconds=version.actual_duration_seconds,
            final_video_path=version.final_video_path,
            final_product_name=version.final_product_name,
            final_copywriting_text=version.final_copywriting_text,
            package_record_id=package_record_id,
            package_record=self.build_package_record_response(package_record),
            latest_check=latest_check,
        )
