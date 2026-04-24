import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Audio, Cover, CreativeInputItem, CreativeItem, PackageRecord, Product, Video
from services.creative_version_service import CreativeVersionService


@pytest.mark.asyncio
async def test_initial_version_package_manifest_follows_current_truth_and_selected_media(
    db_session: AsyncSession,
) -> None:
    product = Product(name="Primary Product", dewu_url="https://example.test/product")
    cover = Cover(name="Current Cover", file_path="covers/current-cover.jpg")
    video_a = Video(name="video-a.mp4", file_path="videos/video-a.mp4")
    video_b = Video(name="video-b.mp4", file_path="videos/video-b.mp4")
    audio_a = Audio(name="audio-a.mp3", file_path="audios/audio-a.mp3")
    audio_b = Audio(name="audio-b.mp3", file_path="audios/audio-b.mp3")
    db_session.add_all([product, cover, video_a, video_b, audio_a, audio_b])
    await db_session.flush()

    creative = CreativeItem(
        creative_no="CR-SLICE6-0001",
        title="Slice 6 Manifest Contract",
        status="PENDING_INPUT",
        latest_version_no=0,
        subject_product_id=product.id,
        subject_product_name_snapshot="compat snapshot should not win",
        current_product_name="Manual Product Truth",
        product_name_mode="manual",
        current_cover_asset_type="cover",
        current_cover_asset_id=cover.id,
        cover_mode="manual",
        main_copywriting_text="compat copy should not win",
        current_copywriting_text="Manual Copy Truth",
        copywriting_mode="manual",
        target_duration_seconds=28,
        input_items=[
            CreativeInputItem(material_type="video", material_id=video_a.id, sequence=1, enabled=True, trim_in=3, trim_out=15, slot_duration_seconds=12),
            CreativeInputItem(material_type="audio", material_id=audio_a.id, sequence=2, enabled=True),
            CreativeInputItem(material_type="video", material_id=video_b.id, sequence=3, enabled=False, trim_in=0, trim_out=9, slot_duration_seconds=9),
            CreativeInputItem(material_type="audio", material_id=audio_b.id, sequence=4, enabled=False),
        ],
    )
    db_session.add(creative)
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(
        creative,
        title="Slice 6 Manifest Contract V1",
    )
    await db_session.commit()

    package = (
        await db_session.execute(
            select(PackageRecord).where(PackageRecord.creative_version_id == version.id)
        )
    ).scalar_one()
    manifest = json.loads(package.manifest_json or "{}")

    assert package.frozen_cover_path == "covers/current-cover.jpg"
    assert manifest == {
        "version": "v1",
        "creative_item_id": creative.id,
        "creative_version_id": version.id,
        "primary_product_id": product.id,
        "current_product_name": "Manual Product Truth",
        "current_cover": {
            "asset_type": "cover",
            "asset_id": cover.id,
        },
        "current_copywriting": {
            "copywriting_id": None,
            "text": "Manual Copy Truth",
            "mode": "manual",
        },
        "selected_videos": [
            {
                "asset_id": video_a.id,
                "sort_order": 1,
                "enabled": True,
                "trim_in": 3,
                "trim_out": 15,
                "slot_duration_seconds": 12,
            }
        ],
        "selected_audios": [
            {
                "asset_id": audio_a.id,
                "sort_order": 1,
                "enabled": True,
            }
        ],
        "frozen_at": manifest["frozen_at"],
        "source": "package",
    }


@pytest.mark.asyncio
async def test_sync_publish_package_reloads_selected_media_from_authoritative_carrier(
    db_session: AsyncSession,
) -> None:
    video = Video(name="sync-video.mp4", file_path="videos/sync-video.mp4")
    db_session.add(video)
    await db_session.flush()

    creative = CreativeItem(
        creative_no="CR-SLICE6-0002",
        title="Slice 6 Reload Carrier",
        status="PENDING_INPUT",
        latest_version_no=0,
        current_product_name="Carrier Product",
        current_copywriting_text="Carrier Copy",
        product_name_mode="manual",
        copywriting_mode="manual",
    )
    db_session.add(creative)
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(creative, title="Reload V1")
    db_session.add(CreativeInputItem(creative_item_id=creative.id, material_type="video", material_id=video.id, sequence=1, enabled=True))
    await db_session.flush()

    package = await CreativeVersionService(db_session).sync_publish_package(
        version,
        frozen_video_path="videos/output.mp4",
        frozen_duration_seconds=10,
    )
    await db_session.commit()

    manifest = json.loads(package.manifest_json or "{}")
    assert manifest["selected_videos"] == [
        {
            "asset_id": video.id,
            "sort_order": 1,
            "enabled": True,
            "trim_in": None,
            "trim_out": None,
            "slot_duration_seconds": None,
        }
    ]
    assert manifest["selected_audios"] == []
