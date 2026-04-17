"""
Step 3 / PR5 tests for scheduler and composition poller runtime auth rules.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_events import auth_event_emitter
import models
from models import Account, CompositionJob, Task
from schemas.auth import LocalAuthSessionSummary
from services.scheduler import (
    CompositionPoller,
    RuntimeAuthDecision,
    RuntimeAuthHalt,
    TaskScheduler,
)


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


def _decision(
    action: str,
    auth_state: str,
    *,
    denial_reason: str | None = None,
    reason_code: str | None = None,
) -> RuntimeAuthDecision:
    return RuntimeAuthDecision(
        action=action,  # type: ignore[arg-type]
        summary=_summary(auth_state, denial_reason=denial_reason),
        reason_code=reason_code,
    )


class _AsyncSessionContext:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def __aenter__(self) -> AsyncSession:
        return self.db

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


async def _create_account(db_session: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"runtime_{suffix}",
        account_name=f"Runtime {suffix}",
        status="active",
        storage_state="{}",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


class TestTaskSchedulerRuntimeAuth:
    @pytest.mark.asyncio
    async def test_start_publishing_denies_grace_and_enters_paused_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scheduler = TaskScheduler()
        monkeypatch.setattr(
            scheduler,
            "_load_runtime_auth_decision_from_new_session",
            AsyncMock(
                return_value=_decision(
                    "pause",
                    "authenticated_grace",
                    denial_reason="network_timeout",
                    reason_code="offline_grace_restricted",
                )
            ),
        )
        scheduler_denied_by_auth = MagicMock()
        monkeypatch.setattr(auth_event_emitter, "scheduler_denied_by_auth", scheduler_denied_by_auth)

        result = await scheduler.start_publishing()

        assert result["success"] is False
        assert result["auth_state"] == "authenticated_grace"
        assert scheduler.get_status() == "paused"
        scheduler_denied_by_auth.assert_called_once_with(
            auth_state="authenticated_grace",
            reason_code="offline_grace_restricted",
        )

    @pytest.mark.asyncio
    async def test_start_publishing_denies_revoked_without_running(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scheduler = TaskScheduler()
        monkeypatch.setattr(
            scheduler,
            "_load_runtime_auth_decision_from_new_session",
            AsyncMock(
                return_value=_decision(
                    "stop",
                    "revoked",
                    denial_reason="remote_auth_revoked",
                    reason_code="remote_auth_revoked",
                )
            ),
        )
        scheduler_denied_by_auth = MagicMock()
        monkeypatch.setattr(auth_event_emitter, "scheduler_denied_by_auth", scheduler_denied_by_auth)

        result = await scheduler.start_publishing()

        assert result["success"] is False
        assert result["reason_code"] == "remote_auth_revoked"
        assert scheduler.get_status() == "idle"
        scheduler_denied_by_auth.assert_called_once_with(
            auth_state="revoked",
            reason_code="remote_auth_revoked",
        )

    @pytest.mark.asyncio
    async def test_publish_loop_pauses_before_fetching_new_task_when_grace(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scheduler = TaskScheduler()
        monkeypatch.setattr(
            scheduler,
            "_load_runtime_auth_decision",
            AsyncMock(
                return_value=_decision(
                    "pause",
                    "authenticated_grace",
                    denial_reason="network_timeout",
                    reason_code="offline_grace_restricted",
                )
            ),
        )
        background_stopped_due_to_auth = MagicMock()
        monkeypatch.setattr(
            auth_event_emitter,
            "background_stopped_due_to_auth",
            background_stopped_due_to_auth,
        )
        get_next_task = AsyncMock()
        monkeypatch.setattr("services.publish_service.PublishService.get_next_task", get_next_task)
        monkeypatch.setattr(models, "async_session", lambda: _AsyncSessionContext(db_session))

        await scheduler._publish_loop()

        assert scheduler.get_status() == "paused"
        get_next_task.assert_not_called()
        background_stopped_due_to_auth.assert_called_once_with(
            component="task_scheduler",
            auth_state="authenticated_grace",
            reason_code="offline_grace_restricted",
        )

    @pytest.mark.asyncio
    async def test_publish_loop_stops_after_current_task_when_post_publish_auth_is_revoked(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scheduler = TaskScheduler()
        task = SimpleNamespace(id=123)
        monkeypatch.setattr(
            scheduler,
            "_load_runtime_auth_decision",
            AsyncMock(
                side_effect=[
                    _decision("allow", "authenticated_active"),
                    _decision("allow", "authenticated_active"),
                    _decision(
                        "stop",
                        "revoked",
                        denial_reason="remote_auth_revoked",
                        reason_code="remote_auth_revoked",
                    ),
                ]
            ),
        )
        monkeypatch.setattr(
            scheduler,
            "_get_schedule_config",
            AsyncMock(return_value=SimpleNamespace(interval_minutes=30, shuffle=False)),
        )
        background_stopped_due_to_auth = MagicMock()
        monkeypatch.setattr(
            auth_event_emitter,
            "background_stopped_due_to_auth",
            background_stopped_due_to_auth,
        )
        monkeypatch.setattr("services.publish_service.PublishService.get_next_task", AsyncMock(return_value=task))
        publish_task = AsyncMock(return_value=(True, "ok"))
        monkeypatch.setattr("services.publish_service.PublishService.publish_task", publish_task)
        monkeypatch.setattr(models, "async_session", lambda: _AsyncSessionContext(db_session))

        await scheduler._publish_loop()

        assert scheduler.get_status() == "idle"
        assert scheduler.current_task_id() is None
        publish_task.assert_awaited_once()
        background_stopped_due_to_auth.assert_called_once_with(
            component="task_scheduler",
            auth_state="revoked",
            reason_code="remote_auth_revoked",
        )

    @pytest.mark.asyncio
    async def test_publish_loop_pauses_after_current_task_when_post_publish_auth_is_grace(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scheduler = TaskScheduler()
        task = SimpleNamespace(id=456)
        monkeypatch.setattr(
            scheduler,
            "_load_runtime_auth_decision",
            AsyncMock(
                side_effect=[
                    _decision("allow", "authenticated_active"),
                    _decision("allow", "authenticated_active"),
                    _decision(
                        "pause",
                        "authenticated_grace",
                        denial_reason="network_timeout",
                        reason_code="offline_grace_restricted",
                    ),
                ]
            ),
        )
        monkeypatch.setattr(
            scheduler,
            "_get_schedule_config",
            AsyncMock(return_value=SimpleNamespace(interval_minutes=30, shuffle=False)),
        )
        background_stopped_due_to_auth = MagicMock()
        monkeypatch.setattr(
            auth_event_emitter,
            "background_stopped_due_to_auth",
            background_stopped_due_to_auth,
        )
        monkeypatch.setattr("services.publish_service.PublishService.get_next_task", AsyncMock(return_value=task))
        publish_task = AsyncMock(return_value=(True, "ok"))
        monkeypatch.setattr("services.publish_service.PublishService.publish_task", publish_task)
        monkeypatch.setattr(models, "async_session", lambda: _AsyncSessionContext(db_session))

        await scheduler._publish_loop()

        assert scheduler.get_status() == "paused"
        assert scheduler.current_task_id() is None
        publish_task.assert_awaited_once()
        background_stopped_due_to_auth.assert_called_once_with(
            component="task_scheduler",
            auth_state="authenticated_grace",
            reason_code="offline_grace_restricted",
        )


class TestCompositionPollerRuntimeAuth:
    @pytest.mark.asyncio
    async def test_start_denies_grace_without_running(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        poller = CompositionPoller()
        monkeypatch.setattr(
            poller,
            "_load_runtime_auth_decision_from_new_session",
            AsyncMock(
                return_value=_decision(
                    "pause",
                    "authenticated_grace",
                    denial_reason="network_timeout",
                    reason_code="offline_grace_restricted",
                )
            ),
        )
        scheduler_denied_by_auth = MagicMock()
        monkeypatch.setattr(auth_event_emitter, "scheduler_denied_by_auth", scheduler_denied_by_auth)

        result = await poller.start()

        assert result["success"] is False
        assert result["auth_state"] == "authenticated_grace"
        assert poller.is_running() is False
        scheduler_denied_by_auth.assert_called_once_with(
            auth_state="authenticated_grace",
            reason_code="offline_grace_restricted",
        )

    @pytest.mark.asyncio
    async def test_start_denies_revoked_without_running(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        poller = CompositionPoller()
        monkeypatch.setattr(
            poller,
            "_load_runtime_auth_decision_from_new_session",
            AsyncMock(
                return_value=_decision(
                    "stop",
                    "revoked",
                    denial_reason="remote_auth_revoked",
                    reason_code="remote_auth_revoked",
                )
            ),
        )
        scheduler_denied_by_auth = MagicMock()
        monkeypatch.setattr(auth_event_emitter, "scheduler_denied_by_auth", scheduler_denied_by_auth)

        result = await poller.start()

        assert result["success"] is False
        assert result["reason_code"] == "remote_auth_revoked"
        assert poller.is_running() is False
        scheduler_denied_by_auth.assert_called_once_with(
            auth_state="revoked",
            reason_code="remote_auth_revoked",
        )

    @pytest.mark.asyncio
    async def test_poll_compositions_hard_stop_after_remote_success_preserves_composing_state(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session, "poller_stop")
        task = Task(account_id=account.id, status="composing")
        db_session.add(task)
        await db_session.flush()
        job = CompositionJob(
            task_id=task.id,
            workflow_type="coze",
            workflow_id="wf-1",
            external_job_id="job-1",
            status="pending",
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(task)
        await db_session.refresh(job)

        poller = CompositionPoller()
        monkeypatch.setattr(
            poller,
            "_load_runtime_auth_decision",
            AsyncMock(
                side_effect=[
                    _decision("allow", "authenticated_active"),
                    _decision(
                        "stop",
                        "revoked",
                        denial_reason="remote_auth_revoked",
                        reason_code="remote_auth_revoked",
                    ),
                ]
            ),
        )
        monkeypatch.setattr(poller, "_get_current_task_id", lambda: task.id)
        handle_success = AsyncMock()
        handle_failure = AsyncMock()
        composition_service_cls = lambda db: SimpleNamespace(
            handle_success=handle_success,
            handle_failure=handle_failure,
        )
        coze_client_cls = lambda: SimpleNamespace(
            check_status=AsyncMock(return_value=("success", {"video_url": "https://example.com/out.mp4"}))
        )

        with pytest.raises(RuntimeAuthHalt) as exc_info:
            await poller._poll_compositions(db_session, composition_service_cls, coze_client_cls)

        assert exc_info.value.decision.reason_code == "remote_auth_revoked"
        handle_success.assert_not_called()
        handle_failure.assert_not_called()
        refreshed_task = await db_session.get(Task, task.id)
        refreshed_job = await db_session.get(CompositionJob, job.id)
        assert refreshed_task.status == "composing"
        assert refreshed_job.status == "pending"

    @pytest.mark.asyncio
    async def test_poll_compositions_grace_after_remote_success_preserves_composing_state(
        self,
        db_session: AsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        account = await _create_account(db_session, "poller_pause")
        task = Task(account_id=account.id, status="composing")
        db_session.add(task)
        await db_session.flush()
        job = CompositionJob(
            task_id=task.id,
            workflow_type="coze",
            workflow_id="wf-2",
            external_job_id="job-2",
            status="pending",
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(task)
        await db_session.refresh(job)

        poller = CompositionPoller()
        monkeypatch.setattr(
            poller,
            "_load_runtime_auth_decision",
            AsyncMock(
                side_effect=[
                    _decision("allow", "authenticated_active"),
                    _decision(
                        "pause",
                        "authenticated_grace",
                        denial_reason="network_timeout",
                        reason_code="offline_grace_restricted",
                    ),
                ]
            ),
        )
        monkeypatch.setattr(poller, "_get_current_task_id", lambda: task.id)
        handle_success = AsyncMock()
        handle_failure = AsyncMock()
        composition_service_cls = lambda db: SimpleNamespace(
            handle_success=handle_success,
            handle_failure=handle_failure,
        )
        coze_client_cls = lambda: SimpleNamespace(
            check_status=AsyncMock(return_value=("success", {"video_url": "https://example.com/out.mp4"}))
        )

        with pytest.raises(RuntimeAuthHalt) as exc_info:
            await poller._poll_compositions(db_session, composition_service_cls, coze_client_cls)

        assert exc_info.value.decision.action == "pause"
        handle_success.assert_not_called()
        handle_failure.assert_not_called()
        refreshed_task = await db_session.get(Task, task.id)
        refreshed_job = await db_session.get(CompositionJob, job.id)
        assert refreshed_task.status == "composing"
        assert refreshed_job.status == "pending"
