"""
Step 3 / PR2 tests for control-plane and high-risk router auth gates.
"""
from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import api.account as account_api
import api.publish as publish_api
import api.system as system_api
from core.auth_dependencies import (
    LocalAuthorizationError,
    POLICY_ACTIVE_REQUIRED,
    POLICY_GRACE_READONLY_ALLOWED,
    enforce_machine_session_policy,
    get_machine_session_summary,
    set_current_auth_summary,
    require_active_machine_session,
    require_grace_readonly_machine_session,
)
from main import app
from models import Account, CompositionJob, RemoteAuthSession, ScheduleConfig, SystemLog, Task
from schemas.auth import LocalAuthSessionSummary


def _summary(
    auth_state: str,
    *,
    denial_reason: str | None = None,
) -> LocalAuthSessionSummary:
    return LocalAuthSessionSummary(
        auth_state=auth_state,
        remote_user_id="u_123" if auth_state != "unauthenticated" else None,
        display_name="Alice" if auth_state != "unauthenticated" else None,
        license_status="active" if auth_state != "unauthenticated" else None,
        entitlements=["dashboard:view"],
        denial_reason=denial_reason,
        device_id="device-1",
    )


@pytest.fixture()
def set_auth_state(db_session: AsyncSession):
    async def _install(auth_state: str, *, denial_reason: str | None = None) -> None:
        summary = _summary(auth_state, denial_reason=denial_reason)
        existing = await db_session.execute(select(RemoteAuthSession))
        for row in existing.scalars().all():
            await db_session.delete(row)
        db_session.add(
            RemoteAuthSession(
                auth_state=auth_state,
                remote_user_id=summary.remote_user_id,
                display_name=summary.display_name,
                license_status=summary.license_status,
                denial_reason=summary.denial_reason,
                device_id=summary.device_id,
            )
        )
        await db_session.commit()

        def _active_override() -> LocalAuthSessionSummary:
            try:
                allowed = enforce_machine_session_policy(summary, policy=POLICY_ACTIVE_REQUIRED)
                set_current_auth_summary(allowed)
                return allowed
            except LocalAuthorizationError as exc:
                raise exc.to_http_exception() from exc

        def _grace_override() -> LocalAuthSessionSummary:
            try:
                allowed = enforce_machine_session_policy(summary, policy=POLICY_GRACE_READONLY_ALLOWED)
                set_current_auth_summary(allowed)
                return allowed
            except LocalAuthorizationError as exc:
                raise exc.to_http_exception() from exc

        app.dependency_overrides[require_active_machine_session] = _active_override
        app.dependency_overrides[require_grace_readonly_machine_session] = _grace_override
        app.dependency_overrides[get_machine_session_summary] = lambda: (set_current_auth_summary(summary), summary)[1]

    yield _install


async def _create_account(db_session: AsyncSession, *, account_id: str = "acct-1") -> Account:
    account = Account(account_id=account_id, account_name=f"Account {account_id}", status="active")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


