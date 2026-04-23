import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import CreativeItem
from services.ai_clip_service import VideoInfo
from services.creative_version_service import CreativeVersionService


async def _seed_creative_workflow_sample(
    db_session: AsyncSession,
    *,
    creative_no: str = "CR-WORKFLOW-0001",
) -> tuple[int, int]:
    creative = CreativeItem(
        creative_no=creative_no,
        title="Creative Workflow Sample",
        status="PENDING_INPUT",
        latest_version_no=0,
        subject_product_name_snapshot="Workflow Product Snapshot",
        main_copywriting_text="Workflow Copywriting Snapshot",
        target_duration_seconds=15,
    )
    db_session.add(creative)
    await db_session.flush()

    initial_version = await CreativeVersionService(db_session).create_initial_version(
        creative,
        title="Creative Workflow V1",
    )
    await db_session.commit()
    return creative.id, initial_version.id


@pytest.mark.asyncio
async def test_creative_workflow_submit_api_contract_returns_new_version(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    creative_id, source_version_id = await _seed_creative_workflow_sample(db_session)
    output_path = tmp_path / "submit-output.mp4"
    output_path.write_bytes(b"video")

    async def _fake_get_video_info(self, video_path: str) -> VideoInfo:
        return VideoInfo(
            path=video_path,
            duration=9.5,
            width=720,
            height=1280,
            fps=25.0,
            size=1024,
            format="h264",
        )

    async def _fake_store_from_path(self, source_path: str, media_type: str):
        return ("data/materials/videos/submit-output.mp4", "submit-output", 1024)

    monkeypatch.setattr(
        "services.ai_clip_workflow_service.AIClipService.get_video_info",
        _fake_get_video_info,
    )
    monkeypatch.setattr(
        "services.ai_clip_workflow_service.MediaStorageService.store_from_path",
        _fake_store_from_path,
    )

    response = await client.post(
        f"/api/creative-workflows/{creative_id}/ai-clip/submit",
        json={
            "source_version_id": source_version_id,
            "output_path": str(output_path),
            "title": "Workflow Submit V2",
            "workflow_type": "full_pipeline",
            "metadata": {"from": "contract-test"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = json.loads(payload["package_record"]["manifest_json"])

    assert payload["creative_id"] == creative_id
    assert payload["source_version_id"] == source_version_id
    assert payload["creative_status"] == "WAITING_REVIEW"
    assert payload["current_version_id"] == payload["version"]["id"]
    assert payload["version"]["parent_version_id"] == source_version_id
    assert payload["version"]["version_type"] == "ai_clip"
    assert payload["version"]["actual_duration_seconds"] == 10
    assert payload["version"]["final_video_path"] == "data/materials/videos/submit-output.mp4"
    assert payload["version"]["final_product_name"] == "Workflow Product Snapshot"
    assert payload["version"]["final_copywriting_text"] == "Workflow Copywriting Snapshot"
    assert payload["package_record"]["package_status"] == "ready"
    assert payload["package_record"]["frozen_video_path"] == "data/materials/videos/submit-output.mp4"
    assert payload["package_record"]["frozen_duration_seconds"] == 10
    assert payload["package_record"]["frozen_product_name"] == "Workflow Product Snapshot"
    assert payload["package_record"]["frozen_copywriting_text"] == "Workflow Copywriting Snapshot"
    assert manifest["workflow_type"] == "full_pipeline"
    assert manifest["metadata"] == {"from": "contract-test"}


@pytest.mark.asyncio
async def test_creative_workflow_submit_rejects_stale_source_version(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    creative_id, source_version_id = await _seed_creative_workflow_sample(
        db_session,
        creative_no="CR-WORKFLOW-STALE-0001",
    )
    output_path = tmp_path / "stale-output.mp4"
    output_path.write_bytes(b"video")

    response = await client.post(
        f"/api/creative-workflows/{creative_id}/ai-clip/submit",
        json={
            "source_version_id": source_version_id + 999,
            "output_path": str(output_path),
            "workflow_type": "smart_clip",
        },
    )

    assert response.status_code == 409
    assert "当前版本" in response.json()["detail"]
