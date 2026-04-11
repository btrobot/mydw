"""
Phase 1 / PR2 config compatibility tests.

These tests verify:
- `/api/schedule-config` is the canonical schedule config API
- `/api/publish/config` is a legacy compatibility bridge backed by ScheduleConfig
- `/api/publish/status` now trusts scheduler-owned runtime truth
- `/api/topics/global` no longer uses ScheduleConfig and now dual-writes a legacy PublishConfig fallback
"""
import asyncio
import json

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, PublishConfig, ScheduleConfig, Task, Topic
from services.scheduler import TaskScheduler, scheduler


@pytest_asyncio.fixture(autouse=True)
async def reset_scheduler_runtime_state() -> None:
    """Reset global scheduler runtime state to keep tests isolated."""
    await scheduler.stop_publishing()
    yield
    await scheduler.stop_publishing()


@pytest.mark.asyncio
async def test_legacy_publish_config_get_creates_default_schedule_config(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    response = await client.get("/api/publish/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "default"
    assert payload["interval_minutes"] == 30
    assert payload["start_hour"] == 9
    assert payload["end_hour"] == 22
    assert payload["max_per_account_per_day"] == 5
    assert payload["shuffle"] is False
    assert payload["auto_start"] is False

    result = await db_session.execute(
        select(ScheduleConfig).where(ScheduleConfig.name == "default")
    )
    config = result.scalar_one_or_none()
    assert config is not None
    assert config.interval_minutes == 30


@pytest.mark.asyncio
async def test_scheduler_reads_schedule_config_through_canonical_service(
    db_session: AsyncSession,
) -> None:
    config = ScheduleConfig(
        name="default",
        start_hour=8,
        end_hour=20,
        interval_minutes=45,
        max_per_account_per_day=7,
        shuffle=True,
        auto_start=False,
    )
    db_session.add(config)
    await db_session.commit()

    scheduler = TaskScheduler()
    loaded = await scheduler._get_schedule_config(db_session)

    assert loaded is not None
    assert loaded.name == "default"
    assert loaded.interval_minutes == 45
    assert loaded.shuffle is True


@pytest.mark.asyncio
async def test_schedule_config_api_and_legacy_publish_config_share_same_truth(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    canonical_update = {
        "start_hour": 10,
        "end_hour": 21,
        "interval_minutes": 15,
        "max_per_account_per_day": 9,
        "shuffle": True,
        "auto_start": True,
    }
    update_response = await client.put("/api/schedule-config", json=canonical_update)

    assert update_response.status_code == 200
    assert update_response.json()["interval_minutes"] == 15

    legacy_response = await client.get("/api/publish/config")
    assert legacy_response.status_code == 200
    legacy_payload = legacy_response.json()
    assert legacy_payload["start_hour"] == 10
    assert legacy_payload["end_hour"] == 21
    assert legacy_payload["interval_minutes"] == 15
    assert legacy_payload["max_per_account_per_day"] == 9
    assert legacy_payload["shuffle"] is True
    assert legacy_payload["auto_start"] is True

    result = await db_session.execute(
        select(ScheduleConfig).where(ScheduleConfig.name == "default")
    )
    config = result.scalar_one_or_none()
    assert config is not None
    assert config.interval_minutes == 15


@pytest.mark.asyncio
async def test_legacy_publish_config_put_updates_canonical_schedule_config(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    legacy_update = {
        "interval_minutes": 20,
        "start_hour": 7,
        "end_hour": 19,
        "max_per_account_per_day": 4,
        "shuffle": False,
        "auto_start": True,
    }
    response = await client.put("/api/publish/config", json=legacy_update)

    assert response.status_code == 200
    payload = response.json()
    assert payload["interval_minutes"] == 20

    canonical_response = await client.get("/api/schedule-config")
    assert canonical_response.status_code == 200
    canonical_payload = canonical_response.json()
    assert canonical_payload["start_hour"] == 7
    assert canonical_payload["end_hour"] == 19
    assert canonical_payload["interval_minutes"] == 20
    assert canonical_payload["max_per_account_per_day"] == 4
    assert canonical_payload["shuffle"] is False
    assert canonical_payload["auto_start"] is True

    legacy_result = await db_session.execute(
        select(PublishConfig).where(PublishConfig.name == "default")
    )
    assert legacy_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_global_topics_dual_write_legacy_publish_config_fallback_not_schedule_config_truth(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    topic_a = Topic(name="phase6_global_a", source="manual")
    topic_b = Topic(name="phase6_global_b", source="manual")
    db_session.add_all([topic_a, topic_b])
    await db_session.commit()

    response = await client.put(
        "/api/topics/global",
        json={"topic_ids": [topic_a.id, topic_b.id]},
    )

    assert response.status_code == 200
    assert sorted(response.json()["topic_ids"]) == sorted([topic_a.id, topic_b.id])

    legacy_result = await db_session.execute(select(PublishConfig).limit(1))
    legacy_config = legacy_result.scalar_one_or_none()
    assert legacy_config is not None
    assert json.loads(legacy_config.global_topic_ids) == [topic_a.id, topic_b.id]

    schedule_result = await db_session.execute(
        select(ScheduleConfig).where(ScheduleConfig.name == "default")
    )
    assert schedule_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_openapi_exposes_canonical_schedule_config_paths(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/schedule-config" in paths
    assert "get" in paths["/api/schedule-config"]
    assert "put" in paths["/api/schedule-config"]


@pytest.mark.asyncio
async def test_publish_status_reflects_scheduler_runtime_truth(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = Account(
        account_id="status_acct",
        account_name="Status Account",
        status="active",
    )
    db_session.add(account)
    await db_session.flush()
    db_session.add_all(
        [
            Task(account_id=account.id, status="ready"),
            Task(account_id=account.id, status="uploaded"),
            Task(account_id=account.id, status="failed"),
        ]
    )
    await db_session.commit()

    async def fake_publish_loop() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(scheduler, "_publish_loop", fake_publish_loop)

    start_response = await client.post("/api/publish/control", json={"action": "start"})
    assert start_response.status_code == 200

    response = await client.get("/api/publish/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["current_task_id"] is None
    assert payload["total_pending"] == 1
    assert payload["total_success"] == 1
    assert payload["total_failed"] == 1

    stop_response = await client.post("/api/publish/control", json={"action": "stop"})
    assert stop_response.status_code == 200


@pytest.mark.asyncio
async def test_publish_control_pause_and_stop_update_scheduler_truth(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_publish_loop() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(scheduler, "_publish_loop", fake_publish_loop)

    start_response = await client.post("/api/publish/control", json={"action": "start"})
    assert start_response.status_code == 200
    assert scheduler.get_status() == "running"

    pause_response = await client.post("/api/publish/control", json={"action": "pause"})
    assert pause_response.status_code == 200
    assert scheduler.get_status() == "paused"

    status_after_pause = await client.get("/api/publish/status")
    assert status_after_pause.status_code == 200
    assert status_after_pause.json()["status"] == "paused"

    stop_response = await client.post("/api/publish/control", json={"action": "stop"})
    assert stop_response.status_code == 200
    assert scheduler.get_status() == "idle"


@pytest.mark.asyncio
async def test_publish_control_rejects_duplicate_start_based_on_scheduler_truth(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_publish_loop() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(scheduler, "_publish_loop", fake_publish_loop)

    first = await client.post("/api/publish/control", json={"action": "start"})
    assert first.status_code == 200

    second = await client.post("/api/publish/control", json={"action": "start"})
    assert second.status_code == 400
    assert second.json()["detail"] == "发布已在运行中"

    await client.post("/api/publish/control", json={"action": "stop"})