class TestTaskRouterAuthGates:
    @pytest.mark.asyncio
    async def test_task_list_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        account = await _create_account(db_session)
        db_session.add(Task(account_id=account.id, status="draft"))
        await db_session.commit()

        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/tasks/")

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_task_publish_denies_grace_before_task_lookup(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session)
        task = Task(account_id=account.id, status="ready")
        db_session.add(task)
        await db_session.commit()

        get_task = AsyncMock()
        monkeypatch.setattr("api.task.TaskService.get_task", get_task)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(f"/api/tasks/{task.id}/publish")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "auth_grace_restricted"
        get_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_composition_denies_grace_before_service_call(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session)
        task = Task(account_id=account.id, status="draft")
        db_session.add(task)
        await db_session.commit()

        submit_composition = AsyncMock()
        monkeypatch.setattr("api.task.CompositionService.submit_composition", submit_composition)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(f"/api/tasks/{task.id}/submit-composition")

        assert response.status_code == 403
        assert response.json()["detail"]["policy"] == POLICY_ACTIVE_REQUIRED
        submit_composition.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_publish_allows_active_and_reaches_handler(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session)
        task = Task(account_id=account.id, status="ready")
        db_session.add(task)
        await db_session.commit()

        task_service_task = Task(id=task.id, account_id=account.id, status="ready")
        get_task = AsyncMock(return_value=task_service_task)
        monkeypatch.setattr("api.task.TaskService.get_task", get_task)

        response = await client.post(f"/api/tasks/{task.id}/publish")

        assert response.status_code == 200
        assert response.json()["success"] is True
        get_task.assert_awaited_once_with(task.id)

    @pytest.mark.asyncio
    async def test_composition_status_is_not_public_for_revoked_state(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        account = await _create_account(db_session)
        task = Task(account_id=account.id, status="composing")
        db_session.add(task)
        await db_session.flush()
        job = CompositionJob(task_id=task.id, status="running")
        db_session.add(job)
        await db_session.flush()
        task.composition_job_id = job.id
        await db_session.commit()

        await set_auth_state("revoked", denial_reason="remote_auth_revoked")

        response = await client.get(f"/api/tasks/{task.id}/composition-status")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "revoked"


class TestPublishRouterAuthGates:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("auth_state", "denial_reason", "expected_status"),
        [
            ("authenticated_grace", "network_timeout", 200),
            ("unauthenticated", None, 401),
            ("expired", "remote_auth_expired", 401),
            ("revoked", "remote_auth_revoked", 403),
            ("device_mismatch", "remote_auth_device_mismatch", 403),
        ],
    )
    async def test_publish_status_follows_grace_and_denial_matrix(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        auth_state: str,
        denial_reason: str | None,
        expected_status: int,
    ) -> None:
        account = await _create_account(db_session)
        db_session.add(Task(account_id=account.id, status="ready"))
        await db_session.commit()

        await set_auth_state(auth_state, denial_reason=denial_reason)

        response = await client.get("/api/publish/status")

        assert response.status_code == expected_status
        if expected_status != 200:
            assert response.json()["detail"]["auth_state"] == auth_state

    @pytest.mark.asyncio
    async def test_publish_control_denies_grace_without_scheduler_side_effect(
        self,
        client: AsyncClient,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        start_publishing = AsyncMock(return_value={"success": True, "message": "started"})
        monkeypatch.setattr(publish_api.scheduler, "start_publishing", start_publishing)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post("/api/publish/control", json={"action": "start"})

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "auth_grace_restricted"
        start_publishing.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_control_allows_active_and_calls_scheduler(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        start_publishing = AsyncMock(return_value={"success": True, "message": "started"})
        monkeypatch.setattr(publish_api.scheduler, "is_running", lambda: False)
        monkeypatch.setattr(publish_api.scheduler, "start_publishing", start_publishing)

        response = await client.post("/api/publish/control", json={"action": "start"})

        assert response.status_code == 200
        assert response.json()["action"] == "start"
        start_publishing.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_publish_logs_denies_device_mismatch(
        self,
        client: AsyncClient,
        set_auth_state,
    ) -> None:
        await set_auth_state("device_mismatch", denial_reason="remote_auth_device_mismatch")

        response = await client.get("/api/publish/logs")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "device_mismatch"


class TestAccountRouterAuthGates:
    @pytest.mark.asyncio
    async def test_account_list_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        await _create_account(db_session)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/accounts/")

        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_account_connect_stream_denies_unauthenticated_before_streaming(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session)
        subscribe = AsyncMock()
        monkeypatch.setattr(account_api.connection_status_manager, "subscribe", subscribe)
        await set_auth_state("unauthenticated")

        response = await client.get(f"/api/accounts/connect/{account.id}/stream")

        assert response.status_code == 401
        assert response.json()["detail"]["error_code"] == "unauthenticated"
        subscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_account_connect_status_requires_active_auth(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session)
        get_context = AsyncMock(return_value=None)
        monkeypatch.setattr(account_api.browser_manager, "get_context", get_context)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get(f"/api/accounts/connect/{account.id}/status")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "auth_grace_restricted"
        get_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_account_import_denies_grace_without_mutating_storage_state(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        account = await _create_account(db_session)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(
            f"/api/accounts/connect/{account.id}/import",
            json={"storage_state": "encrypted-state"},
        )

        assert response.status_code == 403
        await db_session.refresh(account)
        assert account.storage_state is None

    @pytest.mark.asyncio
    async def test_deprecated_login_stream_matches_canonical_denial(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        account = await _create_account(db_session)
        await set_auth_state("revoked", denial_reason="remote_auth_revoked")

        canonical = await client.get(f"/api/accounts/connect/{account.id}/stream")
        deprecated = await client.get(f"/api/accounts/login/{account.id}/stream")

        assert canonical.status_code == 403
        assert deprecated.status_code == 403
        assert canonical.json()["detail"] == deprecated.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("method", "canonical_template", "deprecated_template", "payload"),
        [
            ("get", "/api/accounts/connect/{account_id}/status", "/api/accounts/login/{account_id}/status", None),
            ("post", "/api/accounts/connect/{account_id}/export", "/api/accounts/login/{account_id}/export", None),
            (
                "post",
                "/api/accounts/connect/{account_id}/import",
                "/api/accounts/login/{account_id}/import",
                {"storage_state": "encrypted-state"},
            ),
            ("get", "/api/accounts/connect/{account_id}/screenshot", "/api/accounts/login/{account_id}/screenshot", None),
        ],
    )
    async def test_deprecated_aliases_match_canonical_denial(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        method: str,
        canonical_template: str,
        deprecated_template: str,
        payload: dict | None,
    ) -> None:
        account = await _create_account(db_session)
        await set_auth_state("revoked", denial_reason="remote_auth_revoked")

        request = getattr(client, method)
        request_kwargs = {"json": payload} if payload is not None else {}
        canonical = await request(canonical_template.format(account_id=account.id), **request_kwargs)
        deprecated = await request(deprecated_template.format(account_id=account.id), **request_kwargs)

        assert canonical.status_code == 403
        assert deprecated.status_code == 403
        assert canonical.json()["detail"] == deprecated.json()["detail"]

    @pytest.mark.asyncio
    async def test_account_screenshot_denies_unauthenticated_before_browser_call(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session)
        get_dewu_client = AsyncMock()
        monkeypatch.setattr(account_api, "get_dewu_client", get_dewu_client)
        await set_auth_state("unauthenticated")

        response = await client.get(f"/api/accounts/connect/{account.id}/screenshot")

        assert response.status_code == 401
        assert response.json()["detail"]["error_code"] == "unauthenticated"
        get_dewu_client.assert_not_called()


class TestSystemRouterAuthGates:
    @pytest.mark.asyncio
    async def test_system_logs_allow_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        db_session.add(SystemLog(level="INFO", module="test", message="hello"))
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/system/logs")

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_system_backup_denies_grace_without_service_call(
        self,
        client: AsyncClient,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        create_backup = AsyncMock(return_value=Path("backup.zip"))
        monkeypatch.setattr(system_api.SystemBackupService, "create_backup", create_backup)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post("/api/system/backup", json={"include_logs": True})

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "auth_grace_restricted"
        create_backup.assert_not_called()

    @pytest.mark.asyncio
    async def test_system_config_update_denies_grace_without_service_call(
        self,
        client: AsyncClient,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        update_config = AsyncMock()
        monkeypatch.setattr(system_api.SystemConfigService, "update_config", update_config)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.put("/api/system/config?material_base_path=C:/materials")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "auth_grace_restricted"
        update_config.assert_not_called()


class TestScheduleConfigRouterAuthGates:
    @pytest.mark.asyncio
    async def test_schedule_config_get_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        db_session.add(ScheduleConfig(name="default", interval_minutes=30))
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/schedule-config")

        assert response.status_code == 200
        assert response.json()["name"] == "default"

    @pytest.mark.asyncio
    async def test_schedule_config_put_denies_expired(
        self,
        client: AsyncClient,
        set_auth_state,
    ) -> None:
        await set_auth_state("expired", denial_reason="remote_auth_expired")

        response = await client.put(
            "/api/schedule-config",
            json={
                "start_hour": 9,
                "end_hour": 22,
                "interval_minutes": 20,
                "max_per_account_per_day": 5,
                "shuffle": False,
                "auto_start": False,
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"]["error_code"] == "expired"

    @pytest.mark.asyncio
    async def test_schedule_config_put_allows_active_and_calls_service(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        update_default = AsyncMock(
            return_value=ScheduleConfig(
                id=1,
                name="default",
                start_hour=9,
                end_hour=22,
                interval_minutes=20,
                max_per_account_per_day=5,
                shuffle=False,
                auto_start=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        monkeypatch.setattr("api.schedule_config.ScheduleConfigService.update_default", update_default)

        response = await client.put(
            "/api/schedule-config",
            json={
                "start_hour": 9,
                "end_hour": 22,
                "interval_minutes": 20,
                "max_per_account_per_day": 5,
                "shuffle": False,
                "auto_start": False,
            },
        )

        assert response.status_code == 200
        assert response.json()["interval_minutes"] == 20
        update_default.assert_awaited_once()
