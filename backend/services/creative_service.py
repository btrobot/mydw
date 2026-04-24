"""
Creative aggregate helpers for work-driven flow.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from typing import Any, Optional

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from models import (
    Audio,
    CompositionJob,
    Copywriting,
    Cover,
    CreativeCandidateItem,
    CreativeInputItem,
    CreativeItem,
    CreativeProductLink,
    CreativeVersion,
    Product,
    PublishPoolItem,
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
    CreativeInputMaterialCountsResponse,
    CreativeInputOrchestrationResponse,
    CreativeCandidateItemResponse,
    CreativeItemResponse,
    CreativeLatestTaskSummaryResponse,
    CreativeCandidateStatus,
    CreativeCandidateType,
    CreativeProductLinkResponse,
    CreativeComposeSubmitResponse,
    CreativeReviewSummaryResponse,
    CreativeStatus,
    CreativeUpdateRequest,
    CreativeWorkbenchItemResponse,
    CreativeWorkbenchListResponse,
    CreativeWorkbenchPoolState,
    CreativeWorkbenchSort,
    CreativeWorkbenchSummaryResponse,
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

INPUT_ITEM_TO_RESOURCE_FIELD = {
    "video": "video_ids",
    "copywriting": "copywriting_ids",
    "cover": "cover_ids",
    "audio": "audio_ids",
    "topic": "topic_ids",
}
SELECTED_MEDIA_WRITE_MATERIAL_TYPES = frozenset({"video", "audio"})

INPUT_STATE_FIELD_NAMES = (
    "profile_id",
    "input_items",
)

DUPLICATE_EXECUTION_LIMITATION_REASON = (
    "当前作品定义包含重复素材实例，作品本身有效，但当前执行路径暂不支持将同一素材重复编排到任务资源集合中。"
)


_UNSET = object()


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
        keyword: Optional[str] = None,
        status: Optional[CreativeStatus] = None,
        pool_state: Optional[CreativeWorkbenchPoolState] = None,
        sort: CreativeWorkbenchSort = CreativeWorkbenchSort.UPDATED_DESC,
        recent_failures_only: bool = False,
    ) -> CreativeWorkbenchListResponse:
        result = await self.db.execute(
            select(CreativeItem)
            .order_by(CreativeItem.updated_at.desc(), CreativeItem.id.desc())
            .options(
                selectinload(CreativeItem.current_cover),
                selectinload(CreativeItem.input_items),
                selectinload(CreativeItem.input_profile),
                selectinload(CreativeItem.candidate_items),
                selectinload(CreativeItem.tasks).selectinload(Task.profile),
                selectinload(CreativeItem.publish_pool_items),
            )
        )
        all_items = [await self._build_workbench_item_response(item) for item in result.scalars().all()]
        summary = self._build_workbench_summary(all_items)
        filtered_items = self._filter_workbench_items(
            all_items,
            keyword=keyword,
            status=status,
            pool_state=pool_state,
            recent_failures_only=recent_failures_only,
        )
        sorted_items = self._sort_workbench_items(filtered_items, sort=sort)
        paginated_items = sorted_items[skip:skip + limit]
        return CreativeWorkbenchListResponse(
            total=len(filtered_items),
            items=paginated_items,
            summary=summary,
        )

    async def create_creative(self, payload: CreativeCreateRequest) -> CreativeDetailResponse:
        creative_no = payload.creative_no or await self._generate_creative_no()
        if await self._creative_no_exists(creative_no):
            raise ValueError("作品编号已存在")

        product_links_payload = await self._resolve_authoritative_product_links(
            existing_links=[],
            explicit_product_links=payload.product_links if "product_links" in payload.model_fields_set else None,
            compat_subject_product_id=payload.subject_product_id if "subject_product_id" in payload.model_fields_set else _UNSET,
        )
        candidate_items_payload = await self._resolve_authoritative_candidate_items(
            existing_items=[],
            explicit_candidate_items=payload.candidate_items if "candidate_items" in payload.model_fields_set else None,
        )
        primary_product_id = self._extract_primary_product_id(product_links_payload)
        adopted_cover_candidate = self._extract_adopted_candidate_item(candidate_items_payload, CreativeCandidateType.COVER.value)
        adopted_copywriting_candidate = self._extract_adopted_candidate_item(candidate_items_payload, CreativeCandidateType.COPYWRITING.value)
        product_truth = await self._resolve_current_product_truth(
            subject_product_id=primary_product_id,
            explicit_current_product_name=payload.current_product_name if "current_product_name" in payload.model_fields_set else _UNSET,
            explicit_product_name_mode=payload.product_name_mode.value if "product_name_mode" in payload.model_fields_set and payload.product_name_mode is not None else (None if "product_name_mode" in payload.model_fields_set else _UNSET),
            explicit_legacy_snapshot=payload.subject_product_name_snapshot if "subject_product_name_snapshot" in payload.model_fields_set else _UNSET,
            existing_current_product_name=None,
            existing_product_name_mode=None,
            existing_legacy_snapshot=None,
        )
        copywriting_truth = await self._resolve_current_copywriting_truth(
            explicit_current_copywriting_id=(
                payload.current_copywriting_id
                if "current_copywriting_id" in payload.model_fields_set
                else (adopted_copywriting_candidate["asset_id"] if adopted_copywriting_candidate is not None else _UNSET)
            ),
            explicit_current_copywriting_text=payload.current_copywriting_text if "current_copywriting_text" in payload.model_fields_set else _UNSET,
            explicit_copywriting_mode=(
                payload.copywriting_mode.value
                if "copywriting_mode" in payload.model_fields_set and payload.copywriting_mode is not None
                else (
                    None
                    if "copywriting_mode" in payload.model_fields_set
                    else ("adopted_candidate" if adopted_copywriting_candidate is not None else _UNSET)
                )
            ),
            explicit_legacy_text=payload.main_copywriting_text if "main_copywriting_text" in payload.model_fields_set else _UNSET,
            existing_current_copywriting_id=None,
            existing_current_copywriting_text=None,
            existing_copywriting_mode=None,
            existing_legacy_text=None,
        )
        cover_truth = await self._resolve_current_cover_truth(
            subject_product_id=primary_product_id,
            explicit_current_cover_asset_type=(
                payload.current_cover_asset_type.value
                if "current_cover_asset_type" in payload.model_fields_set and payload.current_cover_asset_type is not None
                else (None if "current_cover_asset_type" in payload.model_fields_set else ("cover" if adopted_cover_candidate is not None else _UNSET))
            ),
            explicit_current_cover_asset_id=(
                payload.current_cover_asset_id
                if "current_cover_asset_id" in payload.model_fields_set
                else (adopted_cover_candidate["asset_id"] if adopted_cover_candidate is not None else _UNSET)
            ),
            explicit_cover_mode=(
                payload.cover_mode.value
                if "cover_mode" in payload.model_fields_set and payload.cover_mode is not None
                else (
                    None
                    if "cover_mode" in payload.model_fields_set
                    else ("adopted_candidate" if adopted_cover_candidate is not None else _UNSET)
                )
            ),
            existing_current_cover_asset_type=None,
            existing_current_cover_asset_id=None,
            existing_cover_mode=None,
        )
        candidate_items_payload = self._synchronize_candidate_items_with_current_truth(
            candidate_items_payload,
            current_cover_asset_id=cover_truth["current_cover_asset_id"],
            cover_mode=cover_truth["cover_mode"],
            current_copywriting_id=copywriting_truth["current_copywriting_id"],
            copywriting_mode=copywriting_truth["copywriting_mode"],
        )
        creative = CreativeItem(
            creative_no=creative_no,
            title=payload.title,
            status=CreativeStatus.PENDING_INPUT.value,
            latest_version_no=0,
            subject_product_id=primary_product_id,
            subject_product_name_snapshot=product_truth["compat_snapshot"],
            main_copywriting_text=copywriting_truth["compat_text"],
            current_product_name=product_truth["current_product_name"],
            product_name_mode=product_truth["product_name_mode"],
            current_cover_asset_type=cover_truth["current_cover_asset_type"],
            current_cover_asset_id=cover_truth["current_cover_asset_id"],
            cover_mode=cover_truth["cover_mode"],
            current_copywriting_id=copywriting_truth["current_copywriting_id"],
            current_copywriting_text=copywriting_truth["current_copywriting_text"],
            copywriting_mode=copywriting_truth["copywriting_mode"],
            target_duration_seconds=payload.target_duration_seconds,
        )
        self.db.add(creative)
        await self.db.flush()
        self._apply_product_links(creative, product_links_payload)
        self._apply_candidate_items(creative, candidate_items_payload)

        input_profile_id, authoritative_input_items = self._resolve_authoritative_input_state(
            profile_id=payload.profile_id,
            current_input_items=[],
            explicit_input_items=payload.input_items if "input_items" in payload.model_fields_set else None,
        )
        await self._apply_authoritative_input_state(
            creative,
            profile_id=input_profile_id,
            input_items=authoritative_input_items,
            preserve_existing_non_media_rows="input_items" in payload.model_fields_set,
        )
        await self._sync_pre_compose_status(creative)
        await self.db.commit()
        runtime_input_state = self._resolve_runtime_input_state(creative)
        input_orchestration = self._build_input_orchestration_response(
            profile_id=runtime_input_state["profile_id"],
            input_items=self._build_input_items_response(
                creative,
                runtime_input_state=runtime_input_state,
            ),
        )
        logger.info(
            "event_name=creative_flow_entry_new creative_item_id={} orchestration_hash={} profile_id={} material_counts={} account_mode=creative_only",
            creative.id,
            input_orchestration.orchestration_hash,
            input_orchestration.profile_id,
            input_orchestration.material_counts.model_dump(),
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
        if "target_duration_seconds" in payload.model_fields_set:
            creative.target_duration_seconds = payload.target_duration_seconds

        next_product_links = await self._resolve_authoritative_product_links(
            existing_links=creative.product_links,
            explicit_product_links=payload.product_links if "product_links" in payload.model_fields_set else None,
            compat_subject_product_id=payload.subject_product_id if "subject_product_id" in payload.model_fields_set else _UNSET,
        )
        next_candidate_items = await self._resolve_authoritative_candidate_items(
            existing_items=creative.candidate_items,
            explicit_candidate_items=payload.candidate_items if "candidate_items" in payload.model_fields_set else None,
        )
        next_subject_product_id = self._extract_primary_product_id(next_product_links)
        adopted_cover_candidate = self._extract_adopted_candidate_item(next_candidate_items, CreativeCandidateType.COVER.value)
        adopted_copywriting_candidate = self._extract_adopted_candidate_item(next_candidate_items, CreativeCandidateType.COPYWRITING.value)
        if self._payload_updates_candidate_items(payload.model_fields_set):
            if (
                creative.cover_mode == "adopted_candidate"
                and creative.current_cover_asset_id is not None
                and adopted_cover_candidate is None
                and not any(field_name in payload.model_fields_set for field_name in ("current_cover_asset_type", "current_cover_asset_id", "cover_mode"))
            ):
                raise ValueError("请先切换当前封面，再移除已采用候选")
            if (
                creative.copywriting_mode == "adopted_candidate"
                and creative.current_copywriting_id is not None
                and adopted_copywriting_candidate is None
                and not any(field_name in payload.model_fields_set for field_name in ("current_copywriting_id", "current_copywriting_text", "copywriting_mode", "main_copywriting_text"))
            ):
                raise ValueError("请先切换当前文案，再移除已采用候选")
        if self._payload_updates_product_truth(payload.model_fields_set):
            product_truth = await self._resolve_current_product_truth(
                subject_product_id=next_subject_product_id,
                explicit_current_product_name=payload.current_product_name if "current_product_name" in payload.model_fields_set else _UNSET,
                explicit_product_name_mode=payload.product_name_mode.value if "product_name_mode" in payload.model_fields_set and payload.product_name_mode is not None else (None if "product_name_mode" in payload.model_fields_set else _UNSET),
                explicit_legacy_snapshot=payload.subject_product_name_snapshot if "subject_product_name_snapshot" in payload.model_fields_set else _UNSET,
                existing_current_product_name=creative.current_product_name,
                existing_product_name_mode=creative.product_name_mode,
                existing_legacy_snapshot=creative.subject_product_name_snapshot,
            )
            creative.subject_product_id = next_subject_product_id
            creative.current_product_name = product_truth["current_product_name"]
            creative.product_name_mode = product_truth["product_name_mode"]
            creative.subject_product_name_snapshot = product_truth["compat_snapshot"]
        elif self._payload_updates_product_links(payload.model_fields_set):
            creative.subject_product_id = next_subject_product_id

        if self._payload_updates_cover_truth(payload.model_fields_set):
            cover_truth = await self._resolve_current_cover_truth(
                subject_product_id=next_subject_product_id,
                explicit_current_cover_asset_type=(
                    payload.current_cover_asset_type.value
                    if "current_cover_asset_type" in payload.model_fields_set and payload.current_cover_asset_type is not None
                    else (None if "current_cover_asset_type" in payload.model_fields_set else ("cover" if adopted_cover_candidate is not None else _UNSET))
                ),
                explicit_current_cover_asset_id=(
                    payload.current_cover_asset_id
                    if "current_cover_asset_id" in payload.model_fields_set
                    else (adopted_cover_candidate["asset_id"] if adopted_cover_candidate is not None else _UNSET)
                ),
                explicit_cover_mode=(
                    payload.cover_mode.value
                    if "cover_mode" in payload.model_fields_set and payload.cover_mode is not None
                    else (
                        None
                        if "cover_mode" in payload.model_fields_set
                        else ("adopted_candidate" if adopted_cover_candidate is not None else _UNSET)
                    )
                ),
                existing_current_cover_asset_type=creative.current_cover_asset_type,
                existing_current_cover_asset_id=creative.current_cover_asset_id,
                existing_cover_mode=creative.cover_mode,
            )
            creative.current_cover_asset_type = cover_truth["current_cover_asset_type"]
            creative.current_cover_asset_id = cover_truth["current_cover_asset_id"]
            creative.cover_mode = cover_truth["cover_mode"]

        if self._payload_updates_product_links(payload.model_fields_set):
            self._apply_product_links(creative, next_product_links)

        if self._payload_updates_copywriting_truth(payload.model_fields_set):
            copywriting_truth = await self._resolve_current_copywriting_truth(
                explicit_current_copywriting_id=(
                    payload.current_copywriting_id
                    if "current_copywriting_id" in payload.model_fields_set
                    else (adopted_copywriting_candidate["asset_id"] if adopted_copywriting_candidate is not None else _UNSET)
                ),
                explicit_current_copywriting_text=payload.current_copywriting_text if "current_copywriting_text" in payload.model_fields_set else _UNSET,
                explicit_copywriting_mode=(
                    payload.copywriting_mode.value
                    if "copywriting_mode" in payload.model_fields_set and payload.copywriting_mode is not None
                    else (
                        None
                        if "copywriting_mode" in payload.model_fields_set
                        else ("adopted_candidate" if adopted_copywriting_candidate is not None else _UNSET)
                    )
                ),
                explicit_legacy_text=payload.main_copywriting_text if "main_copywriting_text" in payload.model_fields_set else _UNSET,
                existing_current_copywriting_id=creative.current_copywriting_id,
                existing_current_copywriting_text=creative.current_copywriting_text,
                existing_copywriting_mode=creative.copywriting_mode,
                existing_legacy_text=creative.main_copywriting_text,
            )
            creative.current_copywriting_id = copywriting_truth["current_copywriting_id"]
            creative.current_copywriting_text = copywriting_truth["current_copywriting_text"]
            creative.copywriting_mode = copywriting_truth["copywriting_mode"]
            creative.main_copywriting_text = copywriting_truth["compat_text"]

        should_sync_candidate_items = self._payload_updates_candidate_items(payload.model_fields_set) or (
            bool(creative.candidate_items)
            and any(
                field_name in payload.model_fields_set
                for field_name in (
                    "current_cover_asset_type",
                    "current_cover_asset_id",
                    "cover_mode",
                    "current_copywriting_id",
                    "current_copywriting_text",
                    "copywriting_mode",
                    "main_copywriting_text",
                )
            )
        )
        if should_sync_candidate_items:
            next_candidate_items = self._synchronize_candidate_items_with_current_truth(
                next_candidate_items,
                current_cover_asset_id=creative.current_cover_asset_id,
                cover_mode=creative.cover_mode,
                current_copywriting_id=creative.current_copywriting_id,
                copywriting_mode=creative.copywriting_mode,
            )
            self._apply_candidate_items(creative, next_candidate_items)

        if self._payload_updates_input_state(payload.model_fields_set):
            current_profile_id = (
                payload.profile_id
                if "profile_id" in payload.model_fields_set
                else creative.input_profile_id
            )
            current_input_items = self._extract_authoritative_input_items(creative)
            input_profile_id, authoritative_input_items = self._resolve_authoritative_input_state(
                profile_id=current_profile_id,
                current_input_items=current_input_items,
                explicit_input_items=payload.input_items if "input_items" in payload.model_fields_set else None,
            )
            await self._apply_authoritative_input_state(
                creative,
                profile_id=input_profile_id,
                input_items=authoritative_input_items,
                preserve_existing_non_media_rows="input_items" in payload.model_fields_set,
            )
        if (
            creative.current_version is not None
            and creative.status not in REVIEW_AND_BEYOND_STATUS_VALUES
            and creative.current_version.final_video_path is None
            and creative.current_version.actual_duration_seconds is None
        ):
            await self.version_service.sync_version_result(
                creative.current_version,
                actual_duration_seconds=None,
                final_video_path=None,
                final_product_name=creative.resolved_current_product_name(),
                final_copywriting_text=creative.resolved_current_copywriting_text(),
            )
            await self.version_service.sync_publish_package(
                creative.current_version,
                publish_profile_id=creative.input_profile_id,
                frozen_video_path=None,
                frozen_cover_path=await self._resolve_current_cover_path(creative),
                frozen_duration_seconds=creative.target_duration_seconds,
                frozen_product_name=creative.resolved_current_product_name(),
                frozen_copywriting_text=creative.resolved_current_copywriting_text(),
            )
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

        runtime_input_state = self._resolve_runtime_input_state(creative)
        execution_inputs = runtime_input_state["execution_inputs"]
        eligibility_status, eligibility_reasons = await self._build_eligibility_projection(
            creative,
            runtime_input_state=runtime_input_state,
        )
        if eligibility_status != CreativeEligibilityStatus.READY_TO_COMPOSE:
            detail = "；".join(eligibility_reasons) if eligibility_reasons else "当前作品输入尚未满足提交条件"
            raise ValueError(detail)

        profile = creative.__dict__.get("input_profile")
        if profile is None and runtime_input_state["profile_id"] is not None:
            profile = await self.db.get(PublishProfile, runtime_input_state["profile_id"])
        if profile is None:
            raise ValueError("所选合成配置不存在")
        if self._has_duplicate_execution_instances(creative, runtime_input_state=runtime_input_state):
            raise ValueError(DUPLICATE_EXECUTION_LIMITATION_REASON)

        expected_inputs = await self._build_expected_task_inputs(
            runtime_input_state=runtime_input_state,
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
                video_ids=execution_inputs["video_ids"],
                copywriting_ids=execution_inputs["copywriting_ids"],
                cover_ids=execution_inputs["cover_ids"],
                audio_ids=execution_inputs["audio_ids"],
                topic_ids=execution_inputs["topic_ids"],
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
                await self._sync_direct_publish_freeze_truth(
                    creative=creative,
                    version=version,
                    task=task,
                    profile=profile,
                )
                await self.db.commit()
            else:
                version = next(
                    (item for item in creative.versions if item.id == task.creative_version_id),
                    None,
                )
                if version is not None:
                    await self._sync_direct_publish_freeze_truth(
                        creative=creative,
                        version=version,
                        task=task,
                        profile=profile,
                    )
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
                selectinload(CreativeItem.current_cover),
                selectinload(CreativeItem.input_items),
                selectinload(CreativeItem.input_profile),
                selectinload(CreativeItem.product_links).selectinload(CreativeProductLink.product),
                selectinload(CreativeItem.candidate_items),
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
        active_pool_item = self._pick_active_pool_item(creative.publish_pool_items)
        pool_state = self._get_creative_workbench_pool_state(
            creative.current_version_id,
            active_pool_item,
        )
        summary_projection = await self._build_workbench_summary_projection(
            creative,
            projection=projection,
        )
        return CreativeWorkbenchItemResponse(
            id=creative.id,
            creative_no=creative.creative_no,
            title=creative.title,
            status=projection["status"],
            current_version_id=creative.current_version_id,
            subject_product_id=creative.subject_product_id,
            subject_product_name_snapshot=creative.resolved_current_product_name(),
            main_copywriting_text=creative.resolved_current_copywriting_text(),
            current_product_name=creative.resolved_current_product_name(),
            current_cover_thumb=summary_projection["current_cover_thumb"],
            current_copy_excerpt=summary_projection["current_copy_excerpt"],
            product_name_mode=creative.resolved_product_name_mode(),
            current_cover_asset_type=creative.resolved_current_cover_asset_type(),
            current_cover_asset_id=creative.current_cover_asset_id,
            cover_mode=creative.resolved_cover_mode(),
            current_copywriting_id=creative.resolved_current_copywriting_id(),
            current_copywriting_text=creative.resolved_current_copywriting_text(),
            copywriting_mode=creative.resolved_copywriting_mode(),
            target_duration_seconds=creative.target_duration_seconds,
            selected_video_count=summary_projection["selected_video_count"],
            selected_audio_count=summary_projection["selected_audio_count"],
            candidate_video_count=summary_projection["candidate_video_count"],
            candidate_audio_count=summary_projection["candidate_audio_count"],
            candidate_cover_count=summary_projection["candidate_cover_count"],
            definition_ready=summary_projection["definition_ready"],
            composition_ready=summary_projection["composition_ready"],
            missing_required_fields=summary_projection["missing_required_fields"],
            input_items=projection["input_items"],
            input_orchestration=projection["input_orchestration"],
            generation_error_msg=creative.generation_error_msg,
            generation_failed_at=creative.generation_failed_at,
            pool_state=pool_state,
            active_pool_item_id=active_pool_item.id if active_pool_item is not None else None,
            active_pool_version_id=active_pool_item.creative_version_id if active_pool_item is not None else None,
            active_pool_aligned=(
                active_pool_item is not None
                and active_pool_item.creative_version_id == creative.current_version_id
            ),
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
            product_links=self._build_product_links_response(creative),
            candidate_items=await self._build_candidate_items_response(creative),
            subject_product_id=creative.subject_product_id,
            subject_product_name_snapshot=creative.resolved_current_product_name(),
            main_copywriting_text=creative.resolved_current_copywriting_text(),
            current_product_name=creative.resolved_current_product_name(),
            product_name_mode=creative.resolved_product_name_mode(),
            current_cover_asset_type=creative.resolved_current_cover_asset_type(),
            current_cover_asset_id=creative.current_cover_asset_id,
            cover_mode=creative.resolved_cover_mode(),
            current_copywriting_id=creative.resolved_current_copywriting_id(),
            current_copywriting_text=creative.resolved_current_copywriting_text(),
            copywriting_mode=creative.resolved_copywriting_mode(),
            target_duration_seconds=creative.target_duration_seconds,
            input_items=projection["input_items"],
            input_orchestration=projection["input_orchestration"],
            generation_error_msg=creative.generation_error_msg,
            generation_failed_at=creative.generation_failed_at,
            eligibility_status=projection["eligibility_status"],
            eligibility_reasons=projection["eligibility_reasons"],
            latest_task_summary=projection["latest_task_summary"],
            created_at=creative.created_at,
            updated_at=creative.updated_at,
        )

    async def _build_projection(self, creative: CreativeItem) -> dict[str, Any]:
        runtime_input_state = self._resolve_runtime_input_state(creative)
        input_items = self._build_input_items_response(
            creative,
            runtime_input_state=runtime_input_state,
        )
        input_orchestration = self._build_input_orchestration_response(
            profile_id=runtime_input_state["profile_id"],
            input_items=input_items,
        )
        eligibility_status, eligibility_reasons = await self._build_eligibility_projection(
            creative,
            runtime_input_state=runtime_input_state,
        )
        latest_task_summary = self._build_latest_task_summary(self._pick_latest_task(creative.tasks))
        status = self._project_creative_status(
            creative,
            eligibility_status=eligibility_status,
        )
        return {
            "status": status,
            "input_items": input_items,
            "input_orchestration": input_orchestration,
            "eligibility_status": eligibility_status,
            "eligibility_reasons": eligibility_reasons,
            "latest_task_summary": latest_task_summary,
        }

    async def _build_workbench_summary_projection(
        self,
        creative: CreativeItem,
        *,
        projection: dict[str, Any],
    ) -> dict[str, Any]:
        current_product_name = creative.resolved_current_product_name()
        current_copywriting_text = creative.resolved_current_copywriting_text()
        current_cover_thumb = await self._resolve_current_cover_path(creative)
        selected_media_counts = self._build_selected_media_counts(projection["input_items"])
        candidate_counts = self._build_candidate_media_counts(creative.candidate_items)
        missing_required_fields = self._build_workbench_missing_required_fields(
            creative,
            selected_video_count=selected_media_counts["selected_video_count"],
            input_profile_id=projection["input_orchestration"].profile_id,
        )
        definition_ready = all(
            field not in missing_required_fields
            for field in (
                "current_product_name",
                "current_cover",
                "current_copywriting",
                "selected_video",
            )
        )
        composition_ready = projection["eligibility_status"] == CreativeEligibilityStatus.READY_TO_COMPOSE
        return {
            "current_cover_thumb": current_cover_thumb,
            "current_copy_excerpt": self._build_workbench_copy_excerpt(current_copywriting_text),
            **selected_media_counts,
            **candidate_counts,
            "definition_ready": definition_ready,
            "composition_ready": composition_ready,
            "missing_required_fields": missing_required_fields,
        }

    def _build_selected_media_counts(
        self,
        input_items: list[CreativeInputItemResponse],
    ) -> dict[str, int]:
        selected_video_count = sum(
            1
            for item in input_items
            if item.enabled and item.material_type == "video"
        )
        selected_audio_count = sum(
            1
            for item in input_items
            if item.enabled and item.material_type == "audio"
        )
        return {
            "selected_video_count": selected_video_count,
            "selected_audio_count": selected_audio_count,
        }

    def _build_candidate_media_counts(
        self,
        candidate_items: list[CreativeCandidateItem],
    ) -> dict[str, int]:
        active_candidate_items = [
            item
            for item in candidate_items
            if item.enabled and item.status != CreativeCandidateStatus.DISMISSED.value
        ]
        return {
            "candidate_video_count": sum(
                1 for item in active_candidate_items if item.candidate_type == CreativeCandidateType.VIDEO.value
            ),
            "candidate_audio_count": sum(
                1 for item in active_candidate_items if item.candidate_type == CreativeCandidateType.AUDIO.value
            ),
            "candidate_cover_count": sum(
                1 for item in active_candidate_items if item.candidate_type == CreativeCandidateType.COVER.value
            ),
        }

    def _build_workbench_missing_required_fields(
        self,
        creative: CreativeItem,
        *,
        selected_video_count: int,
        input_profile_id: Optional[int],
    ) -> list[str]:
        missing_fields: list[str] = []
        if not self._has_display_text(creative.resolved_current_product_name()):
            missing_fields.append("current_product_name")
        if creative.resolved_current_cover_asset_type() is None or creative.current_cover_asset_id is None:
            missing_fields.append("current_cover")
        if not self._has_display_text(creative.resolved_current_copywriting_text()):
            missing_fields.append("current_copywriting")
        if selected_video_count <= 0:
            missing_fields.append("selected_video")
        if input_profile_id is None:
            missing_fields.append("input_profile")
        return missing_fields

    def _build_workbench_copy_excerpt(self, value: Optional[str], *, max_length: int = 80) -> Optional[str]:
        if not self._has_display_text(value):
            return None
        normalized = " ".join((value or "").strip().split())
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 1].rstrip()}…"

    def _has_display_text(self, value: Optional[str]) -> bool:
        return bool(value and value.strip())

    async def _build_eligibility_projection(
        self,
        creative: CreativeItem,
        *,
        runtime_input_state: dict[str, Any],
    ) -> tuple[CreativeEligibilityStatus, list[str]]:
        pending_reasons: list[str] = []
        invalid_reasons: list[str] = []
        execution_inputs = runtime_input_state["execution_inputs"]

        profile = creative.__dict__.get("input_profile")
        if runtime_input_state["profile_id"] is None:
            pending_reasons.append("请选择合成配置")
        elif profile is None:
            profile = await self.db.get(PublishProfile, runtime_input_state["profile_id"])
            if profile is None:
                invalid_reasons.append("所选合成配置不存在")

        if not execution_inputs["video_ids"]:
            pending_reasons.append("至少选择 1 个视频")

        resource_errors = await self._validate_runtime_resource_ids(runtime_input_state)
        invalid_reasons.extend(resource_errors)

        if profile is not None and not invalid_reasons and not pending_reasons:
            try:
                validate_task_resource_inputs(
                    video_ids=execution_inputs["video_ids"],
                    copywriting_ids=execution_inputs["copywriting_ids"],
                    cover_ids=execution_inputs["cover_ids"],
                    audio_ids=execution_inputs["audio_ids"],
                    composition_mode=profile.composition_mode,
                )
            except TaskSemanticsError as exc:
                invalid_reasons.append(str(exc))
        if self._has_duplicate_execution_instances(creative, runtime_input_state=runtime_input_state):
            invalid_reasons.append(DUPLICATE_EXECUTION_LIMITATION_REASON)

        reasons = [*pending_reasons, *invalid_reasons]
        if invalid_reasons:
            return CreativeEligibilityStatus.INVALID, reasons
        if pending_reasons:
            return CreativeEligibilityStatus.PENDING_INPUT, reasons
        return CreativeEligibilityStatus.READY_TO_COMPOSE, []

    async def _validate_runtime_resource_ids(
        self,
        runtime_input_state: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        execution_inputs = runtime_input_state["execution_inputs"]
        checks = [
            ("视频", Video, execution_inputs["video_ids"]),
            ("文案", Copywriting, execution_inputs["copywriting_ids"]),
            ("封面", Cover, execution_inputs["cover_ids"]),
            ("音频", Audio, execution_inputs["audio_ids"]),
            ("话题", Topic, execution_inputs["topic_ids"]),
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

    def _pick_active_pool_item(
        self,
        pool_items: list[PublishPoolItem],
    ) -> Optional[PublishPoolItem]:
        active_items = [item for item in pool_items if item.status == "active"]
        if not active_items:
            return None
        return max(active_items, key=lambda item: (item.updated_at, item.id))

    def _get_creative_workbench_pool_state(
        self,
        current_version_id: Optional[int],
        active_pool_item: Optional[PublishPoolItem],
    ) -> CreativeWorkbenchPoolState:
        if active_pool_item is None:
            return CreativeWorkbenchPoolState.OUT_POOL
        if active_pool_item.creative_version_id == current_version_id:
            return CreativeWorkbenchPoolState.IN_POOL
        return CreativeWorkbenchPoolState.VERSION_MISMATCH

    def _has_recent_failure(self, item: CreativeWorkbenchItemResponse) -> bool:
        return bool(
            item.generation_error_msg
            or item.status == CreativeStatus.FAILED
            or item.generation_failed_at is not None
        )

    def _get_attention_score(self, item: CreativeWorkbenchItemResponse) -> int:
        score = 0

        if self._has_recent_failure(item):
            score += 400

        if item.status == CreativeStatus.REWORK_REQUIRED:
            score += 300

        if item.status == CreativeStatus.WAITING_REVIEW:
            score += 200

        if item.pool_state == CreativeWorkbenchPoolState.VERSION_MISMATCH:
            score += 100

        return score

    def _build_workbench_summary(
        self,
        items: list[CreativeWorkbenchItemResponse],
    ) -> CreativeWorkbenchSummaryResponse:
        return CreativeWorkbenchSummaryResponse(
            all_count=len(items),
            waiting_review_count=sum(1 for item in items if item.status == CreativeStatus.WAITING_REVIEW),
            pending_input_count=sum(1 for item in items if item.status == CreativeStatus.PENDING_INPUT),
            needs_rework_count=sum(1 for item in items if item.status == CreativeStatus.REWORK_REQUIRED),
            recent_failures_count=sum(1 for item in items if self._has_recent_failure(item)),
            active_pool_count=sum(1 for item in items if item.active_pool_item_id is not None),
            aligned_pool_count=sum(1 for item in items if item.pool_state == CreativeWorkbenchPoolState.IN_POOL),
            version_mismatch_count=sum(
                1 for item in items if item.pool_state == CreativeWorkbenchPoolState.VERSION_MISMATCH
            ),
            selected_video_count=sum(item.selected_video_count for item in items),
            selected_audio_count=sum(item.selected_audio_count for item in items),
            candidate_video_count=sum(item.candidate_video_count for item in items),
            candidate_audio_count=sum(item.candidate_audio_count for item in items),
            candidate_cover_count=sum(item.candidate_cover_count for item in items),
            definition_ready_count=sum(1 for item in items if item.definition_ready),
            composition_ready_count=sum(1 for item in items if item.composition_ready),
        )

    def _filter_workbench_items(
        self,
        items: list[CreativeWorkbenchItemResponse],
        *,
        keyword: Optional[str],
        status: Optional[CreativeStatus],
        pool_state: Optional[CreativeWorkbenchPoolState],
        recent_failures_only: bool,
    ) -> list[CreativeWorkbenchItemResponse]:
        normalized_keyword = keyword.strip().lower() if keyword else None
        filtered_items: list[CreativeWorkbenchItemResponse] = []

        for item in items:
            if normalized_keyword is not None:
                haystack = " ".join(filter(None, [item.title, item.creative_no])).lower()
                if normalized_keyword not in haystack:
                    continue

            if status is not None and item.status != status:
                continue

            if pool_state is not None and item.pool_state != pool_state:
                continue

            if recent_failures_only and not self._has_recent_failure(item):
                continue

            filtered_items.append(item)

        return filtered_items

    def _sort_workbench_items(
        self,
        items: list[CreativeWorkbenchItemResponse],
        *,
        sort: CreativeWorkbenchSort,
    ) -> list[CreativeWorkbenchItemResponse]:
        if sort == CreativeWorkbenchSort.UPDATED_ASC:
            return sorted(items, key=lambda item: (item.updated_at, item.id))

        if sort == CreativeWorkbenchSort.ATTENTION_DESC:
            return sorted(
                items,
                key=lambda item: (
                    self._get_attention_score(item),
                    item.updated_at,
                    item.id,
                ),
                reverse=True,
            )

        if sort == CreativeWorkbenchSort.FAILED_DESC:
            return sorted(
                items,
                key=lambda item: (
                    self._has_recent_failure(item),
                    item.generation_failed_at or item.updated_at,
                    item.updated_at,
                    item.id,
                ),
                reverse=True,
            )

        return sorted(items, key=lambda item: (item.updated_at, item.id), reverse=True)

    def _build_input_items_response(
        self,
        creative: CreativeItem,
        *,
        runtime_input_state: Optional[dict[str, Any]] = None,
    ) -> list[CreativeInputItemResponse]:
        resolved_runtime_input_state = runtime_input_state or self._resolve_runtime_input_state(creative)
        authoritative_input_items = resolved_runtime_input_state["input_items"]
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

    def _build_input_orchestration_response(
        self,
        *,
        profile_id: Optional[int],
        input_items: list[CreativeInputItemResponse],
    ) -> CreativeInputOrchestrationResponse:
        material_counts = self._empty_material_counts()
        enabled_material_counts = self._empty_material_counts()
        canonical_items: list[dict[str, Any]] = []

        for item in input_items:
            material_type = item.material_type.value
            material_counts[material_type] += 1
            if item.enabled:
                enabled_material_counts[material_type] += 1
            canonical_items.append(
                {
                    "material_type": material_type,
                    "material_id": item.material_id,
                    "role": item.role,
                    "sequence": item.sequence,
                    "instance_no": item.instance_no,
                    "trim_in": item.trim_in,
                    "trim_out": item.trim_out,
                    "slot_duration_seconds": item.slot_duration_seconds,
                    "enabled": item.enabled,
                }
            )

        return CreativeInputOrchestrationResponse(
            profile_id=profile_id,
            orchestration_hash=self._build_orchestration_hash(
                profile_id=profile_id,
                input_items=canonical_items,
            ),
            item_count=len(canonical_items),
            enabled_item_count=sum(1 for item in canonical_items if item["enabled"]),
            material_counts=CreativeInputMaterialCountsResponse(**material_counts),
            enabled_material_counts=CreativeInputMaterialCountsResponse(**enabled_material_counts),
        )

    def _build_product_links_response(
        self,
        creative: CreativeItem,
    ) -> list[CreativeProductLinkResponse]:
        return [
            CreativeProductLinkResponse(
                id=link.id,
                product_id=link.product_id,
                product_name=link.product.name if link.product is not None else None,
                sort_order=link.sort_order,
                is_primary=link.is_primary,
                enabled=link.enabled,
                source_mode=link.source_mode,
            )
            for link in sorted(creative.product_links, key=lambda item: (item.sort_order, item.id or 0))
        ]

    async def _resolve_authoritative_product_links(
        self,
        *,
        existing_links: list[CreativeProductLink],
        explicit_product_links: Optional[list[Any]],
        compat_subject_product_id: Any,
    ) -> list[dict[str, Any]]:
        if explicit_product_links is not None:
            normalized_links = self._serialize_product_link_payloads(explicit_product_links)
        elif compat_subject_product_id is not _UNSET:
            normalized_links = self._normalize_product_links_from_compat_subject(
                existing_links=existing_links,
                compat_subject_product_id=compat_subject_product_id,
            )
        else:
            normalized_links = self._serialize_existing_product_links(existing_links)

        if normalized_links:
            primary_count = sum(1 for link in normalized_links if link["is_primary"])
            if primary_count == 0:
                normalized_links[0]["is_primary"] = True
            elif primary_count > 1:
                raise ValueError("product_links ????? 1 ?????")

        product_ids = [link["product_id"] for link in normalized_links]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("product_links ???????")

        await self._assert_products_exist(product_ids)
        return normalized_links

    def _normalize_product_links_from_compat_subject(
        self,
        *,
        existing_links: list[CreativeProductLink],
        compat_subject_product_id: Optional[int],
    ) -> list[dict[str, Any]]:
        if compat_subject_product_id is None:
            return []

        normalized_links = self._serialize_existing_product_links(existing_links)
        for index, link in enumerate(normalized_links, start=1):
            link["sort_order"] = index
            link["is_primary"] = int(link["product_id"]) == int(compat_subject_product_id)
        if any(link["is_primary"] for link in normalized_links):
            return normalized_links
        normalized_links.append(
            {
                "product_id": int(compat_subject_product_id),
                "sort_order": len(normalized_links) + 1,
                "is_primary": True,
                "enabled": True,
                "source_mode": "import_bootstrap",
            }
        )
        return normalized_links

    def _serialize_existing_product_links(
        self,
        existing_links: list[CreativeProductLink],
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_product_link_payload(
                product_id=link.product_id,
                sort_order=link.sort_order,
                is_primary=link.is_primary,
                enabled=link.enabled,
                source_mode=link.source_mode,
            )
            for link in sorted(existing_links, key=lambda item: (item.sort_order, item.id or 0))
        ]

    def _serialize_product_link_payloads(
        self,
        product_links: list[Any],
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_product_link_payload(
                product_id=link.product_id,
                sort_order=index + 1,
                is_primary=link.is_primary,
                enabled=link.enabled,
                source_mode=link.source_mode,
            )
            for index, link in enumerate(product_links)
        ]

    def _serialize_product_link_payload(
        self,
        *,
        product_id: Any,
        sort_order: Any,
        is_primary: Any,
        enabled: Any,
        source_mode: Any,
    ) -> dict[str, Any]:
        normalized_source_mode = (
            source_mode.value
            if getattr(source_mode, "value", None) is not None
            else str(source_mode or "manual_add")
        )
        return {
            "product_id": int(product_id),
            "sort_order": int(sort_order),
            "is_primary": bool(is_primary),
            "enabled": bool(enabled),
            "source_mode": normalized_source_mode,
        }

    async def _assert_products_exist(self, product_ids: list[int]) -> None:
        if not product_ids:
            return
        result = await self.db.execute(select(Product.id).where(Product.id.in_(product_ids)))
        existing_ids = set(result.scalars().all())
        if len(existing_ids) != len(set(product_ids)):
            raise ValueError("???????")

    def _extract_primary_product_id(self, product_links: list[dict[str, Any]]) -> Optional[int]:
        for link in product_links:
            if link["is_primary"]:
                return int(link["product_id"])
        return None

    def _apply_product_links(
        self,
        creative: CreativeItem,
        product_links: list[dict[str, Any]],
    ) -> None:
        if "product_links" not in creative.__dict__:
            set_committed_value(creative, "product_links", [])
        existing_links = creative.product_links
        existing_links_by_product_id = {int(link.product_id): link for link in existing_links}
        next_product_ids = {int(link["product_id"]) for link in product_links}

        for existing_link in list(existing_links):
            if int(existing_link.product_id) not in next_product_ids:
                creative.product_links.remove(existing_link)

        for index, link_payload in enumerate(product_links, start=1):
            product_id = int(link_payload["product_id"])
            existing_link = existing_links_by_product_id.get(product_id)
            if existing_link is None:
                creative.product_links.append(
                    CreativeProductLink(
                        creative_item_id=creative.id,
                        product_id=product_id,
                        sort_order=index,
                        is_primary=bool(link_payload["is_primary"]),
                        enabled=bool(link_payload["enabled"]),
                        source_mode=str(link_payload["source_mode"] or "manual_add"),
                    )
                )
                continue

            existing_link.sort_order = index
            existing_link.is_primary = bool(link_payload["is_primary"])
            existing_link.enabled = bool(link_payload["enabled"])
            existing_link.source_mode = str(link_payload["source_mode"] or "manual_add")

    async def _build_candidate_items_response(
        self,
        creative: CreativeItem,
    ) -> list[CreativeCandidateItemResponse]:
        candidate_items = sorted(creative.candidate_items, key=lambda item: (item.sort_order, item.id or 0))
        asset_maps = await self._load_candidate_asset_maps(candidate_items)
        product_name_by_id = await self._load_product_name_map(
            [
                item.source_product_id
                for item in candidate_items
                if item.source_product_id is not None
            ]
        )
        return [
            CreativeCandidateItemResponse(
                id=item.id,
                candidate_type=item.candidate_type,
                asset_id=item.asset_id,
                asset_name=asset_maps[item.candidate_type].get(item.asset_id, {}).get("name"),
                asset_excerpt=asset_maps[item.candidate_type].get(item.asset_id, {}).get("excerpt"),
                source_kind=item.source_kind,
                source_product_id=item.source_product_id,
                source_product_name=product_name_by_id.get(item.source_product_id),
                source_ref=item.source_ref,
                sort_order=item.sort_order,
                enabled=item.enabled,
                status=item.status,
            )
            for item in candidate_items
        ]

    async def _resolve_authoritative_candidate_items(
        self,
        *,
        existing_items: list[CreativeCandidateItem],
        explicit_candidate_items: Optional[list[Any]],
    ) -> list[dict[str, Any]]:
        if explicit_candidate_items is not None:
            normalized_items = self._serialize_candidate_item_payloads(explicit_candidate_items)
        else:
            normalized_items = self._serialize_existing_candidate_items(existing_items)

        candidate_keys = [
            (item["candidate_type"], item["asset_id"])
            for item in normalized_items
        ]
        if len(candidate_keys) != len(set(candidate_keys)):
            raise ValueError("candidate_items 不允许同类型资产重复")

        adopted_counts: dict[str, int] = {}
        for item in normalized_items:
            if item["status"] != CreativeCandidateStatus.ADOPTED.value:
                continue
            adopted_counts[item["candidate_type"]] = adopted_counts.get(item["candidate_type"], 0) + 1
            if item["candidate_type"] not in {
                CreativeCandidateType.COVER.value,
                CreativeCandidateType.COPYWRITING.value,
            }:
                raise ValueError("当前 Slice 仅支持采用封面或文案候选")

        if any(count > 1 for count in adopted_counts.values()):
            raise ValueError("同类型候选最多只能有 1 个 adopted")

        await self._assert_candidate_assets_exist(normalized_items)
        return normalized_items

    def _serialize_existing_candidate_items(
        self,
        existing_items: list[CreativeCandidateItem],
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_candidate_item_payload(
                candidate_type=item.candidate_type,
                asset_id=item.asset_id,
                source_kind=item.source_kind,
                source_product_id=item.source_product_id,
                source_ref=item.source_ref,
                sort_order=item.sort_order,
                enabled=item.enabled,
                status=item.status,
            )
            for item in sorted(existing_items, key=lambda entry: (entry.sort_order, entry.id or 0))
        ]

    def _serialize_candidate_item_payloads(
        self,
        candidate_items: list[Any],
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_candidate_item_payload(
                candidate_type=item.candidate_type,
                asset_id=item.asset_id,
                source_kind=item.source_kind,
                source_product_id=getattr(item, "source_product_id", None),
                source_ref=getattr(item, "source_ref", None),
                sort_order=index + 1,
                enabled=item.enabled,
                status=item.status,
            )
            for index, item in enumerate(candidate_items)
        ]

    def _serialize_candidate_item_payload(
        self,
        *,
        candidate_type: Any,
        asset_id: Any,
        source_kind: Any,
        source_product_id: Any,
        source_ref: Any,
        sort_order: Any,
        enabled: Any,
        status: Any,
    ) -> dict[str, Any]:
        normalized_candidate_type = (
            candidate_type.value
            if getattr(candidate_type, "value", None) is not None
            else str(candidate_type)
        )
        normalized_source_kind = (
            source_kind.value
            if getattr(source_kind, "value", None) is not None
            else str(source_kind or "material_library")
        )
        normalized_status = (
            status.value
            if getattr(status, "value", None) is not None
            else str(status or CreativeCandidateStatus.CANDIDATE.value)
        )
        return {
            "candidate_type": normalized_candidate_type,
            "asset_id": int(asset_id),
            "source_kind": normalized_source_kind,
            "source_product_id": int(source_product_id) if source_product_id is not None else None,
            "source_ref": str(source_ref) if source_ref is not None else None,
            "sort_order": int(sort_order),
            "enabled": bool(enabled),
            "status": normalized_status,
        }

    async def _assert_candidate_assets_exist(
        self,
        candidate_items: list[dict[str, Any]],
    ) -> None:
        for item in candidate_items:
            candidate_type = item["candidate_type"]
            asset_id = int(item["asset_id"])
            if candidate_type == CreativeCandidateType.COVER.value:
                await self._assert_cover_exists(asset_id)
            elif candidate_type == CreativeCandidateType.COPYWRITING.value:
                copywriting = await self.db.get(Copywriting, asset_id)
                if copywriting is None:
                    raise ValueError("所选文案不存在")
            elif candidate_type == CreativeCandidateType.VIDEO.value:
                video = await self.db.get(Video, asset_id)
                if video is None:
                    raise ValueError("所选视频不存在")
            elif candidate_type == CreativeCandidateType.AUDIO.value:
                audio = await self.db.get(Audio, asset_id)
                if audio is None:
                    raise ValueError("所选音频不存在")
            else:
                raise ValueError(f"暂不支持的 candidate_type: {candidate_type}")

            source_product_id = item["source_product_id"]
            if source_product_id is not None:
                product = await self.db.get(Product, source_product_id)
                if product is None:
                    raise ValueError("候选来源商品不存在")

    async def _load_candidate_asset_maps(
        self,
        candidate_items: list[CreativeCandidateItem],
    ) -> dict[str, dict[int, dict[str, Optional[str]]]]:
        asset_ids_by_type: dict[str, set[int]] = {
            CreativeCandidateType.COVER.value: set(),
            CreativeCandidateType.COPYWRITING.value: set(),
            CreativeCandidateType.VIDEO.value: set(),
            CreativeCandidateType.AUDIO.value: set(),
        }
        for item in candidate_items:
            if item.candidate_type in asset_ids_by_type:
                asset_ids_by_type[item.candidate_type].add(item.asset_id)

        asset_maps: dict[str, dict[int, dict[str, Optional[str]]]] = {
            candidate_type: {}
            for candidate_type in asset_ids_by_type
        }
        if asset_ids_by_type[CreativeCandidateType.COVER.value]:
            rows = await self.db.execute(
                select(Cover.id, Cover.name).where(Cover.id.in_(asset_ids_by_type[CreativeCandidateType.COVER.value]))
            )
            asset_maps[CreativeCandidateType.COVER.value] = {
                row[0]: {"name": row[1] or f"封面 #{row[0]}", "excerpt": None}
                for row in rows.all()
            }
        if asset_ids_by_type[CreativeCandidateType.COPYWRITING.value]:
            rows = await self.db.execute(
                select(Copywriting.id, Copywriting.name, Copywriting.content).where(
                    Copywriting.id.in_(asset_ids_by_type[CreativeCandidateType.COPYWRITING.value])
                )
            )
            asset_maps[CreativeCandidateType.COPYWRITING.value] = {
                row[0]: {
                    "name": row[1] or f"文案 #{row[0]}",
                    "excerpt": row[2],
                }
                for row in rows.all()
            }
        if asset_ids_by_type[CreativeCandidateType.VIDEO.value]:
            rows = await self.db.execute(
                select(Video.id, Video.name).where(Video.id.in_(asset_ids_by_type[CreativeCandidateType.VIDEO.value]))
            )
            asset_maps[CreativeCandidateType.VIDEO.value] = {
                row[0]: {"name": row[1] or f"视频 #{row[0]}", "excerpt": None}
                for row in rows.all()
            }
        if asset_ids_by_type[CreativeCandidateType.AUDIO.value]:
            rows = await self.db.execute(
                select(Audio.id, Audio.name).where(Audio.id.in_(asset_ids_by_type[CreativeCandidateType.AUDIO.value]))
            )
            asset_maps[CreativeCandidateType.AUDIO.value] = {
                row[0]: {"name": row[1] or f"音频 #{row[0]}", "excerpt": None}
                for row in rows.all()
            }
        return asset_maps

    async def _load_product_name_map(
        self,
        product_ids: list[Optional[int]],
    ) -> dict[int, str]:
        normalized_ids = {product_id for product_id in product_ids if product_id is not None}
        if not normalized_ids:
            return {}
        result = await self.db.execute(select(Product.id, Product.name).where(Product.id.in_(normalized_ids)))
        return {row[0]: row[1] for row in result.all()}

    def _extract_adopted_candidate_item(
        self,
        candidate_items: list[dict[str, Any]],
        candidate_type: str,
    ) -> Optional[dict[str, Any]]:
        return next(
            (
                item
                for item in candidate_items
                if item["candidate_type"] == candidate_type
                and item["status"] == CreativeCandidateStatus.ADOPTED.value
                and item["enabled"]
            ),
            None,
        )

    def _synchronize_candidate_items_with_current_truth(
        self,
        candidate_items: list[dict[str, Any]],
        *,
        current_cover_asset_id: Optional[int],
        cover_mode: Optional[str],
        current_copywriting_id: Optional[int],
        copywriting_mode: Optional[str],
    ) -> list[dict[str, Any]]:
        synchronized_items: list[dict[str, Any]] = []
        for item in candidate_items:
            next_item = dict(item)
            if item["candidate_type"] == CreativeCandidateType.COVER.value and item["status"] != CreativeCandidateStatus.DISMISSED.value:
                next_item["status"] = (
                    CreativeCandidateStatus.ADOPTED.value
                    if cover_mode == "adopted_candidate" and current_cover_asset_id == item["asset_id"]
                    else CreativeCandidateStatus.CANDIDATE.value
                )
            elif item["candidate_type"] == CreativeCandidateType.COPYWRITING.value and item["status"] != CreativeCandidateStatus.DISMISSED.value:
                next_item["status"] = (
                    CreativeCandidateStatus.ADOPTED.value
                    if copywriting_mode == "adopted_candidate" and current_copywriting_id == item["asset_id"]
                    else CreativeCandidateStatus.CANDIDATE.value
                )
            synchronized_items.append(next_item)
        return synchronized_items

    def _apply_candidate_items(
        self,
        creative: CreativeItem,
        candidate_items: list[dict[str, Any]],
    ) -> None:
        if "candidate_items" not in creative.__dict__:
            set_committed_value(creative, "candidate_items", [])
        existing_items = creative.candidate_items
        existing_items_by_key = {
            (item.candidate_type, int(item.asset_id)): item
            for item in existing_items
        }
        next_keys = {
            (item["candidate_type"], int(item["asset_id"]))
            for item in candidate_items
        }

        for existing_item in list(existing_items):
            if (existing_item.candidate_type, int(existing_item.asset_id)) not in next_keys:
                creative.candidate_items.remove(existing_item)

        for index, item_payload in enumerate(candidate_items, start=1):
            item_key = (item_payload["candidate_type"], int(item_payload["asset_id"]))
            existing_item = existing_items_by_key.get(item_key)
            if existing_item is None:
                creative.candidate_items.append(
                    CreativeCandidateItem(
                        creative_item_id=creative.id,
                        candidate_type=item_payload["candidate_type"],
                        asset_id=int(item_payload["asset_id"]),
                        source_kind=item_payload["source_kind"],
                        source_product_id=item_payload["source_product_id"],
                        source_ref=item_payload["source_ref"],
                        sort_order=index,
                        enabled=bool(item_payload["enabled"]),
                        status=item_payload["status"],
                    )
                )
                continue

            existing_item.source_kind = item_payload["source_kind"]
            existing_item.source_product_id = item_payload["source_product_id"]
            existing_item.source_ref = item_payload["source_ref"]
            existing_item.sort_order = index
            existing_item.enabled = bool(item_payload["enabled"])
            existing_item.status = item_payload["status"]

    def _payload_updates_product_truth(self, model_fields_set: set[str]) -> bool:
        return any(
            field_name in model_fields_set
            for field_name in ("product_links", "subject_product_id", "subject_product_name_snapshot", "current_product_name", "product_name_mode")
        )

    def _payload_updates_cover_truth(self, model_fields_set: set[str]) -> bool:
        return any(
            field_name in model_fields_set
            for field_name in ("product_links", "candidate_items", "subject_product_id", "current_cover_asset_type", "current_cover_asset_id", "cover_mode")
        )

    def _payload_updates_product_links(self, model_fields_set: set[str]) -> bool:
        return any(field_name in model_fields_set for field_name in ("product_links", "subject_product_id"))

    def _payload_updates_candidate_items(self, model_fields_set: set[str]) -> bool:
        return "candidate_items" in model_fields_set

    def _payload_updates_copywriting_truth(self, model_fields_set: set[str]) -> bool:
        return any(
            field_name in model_fields_set
            for field_name in ("candidate_items", "main_copywriting_text", "current_copywriting_id", "current_copywriting_text", "copywriting_mode")
        )

    async def _resolve_current_product_truth(
        self,
        *,
        subject_product_id: Optional[int],
        explicit_current_product_name: Any,
        explicit_product_name_mode: Any,
        explicit_legacy_snapshot: Any,
        existing_current_product_name: Optional[str],
        existing_product_name_mode: Optional[str],
        existing_legacy_snapshot: Optional[str],
    ) -> dict[str, Optional[str]]:
        product = None
        if subject_product_id is not None:
            product = await self.db.get(Product, subject_product_id)
            if product is None:
                raise ValueError("所选商品不存在")

        current_product_name = existing_current_product_name or existing_legacy_snapshot
        if explicit_legacy_snapshot is not _UNSET:
            current_product_name = explicit_legacy_snapshot
        if explicit_current_product_name is not _UNSET:
            current_product_name = explicit_current_product_name

        product_name_mode = explicit_product_name_mode if explicit_product_name_mode is not _UNSET else existing_product_name_mode
        if explicit_current_product_name is not _UNSET or explicit_legacy_snapshot is not _UNSET:
            product_name_mode = product_name_mode or "manual"
        if product_name_mode is None:
            product_name_mode = "follow_primary_product" if subject_product_id is not None else "manual"
        if product_name_mode == "follow_primary_product":
            if product is None:
                raise ValueError("follow_primary_product requires subject_product_id")
            current_product_name = product.name

        return {
            "current_product_name": current_product_name,
            "product_name_mode": product_name_mode,
            "compat_snapshot": current_product_name,
        }

    async def _resolve_current_cover_truth(
        self,
        *,
        subject_product_id: Optional[int],
        explicit_current_cover_asset_type: Any,
        explicit_current_cover_asset_id: Any,
        explicit_cover_mode: Any,
        existing_current_cover_asset_type: Optional[str],
        existing_current_cover_asset_id: Optional[int],
        existing_cover_mode: Optional[str],
    ) -> dict[str, Optional[str] | Optional[int]]:
        current_cover_asset_type = existing_current_cover_asset_type
        current_cover_asset_id = existing_current_cover_asset_id

        if explicit_current_cover_asset_type is not _UNSET:
            current_cover_asset_type = explicit_current_cover_asset_type
        if explicit_current_cover_asset_id is not _UNSET:
            if explicit_current_cover_asset_id is not None:
                await self._assert_cover_exists(explicit_current_cover_asset_id)
            current_cover_asset_id = explicit_current_cover_asset_id
            current_cover_asset_type = current_cover_asset_type or ("cover" if explicit_current_cover_asset_id is not None else None)

        cover_mode = explicit_cover_mode if explicit_cover_mode is not _UNSET else existing_cover_mode
        if explicit_current_cover_asset_id is not _UNSET and explicit_current_cover_asset_id is not None and explicit_cover_mode is _UNSET:
            cover_mode = "manual"
        if cover_mode is None:
            cover_mode = "default_from_primary_product" if subject_product_id is not None else "manual"
        if cover_mode == "default_from_primary_product":
            if subject_product_id is None:
                raise ValueError("default_from_primary_product requires subject_product_id")
            current_cover_asset_id = await self._resolve_default_product_cover_id(subject_product_id)
            current_cover_asset_type = "cover" if current_cover_asset_id is not None else None
        elif current_cover_asset_id is None:
            current_cover_asset_type = None

        if current_cover_asset_id is not None and current_cover_asset_type is None:
            current_cover_asset_type = "cover"
        return {
            "current_cover_asset_type": current_cover_asset_type,
            "current_cover_asset_id": current_cover_asset_id,
            "cover_mode": cover_mode,
        }

    async def _resolve_current_copywriting_truth(
        self,
        *,
        explicit_current_copywriting_id: Any,
        explicit_current_copywriting_text: Any,
        explicit_copywriting_mode: Any,
        explicit_legacy_text: Any,
        existing_current_copywriting_id: Optional[int],
        existing_current_copywriting_text: Optional[str],
        existing_copywriting_mode: Optional[str],
        existing_legacy_text: Optional[str],
    ) -> dict[str, Optional[str] | Optional[int]]:
        current_copywriting_id = existing_current_copywriting_id
        current_copywriting_text = existing_current_copywriting_text or existing_legacy_text

        if explicit_legacy_text is not _UNSET:
            current_copywriting_text = explicit_legacy_text
        if explicit_current_copywriting_text is not _UNSET:
            current_copywriting_text = explicit_current_copywriting_text
        if explicit_current_copywriting_id is not _UNSET:
            if explicit_current_copywriting_id is None:
                current_copywriting_id = None
            else:
                copywriting = await self.db.get(Copywriting, explicit_current_copywriting_id)
                if copywriting is None:
                    raise ValueError("???????")
                current_copywriting_id = explicit_current_copywriting_id
                if explicit_current_copywriting_text is _UNSET:
                    current_copywriting_text = copywriting.content

        copywriting_mode = explicit_copywriting_mode if explicit_copywriting_mode is not _UNSET else existing_copywriting_mode
        if explicit_current_copywriting_text is not _UNSET or explicit_legacy_text is not _UNSET:
            copywriting_mode = copywriting_mode or "manual"
        elif explicit_current_copywriting_id is not _UNSET and explicit_current_copywriting_id is not None:
            copywriting_mode = copywriting_mode or "adopted_candidate"
        if copywriting_mode is None:
            copywriting_mode = "manual"

        return {
            "current_copywriting_id": current_copywriting_id,
            "current_copywriting_text": current_copywriting_text,
            "copywriting_mode": copywriting_mode,
            "compat_text": current_copywriting_text,
        }

    async def _assert_cover_exists(self, cover_id: int) -> None:
        cover = await self.db.get(Cover, cover_id)
        if cover is None:
            raise ValueError("所选封面不存在")

    async def _resolve_default_product_cover_id(self, subject_product_id: int) -> Optional[int]:
        result = await self.db.execute(
            select(Cover.id)
            .where(Cover.product_id == subject_product_id)
            .order_by(Cover.id.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _resolve_current_cover_path(self, creative: CreativeItem) -> Optional[str]:
        cover_id = creative.current_cover_asset_id
        if cover_id is None:
            return None
        cover = creative.__dict__.get("current_cover")
        if cover is None:
            cover = await self.db.get(Cover, cover_id)
        return cover.file_path if cover is not None else None

    def _resolve_authoritative_input_state(
        self,
        *,
        profile_id: Optional[int],
        current_input_items: list[dict[str, Any]],
        explicit_input_items: Optional[list[Any]],
    ) -> tuple[Optional[int], list[dict[str, Any]]]:
        if explicit_input_items is not None:
            return profile_id, self._normalize_input_items(
                explicit_input_items,
                allowed_material_types=SELECTED_MEDIA_WRITE_MATERIAL_TYPES,
            )
        if current_input_items:
            return profile_id, self._normalize_input_items(current_input_items)
        return profile_id, []

    async def _apply_authoritative_input_state(
        self,
        creative: CreativeItem,
        *,
        profile_id: Optional[int],
        input_items: list[dict[str, Any]],
        preserve_existing_non_media_rows: bool = False,
    ) -> None:
        normalized_items = self._normalize_input_items(
            input_items,
            allowed_material_types=(
                SELECTED_MEDIA_WRITE_MATERIAL_TYPES if preserve_existing_non_media_rows else None
            ),
        )
        if preserve_existing_non_media_rows:
            normalized_items = self._normalize_input_items(
                [
                    *normalized_items,
                    *self._extract_legacy_non_media_input_items(creative),
                ]
            )
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
        creative.input_profile_id = profile_id
        creative.__dict__.pop("input_profile", None)
        set_committed_value(creative, "input_items", new_rows)
        creative.updated_at = utc_now_naive()

    def _resolve_runtime_input_state(self, creative: CreativeItem) -> dict[str, Any]:
        authoritative_input_items = self._extract_authoritative_input_items(creative)
        profile_id = creative.input_profile_id
        return {
            "profile_id": profile_id,
            "input_items": authoritative_input_items,
            "execution_inputs": self._project_input_items_to_execution_inputs(
                profile_id=profile_id,
                input_items=authoritative_input_items,
            ),
        }

    def _extract_authoritative_input_items(self, creative: CreativeItem) -> list[dict[str, Any]]:
        rows = list(creative.__dict__.get("input_items") or [])
        if not rows:
            return []
        return self._normalize_input_items(rows)

    def _extract_legacy_non_media_input_items(self, creative: CreativeItem) -> list[dict[str, Any]]:
        return [
            item
            for item in self._extract_authoritative_input_items(creative)
            if item["material_type"] not in SELECTED_MEDIA_WRITE_MATERIAL_TYPES
        ]

    def _normalize_input_items(
        self,
        items: list[Any],
        *,
        allowed_material_types: Optional[frozenset[str]] = None,
    ) -> list[dict[str, Any]]:
        staged: list[tuple[int, int, dict[str, Any]]] = []
        for index, raw_item in enumerate(items, start=1):
            material_type = self._read_input_item_value(raw_item, "material_type")
            if material_type is None:
                raise ValueError("input_items.material_type 不能为空")
            material_type_value = getattr(material_type, "value", material_type)
            material_type_value = str(material_type_value)
            if material_type_value not in INPUT_ITEM_TO_RESOURCE_FIELD:
                raise ValueError(f"不支持的 input_items.material_type: {material_type_value}")
            if (
                allowed_material_types is not None
                and material_type_value not in allowed_material_types
            ):
                raise ValueError(
                    "input_items.material_type authoritative write only supports video/audio"
                )
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

    def _project_input_items_to_execution_inputs(
        self,
        *,
        profile_id: Optional[int],
        input_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        resource_inputs = {
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
            target_field = INPUT_ITEM_TO_RESOURCE_FIELD[item["material_type"]]
            resource_inputs[target_field].append(int(item["material_id"]))
        return resource_inputs

    def _build_orchestration_hash(
        self,
        *,
        profile_id: Optional[int],
        input_items: list[dict[str, Any]],
    ) -> str:
        canonical_payload = {
            "profile_id": profile_id,
            "input_items": [
                {
                    "material_type": item["material_type"],
                    "material_id": int(item["material_id"]),
                    "role": item.get("role"),
                    "sequence": int(item["sequence"]),
                    "instance_no": int(item["instance_no"]),
                    "trim_in": item.get("trim_in"),
                    "trim_out": item.get("trim_out"),
                    "slot_duration_seconds": item.get("slot_duration_seconds"),
                    "enabled": bool(item.get("enabled", True)),
                }
                for item in input_items
            ],
        }
        return hashlib.sha256(
            json.dumps(
                canonical_payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

    def _empty_material_counts(self) -> dict[str, int]:
        return {
            "video": 0,
            "copywriting": 0,
            "cover": 0,
            "audio": 0,
            "topic": 0,
        }

    def _read_input_item_value(self, item: Any, key: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    def _payload_updates_input_state(self, model_fields_set: set[str]) -> bool:
        return any(field_name in model_fields_set for field_name in INPUT_STATE_FIELD_NAMES)

    def _has_duplicate_execution_instances(
        self,
        creative: CreativeItem,
        *,
        runtime_input_state: Optional[dict[str, Any]] = None,
    ) -> bool:
        authoritative_input_items = (
            runtime_input_state["input_items"]
            if runtime_input_state is not None
            else self._resolve_runtime_input_state(creative)["input_items"]
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
        runtime_input_state: dict[str, Any],
        profile: PublishProfile,
    ) -> dict[str, Any]:
        execution_inputs = runtime_input_state["execution_inputs"]
        merged_topic_ids = merge_task_topic_ids(
            explicit_topic_ids=execution_inputs["topic_ids"],
            profile_default_topic_ids=await get_profile_topic_ids(self.db, profile),
        )
        return {
            "profile_id": runtime_input_state["profile_id"],
            "video_ids": execution_inputs["video_ids"],
            "copywriting_ids": execution_inputs["copywriting_ids"],
            "cover_ids": execution_inputs["cover_ids"],
            "audio_ids": execution_inputs["audio_ids"],
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

    async def _sync_direct_publish_freeze_truth(
        self,
        *,
        creative: CreativeItem,
        version: CreativeVersion,
        task: Task,
        profile: PublishProfile,
    ) -> None:
        resolved_video_path = self._resolve_direct_publish_video_path(task)
        resolved_cover_path = self._resolve_direct_publish_cover_path(task)
        resolved_copywriting_text = self._resolve_direct_publish_copywriting_text(task)
        resolved_duration_seconds = self._resolve_direct_publish_duration_seconds(
            creative=creative,
            task=task,
        )
        await self.version_service.sync_version_result(
            version,
            actual_duration_seconds=resolved_duration_seconds,
            final_video_path=resolved_video_path,
            final_product_name=creative.resolved_current_product_name(),
            final_copywriting_text=resolved_copywriting_text,
        )
        await self.version_service.sync_publish_package(
            version,
            package_status="ready",
            publish_profile_id=profile.id,
            frozen_video_path=resolved_video_path,
            frozen_cover_path=resolved_cover_path or await self._resolve_current_cover_path(creative),
            frozen_duration_seconds=resolved_duration_seconds,
            frozen_product_name=creative.resolved_current_product_name(),
            frozen_copywriting_text=resolved_copywriting_text,
        )

    def _resolve_direct_publish_video_path(self, task: Task) -> str | None:
        if task.final_video_path:
            return task.final_video_path
        videos = list(task.videos or [])
        if len(videos) != 1:
            return None
        return videos[0].file_path

    def _resolve_direct_publish_cover_path(self, task: Task) -> str | None:
        covers = list(task.covers or [])
        if not covers:
            return None
        return covers[0].file_path

    def _resolve_direct_publish_copywriting_text(self, task: Task) -> str:
        copywritings = list(task.copywritings or [])
        if not copywritings:
            return ""
        return copywritings[0].content

    def _resolve_direct_publish_duration_seconds(
        self,
        *,
        creative: CreativeItem,
        task: Task,
    ) -> int | None:
        if task.final_video_duration is not None:
            return task.final_video_duration
        videos = list(task.videos or [])
        if len(videos) == 1 and videos[0].duration is not None:
            return videos[0].duration
        return creative.target_duration_seconds

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
        runtime_input_state = self._resolve_runtime_input_state(creative)
        eligibility_status, _ = await self._build_eligibility_projection(
            creative,
            runtime_input_state=runtime_input_state,
        )
        if eligibility_status == CreativeEligibilityStatus.READY_TO_COMPOSE:
            creative.status = CreativeStatus.READY_TO_COMPOSE.value
        else:
            creative.status = CreativeStatus.PENDING_INPUT.value
        creative.updated_at = utc_now_naive()
        await self.db.flush()

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
        input_items = self._build_input_items_response(creative)
        runtime_input_state = self._resolve_runtime_input_state(creative)
        input_orchestration = self._build_input_orchestration_response(
            profile_id=runtime_input_state["profile_id"],
            input_items=input_items,
        )
        return CreativeItemResponse(
            id=creative.id,
            creative_no=creative.creative_no,
            title=creative.title,
            status=self._coerce_creative_status(creative.status),
            current_version_id=creative.current_version_id,
            latest_version_no=creative.latest_version_no,
            subject_product_id=creative.subject_product_id,
            subject_product_name_snapshot=creative.resolved_current_product_name(),
            main_copywriting_text=creative.resolved_current_copywriting_text(),
            current_product_name=creative.resolved_current_product_name(),
            product_name_mode=creative.resolved_product_name_mode(),
            current_cover_asset_type=creative.resolved_current_cover_asset_type(),
            current_cover_asset_id=creative.current_cover_asset_id,
            cover_mode=creative.resolved_cover_mode(),
            current_copywriting_id=creative.resolved_current_copywriting_id(),
            current_copywriting_text=creative.resolved_current_copywriting_text(),
            copywriting_mode=creative.resolved_copywriting_mode(),
            target_duration_seconds=creative.target_duration_seconds,
            input_items=input_items,
            input_orchestration=input_orchestration,
            generation_error_msg=creative.generation_error_msg,
            generation_failed_at=creative.generation_failed_at,
            eligibility_status=CreativeEligibilityStatus.PENDING_INPUT,
            eligibility_reasons=[],
            latest_task_summary=None,
            created_at=creative.created_at,
            updated_at=creative.updated_at,
        )
