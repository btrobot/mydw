"""
Step 3 / PR4 tests for service-layer auth enforcement.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import LocalAuthorizationError
from models import Account, CompositionJob, Product, PublishProfile, RemoteAuthSession, Task, Video
from schemas.auth import LocalAuthSessionSummary
from services.composition_service import CompositionService
from services.media_storage_service import MediaStorageService
from services.product_parse_service import parse_and_create_materials
from services.publish_service import PublishService
from services.system_backup_service import SystemBackupService
from services.task_distributor import TaskDistributor
from services.task_service import TaskService


async def _seed_auth_state(
    db_session: AsyncSession,
    auth_state: str,
    *,
    denial_reason: str | None = None,
) -> RemoteAuthSession:
    existing = await db_session.execute(select(RemoteAuthSession))
    for row in existing.scalars().all():
        await db_session.delete(row)
    session = RemoteAuthSession(
        auth_state=auth_state,
        remote_user_id="u_123" if auth_state != "unauthenticated" else None,
        display_name="Alice" if auth_state != "unauthenticated" else None,
        license_status="active" if auth_state != "unauthenticated" else None,
        expires_at=datetime.now(UTC) + timedelta(hours=1)
        if auth_state == "authenticated_active"
        else None,
        offline_grace_until=datetime.now(UTC) + timedelta(hours=1)
        if auth_state == "authenticated_grace"
        else None,
        denial_reason=denial_reason,
        device_id="device-1",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


async def _create_account(db_session: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"svc_{suffix}",
        account_name=f"Service {suffix}",
        status="active",
        storage_state="{}",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


class TestTaskServiceAuthGuards:
    @pytest.mark.asyncio
    async def test_service_guard_ignores_stale_active_context_and_reloads_db_truth(
        self,
        db_session: AsyncSession,
    ) -> None:
        from core.auth_dependencies import require_active_service_session, set_current_auth_summary

        await _seed_auth_state(db_session, "revoked", denial_reason="remote_auth_revoked")
        set_current_auth_summary(
            LocalAuthSessionSummary(
                auth_state="authenticated_active",
                remote_user_id="u_123",
                display_name="Alice",
                license_status="active",
                entitlements=["dashboard:view"],
                device_id="device-1",
            )
        )

        with pytest.raises(LocalAuthorizationError) as exc_info:
            await require_active_service_session(db_session)

        assert exc_info.value.error_code == "revoked"

    @pytest.mark.asyncio
    async def test_publish_service_rejects_stale_active_summary_when_db_is_revoked(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session, "publish_stale_summary")
        task = Task(account_id=account.id, status="ready")
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        await _seed_auth_state(db_session, "revoked", denial_reason="remote_auth_revoked")

        mark_uploading = AsyncMock()
        monkeypatch.setattr("services.task_service.TaskService.mark_task_uploading", mark_uploading)

        service = PublishService(
            db_session,
            auth_summary=LocalAuthSessionSummary(
                auth_state="authenticated_active",
                remote_user_id="u_123",
                display_name="Alice",
                license_status="active",
                entitlements=["dashboard:view"],
                device_id="device-1",
            ),
        )

        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.publish_task(task)

        assert exc_info.value.error_code == "revoked"
        mark_uploading.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_service_create_task_denies_grace_before_commit(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session, "task_create_grace")
        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        commit = AsyncMock()
        monkeypatch.setattr(db_session, "commit", commit)

        service = TaskService(db_session)

        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.create_task({"account_id": account.id, "status": "draft"})

        assert exc_info.value.error_code == "auth_grace_restricted"
        commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_service_get_tasks_allows_grace_readonly(
        self,
        db_session: AsyncSession,
    ) -> None:
        account = await _create_account(db_session, "task_read_grace")
        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        db_session.add(Task(account_id=account.id, status="draft"))
        await db_session.commit()

        service = TaskService(db_session)
        total, tasks = await service.get_tasks()

        assert total == 1
        assert len(tasks) == 1

    @pytest.mark.asyncio
    async def test_task_service_quick_retry_denies_expired_without_mutation(
        self,
        db_session: AsyncSession,
    ) -> None:
        account = await _create_account(db_session, "task_retry_expired")
        await _seed_auth_state(db_session, "expired", denial_reason="remote_auth_expired")
        task = Task(
            account_id=account.id,
            status="failed",
            retry_count=0,
            failed_at_status="ready",
            error_msg="broken",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        service = TaskService(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.quick_retry(task.id)

        assert exc_info.value.error_code == "expired"
        await db_session.refresh(task)
        assert task.status == "failed"
        assert task.retry_count == 0


class TestTaskDistributorAuthGuards:
    @pytest.mark.asyncio
    async def test_task_distributor_denies_grace_before_assemble(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        assemble = AsyncMock()
        monkeypatch.setattr("services.task_assembler.TaskAssembler.assemble", assemble)

        distributor = TaskDistributor(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await distributor.distribute(video_ids=[1], account_ids=[1])

        assert exc_info.value.error_code == "auth_grace_restricted"
        assemble.assert_not_called()


class TestPublishServiceAuthGuards:
    @pytest.mark.asyncio
    async def test_publish_service_publish_task_denies_grace_before_side_effects(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session, "publish_grace")
        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        task = Task(account_id=account.id, status="ready")
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        mark_uploading = AsyncMock()
        get_dewu_client = AsyncMock()
        browser_context = AsyncMock()
        monkeypatch.setattr("services.task_service.TaskService.mark_task_uploading", mark_uploading)
        monkeypatch.setattr("services.publish_service.get_dewu_client", get_dewu_client)
        monkeypatch.setattr("services.publish_service.browser_manager.get_or_create_context", browser_context)

        service = PublishService(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.publish_task(task)

        assert exc_info.value.error_code == "auth_grace_restricted"
        mark_uploading.assert_not_called()
        get_dewu_client.assert_not_called()
        browser_context.assert_not_called()


class TestCompositionServiceAuthGuards:
    @pytest.mark.asyncio
    async def test_submit_composition_denies_grace_before_coze_upload(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session, "composition_grace")
        profile = PublishProfile(
            name="profile_pr4",
            composition_mode="coze",
            coze_workflow_id="wf_pr4",
        )
        db_session.add(profile)
        await db_session.flush()
        task = Task(account_id=account.id, status="draft", profile_id=profile.id)
        db_session.add(task)
        await db_session.flush()
        video = Video(name="video.mp4", file_path="E:/video.mp4")
        db_session.add(video)
        await db_session.flush()
        await db_session.execute(
            Task.__table__.update().where(Task.id == task.id).values()
        )
        await db_session.commit()

        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        upload_file = AsyncMock()
        submit_composition = AsyncMock()
        monkeypatch.setattr("services.composition_service.CozeClient", lambda: MagicMock(upload_file=upload_file, submit_composition=submit_composition))

        service = CompositionService(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.submit_composition(task.id)

        assert exc_info.value.error_code == "auth_grace_restricted"
        upload_file.assert_not_called()
        submit_composition.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_submit_denies_device_mismatch_without_creating_jobs(
        self,
        db_session: AsyncSession,
    ) -> None:
        account = await _create_account(db_session, "composition_device")
        task = Task(account_id=account.id, status="draft")
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        await _seed_auth_state(
            db_session,
            "device_mismatch",
            denial_reason="remote_auth_device_mismatch",
        )

        service = CompositionService(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.batch_submit([task.id])

        assert exc_info.value.error_code == "device_mismatch"
        jobs = (await db_session.execute(select(CompositionJob))).scalars().all()
        assert jobs == []


class TestProductParseAuthGuards:
    @pytest.mark.asyncio
    async def test_parse_and_create_materials_denies_grace_before_page_parse(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        product = Product(name="Product Parse", dewu_url="https://example.com/item", parse_status="pending")
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        parse_page = AsyncMock()
        monkeypatch.setattr("services.product_parse_service.parse_product_page", parse_page)

        with pytest.raises(LocalAuthorizationError) as exc_info:
            await parse_and_create_materials(db_session, product)

        assert exc_info.value.error_code == "auth_grace_restricted"
        parse_page.assert_not_called()


class TestMediaStorageAuthGuards:
    @pytest.mark.asyncio
    async def test_store_from_path_denies_expired_before_copy(
        self,
        db_session: AsyncSession,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await _seed_auth_state(db_session, "expired", denial_reason="remote_auth_expired")
        source = tmp_path / "input.bin"
        source.write_bytes(b"payload")
        copy2 = MagicMock()
        monkeypatch.setattr("services.media_storage_service.shutil.copy2", copy2)

        service = MediaStorageService(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.store_from_path(str(source), "videos")

        assert exc_info.value.error_code == "expired"
        copy2.assert_not_called()

    @pytest.mark.asyncio
    async def test_safe_delete_denies_revoked_before_unlink(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await _seed_auth_state(db_session, "revoked", denial_reason="remote_auth_revoked")
        unlink = MagicMock()
        monkeypatch.setattr("services.media_storage_service.os.unlink", unlink)

        service = MediaStorageService(db_session)
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.safe_delete_async("E:/file.bin", "hash", "videos", db_session)

        assert exc_info.value.error_code == "revoked"
        unlink.assert_not_called()


class TestSystemBackupAuthGuards:
    @pytest.mark.asyncio
    async def test_create_backup_denies_grace_before_artifact_creation(
        self,
        db_session: AsyncSession,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await _seed_auth_state(db_session, "authenticated_grace", denial_reason="network_timeout")
        copy2 = MagicMock()
        monkeypatch.setattr("services.system_backup_service.shutil.copy2", copy2)

        service = SystemBackupService(db_session, backup_root=tmp_path / "backups")
        with pytest.raises(LocalAuthorizationError) as exc_info:
            await service.create_backup(include_logs=False)

        assert exc_info.value.error_code == "auth_grace_restricted"
        copy2.assert_not_called()
        assert not (tmp_path / "backups").exists()
