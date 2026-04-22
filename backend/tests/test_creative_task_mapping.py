import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Account, CreativeInputItem, CreativeItem, CreativeVersion, PackageRecord, Task
from schemas import TaskResponse


@pytest.mark.asyncio
async def test_task_can_reference_creative_entities_via_orm(db_session) -> None:
    account = Account(account_id="creative-phase-a", account_name="Creative Phase A")
    db_session.add(account)
    await db_session.flush()

    creative = CreativeItem(
        creative_no="CR-0001",
        title="Creative Skeleton",
        status="PENDING_INPUT",
        latest_version_no=1,
    )
    db_session.add(creative)
    await db_session.flush()

    version = CreativeVersion(
        creative_item_id=creative.id,
        version_no=1,
        version_type="generated",
        title="Creative Skeleton V1",
    )
    db_session.add(version)
    await db_session.flush()

    creative.current_version_id = version.id

    package = PackageRecord(
        creative_version_id=version.id,
        package_status="pending",
    )
    db_session.add(package)

    task = Task(
        account_id=account.id,
        status="draft",
        creative_item_id=creative.id,
        creative_version_id=version.id,
        task_kind="composition",
    )
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(
        select(Task)
        .options(
            selectinload(Task.videos),
            selectinload(Task.copywritings),
            selectinload(Task.covers),
            selectinload(Task.audios),
            selectinload(Task.topics),
        )
        .where(Task.id == task.id)
    )
    persisted_task = result.scalar_one()
    response = TaskResponse.model_validate(persisted_task)

    assert response.creative_item_id == creative.id
    assert response.creative_version_id == version.id
    assert response.task_kind.value == "composition"


@pytest.mark.asyncio
async def test_task_without_creative_mapping_remains_compatible(db_session) -> None:
    account = Account(account_id="legacy-task", account_name="Legacy Task")
    db_session.add(account)
    await db_session.flush()

    task = Task(account_id=account.id, status="draft")
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(
        select(Task)
        .options(
            selectinload(Task.videos),
            selectinload(Task.copywritings),
            selectinload(Task.covers),
            selectinload(Task.audios),
            selectinload(Task.topics),
        )
        .where(Task.id == task.id)
    )
    persisted_task = result.scalar_one()
    response = TaskResponse.model_validate(persisted_task)

    assert response.creative_item_id is None
    assert response.creative_version_id is None
    assert response.task_kind is None


@pytest.mark.asyncio
async def test_task_mapping_remains_identity_link_only_while_creative_input_items_are_authoritative(db_session) -> None:
    creative = CreativeItem(
        creative_no="CR-TASK-ID-ONLY-0001",
        title="Identity Link Only",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()
    db_session.add_all(
        [
            CreativeInputItem(
                creative_item_id=creative.id,
                material_type="video",
                material_id=101,
                sequence=1,
                instance_no=1,
            ),
            CreativeInputItem(
                creative_item_id=creative.id,
                material_type="video",
                material_id=101,
                sequence=2,
                instance_no=2,
            ),
        ]
    )
    version = CreativeVersion(
        creative_item_id=creative.id,
        version_no=1,
        version_type="generated",
        title="Identity Link V1",
    )
    db_session.add(version)
    await db_session.flush()
    task = Task(
        status="draft",
        creative_item_id=creative.id,
        creative_version_id=version.id,
        task_kind="composition",
    )
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(
        select(Task)
        .options(
            selectinload(Task.videos),
            selectinload(Task.copywritings),
            selectinload(Task.covers),
            selectinload(Task.audios),
            selectinload(Task.topics),
        )
        .where(Task.id == task.id)
    )
    persisted_task = result.scalar_one()
    response = TaskResponse.model_validate(persisted_task)

    assert response.creative_item_id == creative.id
    assert response.creative_version_id == version.id
    assert response.video_ids == []
