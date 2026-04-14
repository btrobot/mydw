"""
Step 5 PR2: auth metrics tests.

Goals:
1. validate auth metric snapshot values
2. validate login/refresh counter behavior
3. validate duration metrics
4. validate Prometheus text exposure
5. validate `/metrics` endpoint wiring
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from core.auth_events import AuthEvent, AuthEventType, auth_event_emitter
from core.auth_metrics import (
    AuthMetricsCollector,
    AuthMetricsSnapshot,
    MetricValue,
    PrometheusMetricsExporter,
    auth_metrics_collector,
)


class TestMetricValue:
    def test_metric_value_creation(self):
        mv = MetricValue(42.0)
        assert mv.value == 42.0
        assert mv.timestamp is not None
        assert mv.labels == {}

    def test_metric_value_with_labels(self):
        mv = MetricValue(1.0, labels={"status": "success", "type": "login"})
        assert mv.labels["status"] == "success"
        assert mv.labels["type"] == "login"


class TestAuthMetricsSnapshot:
    def test_snapshot_defaults(self):
        snapshot = AuthMetricsSnapshot()
        assert snapshot.login_attempts_total == 0
        assert snapshot.login_success_rate == 0.0
        assert snapshot.refresh_avg_latency_ms == 0.0
        assert snapshot.active_sessions_count == 0

    def test_snapshot_to_dict(self):
        snapshot = AuthMetricsSnapshot()
        snapshot.login_attempts_total = 10
        snapshot.login_success_total = 8
        snapshot.login_success_rate = 80.0
        snapshot.active_sessions_count = 1

        data = snapshot.to_dict()
        assert data["login"]["attempts_total"] == 10
        assert data["login"]["success_total"] == 8
        assert data["login"]["success_rate"] == 80.0
        assert data["sessions"]["active_count"] == 1
        assert "timestamp" in data


class TestAuthMetricsCollector:
    @pytest.fixture(autouse=True)
    def setup(self):
        auth_metrics_collector.reset()
        auth_metrics_collector.register()
        yield
        auth_metrics_collector.unregister()
        auth_metrics_collector.reset()

    def test_collector_registers_with_event_emitter(self):
        assert auth_metrics_collector._registered is True

    def test_login_succeeded_increments_counters(self):
        auth_event_emitter.login_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.login_attempts_total == 1
        assert snapshot.login_success_total == 1
        assert snapshot.login_failure_total == 0
        assert snapshot.login_success_rate == 100.0
        assert snapshot.active_sessions_count == 1

    def test_login_failed_increments_counters(self):
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="invalid_credentials",
            is_network_error=False,
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.login_attempts_total == 1
        assert snapshot.login_success_total == 0
        assert snapshot.login_failure_total == 1
        assert snapshot.login_success_rate == 0.0

    def test_login_mixed_calculates_rate(self):
        for i in range(3):
            auth_event_emitter.login_succeeded(
                remote_user_id=f"user{i}",
                device_id="device456",
                auth_state="authenticated_active",
            )
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="invalid_credentials",
            is_network_error=False,
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.login_attempts_total == 4
        assert snapshot.login_success_total == 3
        assert snapshot.login_failure_total == 1
        assert snapshot.login_success_rate == 75.0

    def test_login_failed_network_error_tracked(self):
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="network_timeout",
            is_network_error=True,
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.errors_network_total == 1
        assert snapshot.errors_remote_rejection_total == 0

    def test_refresh_succeeded_tracks_latency(self):
        auth_event_emitter.refresh_started(remote_user_id="user123", device_id="device456")
        auth_event_emitter.refresh_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.refresh_attempts_total == 1
        assert snapshot.refresh_success_total == 1
        assert snapshot.refresh_success_rate == 100.0
        assert snapshot.refresh_avg_latency_ms >= 0

    def test_refresh_failed_network_error(self):
        auth_event_emitter.refresh_started(remote_user_id="user123", device_id="device456")
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="network_error",
            is_network_error=True,
            is_remote_rejection=False,
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.refresh_attempts_total == 1
        assert snapshot.refresh_failure_total == 1
        assert snapshot.errors_network_total == 1

    def test_refresh_failed_remote_rejection(self):
        auth_event_emitter.refresh_started(remote_user_id="user123", device_id="device456")
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="revoked",
            is_network_error=False,
            is_remote_rejection=True,
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.refresh_failure_total == 1
        assert snapshot.errors_remote_rejection_total == 1

    def test_revoked_tracked_as_remote_rejection(self):
        auth_event_emitter.revoked(
            remote_user_id="user123",
            device_id="device456",
            previous_state="authenticated_active",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.errors_remote_rejection_total == 1
        assert snapshot.sessions_revoked == 1

    def test_device_mismatch_tracked(self):
        auth_event_emitter.device_mismatch(
            remote_user_id="user123",
            expected_device_id="device456",
            actual_device_id="device789",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.errors_device_mismatch_total == 1
        assert snapshot.sessions_device_mismatch == 1

    def test_session_state_tracking(self):
        auth_event_emitter.login_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.sessions_active == 1
        auth_event_emitter.offline_grace_used(remote_user_id="user123", device_id="device456")
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.sessions_grace == 1
        assert snapshot.sessions_active == 0

    def test_background_stopped_tracked(self):
        auth_event_emitter.background_stopped_due_to_auth(
            component="task_scheduler",
            auth_state="revoked",
            reason_code="revoked",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.background_stopped_total == 1

    def test_scheduler_denied_tracked(self):
        auth_event_emitter.scheduler_denied_by_auth(
            auth_state="offline_grace",
            reason_code="offline_grace_restricted",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.scheduler_denied_total == 1

    def test_composition_poller_stopped_tracked(self):
        auth_event_emitter.composition_poller_stopped_due_to_auth(
            auth_state="device_mismatch",
            reason_code="device_mismatch",
        )
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.background_stopped_total == 1

    def test_reset_clears_all_metrics(self):
        auth_event_emitter.login_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        auth_metrics_collector.reset()
        snapshot = auth_metrics_collector.get_snapshot()
        assert snapshot.login_attempts_total == 0
        assert snapshot.login_success_total == 0


class TestAuthMetricsTimeWindows:
    @pytest.fixture(autouse=True)
    def setup(self):
        auth_metrics_collector.reset()
        auth_metrics_collector.register()
        yield
        auth_metrics_collector.unregister()
        auth_metrics_collector.reset()

    def test_get_login_success_rate_default_window(self):
        for i in range(4):
            auth_event_emitter.login_succeeded(
                remote_user_id=f"user{i}",
                device_id="device456",
                auth_state="authenticated_active",
            )
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="invalid_credentials",
            is_network_error=False,
        )
        rate = auth_metrics_collector.get_login_success_rate()
        assert rate == 80.0

    def test_get_login_success_rate_empty(self):
        assert auth_metrics_collector.get_login_success_rate() == 100.0

    def test_get_refresh_stats(self):
        auth_event_emitter.refresh_started(remote_user_id="user123", device_id="device456")
        auth_event_emitter.refresh_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        stats = auth_metrics_collector.get_refresh_stats()
        assert stats["attempts"] == 1
        assert stats["successes"] == 1
        assert stats["success_rate"] == 100.0
        assert stats["avg_latency_ms"] >= 0


class TestAuthMetricsCollectorIndependent:
    def test_independent_collector(self):
        collector = AuthMetricsCollector()
        collector._handle_auth_login_succeeded(
            AuthEvent(
                event_name=AuthEventType.AUTH_LOGIN_SUCCEEDED,
                remote_user_id="user123",
                device_id="device456",
                auth_state="authenticated_active",
            )
        )
        snapshot = collector.get_snapshot()
        assert snapshot.login_attempts_total == 1
        assert snapshot.login_success_total == 1

    def test_session_duration_and_grace_usage_accumulate(self):
        collector = AuthMetricsCollector(now_fn=lambda: datetime(2026, 4, 14, 0, 0, 12, tzinfo=UTC))
        collector._handle_auth_login_succeeded(
            AuthEvent(
                event_name=AuthEventType.AUTH_LOGIN_SUCCEEDED,
                auth_state="authenticated_active",
                timestamp=datetime(2026, 4, 14, 0, 0, 0, tzinfo=UTC),
            )
        )
        collector._handle_auth_offline_grace_used(
            AuthEvent(
                event_name=AuthEventType.AUTH_OFFLINE_GRACE_USED,
                auth_state="authenticated_grace",
                timestamp=datetime(2026, 4, 14, 0, 0, 5, tzinfo=UTC),
            )
        )
        collector._handle_auth_refresh_succeeded(
            AuthEvent(
                event_name=AuthEventType.AUTH_REFRESH_SUCCEEDED,
                auth_state="authenticated_active",
                timestamp=datetime(2026, 4, 14, 0, 0, 9, tzinfo=UTC),
            )
        )
        collector._handle_auth_logout_completed(
            AuthEvent(
                event_name=AuthEventType.AUTH_LOGOUT_COMPLETED,
                auth_state="unauthenticated",
                timestamp=datetime(2026, 4, 14, 0, 0, 12, tzinfo=UTC),
            )
        )
        snapshot = collector.get_snapshot()
        assert snapshot.session_duration_seconds_total == 8.0
        assert snapshot.grace_period_usage_seconds_total == 4.0


class TestPrometheusExporter:
    def test_export_contains_required_pr2_metrics(self):
        collector = AuthMetricsCollector()
        collector._handle_auth_login_succeeded(
            AuthEvent(
                event_name=AuthEventType.AUTH_LOGIN_SUCCEEDED,
                auth_state="authenticated_active",
                timestamp=datetime.now(UTC),
            )
        )
        payload = PrometheusMetricsExporter(collector).export()
        assert "auth_active_sessions_count" in payload
        assert "auth_login_attempts_total" in payload
        assert "auth_login_failures_total" in payload
        assert "auth_refresh_attempts_total" in payload
        assert "auth_refresh_failures_total" in payload
        assert "auth_session_duration_seconds" in payload
        assert "auth_grace_period_usage_seconds" in payload


class TestMetricsEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self):
        auth_metrics_collector.reset()
        auth_metrics_collector.register()
        yield
        auth_metrics_collector.unregister()
        auth_metrics_collector.reset()

    @pytest.mark.asyncio
    async def test_metrics_endpoint_exists(self, client: AsyncClient) -> None:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert response.text

    @pytest.mark.asyncio
    async def test_metrics_format_valid(self, client: AsyncClient) -> None:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "# HELP auth_login_attempts_total" in response.text
        assert "# TYPE auth_login_attempts_total counter" in response.text

    @pytest.mark.asyncio
    async def test_metrics_values_correct(self, client: AsyncClient) -> None:
        auth_event_emitter.login_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="invalid_credentials",
            is_network_error=False,
        )
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "auth_login_attempts_total 2" in response.text
        assert "auth_login_failures_total 1" in response.text
        assert "auth_active_sessions_count 1" in response.text
