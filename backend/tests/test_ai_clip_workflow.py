import json
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CheckRecord, CreativeItem, CreativeVersion, PackageRecord
from services.ai_clip_service import VideoInfo
from services.ai_clip_workflow_service import AIClipWorkflowService, CreativeWorkflowError
from services.creative_review_service import CreativeReviewService
from services.creative_version_service import CreativeVersionService


async def _seed_creative(
    db_session: AsyncSession,
    *,
    creative_no: str = "CR-AICLIP-0001",
    creative_status: str = "PENDING_INPUT",
) -> tuple[CreativeItem, CreativeVersion]:
    creative = CreativeItem(
        creative_no=creative_no,
        title="AIClip Workflow Sample",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(
        creative,
        title="AIClip Workflow V1",
    )
    creative.status = creative_status
    await db_session.commit()
    await db_session.refresh(creative)
    await db_session.refresh(version)
    return creative, version


@pytest.mark.asyncio
async def test_ai_clip_workflow_submit_creates_reviewable_next_version(
    db_session: AsyncSession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    creative, initial_version = await _seed_creative(db_session)
    output_path = tmp_path / "workflow-output.mp4"
    output_path.write_bytes(b"fake video")

    async def _fake_get_video_info(self, video_path: str) -> VideoInfo:
        return VideoInfo(
            path=video_path,
            duration=12.5,
            width=1080,
            height=1920,
            fps=30.0,
            size=2048,
            format="h264",
        )

    async def _fake_store_from_path(self, source_path: str, media_type: str):
        assert source_path == str(output_path)
        assert media_type == "videos"
        return ("data/materials/videos/a1b2c3d4.mp4", "a1b2c3d4", 2048)

    monkeypatch.setattr(
        "services.ai_clip_workflow_service.AIClipService.get_video_info",
        _fake_get_video_info,
    )
    monkeypatch.setattr(
        "services.ai_clip_workflow_service.MediaStorageService.store_from_path",
        _fake_store_from_path,
    )

    service = AIClipWorkflowService(db_session)
    response = await service.submit_result(
        creative.id,
        source_version_id=initial_version.id,
        output_path=str(output_path),
        title="AIClip Workflow V2",
        workflow_type="smart_clip",
        metadata={"trigger": "test"},
    )
    await db_session.commit()

    persisted_creative = await db_session.get(CreativeItem, creative.id)
    versions = (
        await db_session.execute(
            select(CreativeVersion)
            .where(CreativeVersion.creative_item_id == creative.id)
            .order_by(CreativeVersion.version_no.asc())
        )
    ).scalars().all()
    packages = (
        await db_session.execute(
            select(PackageRecord).where(
                PackageRecord.creative_version_id == persisted_creative.current_version_id
            )
        )
    ).scalars().all()

    assert response.creative_id == creative.id
    assert response.source_version_id == initial_version.id
    assert response.creative_status.value == "WAITING_REVIEW"
    assert response.current_version_id != initial_version.id
    assert response.version.parent_version_id == initial_version.id
    assert response.version.version_type == "ai_clip"
    assert response.package_record.package_status == "ready"
    assert len(versions) == 2
    assert persisted_creative is not None
    assert persisted_creative.status == "WAITING_REVIEW"
    assert persisted_creative.current_version_id == versions[-1].id
    assert len(packages) == 1
    manifest = json.loads(packages[0].manifest_json)
    assert manifest["version"] == "v1"
    assert manifest["creative_item_id"] == creative.id
    assert manifest["creative_version_id"] == versions[-1].id
    assert manifest["current_product_name"] == ""
    assert manifest["current_copywriting"]["text"] == ""
    assert manifest["selected_videos"] == []
    assert manifest["selected_audios"] == []
    assert manifest["source"] == "package"


@pytest.mark.asyncio
async def test_ai_clip_workflow_failure_keeps_existing_review_truth(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    creative, initial_version = await _seed_creative(
        db_session,
        creative_no="CR-AICLIP-FAIL-0001",
        creative_status="WAITING_REVIEW",
    )
    await CreativeReviewService(db_session).approve(
        creative.id,
        version_id=initial_version.id,
        note="approved before ai clip retry",
    )
    await db_session.commit()

    async def _fail_store_from_path(self, source_path: str, media_type: str):
        raise AssertionError("store_from_path should not run for missing file")

    monkeypatch.setattr(
        "services.ai_clip_workflow_service.MediaStorageService.store_from_path",
        _fail_store_from_path,
    )

    service = AIClipWorkflowService(db_session)
    with pytest.raises(CreativeWorkflowError) as exc_info:
        await service.submit_result(
            creative.id,
            source_version_id=initial_version.id,
            output_path="E:/missing/ai-clip-output.mp4",
            workflow_type="smart_clip",
        )

    persisted_creative = await db_session.get(CreativeItem, creative.id)
    versions = (
        await db_session.execute(
            select(CreativeVersion).where(CreativeVersion.creative_item_id == creative.id)
        )
    ).scalars().all()
    checks = (await db_session.execute(select(CheckRecord))).scalars().all()

    assert exc_info.value.status_code == 400
    assert persisted_creative is not None
    assert persisted_creative.status == "APPROVED"
    assert persisted_creative.current_version_id == initial_version.id
    assert len(versions) == 1
    assert len(checks) == 1
    assert checks[0].conclusion == "APPROVED"
