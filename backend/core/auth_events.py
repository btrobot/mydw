"""
认证事件系统 - 结构化事件日志和追踪

遵循 Step 0 PR3 定义的 frozen event taxonomy
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from loguru import logger
from core.observability import get_current_auth_trace_context


class AuthEventType(str, Enum):
    """Frozen event names from Step 0 PR3 observability-events.md"""
    
    # Frontend / session lifecycle
    AUTH_LOGIN_SUCCEEDED = "auth_login_succeeded"
    AUTH_LOGIN_FAILED = "auth_login_failed"
    AUTH_SESSION_RESTORED = "auth_session_restored"
    AUTH_SESSION_RESTORE_FAILED = "auth_session_restore_failed"
    AUTH_LOGOUT_COMPLETED = "auth_logout_completed"
    
    # Refresh / validation
    AUTH_REFRESH_STARTED = "auth_refresh_started"
    AUTH_REFRESH_SUCCEEDED = "auth_refresh_succeeded"
    AUTH_REFRESH_FAILED = "auth_refresh_failed"
    AUTH_ME_VALIDATION_FAILED = "auth_me_validation_failed"
    
    # Authorization status changes
    AUTH_REVOKED = "auth_revoked"
    AUTH_EXPIRED = "auth_expired"
    AUTH_OFFLINE_GRACE_USED = "auth_offline_grace_used"
    AUTH_DEVICE_MISMATCH = "auth_device_mismatch"
    
    # Background enforcement
    SCHEDULER_DENIED_BY_AUTH = "scheduler_denied_by_auth"
    BACKGROUND_STOPPED_DUE_TO_AUTH = "background_stopped_due_to_auth"
    PUBLISH_TASK_FAILED_DUE_TO_AUTH = "publish_task_failed_due_to_auth"
    COMPOSITION_POLLER_STOPPED_DUE_TO_AUTH = "composition_poller_stopped_due_to_auth"


class AuthEventReason(str, Enum):
    """Standard reason codes for auth events"""
    
    # Network/transport errors
    NETWORK_ERROR = "network_error"
    TRANSPORT_ERROR = "transport_error"
    TIMEOUT = "timeout"
    
    # Remote rejection (hard deny)
    REVOKED = "revoked"
    DISABLED = "disabled"
    DEVICE_MISMATCH = "device_mismatch"
    INVALID_CREDENTIALS = "invalid_credentials"
    
    # Grace/offline
    GRACE_WINDOW_EXPIRED = "grace_window_expired"
    OFFLINE_GRACE_USED = "offline_grace_used"
    
    # Session lifecycle
    TOKEN_EXPIRED = "token_expired"
    REFRESH_TOKEN_MISSING = "refresh_token_missing"
    SESSION_NOT_FOUND = "session_not_found"
    
    # Validation
    ME_VALIDATION_FAILED = "me_validation_failed"
    
    # Unknown
    UNKNOWN = "unknown"


@dataclass
class AuthEvent:
    """
    标准认证事件结构
    
    Required fields per Step 0 PR3:
    - event_name: frozen event name
    - timestamp: ISO format timestamp
    - remote_user_id: if available
    - device_id: if available
    - auth_state: current auth state
    - reason_code: why this event occurred
    """
    event_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    remote_user_id: str | None = None
    device_id: str | None = None
    auth_state: str | None = None
    reason_code: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    route_name: str | None = None
    method: str | None = None
    path: str | None = None
    
    # Optional additional context
    error_message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for logging/serialization"""
        return {
            "event_name": self.event_name,
            "timestamp": self.timestamp.isoformat(),
            "remote_user_id": self.remote_user_id,
            "device_id": self.device_id,
            "auth_state": self.auth_state,
            "reason_code": self.reason_code,
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "route_name": self.route_name,
            "method": self.method,
            "path": self.path,
            "error_message": self.error_message,
            **self.extra,
        }
    
    def to_log_message(self) -> str:
        """Format event as structured log message"""
        parts = [f"event_name={self.event_name}"]
        
        if self.remote_user_id:
            parts.append(f"remote_user_id={self.remote_user_id}")
        if self.device_id:
            parts.append(f"device_id={self.device_id}")
        if self.auth_state:
            parts.append(f"auth_state={self.auth_state}")
        if self.reason_code:
            parts.append(f"reason_code={self.reason_code}")
        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        if self.route_name:
            parts.append(f"route_name={self.route_name}")
        if self.method:
            parts.append(f"method={self.method}")
        if self.path:
            parts.append(f"path={self.path}")
        if self.error_message:
            parts.append(f"error={self.error_message}")
            
        for key, value in self.extra.items():
            parts.append(f"{key}={value}")
            
        return " ".join(parts)


