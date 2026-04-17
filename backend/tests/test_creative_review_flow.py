import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CheckRecord, CreativeItem, PublishPoolItem
from services.creative_version_service import CreativeVersionService


async def _seed_creative_review_sample(
    db_session: AsyncSession,
    *,
    with_second_version: bool = False,
) -> tuple[int, int, int | None]:
    creative = CreativeItem(
        creative_no="CR-REVIEW-0001" if not with_second_version else "CR-REVIEW-0002",
        title="Creative Review Sample",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()

    version_service = CreativeVersionService(db_session)
    initial = await version_service.create_initial_version(creative, title="Review V1")
    creative.status = "WAITING_REVIEW"
    latest = None
    if with_second_version:
        latest = await version_service.create_next_version(creative, title="Review V2")

    await db_session.commit()
    return creative.id, (latest or initial).id, initial.id if with_second_version else None


async def _load_creative(db_session: AsyncSession, creative_id: int) -> CreativeItem:
    result = await db_session.execute(select(CreativeItem).where(CreativeItem.id == creative_id))
    return result.scalar_one()


async def _load_checks(db_session: AsyncSession, creative_id: int) -> list[CheckRecord]:
    result = await db_session.execute(
        select(CheckRecord)
        .where(CheckRecord.creative_item_id == creative_id)
        .order_by(CheckRecord.id.asc())
    )
    return list(result.scalars().all())


async def _load_pool_items(db_session: AsyncSession, creative_id: int) -> list[PublishPoolItem]:
    result = await db_session.execute(
        select(PublishPoolItem)
        .where(PublishPoolItem.creative_item_id == creative_id)
        .order_by(PublishPoolItem.id.asc())
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_approve_current_version_writes_check_record_and_updates_business_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, current_version_id, _ = await _seed_creative_review_sample(db_session)

    response = await client.post(
        f"/api/creative-reviews/{creative_id}/approve",
        json={"version_id": current_version_id, "note": "looks good"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_status"] == "APPROVED"
    assert payload["check"]["creative_version_id"] == current_version_id
    assert payload["check"]["conclusion"] == "APPROVED"

    creative = await _load_creative(db_session, creative_id)
    checks = await _load_checks(db_session, creative_id)
    pool_items = await _load_pool_items(db_session, creative_id)
    assert creative.status == "APPROVED"
    assert len(checks) == 1
    assert checks[0].conclusion == "APPROVED"
    assert len(pool_items) == 1
    assert pool_items[0].status == "active"
    assert pool_items[0].creative_version_id == current_version_id


@pytest.mark.asyncio
async def test_non_current_version_cannot_be_approved(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, current_version_id, previous_version_id = await _seed_creative_review_sample(
        db_session,
        with_second_version=True,
    )
    assert previous_version_id is not None

    response = await client.post(
        f"/api/creative-reviews/{creative_id}/approve",
        json={"version_id": previous_version_id, "note": "stale"},
    )

    assert response.status_code == 409
    assert "当前版本" in response.json()["detail"]

    creative = await _load_creative(db_session, creative_id)
    checks = await _load_checks(db_session, creative_id)
    pool_items = await _load_pool_items(db_session, creative_id)
    assert creative.current_version_id == current_version_id
    assert checks == []
    assert pool_items == []


@pytest.mark.asyncio
async def test_rework_requires_rework_type(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, current_version_id, _ = await _seed_creative_review_sample(db_session)

    response = await client.post(
        f"/api/creative-reviews/{creative_id}/rework",
        json={"version_id": current_version_id, "note": "needs changes"},
    )

    assert response.status_code == 400
    assert "rework_type" in response.json()["detail"]

    checks = await _load_checks(db_session, creative_id)
    pool_items = await _load_pool_items(db_session, creative_id)
    assert checks == []
    assert pool_items == []


@pytest.mark.asyncio
async def test_reject_writes_check_record_and_terminal_business_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, current_version_id, _ = await _seed_creative_review_sample(db_session)

    response = await client.post(
        f"/api/creative-reviews/{creative_id}/reject",
        json={"version_id": current_version_id, "note": "not acceptable"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_status"] == "REJECTED"
    assert payload["check"]["conclusion"] == "REJECTED"

    creative = await _load_creative(db_session, creative_id)
    checks = await _load_checks(db_session, creative_id)
    pool_items = await _load_pool_items(db_session, creative_id)
    assert creative.status == "REJECTED"
    assert len(checks) == 1
    assert checks[0].conclusion == "REJECTED"
    assert pool_items == []


@pytest.mark.asyncio
async def test_reject_invalidates_existing_publish_pool_item(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, current_version_id, _ = await _seed_creative_review_sample(db_session)

    approve_response = await client.post(
        f"/api/creative-reviews/{creative_id}/approve",
        json={"version_id": current_version_id, "note": "approved first"},
    )
    assert approve_response.status_code == 200

    reject_response = await client.post(
        f"/api/creative-reviews/{creative_id}/reject",
        json={"version_id": current_version_id, "note": "reject later"},
    )

    assert reject_response.status_code == 200
    pool_items = await _load_pool_items(db_session, creative_id)
    assert len(pool_items) == 1
    assert pool_items[0].status == "invalidated"
    assert pool_items[0].invalidation_reason == "review_rejected"
