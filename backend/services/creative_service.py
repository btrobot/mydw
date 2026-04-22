"""
Creative aggregate helpers for work-driven flow.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from typing import Any, Optional

from loguru import logger
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from models import (
    Audio,
    CompositionJob,
    Copywriting,
    Cover,
    CreativeInputItem,
    CreativeItem,
    CreativeInputSnapshot,
    CreativeVersion,
    Product,
    PublishProfile,
    Task,
    TaskAudio,
    TaskCopywriting,
    TaskCover,
    TaskTopic,
    TaskVideo,
    Topic,
    Video,
)
from schemas import (
    CreativeCreateRequest,
    CreativeDetailResponse,
    CreativeEligibilityStatus,
    CreativeInputItemResponse,
    CreativeInputSnapshotResponse,
    CreativeItemResponse,
    CreativeLatestTaskSummaryResponse,
    CreativeComposeSubmitResponse,
    CreativeReviewSummaryResponse,
    CreativeStatus,
    CreativeUpdateRequest,
    CreativeWorkbenchItemResponse,
    CreativeWorkbenchListResponse,
    CompositionJobStatus,
    TaskKind,
    TaskStatus,
)
from services.composition_service import CompositionService
from services.creative_version_service import CreativeVersionService
from services.task_assembler import TaskAssembler
from services.task_execution_semantics import TaskSemanticsError, validate_task_resource_inputs
from services.task_service import TaskService
from services.topic_relation_service import get_profile_topic_ids
from services.topic_semantics import merge_task_topic_ids
from utils.time import utc_now_naive


REVIEW_AND_BEYOND_STATUS_VALUES = {
    CreativeStatus.WAITING_REVIEW.value,
    CreativeStatus.APPROVED.value,
    CreativeStatus.REWORK_REQUIRED.value,
    CreativeStatus.REJECTED.value,
    CreativeStatus.IN_PUBLISH_POOL.value,
    CreativeStatus.PUBLISHING.value,
    CreativeStatus.PUBLISHED.value,
}

INPUT_ITEM_TO_SNAPSHOT_FIELD = {
    "video": "video_ids",
    "copywriting": "copywriting_ids",
    "cover": "cover_ids",
    "audio": "audio_ids",
    "topic": "topic_ids",
}

SNAPSHOT_FIELD_ORDER: tuple[tuple[str, str], ...] = (
    ("video_ids", "video"),
    ("copywriting_ids", "copywriting"),
    ("cover_ids", "cover"),
    ("audio_ids", "audio"),
    ("topic_ids", "topic"),
)

INPUT_STATE_FIELD_NAMES = (
    "profile_id",
    "video_ids",
    "copywriting_ids",
    "cover_ids",
    "audio_ids",
    "topic_ids",
    "input_items",
)

DUPLICATE_EXECUTION_LIMITATION_REASON = (
    "当前作品定义包含重复素材实例，作品本身有效，但当前执行路径暂不支持将同一素材重复编排到任务资源集合中。"
)


class CreativeService:
    """Creative aggregate service for work-driven creation and projection."""

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
            .options(
                selectinload(CreativeItem.input_items),
                selectinload(CreativeItem.input_profile),
                selectinload(CreativeItem.input_snapshot_record),
                selectinload(CreativeItem.tasks).selectinload(Task.profile),
                selectinload(CreativeItem.publish_pool_items),
            )
        )
        items = [await self._build_workbench_item_response(item) for item in result.scalars().all()]
        return CreativeWorkbenchListResponse(total=total, items=items)

    async def create_creative(self, payload: CreativeCreateRequest) -> CreativeDetailResponse:
        creative_no = payload.creative_no or await self._generate_creative_no()
        if await self._creative_no_exists(creative_no):
            raise ValueError("作品编号已存在")

        subject_product_name_snapshot = await self._resolve_subject_product_name_snapshot(
            subject_product_id=payload.subject_product_id,
            explicit_snapshot=payload.subject_product_name_snapshot,
        )
        creative = CreativeItem(
            creative_no=creative_no,
            title=payload.title,
            status=CreativeStatus.PENDING_INPUT.value,
            latest_version_no=0,
            subject_product_id=payload.subject_product_id,
            subject_product_name_snapshot=subject_product_name_snapshot,
            main_copywriting_text=payload.main_copywriting_text,
            target_duration_seconds=payload.target_duration_seconds,
        )
        self.db.add(creative)
        await self.db.flush()

        input_profile_id, authoritative_input_items = self._resolve_authoritative_input_state(
            profile_id=payload.profile_id,
            current_input_items=[],
            current_snapshot=None,
            explicit_input_items=payload.input_items if "input_items" in payload.model_fields_set else None,
            explicit_snapshot_overrides={
                "video_ids": payload.video_ids,
                "copywriting_ids": payload.copywriting_ids,
                "cover_ids": payload.cover_ids,
                "audio_ids": payload.audio_ids,
                "topic_ids": payload.topic_ids,
            },
        )
        await self._apply_authoritative_input_state(
            creative,
            profile_id=input_profile_id,
            input_items=authoritative_input_items,
        )
        await self._sync_pre_compose_status(creative)
        await self.db.commit()
        input_snapshot = self._build_input_snapshot_response(creative)
        logger.info(
            "event_name=creative_flow_entry_new creative_item_id={} snapshot_hash={} profile_id={} material_counts={} account_mode=creative_only",
            creative.id,
            input_snapshot.snapshot_hash,
            input_snapshot.profile_id,
            {
                "videos": len(input_snapshot.video_ids),
                "copywritings": len(input_snapshot.copywriting_ids),
                "covers": len(input_snapshot.cover_ids),
                "audios": len(input_snapshot.audio_ids),
                "topics": len(input_snapshot.topic_ids),
            },
        )
        return await self.get_creative_detail(creative.id)  # type: ignore[return-value]

    async def get_creative_detail(self, creative_id: int) -> Optional[CreativeDetailResponse]:
        creative = await self._load_creative_detail(creative_id)
        if creative is None:
            return None
        return await self._build_creative_detail_response(creative)

    async def update_creative(
        self,
        creative_id: int,
        payload: CreativeUpdateRequest,
    ) -> Optional[CreativeDetailResponse]:
        creative = await self._load_creative_detail(creative_id)
        if creative is None:
            return None

        if "title" in payload.model_fields_set:
            creative.title = payload.title
        if "subject_product_id" in payload.model_fields_set:
            creative.subject_product_id = payload.subject_product_id
        if (
            "subject_product_id" in payload.model_fields_set
            or "subject_product_name_snapshot" in payload.model_fields_set
        ):
            explicit_snapshot = (
                payload.subject_product_name_snapshot
                if "subject_product_name_snapshot" in payload.model_fields_set
                else creative.subject_product_name_snapshot
            )
            creative.subject_product_name_snapshot = await self._resolve_subject_product_name_snapshot(
                subject_product_id=creative.subject_product_id,
                explicit_snapshot=explicit_snapshot,
            )
        if "main_copywriting_text" in payload.model_fields_set:
            creative.main_copywriting_text = payload.main_copywriting_text
        if "target_duration_seconds" in payload.model_fields_set:
            creative.target_duration_seconds = payload.target_duration_seconds

        if self._payload_updates_input_state(payload.model_fields_set):
            current_snapshot = self._extract_legacy_input_snapshot(creative)
            current_profile_id = (
                payload.profile_id if "profile_id" in payload.model_fields_set else current_snapshot["profile_id"]
            )
            current_input_items = self._extract_authoritative_input_items(creative)
            input_profile_id, authoritative_input_items = self._resolve_authoritative_input_state(
                profile_id=current_profile_id,
                current_input_items=current_input_items,
                current_snapshot=current_snapshot,
                explicit_input_items=payload.input_items if "input_items" in payload.model_fields_set else None,
                explicit_snapshot_overrides={
                    field_name: (getattr(payload, field_name) or [])
                    for field_name in ("video_ids", "copywriting_ids", "cover_ids", "audio_ids", "topic_ids")
                    if field_name in payload.model_fields_set
                },
            )
            await self._apply_authoritative_input_state(
                creative,
                profile_id=input_profile_id,
                input_items=authoritative_input_items,
            )
        elif creative.__dict__.get("input_snapshot_record") is None:
            self._sync_compatibility_snapshot_from_current_state(creative)
        await self._sync_pre_compose_status(creative)
        await self.db.commit()
        return await self.get_creative_detail(creative.id)

    async def submit_composition(
        self,
        creative_id: int,
    ) -> CreativeComposeSubmitResponse:
        creative = await self._load_creative_detail(creative_id)
        if creative is None:
            raise ValueError("作品不存在")

        input_snapshot = self._build_input_snapshot_response(creative)
        eligibility_status, eligibility_reasons = await self._build_eligibility_projection(
            creative,
            input_snapshot=input_snapshot,
        )
        if eligibility_status != CreativeEligibilityStatus.READY_TO_COMPOSE:
            detail = "；".join(eligibility_reasons) if eligibility_reasons else "当前作品输入尚未满足提交条件"
            raise ValueError(detail)

        profile = creative.__dict__.get("input_profile")
        if profile is None and input_snapshot.profile_id is not None:
            profile = await self.db.get(PublishProfile, input_snapshot.profile_id)
        if profile is None:
            raise ValueError("所选合成配置不存在")
        if self._has_duplicate_execution_instances(creative):
            raise ValueError(DUPLICATE_EXECUTION_LIMITATION_REASON)

        expected_inputs = await self._build_expected_task_inputs(
            input_snapshot=input_snapshot,
            profile=profile,
        )
        composition_service = CompositionService(self.db)

        matching_composing_task = await self._find_matching_task(
            creative.tasks,
            expected_inputs,
            status=TaskStatus.COMPOSING.value,
        )
        if matching_composing_task is not None:
            return await self._build_submit_response(
                creative=creative,
                task=matching_composing_task,
                profile=profile,
                submission_action="reused_composing",
                reused_existing_task=True,
                created_new_task=False,
            )

        if profile.composition_mode == "none":
            matching_ready_task = await self._find_matching_task(
                creative.tasks,
                expected_inputs,
                status=TaskStatus.READY.value,
            )
            if matching_ready_task is not None and matching_ready_task.creative_version_id is not None:
                return await self._build_submit_response(
                    creative=creative,
                    task=matching_ready_task,
                    profile=profile,
                    submission_action="reused_ready_task",
                    reused_existing_task=True,
                    created_new_task=False,
                )

        matching_draft_task = await self._find_matching_task(
            creative.tasks,
            expected_inputs,
            status=TaskStatus.DRAFT.value,
        )

        created_new_task = False
        submission_action = "reused_draft_and_submitted"
        task = matching_draft_task

        if task is None:
            stale_draft_tasks = [
                item for item in creative.tasks
                if item.task_kind != TaskKind.PUBLISH.value and item.status == TaskStatus.DRAFT.value
            ]
            for stale_task in stale_draft_tasks:
                await TaskService(self.db).delete_task(stale_task.id)

            task = await TaskAssembler(self.db).assemble(
                account_id=None,
                video_ids=input_snapshot.video_ids,
                copywriting_ids=input_snapshot.copywriting_ids,
                cover_ids=input_snapshot.cover_ids,
                audio_ids=input_snapshot.audio_ids,
                topic_ids=input_snapshot.topic_ids,
                profile_id=profile.id,
                name=self._build_task_name(creative),
                creative_item_id=creative.id,
                task_kind=TaskKind.COMPOSITION.value,
            )
            created_new_task = True
            submission_action = "created_ready_task" if profile.composition_mode == "none" else "created_and_submitted"

        if profile.composition_mode == "none":
            if task.creative_version_id is None:
                version = await self.version_service.create_next_version(
                    creative,
                    title=task.name or creative.title,
                    version_type="generated",
                    package_status="ready",
                    status_on_activate=CreativeStatus.WAITING_REVIEW.value,
                )
                task.creative_version_id = version.id
                task.task_kind = TaskKind.COMPOSITION.value
                task.status = TaskStatus.READY.value
                task.error_msg = None
                task.failed_at_status = None
                task.updated_at = utc_now_naive()
                creative.generation_error_msg = None
                creative.generation_failed_at = None
                creative.updated_at = utc_now_naive()
                await self.db.commit()

            refreshed = await self._load_creative_detail(creative.id)
            if refreshed is None:
                raise ValueError("作品不存在")
            refreshed_task = next((item for item in refreshed.tasks if item.id == task.id), None)
            if refreshed_task is None:
                raise ValueError("任务不存在")
            return await self._build_submit_response(
                creative=refreshed,
                task=refreshed_task,
                profile=profile,
                submission_action=submission_action,
                reused_existing_task=not created_new_task,
                created_new_task=created_new_task,
            )

        job = await composition_service.submit_composition(task.id)
        refreshed = await self._load_creative_detail(creative.id)
        if refreshed is None:
            raise ValueError("作品不存在")
        refreshed_task = next((item for item in refreshed.tasks if item.id == task.id), None)
        if refreshed_task is None:
            raise ValueError("任务不存在")
        return await self._build_submit_response(
            creative=refreshed,
            task=refreshed_task,
            profile=profile,
            composition_job=job,
            submission_action=submission_action,
            reused_existing_task=not created_new_task,
            created_new_task=created_new_task,
        )

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
            status=CreativeStatus.PENDING_INPUT.value,
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
            .execution_options(populate_existing=True)
            .options(
                selectinload(CreativeItem.input_items),
                selectinload(CreativeItem.input_profile),
                selectinload(CreativeItem.input_snapshot_record),
                selectinload(CreativeItem.current_version).selectinload(CreativeVersion.package_records),
                selectinload(CreativeItem.current_version).selectinload(CreativeVersion.check_records),
                selectinload(CreativeItem.versions).selectinload(CreativeVersion.package_records),
                selectinload(CreativeItem.versions).selectinload(CreativeVersion.check_records),
                selectinload(CreativeItem.tasks).selectinload(Task.profile),
                selectinload(CreativeItem.tasks).selectinload(Task.videos),
                selectinload(CreativeItem.tasks).selectinload(Task.copywritings),
                selectinload(CreativeItem.tasks).selectinload(Task.covers),
                selectinload(CreativeItem.tasks).selectinload(Task.audios),
                selectinload(CreativeItem.tasks).selectinload(Task.topics),
                selectinload(CreativeItem.tasks).selectinload(Task.composition_jobs),
                selectinload(CreativeItem.publish_pool_items),
            )
        )
        return result.scalars().first()

    async def _build_workbench_item_response(self, creative: CreativeItem) -> CreativeWorkbenchItemResponse:
        projection = await self._build_projection(creative)
        return CreativeWorkbenchItemResponse(
            id=creative.id,
            creative_no=creative.creative_no,
            title=creative.title,
            status=projection["status"],
            current_version_id=creative.current_version_id,
            subject_product_id=creative.subject_product_id,
            subject_product_name_snapshot=creative.subject_product_name_snapshot,
            main_copywriting_text=creative.main_copywriting_text,
            target_duration_seconds=creative.target_duration_seconds,
            input_items=projection["input_items"],
            input_snapshot=projection["input_snapshot"],
            generation_error_msg=creative.generation_error_msg,
            generation_failed_at=creative.generation_failed_at,
            eligibility_status=projection["eligibility_status"],
            eligibility_reasons=projection["eligibility_reasons"],
            latest_task_summary=projection["latest_task_summary"],
            updated_at=creative.updated_at,
        )

    async def _build_creative_detail_response(self, creative: CreativeItem) -> CreativeDetailResponse:
        linked_task_ids = sorted(task.id for task in creative.tasks)
        current_version = self.version_service.build_current_version_response(creative.current_version)
        ordered_versions = sorted(
            creative.versions,
            key=lambda version: (version.version_no, version.id),
            reverse=True,
        )
        versions = [
            self.version_service.build_version_summary_response(
                version,
                current_version_id=creative.current_version_id,
            )
            for version in ordered_versions
        ]
        total_checks = sum(len(version.check_records) for version in creative.versions)
        current_check = None
        if creative.current_version and creative.current_version.check_records:
            current_check = self.version_service.build_check_record_response(
                creative.current_version.check_records[-1]
            )
        review_summary = CreativeReviewSummaryResponse(
            current_version_id=creative.current_version_id,
            current_check=current_check,
            total_checks=total_checks,
        )
        projection = await self._build_projection(creative)

        return CreativeDetailResponse(
            id=creative.id,
            creative_no=creative.creative_no,
            title=creative.title,
            status=projection["status"],
            current_version_id=creative.current_version_id,
            current_version=current_version,
            versions=versions,
            review_summary=review_summary,
            linked_task_ids=linked_task_ids,
            subject_product_id=creative.subject_product_id,
            subject_product_name_snapshot=creative.subject_product_name_snapshot,
            main_copywriting_text=creative.main_copywriting_text,
            target_duration_seconds=creative.target_duration_seconds,
            input_items=projection["input_items"],
            generation_error_msg=creative.generation_error_msg,
            generation_failed_at=creative.generation_failed_at,
            input_snapshot=projection["input_snapshot"],
            eligibility_status=projection["eligibility_status"],
            eligibility_reasons=projection["eligibility_reasons"],
            latest_task_summary=projection["latest_task_summary"],
            created_at=creative.created_at,
            updated_at=creative.updated_at,
        )

    async def _build_projection(self, creative: CreativeItem) -> dict[str, Any]:
        input_items = self._build_input_items_response(creative)
        input_snapshot = self._build_input_snapshot_response(creative)
        eligibility_status, eligibility_reasons = await self._build_eligibility_projection(
            creative,
            input_snapshot=input_snapshot,
        )
        latest_task_summary = self._build_latest_task_summary(self._pick_latest_task(creative.tasks))
        status = self._project_creative_status(
            creative,
            eligibility_status=eligibility_status,
        )
        return {
            "status": status,
            "input_items": input_items,
            "input_snapshot": input_snapshot,
            "eligibility_status": eligibility_status,
            "eligibility_reasons": eligibility_reasons,
            "latest_task_summary": latest_task_summary,
        }

    async def _build_eligibility_projection(
        self,
        creative: CreativeItem,
        *,
        input_snapshot: CreativeInputSnapshotResponse,
    ) -> tuple[CreativeEligibilityStatus, list[str]]:
        pending_reasons: list[str] = []
        invalid_reasons: list[str] = []

        profile = creative.__dict__.get("input_profile")
        if input_snapshot.profile_id is None:
            pending_reasons.append("请选择合成配置")
        elif profile is None:
            profile = await self.db.get(PublishProfile, input_snapshot.profile_id)
            if profile is None:
                invalid_reasons.append("所选合成配置不存在")

        if not input_snapshot.video_ids:
            pending_reasons.append("至少选择 1 个视频")

        resource_errors = await self._validate_snapshot_resource_ids(input_snapshot)
        invalid_reasons.extend(resource_errors)

        if profile is not None and not invalid_reasons and not pending_reasons:
            try:
                validate_task_resource_inputs(
                    video_ids=input_snapshot.video_ids,
                    copywriting_ids=input_snapshot.copywriting_ids,
                    cover_ids=input_snapshot.cover_ids,
                    audio_ids=input_snapshot.audio_ids,
                    composition_mode=profile.composition_mode,
                )
            except TaskSemanticsError as exc:
                invalid_reasons.append(str(exc))
        if self._has_duplicate_execution_instances(creative):
            invalid_reasons.append(DUPLICATE_EXECUTION_LIMITATION_REASON)

        reasons = [*pending_reasons, *invalid_reasons]
        if invalid_reasons:
            return CreativeEligibilityStatus.INVALID, reasons
        if pending_reasons:
            return CreativeEligibilityStatus.PENDING_INPUT, reasons
        return CreativeEligibilityStatus.READY_TO_COMPOSE, []

    async def _validate_snapshot_resource_ids(
        self,
        input_snapshot: CreativeInputSnapshotResponse,
    ) -> list[str]:
        errors: list[str] = []
        checks = [
            ("视频", Video, input_snapshot.video_ids),
            ("文案", Copywriting, input_snapshot.copywriting_ids),
            ("封面", Cover, input_snapshot.cover_ids),
            ("音频", Audio, input_snapshot.audio_ids),
            ("话题", Topic, input_snapshot.topic_ids),
        ]
        for label, model, ids in checks:
            if not ids:
                continue
            rows = await self.db.execute(select(model.id).where(model.id.in_(ids)))
            existing_ids = set(rows.scalars().all())
            missing_ids = [item_id for item_id in ids if item_id not in existing_ids]
            if missing_ids:
                errors.append(f"{label}素材不存在: {', '.join(str(item_id) for item_id in missing_ids)}")
        return errors

    def _project_creative_status(
        self,
        creative: CreativeItem,
        *,
        eligibility_status: CreativeEligibilityStatus,
    ) -> CreativeStatus:
        latest_publish_task = self._pick_latest_task(
            [task for task in creative.tasks if task.task_kind == TaskKind.PUBLISH.value]
        )
        if latest_publish_task is not None:
            if latest_publish_task.status == TaskStatus.UPLOADING.value:
                return CreativeStatus.PUBLISHING
            if latest_publish_task.status == TaskStatus.UPLOADED.value:
                return CreativeStatus.PUBLISHED

        if creative.current_version_id is not None and any(
            pool_item.status == "active" and pool_item.creative_version_id == creative.current_version_id
            for pool_item in creative.publish_pool_items
        ):
            return CreativeStatus.IN_PUBLISH_POOL

        stored_status = self._coerce_creative_status(creative.status)
        if stored_status in {
            CreativeStatus.WAITING_REVIEW,
            CreativeStatus.APPROVED,
            CreativeStatus.REWORK_REQUIRED,
            CreativeStatus.REJECTED,
            CreativeStatus.IN_PUBLISH_POOL,
            CreativeStatus.PUBLISHING,
            CreativeStatus.PUBLISHED,
        }:
            return stored_status

        latest_composition_task = self._pick_latest_task(
            [task for task in creative.tasks if task.task_kind != TaskKind.PUBLISH.value]
        )
        if latest_composition_task is not None:
            if latest_composition_task.status == TaskStatus.COMPOSING.value:
                return CreativeStatus.COMPOSING
            if (
                latest_composition_task.status == TaskStatus.FAILED.value
                and creative.status not in REVIEW_AND_BEYOND_STATUS_VALUES
                and creative.generation_failed_at is not None
            ):
                return CreativeStatus.FAILED

        if eligibility_status == CreativeEligibilityStatus.READY_TO_COMPOSE:
            return CreativeStatus.READY_TO_COMPOSE
        if eligibility_status == CreativeEligibilityStatus.INVALID and creative.generation_failed_at is not None:
            return CreativeStatus.FAILED
        return CreativeStatus.PENDING_INPUT

    def _build_input_snapshot_response(self, creative: CreativeItem) -> CreativeInputSnapshotResponse:
        snapshot = self._resolve_current_snapshot_state(creative)
        return CreativeInputSnapshotResponse(
            profile_id=snapshot["profile_id"],
            video_ids=snapshot["video_ids"],
            copywriting_ids=snapshot["copywriting_ids"],
            cover_ids=snapshot["cover_ids"],
            audio_ids=snapshot["audio_ids"],
            topic_ids=snapshot["topic_ids"],
            snapshot_hash=snapshot["snapshot_hash"],
        )

    def _build_input_items_response(self, creative: CreativeItem) -> list[CreativeInputItemResponse]:
        authoritative_input_items = self._extract_authoritative_input_items(creative)
        if not authoritative_input_items:
            authoritative_input_items = self._synthesize_input_items_from_snapshot(
                self._extract_legacy_input_snapshot(creative)
            )
        return [
            CreativeInputItemResponse(
                id=item.get("id"),
                material_type=item["material_type"],
                material_id=item["material_id"],
                role=item.get("role"),
                sequence=item["sequence"],
                instance_no=item["instance_no"],
                trim_in=item.get("trim_in"),
                trim_out=item.get("trim_out"),
                slot_duration_seconds=item.get("slot_duration_seconds"),
                enabled=item.get("enabled", True),
            )
            for item in authoritative_input_items
        ]

    async def _resolve_subject_product_name_snapshot(
        self,
        *,
        subject_product_id: Optional[int],
        explicit_snapshot: Optional[str],
    ) -> Optional[str]:
        if subject_product_id is None:
            return explicit_snapshot
        product = await self.db.get(Product, subject_product_id)
        if product is None:
            raise ValueError("所选商品不存在")
        if explicit_snapshot is not None:
            return explicit_snapshot
        return product.name

    def _resolve_authoritative_input_state(
        self,
        *,
        profile_id: Optional[int],
        current_input_items: list[dict[str, Any]],
        current_snapshot: Optional[dict[str, Any]],
        explicit_input_items: Optional[list[Any]],
        explicit_snapshot_overrides: dict[str, list[int]],
    ) -> tuple[Optional[int], list[dict[str, Any]]]:
        if explicit_input_items is not None:
            return profile_id, self._normalize_input_items(explicit_input_items)
        if explicit_snapshot_overrides:
            snapshot = {
                "profile_id": profile_id,
                "video_ids": list((current_snapshot or {}).get("video_ids", [])),
                "copywriting_ids": list((current_snapshot or {}).get("copywriting_ids", [])),
                "cover_ids": list((current_snapshot or {}).get("cover_ids", [])),
                "audio_ids": list((current_snapshot or {}).get("audio_ids", [])),
                "topic_ids": list((current_snapshot or {}).get("topic_ids", [])),
            }
            snapshot.update(
                {
                    field_name: self._deduplicate_legacy_ids(item_ids)
                    for field_name, item_ids in explicit_snapshot_overrides.items()
                }
            )
            return profile_id, self._synthesize_input_items_from_snapshot(snapshot)
        if current_input_items:
            return profile_id, self._normalize_input_items(current_input_items)
        if current_snapshot is not None:
            return profile_id, self._synthesize_input_items_from_snapshot(current_snapshot)
        return profile_id, []

    async def _apply_authoritative_input_state(
        self,
        creative: CreativeItem,
        *,
        profile_id: Optional[int],
        input_items: list[dict[str, Any]],
    ) -> None:
        normalized_items = self._normalize_input_items(input_items)
        if creative.id is not None:
            await self.db.execute(
                delete(CreativeInputItem).where(CreativeInputItem.creative_item_id == creative.id)
            )
        new_rows = [
            CreativeInputItem(
                creative_item_id=creative.id,
                material_type=item["material_type"],
                material_id=item["material_id"],
                role=item.get("role"),
                sequence=item["sequence"],
                instance_no=item["instance_no"],
                trim_in=item.get("trim_in"),
                trim_out=item.get("trim_out"),
                slot_duration_seconds=item.get("slot_duration_seconds"),
                enabled=item.get("enabled", True),
            )
            for item in normalized_items
        ]
        self.db.add_all(new_rows)
        set_committed_value(creative, "input_items", new_rows)
        projected_snapshot = self._project_input_items_to_snapshot(
            profile_id=profile_id,
            input_items=normalized_items,
        )
        self._apply_input_snapshot(
            creative,
            profile_id=projected_snapshot["profile_id"],
            video_ids=projected_snapshot["video_ids"],
            copywriting_ids=projected_snapshot["copywriting_ids"],
            cover_ids=projected_snapshot["cover_ids"],
            audio_ids=projected_snapshot["audio_ids"],
            topic_ids=projected_snapshot["topic_ids"],
        )

    def _sync_compatibility_snapshot_from_current_state(self, creative: CreativeItem) -> None:
        snapshot = self._resolve_current_snapshot_state(creative)
        self._apply_input_snapshot(
            creative,
            profile_id=snapshot["profile_id"],
            video_ids=snapshot["video_ids"],
            copywriting_ids=snapshot["copywriting_ids"],
            cover_ids=snapshot["cover_ids"],
            audio_ids=snapshot["audio_ids"],
            topic_ids=snapshot["topic_ids"],
        )

    def _resolve_current_snapshot_state(self, creative: CreativeItem) -> dict[str, Any]:
        authoritative_input_items = self._extract_authoritative_input_items(creative)
        if not authoritative_input_items:
            return self._extract_legacy_input_snapshot(creative)
        profile_id = creative.input_profile_id
        if profile_id is None:
            profile_id = self._extract_legacy_input_snapshot(creative)["profile_id"]
        return self._project_input_items_to_snapshot(
            profile_id=profile_id,
            input_items=authoritative_input_items,
        )

    def _extract_authoritative_input_items(self, creative: CreativeItem) -> list[dict[str, Any]]:
        rows = list(creative.__dict__.get("input_items") or [])
        if not rows:
            return []
        return self._normalize_input_items(rows)

    def _normalize_input_items(self, items: list[Any]) -> list[dict[str, Any]]:
        staged: list[tuple[int, int, dict[str, Any]]] = []
        for index, raw_item in enumerate(items, start=1):
            material_type = self._read_input_item_value(raw_item, "material_type")
            if material_type is None:
                raise ValueError("input_items.material_type 不能为空")
            material_type_value = getattr(material_type, "value", material_type)
            material_type_value = str(material_type_value)
            if material_type_value not in INPUT_ITEM_TO_SNAPSHOT_FIELD:
                raise ValueError(f"不支持的 input_items.material_type: {material_type_value}")
            material_id = self._read_input_item_value(raw_item, "material_id")
            if material_id is None:
                raise ValueError("input_items.material_id 不能为空")
            sort_key = self._read_input_item_value(raw_item, "sequence")
            staged.append(
                (
                    int(sort_key) if sort_key is not None else index,
                    index,
                    {
                        "id": self._read_input_item_value(raw_item, "id"),
                        "material_type": material_type_value,
                        "material_id": int(material_id),
                        "role": self._read_input_item_value(raw_item, "role"),
                        "instance_no": self._read_input_item_value(raw_item, "instance_no"),
                        "trim_in": self._read_input_item_value(raw_item, "trim_in"),
                        "trim_out": self._read_input_item_value(raw_item, "trim_out"),
                        "slot_duration_seconds": self._read_input_item_value(raw_item, "slot_duration_seconds"),
                        "enabled": self._read_input_item_value(raw_item, "enabled", True),
                    },
                )
            )
        staged.sort(key=lambda item: (item[0], item[1]))
        material_instance_counts: defaultdict[tuple[str, int], int] = defaultdict(int)
        normalized: list[dict[str, Any]] = []
        for sequence, (_, _, item) in enumerate(staged, start=1):
            duplicate_key = (item["material_type"], item["material_id"])
            material_instance_counts[duplicate_key] += 1
            normalized.append(
                {
                    **item,
                    "sequence": sequence,
                    "instance_no": (
                        int(item["instance_no"])
                        if item.get("instance_no") is not None
                        else material_instance_counts[duplicate_key]
                    ),
                    "enabled": bool(item.get("enabled", True)),
                }
            )
        return normalized

    def _synthesize_input_items_from_snapshot(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        synthesized: list[dict[str, Any]] = []
        for field_name, material_type in SNAPSHOT_FIELD_ORDER:
            for material_id in snapshot.get(field_name, []) or []:
                synthesized.append(
                    {
                        "material_type": material_type,
                        "material_id": int(material_id),
                        "enabled": True,
                    }
                )
        return self._normalize_input_items(synthesized)

    def _project_input_items_to_snapshot(
        self,
        *,
        profile_id: Optional[int],
        input_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        snapshot = {
            "profile_id": profile_id,
            "video_ids": [],
            "copywriting_ids": [],
            "cover_ids": [],
            "audio_ids": [],
            "topic_ids": [],
        }
        for item in self._normalize_input_items(input_items):
            if not item.get("enabled", True):
                continue
            target_field = INPUT_ITEM_TO_SNAPSHOT_FIELD[item["material_type"]]
            snapshot[target_field].append(int(item["material_id"]))
        snapshot["snapshot_hash"] = self._build_snapshot_hash(
            profile_id=profile_id,
            video_ids=snapshot["video_ids"],
            copywriting_ids=snapshot["copywriting_ids"],
            cover_ids=snapshot["cover_ids"],
            audio_ids=snapshot["audio_ids"],
            topic_ids=snapshot["topic_ids"],
        )
        return snapshot

    def _read_input_item_value(self, item: Any, key: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    def _deduplicate_legacy_ids(self, values: list[int]) -> list[int]:
        ordered_ids: list[int] = []
        seen: set[int] = set()
        for raw_value in values:
            item_id = int(raw_value)
            if item_id in seen:
                continue
            seen.add(item_id)
            ordered_ids.append(item_id)
        return ordered_ids

    def _payload_updates_input_state(self, model_fields_set: set[str]) -> bool:
        return any(field_name in model_fields_set for field_name in INPUT_STATE_FIELD_NAMES)

    def _has_duplicate_execution_instances(self, creative: CreativeItem) -> bool:
        authoritative_input_items = self._extract_authoritative_input_items(creative)
        if not authoritative_input_items:
            authoritative_input_items = self._synthesize_input_items_from_snapshot(
                self._extract_legacy_input_snapshot(creative)
            )
        seen: set[tuple[str, int]] = set()
        for item in authoritative_input_items:
            if not item.get("enabled", True):
                continue
            duplicate_key = (item["material_type"], item["material_id"])
            if duplicate_key in seen:
                return True
            seen.add(duplicate_key)
        return False

    def _build_latest_task_summary(self, task: Optional[Task]) -> Optional[CreativeLatestTaskSummaryResponse]:
        if task is None:
            return None
        return CreativeLatestTaskSummaryResponse(
            task_id=task.id,
            task_kind=self._coerce_task_kind(task.task_kind),
            task_status=self._coerce_task_status(task.status),
            composition_job_id=task.composition_job_id,
            error_msg=task.error_msg,
            updated_at=task.updated_at,
        )

    def _pick_latest_task(self, tasks: list[Task]) -> Optional[Task]:
        if not tasks:
            return None
        return max(tasks, key=lambda task: (task.updated_at, task.id))

    async def _build_expected_task_inputs(
        self,
        *,
        input_snapshot: CreativeInputSnapshotResponse,
        profile: PublishProfile,
    ) -> dict[str, Any]:
        merged_topic_ids = merge_task_topic_ids(
            explicit_topic_ids=input_snapshot.topic_ids,
            profile_default_topic_ids=await get_profile_topic_ids(self.db, profile),
        )
        return {
            "profile_id": input_snapshot.profile_id,
            "video_ids": input_snapshot.video_ids,
            "copywriting_ids": input_snapshot.copywriting_ids,
            "cover_ids": input_snapshot.cover_ids,
            "audio_ids": input_snapshot.audio_ids,
            "topic_ids": merged_topic_ids,
        }

    async def _find_matching_task(
        self,
        tasks: list[Task],
        expected_inputs: dict[str, Any],
        *,
        status: str,
    ) -> Optional[Task]:
        candidates = sorted(
            [
                task for task in tasks
                if task.task_kind != TaskKind.PUBLISH.value and task.status == status
            ],
            key=lambda task: (task.updated_at, task.id),
            reverse=True,
        )
        for task in candidates:
            if await self._task_matches_expected_inputs(task, expected_inputs):
                return task
        return None

    async def _task_matches_expected_inputs(
        self,
        task: Task,
        expected_inputs: dict[str, Any],
    ) -> bool:
        if task.profile_id != expected_inputs["profile_id"]:
            return False
        task_inputs = await self._load_task_resource_ids(task.id)
        return (
            task_inputs["video_ids"] == expected_inputs["video_ids"]
            and task_inputs["copywriting_ids"] == expected_inputs["copywriting_ids"]
            and task_inputs["cover_ids"] == expected_inputs["cover_ids"]
            and task_inputs["audio_ids"] == expected_inputs["audio_ids"]
            and task_inputs["topic_ids"] == expected_inputs["topic_ids"]
        )

    async def _load_task_resource_ids(self, task_id: int) -> dict[str, list[int]]:
        async def _ordered_ids(model, field_name: str) -> list[int]:
            result = await self.db.execute(
                select(getattr(model, field_name))
                .where(model.task_id == task_id)
                .order_by(model.sort_order.asc(), model.id.asc())
            )
            return [int(value) for value in result.scalars().all()]

        topic_rows = await self.db.execute(
            select(TaskTopic.topic_id)
            .where(TaskTopic.task_id == task_id)
            .order_by(TaskTopic.id.asc())
        )
        return {
            "video_ids": await _ordered_ids(TaskVideo, "video_id"),
            "copywriting_ids": await _ordered_ids(TaskCopywriting, "copywriting_id"),
            "cover_ids": await _ordered_ids(TaskCover, "cover_id"),
            "audio_ids": await _ordered_ids(TaskAudio, "audio_id"),
            "topic_ids": [int(value) for value in topic_rows.scalars().all()],
        }

    def _build_task_name(self, creative: CreativeItem) -> str:
        title = (creative.title or "").strip()
        if title:
            return title
        return creative.creative_no

    async def _build_submit_response(
        self,
        *,
        creative: CreativeItem,
        task: Task,
        profile: PublishProfile,
        submission_action: str,
        reused_existing_task: bool,
        created_new_task: bool,
        composition_job: CompositionJob | None = None,
    ) -> CreativeComposeSubmitResponse:
        projection = await self._build_projection(creative)
        resolved_job = composition_job
        if resolved_job is None and task.composition_jobs:
            resolved_job = task.composition_jobs[-1]
        return CreativeComposeSubmitResponse(
            creative_id=creative.id,
            task_id=task.id,
            task_status=self._coerce_task_status(task.status),
            task_kind=self._coerce_task_kind(task.task_kind) or TaskKind.COMPOSITION,
            creative_status=projection["status"],
            current_version_id=creative.current_version_id,
            composition_mode=profile.composition_mode or "none",
            composition_job_id=resolved_job.id if resolved_job is not None else task.composition_job_id,
            composition_job_status=(
                CompositionJobStatus(resolved_job.status)
                if resolved_job is not None and resolved_job.status is not None
                else None
            ),
            submission_action=submission_action,
            reused_existing_task=reused_existing_task,
            created_new_task=created_new_task,
        )

    async def _sync_pre_compose_status(self, creative: CreativeItem) -> None:
        if creative.current_version_id is not None and creative.status in REVIEW_AND_BEYOND_STATUS_VALUES:
            return
        input_snapshot = self._build_input_snapshot_response(creative)
        eligibility_status, _ = await self._build_eligibility_projection(
            creative,
            input_snapshot=input_snapshot,
        )
        if eligibility_status == CreativeEligibilityStatus.READY_TO_COMPOSE:
            creative.status = CreativeStatus.READY_TO_COMPOSE.value
        else:
            creative.status = CreativeStatus.PENDING_INPUT.value
        creative.updated_at = utc_now_naive()
        await self.db.flush()

    def _apply_input_snapshot(
        self,
        creative: CreativeItem,
        *,
        profile_id: Optional[int],
        video_ids: list[int],
        copywriting_ids: list[int],
        cover_ids: list[int],
        audio_ids: list[int],
        topic_ids: list[int],
    ) -> None:
        snapshot_hash = self._build_snapshot_hash(
            profile_id=profile_id,
            video_ids=video_ids,
            copywriting_ids=copywriting_ids,
            cover_ids=cover_ids,
            audio_ids=audio_ids,
            topic_ids=topic_ids,
        )
        creative.input_profile_id = profile_id
        creative.input_video_ids = self._encode_id_list(video_ids)
        creative.input_copywriting_ids = self._encode_id_list(copywriting_ids)
        creative.input_cover_ids = self._encode_id_list(cover_ids)
        creative.input_audio_ids = self._encode_id_list(audio_ids)
        creative.input_topic_ids = self._encode_id_list(topic_ids)
        creative.input_snapshot_hash = snapshot_hash
        snapshot_record = creative.__dict__.get("input_snapshot_record")
        if snapshot_record is None:
            snapshot_record = CreativeInputSnapshot(creative_item=creative)
            self.db.add(snapshot_record)
            creative.input_snapshot_record = snapshot_record
        snapshot_record.profile_id = profile_id
        snapshot_record.video_ids = self._encode_id_list(video_ids)
        snapshot_record.copywriting_ids = self._encode_id_list(copywriting_ids)
        snapshot_record.cover_ids = self._encode_id_list(cover_ids)
        snapshot_record.audio_ids = self._encode_id_list(audio_ids)
        snapshot_record.topic_ids = self._encode_id_list(topic_ids)
        snapshot_record.snapshot_hash = snapshot_hash
        snapshot_record.updated_at = utc_now_naive()
        snapshot_record.__dict__.pop("profile", None)
        creative.__dict__.pop("input_profile", None)
        creative.updated_at = utc_now_naive()

    def _extract_legacy_input_snapshot(self, creative: CreativeItem) -> dict[str, Any]:
        snapshot_record = creative.__dict__.get("input_snapshot_record")
        if snapshot_record is not None:
            return {
                "profile_id": snapshot_record.profile_id,
                "video_ids": self._decode_id_list(snapshot_record.video_ids),
                "copywriting_ids": self._decode_id_list(snapshot_record.copywriting_ids),
                "cover_ids": self._decode_id_list(snapshot_record.cover_ids),
                "audio_ids": self._decode_id_list(snapshot_record.audio_ids),
                "topic_ids": self._decode_id_list(snapshot_record.topic_ids),
                "snapshot_hash": snapshot_record.snapshot_hash,
            }
        return {
            "profile_id": creative.input_profile_id,
            "video_ids": self._decode_id_list(creative.input_video_ids),
            "copywriting_ids": self._decode_id_list(creative.input_copywriting_ids),
            "cover_ids": self._decode_id_list(creative.input_cover_ids),
            "audio_ids": self._decode_id_list(creative.input_audio_ids),
            "topic_ids": self._decode_id_list(creative.input_topic_ids),
            "snapshot_hash": creative.input_snapshot_hash,
        }

    def _build_snapshot_hash(
        self,
        *,
        profile_id: Optional[int],
        video_ids: list[int],
        copywriting_ids: list[int],
        cover_ids: list[int],
        audio_ids: list[int],
        topic_ids: list[int],
    ) -> str:
        payload = {
            "profile_id": profile_id,
            "video_ids": video_ids,
            "copywriting_ids": copywriting_ids,
            "cover_ids": cover_ids,
            "audio_ids": audio_ids,
            "topic_ids": topic_ids,
        }
        canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _encode_id_list(self, values: list[int]) -> str:
        return json.dumps(values, ensure_ascii=False, separators=(",", ":"))

    def _decode_id_list(self, raw_value: Optional[str]) -> list[int]:
        if raw_value in (None, ""):
            return []
        try:
            parsed = json.loads(raw_value)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return [int(item) for item in parsed]

    async def _creative_no_exists(self, creative_no: str) -> bool:
        result = await self.db.execute(
            select(CreativeItem.id).where(CreativeItem.creative_no == creative_no)
        )
        return result.scalars().first() is not None

    async def _generate_creative_no(self) -> str:
        while True:
            candidate = f"CR-{utc_now_naive():%Y%m%d%H%M%S%f}"
            if not await self._creative_no_exists(candidate):
                return candidate

    def _coerce_creative_status(self, value: str | CreativeStatus) -> CreativeStatus:
        if isinstance(value, CreativeStatus):
            return value
        try:
            return CreativeStatus(value)
        except ValueError:
            return CreativeStatus.PENDING_INPUT

    def _coerce_task_kind(self, value: Optional[str]) -> Optional[TaskKind]:
        if value is None:
            return None
        try:
            return TaskKind(value)
        except ValueError:
            return None

    def _coerce_task_status(self, value: str | TaskStatus) -> TaskStatus:
        if isinstance(value, TaskStatus):
            return value
        try:
            return TaskStatus(value)
        except ValueError:
            return TaskStatus.DRAFT

    def build_item_response(self, creative: CreativeItem) -> CreativeItemResponse:
        """
        Legacy helper kept for schema-instantiation compatibility in tests.
        """
        input_snapshot = self._build_input_snapshot_response(creative)
        input_items = self._build_input_items_response(creative)
        return CreativeItemResponse(
            id=creative.id,
            creative_no=creative.creative_no,
            title=creative.title,
            status=self._coerce_creative_status(creative.status),
            current_version_id=creative.current_version_id,
            latest_version_no=creative.latest_version_no,
            subject_product_id=creative.subject_product_id,
            subject_product_name_snapshot=creative.subject_product_name_snapshot,
            main_copywriting_text=creative.main_copywriting_text,
            target_duration_seconds=creative.target_duration_seconds,
            input_items=input_items,
            generation_error_msg=creative.generation_error_msg,
            generation_failed_at=creative.generation_failed_at,
            input_snapshot=input_snapshot,
            eligibility_status=CreativeEligibilityStatus.PENDING_INPUT,
            eligibility_reasons=[],
            latest_task_summary=None,
            created_at=creative.created_at,
            updated_at=creative.updated_at,
        )