class AuthEventEmitter:
    """
    认证事件发射器 - 集中管理所有认证事件的记录
    
    支持:
    - 结构化日志输出
    - 事件回调注册（用于测试和监控）
    - 区分网络失败和远程拒绝
    """
    
    def __init__(self) -> None:
        self._callbacks: list[Callable[[AuthEvent], None]] = []
        self._capture_mode: bool = False
        self._captured_events: list[AuthEvent] = []
    
    def register_callback(self, callback: Callable[[AuthEvent], None]) -> None:
        """Register a callback to receive all auth events"""
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[AuthEvent], None]) -> None:
        """Unregister a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def start_capture(self) -> None:
        """Start capturing events for testing"""
        self._capture_mode = True
        self._captured_events = []
    
    def stop_capture(self) -> list[AuthEvent]:
        """Stop capturing and return captured events"""
        self._capture_mode = False
        events = self._captured_events
        self._captured_events = []
        return events
    
    def get_captured_events(self) -> list[AuthEvent]:
        """Get currently captured events without stopping capture"""
        return self._captured_events.copy()
    
    def clear_captured_events(self) -> None:
        """Clear captured events"""
        self._captured_events = []

    def _enrich_from_trace_context(self, event: AuthEvent) -> AuthEvent:
        """Attach request-scoped trace context to an event when available."""
        trace_context = get_current_auth_trace_context()
        if trace_context is None:
            return event

        return replace(
            event,
            trace_id=event.trace_id or trace_context.trace_id,
            request_id=event.request_id or trace_context.request_id,
            route_name=event.route_name or trace_context.route_name,
            method=event.method or trace_context.method,
            path=event.path or trace_context.path,
        )
    
    def emit(self, event: AuthEvent) -> None:
        """Emit an auth event"""
        event = self._enrich_from_trace_context(event)

        # Log the event
        logger.bind(
            is_auth_event=True,
            **{
                key: value
                for key, value in event.to_dict().items()
                if value is not None
            },
        ).info(event.to_log_message())
        
        # Capture if in capture mode
        if self._capture_mode:
            self._captured_events.append(event)
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.bind(is_auth_event=True).error(f"Auth event callback failed: {e}")
    
    # Convenience methods for common events
    
    def login_succeeded(
        self,
        *,
        remote_user_id: str,
        device_id: str,
        auth_state: str,
    ) -> None:
        """Emit auth_login_succeeded event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_LOGIN_SUCCEEDED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state=auth_state,
        ))
    
    def login_failed(
        self,
        *,
        device_id: str | None,
        reason_code: str,
        auth_state: str | None = None,
        error_message: str | None = None,
        is_network_error: bool = False,
    ) -> None:
        """Emit auth_login_failed event"""
        extra = {"is_network_error": is_network_error}
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_LOGIN_FAILED,
            device_id=device_id,
            reason_code=reason_code,
            auth_state=auth_state,
            error_message=error_message,
            extra=extra,
        ))
    
    def session_restored(
        self,
        *,
        remote_user_id: str | None,
        device_id: str | None,
        auth_state: str,
    ) -> None:
        """Emit auth_session_restored event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_SESSION_RESTORED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state=auth_state,
        ))
    
    def session_restore_failed(
        self,
        *,
        reason_code: str,
        auth_state: str | None = None,
    ) -> None:
        """Emit auth_session_restore_failed event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_SESSION_RESTORE_FAILED,
            reason_code=reason_code,
            auth_state=auth_state,
        ))
    
    def logout_completed(
        self,
        *,
        remote_user_id: str | None = None,
        device_id: str | None = None,
    ) -> None:
        """Emit auth_logout_completed event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_LOGOUT_COMPLETED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state="unauthenticated",
        ))
    
    def refresh_started(
        self,
        *,
        remote_user_id: str | None,
        device_id: str | None,
    ) -> None:
        """Emit auth_refresh_started event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_REFRESH_STARTED,
            remote_user_id=remote_user_id,
            device_id=device_id,
        ))
    
    def refresh_succeeded(
        self,
        *,
        remote_user_id: str,
        device_id: str,
        auth_state: str,
    ) -> None:
        """Emit auth_refresh_succeeded event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_REFRESH_SUCCEEDED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state=auth_state,
        ))
    
    def refresh_failed(
        self,
        *,
        remote_user_id: str | None,
        device_id: str | None,
        reason_code: str,
        auth_state: str | None = None,
        error_message: str | None = None,
        is_network_error: bool = False,
        is_remote_rejection: bool = False,
    ) -> None:
        """
        Emit auth_refresh_failed event
        
        Distinguishes between:
        - Network failure (is_network_error=True)
        - Remote rejection (is_remote_rejection=True): revoked, disabled, device_mismatch
        """
        extra = {
            "is_network_error": is_network_error,
            "is_remote_rejection": is_remote_rejection,
        }
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_REFRESH_FAILED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            reason_code=reason_code,
            auth_state=auth_state,
            error_message=error_message,
            extra=extra,
        ))
    
    def me_validation_failed(
        self,
        *,
        remote_user_id: str | None,
        device_id: str | None,
        reason_code: str,
        auth_state: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Emit auth_me_validation_failed event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_ME_VALIDATION_FAILED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            reason_code=reason_code,
            auth_state=auth_state,
            error_message=error_message,
        ))
    
    def revoked(
        self,
        *,
        remote_user_id: str,
        device_id: str,
        previous_state: str,
        reason_code: str = AuthEventReason.REVOKED,
    ) -> None:
        """Emit auth_revoked event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_REVOKED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state="revoked",
            reason_code=reason_code,
            extra={"previous_state": previous_state},
        ))
    
    def expired(
        self,
        *,
        remote_user_id: str | None,
        device_id: str | None,
        previous_state: str,
    ) -> None:
        """Emit auth_expired event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_EXPIRED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state="expired",
            reason_code=AuthEventReason.GRACE_WINDOW_EXPIRED,
            extra={"previous_state": previous_state},
        ))
    
    def offline_grace_used(
        self,
        *,
        remote_user_id: str | None,
        device_id: str | None,
        grace_remaining_minutes: int | None = None,
    ) -> None:
        """Emit auth_offline_grace_used event"""
        extra = {}
        if grace_remaining_minutes is not None:
            extra["grace_remaining_minutes"] = grace_remaining_minutes
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_OFFLINE_GRACE_USED,
            remote_user_id=remote_user_id,
            device_id=device_id,
            auth_state="offline_grace",
            reason_code=AuthEventReason.OFFLINE_GRACE_USED,
            extra=extra,
        ))
    
    def device_mismatch(
        self,
        *,
        remote_user_id: str,
        expected_device_id: str,
        actual_device_id: str,
        previous_state: str | None = None,
    ) -> None:
        """Emit auth_device_mismatch event"""
        extra = {"actual_device_id": actual_device_id}
        if previous_state is not None:
            extra["previous_state"] = previous_state
        self.emit(AuthEvent(
            event_name=AuthEventType.AUTH_DEVICE_MISMATCH,
            remote_user_id=remote_user_id,
            device_id=expected_device_id,
            auth_state="device_mismatch",
            reason_code=AuthEventReason.DEVICE_MISMATCH,
            extra=extra,
        ))
    
    def scheduler_denied_by_auth(
        self,
        *,
        auth_state: str,
        reason_code: str,
    ) -> None:
        """Emit scheduler_denied_by_auth event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.SCHEDULER_DENIED_BY_AUTH,
            auth_state=auth_state,
            reason_code=reason_code,
        ))
    
    def background_stopped_due_to_auth(
        self,
        *,
        component: str,
        auth_state: str,
        reason_code: str,
    ) -> None:
        """Emit background_stopped_due_to_auth event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.BACKGROUND_STOPPED_DUE_TO_AUTH,
            auth_state=auth_state,
            reason_code=reason_code,
            extra={"component": component},
        ))
    
    def publish_task_failed_due_to_auth(
        self,
        *,
        task_id: int,
        auth_state: str,
        reason_code: str,
    ) -> None:
        """Emit publish_task_failed_due_to_auth event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.PUBLISH_TASK_FAILED_DUE_TO_AUTH,
            auth_state=auth_state,
            reason_code=reason_code,
            extra={"task_id": task_id},
        ))
    
    def composition_poller_stopped_due_to_auth(
        self,
        *,
        auth_state: str,
        reason_code: str,
    ) -> None:
        """Emit composition_poller_stopped_due_to_auth event"""
        self.emit(AuthEvent(
            event_name=AuthEventType.COMPOSITION_POLLER_STOPPED_DUE_TO_AUTH,
            auth_state=auth_state,
            reason_code=reason_code,
        ))


# Global event emitter instance
auth_event_emitter = AuthEventEmitter()
