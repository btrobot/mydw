"""
Authentication metrics collection and Prometheus export.

Step 5 / PR2 focuses on auth observability without changing the auth
state-machine semantics introduced in earlier steps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable

from core.auth_events import AuthEvent, AuthEventType, auth_event_emitter


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class AuthMetricsSnapshot:
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    login_attempts_total: int = 0
    login_success_total: int = 0
    login_failure_total: int = 0
    login_success_rate: float = 0.0
    refresh_attempts_total: int = 0
    refresh_success_total: int = 0
    refresh_failure_total: int = 0
    refresh_success_rate: float = 0.0
    refresh_avg_latency_ms: float = 0.0
    active_sessions_count: int = 0
    sessions_active: int = 0
    sessions_grace: int = 0
    sessions_expired: int = 0
    sessions_revoked: int = 0
    sessions_unauthenticated: int = 0
    sessions_device_mismatch: int = 0
    errors_network_total: int = 0
    errors_remote_rejection_total: int = 0
    errors_device_mismatch_total: int = 0
    scheduler_denied_total: int = 0
    background_stopped_total: int = 0
    session_duration_seconds_total: float = 0.0
    grace_period_usage_seconds_total: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "login": {
                "attempts_total": self.login_attempts_total,
                "success_total": self.login_success_total,
                "failure_total": self.login_failure_total,
                "success_rate": round(self.login_success_rate, 2),
            },
            "refresh": {
                "attempts_total": self.refresh_attempts_total,
                "success_total": self.refresh_success_total,
                "failure_total": self.refresh_failure_total,
                "success_rate": round(self.refresh_success_rate, 2),
                "avg_latency_ms": round(self.refresh_avg_latency_ms, 2),
            },
            "sessions": {
                "active_count": self.active_sessions_count,
                "active": self.sessions_active,
                "grace": self.sessions_grace,
                "expired": self.sessions_expired,
                "revoked": self.sessions_revoked,
                "unauthenticated": self.sessions_unauthenticated,
                "device_mismatch": self.sessions_device_mismatch,
            },
            "errors": {
                "network_total": self.errors_network_total,
                "remote_rejection_total": self.errors_remote_rejection_total,
                "device_mismatch_total": self.errors_device_mismatch_total,
            },
            "background": {
                "scheduler_denied_total": self.scheduler_denied_total,
                "stopped_total": self.background_stopped_total,
            },
            "durations": {
                "session_duration_seconds_total": round(self.session_duration_seconds_total, 2),
                "grace_period_usage_seconds_total": round(self.grace_period_usage_seconds_total, 2),
            },
        }


class AuthMetricsCollector:
    def __init__(self, *, now_fn: Callable[[], datetime] | None = None) -> None:
        self.now_fn = now_fn or (lambda: datetime.now(UTC))
        self._registered = False
        self.reset()

    def register(self) -> None:
        if not self._registered:
            auth_event_emitter.register_callback(self._on_event)
            self._registered = True

    def unregister(self) -> None:
        if self._registered:
            auth_event_emitter.unregister_callback(self._on_event)
            self._registered = False

    def reset(self) -> None:
        self._login_attempts: list[MetricValue] = []
        self._login_successes: list[MetricValue] = []
        self._login_failures: list[MetricValue] = []
        self._refresh_attempts: list[MetricValue] = []
        self._refresh_successes: list[MetricValue] = []
        self._refresh_failures: list[MetricValue] = []
        self._refresh_latencies: list[MetricValue] = []
        self._errors_network: list[MetricValue] = []
        self._errors_remote_rejection: list[MetricValue] = []
        self._errors_device_mismatch: list[MetricValue] = []
        self._scheduler_denied: list[MetricValue] = []
        self._background_stopped: list[MetricValue] = []
        self._session_duration_seconds_total = 0.0
        self._grace_period_usage_seconds_total = 0.0
        self._refresh_start_time: datetime | None = None
        self._active_started_at: datetime | None = None
        self._grace_started_at: datetime | None = None
        self._current_session_state: str | None = None

    def _timestamp_or_now(self, event: AuthEvent | None = None) -> datetime:
        if event is None:
            return self.now_fn()
        timestamp = event.timestamp
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=UTC)
        return timestamp

    def _record_point(self, bucket: list[MetricValue], value: float = 1.0, *, at: datetime | None = None) -> None:
        bucket.append(MetricValue(value=value, timestamp=at or self.now_fn()))

    def _normalize_event_name(self, event_name: str | AuthEventType) -> str:
        return event_name.value if isinstance(event_name, AuthEventType) else str(event_name)

    def _state_bucket_name(self, state: str) -> str | None:
        return {
            "authenticated_active": "sessions_active",
            "authenticated_grace": "sessions_grace",
            "expired": "sessions_expired",
            "revoked": "sessions_revoked",
            "unauthenticated": "sessions_unauthenticated",
            "device_mismatch": "sessions_device_mismatch",
        }.get(state)

    def _close_active_session(self, ended_at: datetime) -> None:
        if self._active_started_at is not None:
            self._session_duration_seconds_total += max((ended_at - self._active_started_at).total_seconds(), 0.0)
            self._active_started_at = None

    def _close_grace_session(self, ended_at: datetime) -> None:
        if self._grace_started_at is not None:
            self._grace_period_usage_seconds_total += max((ended_at - self._grace_started_at).total_seconds(), 0.0)
            self._grace_started_at = None

    def _transition_state(self, new_state: str | None, *, at: datetime) -> None:
        if new_state is None or self._current_session_state == new_state:
            return
        if self._current_session_state == "authenticated_active":
            self._close_active_session(at)
        if self._current_session_state == "authenticated_grace":
            self._close_grace_session(at)
        self._current_session_state = new_state
        if new_state == "authenticated_active":
            self._active_started_at = at
        elif new_state == "authenticated_grace":
            self._grace_started_at = at

    def _on_event(self, event: AuthEvent) -> None:
        handler = getattr(self, f"_handle_{self._normalize_event_name(event.event_name)}", None)
        if handler is not None:
            handler(event)

    def _handle_auth_login_succeeded(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._record_point(self._login_attempts, at=at)
        self._record_point(self._login_successes, at=at)
        self._transition_state("authenticated_active", at=at)

    def _handle_auth_login_failed(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._record_point(self._login_attempts, at=at)
        self._record_point(self._login_failures, at=at)
        if event.extra.get("is_network_error"):
            self._record_point(self._errors_network, at=at)
        if event.auth_state:
            self._transition_state(event.auth_state, at=at)

    def _handle_auth_session_restored(self, event: AuthEvent) -> None:
        self._transition_state(event.auth_state, at=self._timestamp_or_now(event))

    def _handle_auth_session_restore_failed(self, event: AuthEvent) -> None:
        self._transition_state(event.auth_state or "unauthenticated", at=self._timestamp_or_now(event))

    def _handle_auth_logout_completed(self, event: AuthEvent) -> None:
        self._transition_state("unauthenticated", at=self._timestamp_or_now(event))

    def _handle_auth_refresh_started(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._refresh_start_time = at
        self._record_point(self._refresh_attempts, at=at)

    def _handle_auth_refresh_succeeded(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._record_point(self._refresh_successes, at=at)
        if self._refresh_start_time is not None:
            self._record_point(self._refresh_latencies, value=max((at - self._refresh_start_time).total_seconds() * 1000, 0.0), at=at)
        self._refresh_start_time = None
        self._transition_state("authenticated_active", at=at)

    def _handle_auth_refresh_failed(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._record_point(self._refresh_failures, at=at)
        self._refresh_start_time = None
        if event.extra.get("is_network_error"):
            self._record_point(self._errors_network, at=at)
        if event.extra.get("is_remote_rejection"):
            self._record_point(self._errors_remote_rejection, at=at)
        if event.auth_state:
            self._transition_state(event.auth_state, at=at)

    def _handle_auth_me_validation_failed(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        if event.reason_code == "network_error":
            self._record_point(self._errors_network, at=at)
        if event.auth_state:
            self._transition_state(event.auth_state, at=at)

    def _handle_auth_revoked(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._record_point(self._errors_remote_rejection, at=at)
        self._transition_state("revoked", at=at)

    def _handle_auth_device_mismatch(self, event: AuthEvent) -> None:
        at = self._timestamp_or_now(event)
        self._record_point(self._errors_device_mismatch, at=at)
        self._transition_state("device_mismatch", at=at)

    def _handle_auth_expired(self, event: AuthEvent) -> None:
        self._transition_state("expired", at=self._timestamp_or_now(event))

    def _handle_auth_offline_grace_used(self, event: AuthEvent) -> None:
        self._transition_state("authenticated_grace", at=self._timestamp_or_now(event))

    def _handle_scheduler_denied_by_auth(self, event: AuthEvent) -> None:
        self._record_point(self._scheduler_denied, at=self._timestamp_or_now(event))

    def _handle_background_stopped_due_to_auth(self, event: AuthEvent) -> None:
        self._record_point(self._background_stopped, at=self._timestamp_or_now(event))

    def _handle_composition_poller_stopped_due_to_auth(self, event: AuthEvent) -> None:
        self._record_point(self._background_stopped, at=self._timestamp_or_now(event))

    def get_snapshot(self) -> AuthMetricsSnapshot:
        snapshot = AuthMetricsSnapshot(timestamp=self.now_fn())
        snapshot.login_attempts_total = len(self._login_attempts)
        snapshot.login_success_total = len(self._login_successes)
        snapshot.login_failure_total = len(self._login_failures)
        if snapshot.login_attempts_total:
            snapshot.login_success_rate = (snapshot.login_success_total / snapshot.login_attempts_total) * 100
        snapshot.refresh_attempts_total = len(self._refresh_attempts)
        snapshot.refresh_success_total = len(self._refresh_successes)
        snapshot.refresh_failure_total = len(self._refresh_failures)
        if snapshot.refresh_attempts_total:
            snapshot.refresh_success_rate = (snapshot.refresh_success_total / snapshot.refresh_attempts_total) * 100
        if self._refresh_latencies:
            snapshot.refresh_avg_latency_ms = sum(v.value for v in self._refresh_latencies) / len(self._refresh_latencies)
        snapshot.errors_network_total = len(self._errors_network)
        snapshot.errors_remote_rejection_total = len(self._errors_remote_rejection)
        snapshot.errors_device_mismatch_total = len(self._errors_device_mismatch)
        snapshot.scheduler_denied_total = len(self._scheduler_denied)
        snapshot.background_stopped_total = len(self._background_stopped)
        snapshot.session_duration_seconds_total = self._session_duration_seconds_total
        snapshot.grace_period_usage_seconds_total = self._grace_period_usage_seconds_total
        if self._current_session_state == "authenticated_active" and self._active_started_at is not None:
            snapshot.session_duration_seconds_total += max((self.now_fn() - self._active_started_at).total_seconds(), 0.0)
        if self._current_session_state == "authenticated_grace" and self._grace_started_at is not None:
            snapshot.grace_period_usage_seconds_total += max((self.now_fn() - self._grace_started_at).total_seconds(), 0.0)
        if self._current_session_state is None:
            snapshot.sessions_unauthenticated = 1
        else:
            bucket = self._state_bucket_name(self._current_session_state)
            if bucket is not None:
                setattr(snapshot, bucket, 1)
        snapshot.active_sessions_count = snapshot.sessions_active
        return snapshot

    def get_login_success_rate(self, window_minutes: int = 60) -> float:
        cutoff = self.now_fn() - timedelta(minutes=window_minutes)
        attempts = [v for v in self._login_attempts if v.timestamp >= cutoff]
        successes = [v for v in self._login_successes if v.timestamp >= cutoff]
        return 100.0 if not attempts else (len(successes) / len(attempts)) * 100

    def get_refresh_stats(self, window_minutes: int = 60) -> dict[str, float]:
        cutoff = self.now_fn() - timedelta(minutes=window_minutes)
        attempts = [v for v in self._refresh_attempts if v.timestamp >= cutoff]
        successes = [v for v in self._refresh_successes if v.timestamp >= cutoff]
        latencies = [v for v in self._refresh_latencies if v.timestamp >= cutoff]
        return {
            "attempts": len(attempts),
            "successes": len(successes),
            "success_rate": round((len(successes) / len(attempts)) * 100 if attempts else 100.0, 2),
            "avg_latency_ms": round(sum(v.value for v in latencies) / len(latencies) if latencies else 0.0, 2),
        }


class PrometheusMetricsExporter:
    def __init__(self, collector: AuthMetricsCollector) -> None:
        self.collector = collector

    def export(self) -> str:
        snapshot = self.collector.get_snapshot()
        lines: list[str] = []
        def metric(name: str, kind: str, help_text: str, value: float | int) -> None:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {kind}")
            lines.append(f"{name} {value}")
        metric("auth_active_sessions_count", "gauge", "Current number of active auth sessions.", snapshot.active_sessions_count)
        metric("auth_login_attempts_total", "counter", "Total auth login attempts.", snapshot.login_attempts_total)
        metric("auth_login_failures_total", "counter", "Total auth login failures.", snapshot.login_failure_total)
        metric("auth_refresh_attempts_total", "counter", "Total auth refresh attempts.", snapshot.refresh_attempts_total)
        metric("auth_refresh_failures_total", "counter", "Total auth refresh failures.", snapshot.refresh_failure_total)
        metric("auth_session_duration_seconds", "counter", "Accumulated authenticated session duration in seconds.", round(snapshot.session_duration_seconds_total, 6))
        metric("auth_grace_period_usage_seconds", "counter", "Accumulated authenticated grace-period usage in seconds.", round(snapshot.grace_period_usage_seconds_total, 6))
        metric("auth_login_success_total", "counter", "Total successful auth logins.", snapshot.login_success_total)
        metric("auth_refresh_success_total", "counter", "Total successful auth refreshes.", snapshot.refresh_success_total)
        metric("auth_refresh_avg_latency_ms", "gauge", "Average auth refresh latency in milliseconds.", round(snapshot.refresh_avg_latency_ms, 6))
        metric("auth_scheduler_denied_total", "counter", "Total scheduler starts denied by auth.", snapshot.scheduler_denied_total)
        metric("auth_background_stopped_total", "counter", "Total background auth stops.", snapshot.background_stopped_total)
        lines.append("# HELP auth_sessions_current Current auth sessions by state.")
        lines.append("# TYPE auth_sessions_current gauge")
        lines.append(f'auth_sessions_current{{state="active"}} {snapshot.sessions_active}')
        lines.append(f'auth_sessions_current{{state="grace"}} {snapshot.sessions_grace}')
        lines.append(f'auth_sessions_current{{state="expired"}} {snapshot.sessions_expired}')
        lines.append(f'auth_sessions_current{{state="revoked"}} {snapshot.sessions_revoked}')
        lines.append(f'auth_sessions_current{{state="device_mismatch"}} {snapshot.sessions_device_mismatch}')
        lines.append(f'auth_sessions_current{{state="unauthenticated"}} {snapshot.sessions_unauthenticated}')
        lines.append("# HELP auth_errors_total Total auth errors grouped by error type.")
        lines.append("# TYPE auth_errors_total counter")
        lines.append(f'auth_errors_total{{type="network"}} {snapshot.errors_network_total}')
        lines.append(f'auth_errors_total{{type="remote_rejection"}} {snapshot.errors_remote_rejection_total}')
        lines.append(f'auth_errors_total{{type="device_mismatch"}} {snapshot.errors_device_mismatch_total}')
        return "\n".join(lines) + "\n"


auth_metrics_collector = AuthMetricsCollector()
