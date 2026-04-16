import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, Task
from services.creative_service import CreativeService


async def _seed_creative_sample(db_session: AsyncSession) -> tuple[int, int]:
    account = Account(account_id="creative-api-account", account_name="Creative API Account")
    db_session.add(account)
    await db_session.flush()

    task = Task(account_id=account.id, status="draft", name="Creative API sample task")
    db_session.add(task)
    await db_session.commit()

    service = CreativeService(db_session)
    mapped_task = await service.attach_task_to_creative_sample(
        task.id,
        creative_no="CR-API-0001",
        title="Creative API Sample",
    )
    return mapped_task.creative_item_id, mapped_task.id


@pytest.mark.asyncio
async def test_list_creatives_returns_empty_state(client: AsyncClient) -> None:
    response = await client.get("/api/creatives")

    assert response.status_code == 200
    assert response.json() == {"total": 0, "items": []}


@pytest.mark.asyncio
async def test_get_creative_returns_404_for_missing_record(client: AsyncClient) -> None:
    response = await client.get("/api/creatives/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_creative_list_and_detail_return_phase_a_projection(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, task_id = await _seed_creative_sample(db_session)

    list_response = await client.get("/api/creatives")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["id"] == creative_id
    assert list_payload["items"][0]["creative_no"] == "CR-API-0001"
    assert list_payload["items"][0]["title"] == "Creative API Sample"
    assert list_payload["items"][0]["status"] == "PENDING_INPUT"
    assert list_payload["items"][0]["current_version_id"] is not None

    detail_response = await client.get(f"/api/creatives/{creative_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == creative_id
    assert detail_payload["creative_no"] == "CR-API-0001"
    assert detail_payload["current_version"]["version_no"] == 1
    assert detail_payload["current_version"]["title"] == "Creative API Sample"
    assert detail_payload["current_version"]["package_record_id"] is not None
    assert detail_payload["linked_task_ids"] == [task_id]


@pytest.mark.asyncio
async def test_task_detail_remains_compatible_after_creative_attach_helper(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, task_id = await _seed_creative_sample(db_session)

    response = await client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_item_id"] == creative_id
    assert payload["creative_version_id"] is not None
    assert payload["task_kind"] == "composition"
