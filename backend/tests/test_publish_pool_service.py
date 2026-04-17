import importlib

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import CreativeItem, CreativeVersion, PublishPoolItem
from services.creative_review_service import CreativeReviewService
from services.creative_version_service import CreativeVersionService
from services.publish_pool_service import PublishPoolService


@pytest.mark.asyncio
async def test_migration_027_is_idempotent_and_publish_pool_table_exists() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    status VARCHAR(32) DEFAULT 'draft'
                )
                """
            )

        migration_024 = importlib.import_module("migrations.024_creative_phase_a_skeleton")
        migration_025 = importlib.import_module("migrations.025_creative_phase_b_review_invariants")
        migration_027 = importlib.import_module("migrations.027_creative_phase_c_publish_pool")
        await migration_024.run_migration(engine)
        await migration_025.run_migration(engine)
        await migration_027.run_migration(engine)
        await migration_027.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }
            indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('publish_pool_items')")).fetchall()
            }

        assert "publish_pool_items" in tables
        assert "ix_publish_pool_items_status" in indexes
    finally:
        await engine.dispose()


async def _seed_creative_for_pool(
    db_session: AsyncSession,
    *,
    creative_no: str = "CR-POOL-0001",
) -> tuple[CreativeItem, int]:
    creative = CreativeItem(
        creative_no=creative_no,
        title="Creative Pool Sample",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(creative, title="Pool V1")
    creative.status = "WAITING_REVIEW"
    await db_session.commit()
    return creative, version.id


@pytest.mark.asyncio
async def test_approve_current_version_creates_active_publish_pool_item(
    db_session: AsyncSession,
) -> None:
    creative, version_id = await _seed_creative_for_pool(db_session)

    await CreativeReviewService(db_session).approve(creative.id, version_id=version_id, note="pool it")
    await db_session.commit()

    result = await db_session.execute(
        select(PublishPoolItem).where(PublishPoolItem.creative_item_id == creative.id)
    )
    items = list(result.scalars().all())

    assert len(items) == 1
    assert items[0].creative_version_id == version_id
    assert items[0].status == "active"
    assert items[0].invalidation_reason is None


@pytest.mark.asyncio
async def test_rework_invalidates_existing_publish_pool_item(
    db_session: AsyncSession,
) -> None:
    creative, version_id = await _seed_creative_for_pool(db_session, creative_no="CR-POOL-0002")
    review_service = CreativeReviewService(db_session)

    await review_service.approve(creative.id, version_id=version_id, note="approved")
    await db_session.commit()

    await review_service.rework(
        creative.id,
        version_id=version_id,
        rework_type="copy",
        note="needs changes",
    )
    await db_session.commit()

    pool_item = (
        await db_session.execute(select(PublishPoolItem).where(PublishPoolItem.creative_item_id == creative.id))
    ).scalar_one()
    assert pool_item.status == "invalidated"
    assert pool_item.invalidation_reason == "review_rework_required"
    assert pool_item.invalidated_at is not None


@pytest.mark.asyncio
async def test_new_version_invalidates_old_active_publish_pool_item(
    db_session: AsyncSession,
) -> None:
    creative, version_id = await _seed_creative_for_pool(db_session, creative_no="CR-POOL-0003")
    review_service = CreativeReviewService(db_session)
    version_service = CreativeVersionService(db_session)

    await review_service.approve(creative.id, version_id=version_id, note="approved")
    await db_session.commit()

    persisted_creative = await db_session.get(CreativeItem, creative.id)
    await version_service.create_next_version(persisted_creative, title="Pool V2")
    await db_session.commit()

    pool_item = (
        await db_session.execute(select(PublishPoolItem).where(PublishPoolItem.creative_version_id == version_id))
    ).scalar_one()
    assert pool_item.status == "invalidated"
    assert pool_item.invalidation_reason == "superseded_by_new_version"


@pytest.mark.asyncio
async def test_publish_pool_rejects_non_current_version_activation(
    db_session: AsyncSession,
) -> None:
    creative, version_id = await _seed_creative_for_pool(db_session, creative_no="CR-POOL-0004")
    creative = await db_session.get(CreativeItem, creative.id)
    version_service = CreativeVersionService(db_session)
    previous_version_id = version_id

    next_version = await version_service.create_next_version(creative, title="Pool V2")
    await db_session.commit()

    stale_version = await db_session.get(CreativeVersion, previous_version_id)
    creative = await db_session.get(CreativeItem, creative.id)
    assert next_version.id != previous_version_id
    with pytest.raises(ValueError, match="current Creative version"):
        await PublishPoolService(db_session).activate_for_version(creative, stale_version)


@pytest.mark.asyncio
async def test_publish_pool_api_lists_active_items_by_default(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative, version_id = await _seed_creative_for_pool(db_session, creative_no="CR-POOL-API-0001")
    await CreativeReviewService(db_session).approve(creative.id, version_id=version_id, note="approved")
    await db_session.commit()

    response = await client.get("/api/creative-publish-pool")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["creative_item_id"] == creative.id
    assert payload["items"][0]["creative_version_id"] == version_id
    assert payload["items"][0]["status"] == "active"
