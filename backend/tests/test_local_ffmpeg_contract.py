from __future__ import annotations

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import CompositionMode, PublishProfileCreate


def test_publish_profile_create_rejects_local_ffmpeg_non_object_params() -> None:
    with pytest.raises(ValidationError, match="local_ffmpeg 的 composition_params 必须是 JSON object"):
        PublishProfileCreate(
            name="ffmpeg-invalid-shape",
            composition_mode=CompositionMode.LOCAL_FFMPEG,
            composition_params='["not-object"]',
        )


def test_publish_profile_create_accepts_local_ffmpeg_v1_params() -> None:
    profile = PublishProfileCreate(
        name="ffmpeg-v1",
        composition_mode=CompositionMode.LOCAL_FFMPEG,
        composition_params='{"audio_mix_volume":0.8,"video_codec":"libx264","audio_codec":"aac","preset":"medium","crf":23}',
    )

    assert profile.composition_mode == CompositionMode.LOCAL_FFMPEG
    assert profile.composition_params is not None


@pytest.mark.asyncio
async def test_create_profile_rejects_local_ffmpeg_with_coze_workflow_id(
    client: AsyncClient,
    active_remote_auth_session,
) -> None:
    response = await client.post(
        "/api/profiles",
        json={
            "name": "local-ffmpeg-invalid",
            "composition_mode": "local_ffmpeg",
            "coze_workflow_id": "coze-should-not-exist",
            "composition_params": '{"audio_mix_volume": 1}',
            "global_topic_ids": [],
            "auto_retry": True,
            "max_retry_count": 3,
        },
    )

    assert response.status_code == 422
    assert "local_ffmpeg 模式不允许填写 coze_workflow_id" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_profile_rejects_local_ffmpeg_unknown_params(
    client: AsyncClient,
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    create_response = await client.post(
        "/api/profiles",
        json={
            "name": "local-ffmpeg-update",
            "composition_mode": "local_ffmpeg",
            "composition_params": '{"audio_mix_volume": 1}',
            "global_topic_ids": [],
            "auto_retry": True,
            "max_retry_count": 3,
        },
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/profiles/{profile_id}",
        json={
            "composition_params": '{"unexpected":"value"}',
        },
    )

    assert update_response.status_code == 422
    assert "收到未知字段：unexpected" in update_response.json()["detail"]
