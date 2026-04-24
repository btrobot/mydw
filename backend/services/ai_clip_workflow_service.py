"""
AIClip-to-Creative workflow orchestration for Phase D PR-D1.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from models import CreativeItem
from schemas import (
    CreativeAIClipWorkflowResponse,
    CreativeStatus,
    CreativeVersionSummaryResponse,
    PackageRecordResponse,
)
from services.ai_clip_service import AIClipService
from services.creative_version_service import CreativeVersionService
from services.media_storage_service import MediaStorageService
from utils.time import utc_now_naive


class CreativeWorkflowError(ValueError):
    """Domain error for Creative workflow actions."""

    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIClipWorkflowService:
    """Keep AIClip tool execution separate from Creative business writeback."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_clip_service = AIClipService()
        self.version_service = CreativeVersionService(db)
        self.media_storage = MediaStorageService(db)

    async def submit_result(
        self,
        creative_id: int,
        *,
        source_version_id: int,
        output_path: str,
        title: str | None = None,
        workflow_type: str = "ai_clip",
        metadata: dict[str, Any] | None = None,
    ) -> CreativeAIClipWorkflowResponse:
        creative = await self.db.get(CreativeItem, creative_id)
        if creative is None:
            raise CreativeWorkflowError("作品不存在", status_code=404)
        if creative.current_version_id is None:
            raise CreativeWorkflowError("作品当前版本不存在", status_code=409)
        if creative.current_version_id != source_version_id:
            raise CreativeWorkflowError("仅允许基于当前版本提交 AIClip workflow", status_code=409)

        resolved_output_path = Path(output_path)
        if not resolved_output_path.is_file():
            raise CreativeWorkflowError("AIClip 输出文件不存在", status_code=400)

        video_info = await self.ai_clip_service.get_video_info(str(resolved_output_path))
        if video_info is None:
            raise CreativeWorkflowError("无法识别 AIClip 输出视频", status_code=400)

        stored_path, _, _ = await self.media_storage.store_from_path(
            str(resolved_output_path),
            "videos",
        )

        version = await self.version_service.create_next_version(
            creative,
            title=title or creative.title,
            version_type="ai_clip",
            package_status="ready",
            status_on_activate=CreativeStatus.WAITING_REVIEW.value,
        )
        rounded_duration = int(round(video_info.duration))
        await self.version_service.sync_version_result(
            version,
            actual_duration_seconds=rounded_duration,
            final_video_path=stored_path,
            final_product_name=creative.resolved_current_product_name(),
            final_copywriting_text=creative.resolved_current_copywriting_text(),
        )
        package_record = await self.version_service.sync_publish_package(
            version,
            creative_item=creative,
            package_status="ready",
            publish_profile_id=creative.input_profile_id,
            frozen_video_path=stored_path,
            frozen_duration_seconds=rounded_duration,
            frozen_product_name=creative.resolved_current_product_name(),
            frozen_copywriting_text=creative.resolved_current_copywriting_text(),
        )
        creative.generation_error_msg = None
        creative.generation_failed_at = None
        creative.updated_at = utc_now_naive()
        await self.db.flush()

        logger.info(
            "ai_clip_workflow_submitted creative_item_id={} source_version_id={} creative_version_id={} workflow_type={}",
            creative.id,
            source_version_id,
            version.id,
            workflow_type,
        )

        return CreativeAIClipWorkflowResponse(
            creative_id=creative.id,
            creative_status=CreativeStatus(creative.status),
            source_version_id=source_version_id,
            current_version_id=version.id,
            workflow_type=workflow_type,
            version=CreativeVersionSummaryResponse(
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
                package_record_id=package_record.id,
                package_record=PackageRecordResponse.model_validate(package_record),
                is_current=True,
                latest_check=None,
                created_at=version.created_at,
                updated_at=version.updated_at,
            ),
            package_record=PackageRecordResponse.model_validate(package_record),
        )
