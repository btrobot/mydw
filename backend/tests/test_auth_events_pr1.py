"""
Step 5 PR1: 认证事件日志和追踪测试

测试目标：
1. 所有 Step 0 PR3 定义的 frozen event names 都被正确发射
2. 事件包含标准字段：event_name, timestamp, remote_user_id, device_id, auth_state, reason_code
3. 区分网络失败和远程拒绝（revoke/disabled/device_mismatch）
4. 背景任务停止原因可见
"""
from __future__ import annotations

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.auth_events import (
    AuthEvent,
    AuthEventEmitter,
    AuthEventReason,
    AuthEventType,
    auth_event_emitter,
)
from core.observability import auth_trace_scope, build_auth_trace_context


class TestAuthEventTypes:
    """测试事件类型定义"""
    
    def test_frontend_session_lifecycle_events(self):
        """测试前端/会话生命周期事件"""
        assert AuthEventType.AUTH_LOGIN_SUCCEEDED == "auth_login_succeeded"
        assert AuthEventType.AUTH_LOGIN_FAILED == "auth_login_failed"
        assert AuthEventType.AUTH_SESSION_RESTORED == "auth_session_restored"
        assert AuthEventType.AUTH_SESSION_RESTORE_FAILED == "auth_session_restore_failed"
        assert AuthEventType.AUTH_LOGOUT_COMPLETED == "auth_logout_completed"
    
    def test_refresh_validation_events(self):
        """测试刷新/验证事件"""
        assert AuthEventType.AUTH_REFRESH_STARTED == "auth_refresh_started"
        assert AuthEventType.AUTH_REFRESH_SUCCEEDED == "auth_refresh_succeeded"
        assert AuthEventType.AUTH_REFRESH_FAILED == "auth_refresh_failed"
        assert AuthEventType.AUTH_ME_VALIDATION_FAILED == "auth_me_validation_failed"
    
    def test_authorization_status_events(self):
        """测试授权状态变更事件"""
        assert AuthEventType.AUTH_REVOKED == "auth_revoked"
        assert AuthEventType.AUTH_EXPIRED == "auth_expired"
        assert AuthEventType.AUTH_OFFLINE_GRACE_USED == "auth_offline_grace_used"
        assert AuthEventType.AUTH_DEVICE_MISMATCH == "auth_device_mismatch"
    
    def test_background_enforcement_events(self):
        """测试背景执行事件"""
        assert AuthEventType.SCHEDULER_DENIED_BY_AUTH == "scheduler_denied_by_auth"
        assert AuthEventType.BACKGROUND_STOPPED_DUE_TO_AUTH == "background_stopped_due_to_auth"
        assert AuthEventType.PUBLISH_TASK_FAILED_DUE_TO_AUTH == "publish_task_failed_due_to_auth"
        assert AuthEventType.COMPOSITION_POLLER_STOPPED_DUE_TO_AUTH == "composition_poller_stopped_due_to_auth"


class TestAuthEventStructure:
    """测试事件结构"""
    
    def test_event_has_required_fields(self):
        """测试事件包含所有必需字段"""
        event = AuthEvent(
            event_name="auth_login_succeeded",
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
            reason_code="success",
        )
        
        assert event.event_name == "auth_login_succeeded"
        assert event.remote_user_id == "user123"
        assert event.device_id == "device456"
        assert event.auth_state == "authenticated_active"
        assert event.reason_code == "success"
        assert event.timestamp is not None
    
    def test_event_to_dict(self):
        """测试事件转换为字典"""
        event = AuthEvent(
            event_name="auth_login_failed",
            remote_user_id="user123",
            device_id="device456",
            auth_state="error",
            reason_code="invalid_credentials",
            error_message="Invalid password",
            extra={"is_network_error": False},
        )
        
        data = event.to_dict()
        assert data["event_name"] == "auth_login_failed"
        assert data["remote_user_id"] == "user123"
        assert data["device_id"] == "device456"
        assert data["auth_state"] == "error"
        assert data["reason_code"] == "invalid_credentials"
        assert data["error_message"] == "Invalid password"
        assert data["is_network_error"] is False
        assert "timestamp" in data
    
    def test_event_to_log_message(self):
        """测试事件转换为日志消息"""
        event = AuthEvent(
            event_name="auth_refresh_failed",
            remote_user_id="user123",
            device_id="device456",
            auth_state="error",
            reason_code="network_error",
            extra={"is_network_error": True},
        )
        
        msg = event.to_log_message()
        assert "event_name=auth_refresh_failed" in msg
        assert "remote_user_id=user123" in msg
        assert "device_id=device456" in msg
        assert "auth_state=error" in msg
        assert "reason_code=network_error" in msg
        assert "is_network_error=True" in msg


class TestAuthEventEmitter:
    """测试事件发射器"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前清理发射器状态"""
        auth_event_emitter.clear_captured_events()
        auth_event_emitter._callbacks = []
        yield
        auth_event_emitter.stop_capture()
        auth_event_emitter.clear_captured_events()
        auth_event_emitter._callbacks = []
    
    def test_capture_mode(self):
        """测试事件捕获模式"""
        auth_event_emitter.start_capture()
        
        event = AuthEvent(event_name="test_event")
        auth_event_emitter.emit(event)
        
        captured = auth_event_emitter.get_captured_events()
        assert len(captured) == 1
        assert captured[0].event_name == "test_event"
    
    def test_stop_capture_returns_events(self):
        """测试停止捕获返回事件"""
        auth_event_emitter.start_capture()
        
        auth_event_emitter.emit(AuthEvent(event_name="event1"))
        auth_event_emitter.emit(AuthEvent(event_name="event2"))
        
        captured = auth_event_emitter.stop_capture()
        assert len(captured) == 2
        assert captured[0].event_name == "event1"
        assert captured[1].event_name == "event2"
        
        # After stop, capture list should be empty
        assert len(auth_event_emitter.get_captured_events()) == 0
    
    def test_callback_registration(self):
        """测试回调注册"""
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        auth_event_emitter.register_callback(callback)
        auth_event_emitter.emit(AuthEvent(event_name="callback_test"))
        
        assert len(received_events) == 1
        assert received_events[0].event_name == "callback_test"
    
    def test_callback_unregistration(self):
        """测试回调注销"""
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        auth_event_emitter.register_callback(callback)
        auth_event_emitter.emit(AuthEvent(event_name="event1"))
        
        auth_event_emitter.unregister_callback(callback)
        auth_event_emitter.emit(AuthEvent(event_name="event2"))
        
        assert len(received_events) == 1
        assert received_events[0].event_name == "event1"


class TestAuthEventConvenienceMethods:
    """测试便捷方法"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前启动捕获模式"""
        auth_event_emitter.start_capture()
        yield
        auth_event_emitter.stop_capture()
        auth_event_emitter.clear_captured_events()
    
    def test_login_succeeded(self):
        """测试登录成功事件"""
        auth_event_emitter.login_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_LOGIN_SUCCEEDED
        assert events[0].remote_user_id == "user123"
        assert events[0].device_id == "device456"
        assert events[0].auth_state == "authenticated_active"
    
    def test_login_failed_network_error(self):
        """测试登录失败（网络错误）"""
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="network_timeout",
            error_message="Connection timeout",
            is_network_error=True,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_LOGIN_FAILED
        assert events[0].reason_code == "network_timeout"
        assert events[0].extra["is_network_error"] is True
    
    def test_login_failed_remote_rejection(self):
        """测试登录失败（远程拒绝）"""
        auth_event_emitter.login_failed(
            device_id="device456",
            reason_code="invalid_credentials",
            error_message="Invalid password",
            is_network_error=False,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_LOGIN_FAILED
        assert events[0].reason_code == "invalid_credentials"
        assert events[0].extra["is_network_error"] is False
    
    def test_session_restored(self):
        """测试会话恢复事件"""
        auth_event_emitter.session_restored(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_SESSION_RESTORED
    
    def test_session_restore_failed(self):
        """测试会话恢复失败事件"""
        auth_event_emitter.session_restore_failed(
            reason_code=AuthEventReason.SESSION_NOT_FOUND,
            auth_state="unauthenticated",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_SESSION_RESTORE_FAILED
        assert events[0].reason_code == AuthEventReason.SESSION_NOT_FOUND
    
    def test_logout_completed(self):
        """测试登出完成事件"""
        auth_event_emitter.logout_completed(
            remote_user_id="user123",
            device_id="device456",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_LOGOUT_COMPLETED
        assert events[0].auth_state == "unauthenticated"
    
    def test_refresh_started(self):
        """测试刷新开始事件"""
        auth_event_emitter.refresh_started(
            remote_user_id="user123",
            device_id="device456",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_REFRESH_STARTED
    
    def test_refresh_succeeded(self):
        """测试刷新成功事件"""
        auth_event_emitter.refresh_succeeded(
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_REFRESH_SUCCEEDED
    
    def test_refresh_failed_network_error(self):
        """测试刷新失败（网络错误）"""
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="network_error",
            error_message="Connection failed",
            is_network_error=True,
            is_remote_rejection=False,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_REFRESH_FAILED
        assert events[0].extra["is_network_error"] is True
        assert events[0].extra["is_remote_rejection"] is False
    
    def test_refresh_failed_remote_rejection_revoked(self):
        """测试刷新失败（远程拒绝 - revoked）"""
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="revoked",
            error_message="Token revoked",
            is_network_error=False,
            is_remote_rejection=True,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_REFRESH_FAILED
        assert events[0].extra["is_network_error"] is False
        assert events[0].extra["is_remote_rejection"] is True
    
    def test_refresh_failed_remote_rejection_disabled(self):
        """测试刷新失败（远程拒绝 - disabled）"""
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="disabled",
            error_message="Account disabled",
            is_network_error=False,
            is_remote_rejection=True,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].reason_code == "disabled"
        assert events[0].extra["is_remote_rejection"] is True
    
    def test_refresh_failed_remote_rejection_device_mismatch(self):
        """测试刷新失败（远程拒绝 - device_mismatch）"""
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="device_mismatch",
            error_message="Device mismatch",
            is_network_error=False,
            is_remote_rejection=True,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].reason_code == "device_mismatch"
        assert events[0].extra["is_remote_rejection"] is True
    
    def test_me_validation_failed(self):
        """测试 /me 验证失败事件"""
        auth_event_emitter.me_validation_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="token_expired",
            error_message="Token expired",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_ME_VALIDATION_FAILED
    
    def test_revoked(self):
        """测试吊销事件"""
        auth_event_emitter.revoked(
            remote_user_id="user123",
            device_id="device456",
            previous_state="authenticated_active",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_REVOKED
        assert events[0].auth_state == "revoked"
        assert events[0].reason_code == AuthEventReason.REVOKED
        assert events[0].extra["previous_state"] == "authenticated_active"
    
    def test_expired(self):
        """测试过期事件"""
        auth_event_emitter.expired(
            remote_user_id="user123",
            device_id="device456",
            previous_state="authenticated_grace",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_EXPIRED
        assert events[0].auth_state == "expired"
    
    def test_offline_grace_used(self):
        """测试离线宽限期使用事件"""
        auth_event_emitter.offline_grace_used(
            remote_user_id="user123",
            device_id="device456",
            grace_remaining_minutes=120,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_OFFLINE_GRACE_USED
        assert events[0].extra["grace_remaining_minutes"] == 120
    
    def test_device_mismatch(self):
        """测试设备不匹配事件"""
        auth_event_emitter.device_mismatch(
            remote_user_id="user123",
            expected_device_id="device456",
            actual_device_id="device789",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.AUTH_DEVICE_MISMATCH
        assert events[0].extra["actual_device_id"] == "device789"
    
    def test_scheduler_denied_by_auth(self):
        """测试调度器被认证拒绝事件"""
        auth_event_emitter.scheduler_denied_by_auth(
            auth_state="revoked",
            reason_code="revoked",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.SCHEDULER_DENIED_BY_AUTH
    
    def test_background_stopped_due_to_auth(self):
        """测试后台任务因认证停止事件"""
        auth_event_emitter.background_stopped_due_to_auth(
            component="task_scheduler",
            auth_state="revoked",
            reason_code="revoked",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.BACKGROUND_STOPPED_DUE_TO_AUTH
        assert events[0].extra["component"] == "task_scheduler"
    
    def test_publish_task_failed_due_to_auth(self):
        """测试发布任务因认证失败事件"""
        auth_event_emitter.publish_task_failed_due_to_auth(
            task_id=123,
            auth_state="offline_grace",
            reason_code="offline_grace_restricted",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.PUBLISH_TASK_FAILED_DUE_TO_AUTH
        assert events[0].extra["task_id"] == 123
    
    def test_composition_poller_stopped_due_to_auth(self):
        """测试合成轮询器因认证停止事件"""
        auth_event_emitter.composition_poller_stopped_due_to_auth(
            auth_state="device_mismatch",
            reason_code="device_mismatch",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].event_name == AuthEventType.COMPOSITION_POLLER_STOPPED_DUE_TO_AUTH


class TestNetworkVsRemoteRejection:
    """测试网络失败 vs 远程拒绝的区分"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前启动捕获模式"""
        auth_event_emitter.start_capture()
        yield
        auth_event_emitter.stop_capture()
        auth_event_emitter.clear_captured_events()
    
    def test_network_error_has_is_network_error_flag(self):
        """测试网络错误有 is_network_error 标记"""
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="timeout",
            is_network_error=True,
            is_remote_rejection=False,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert events[0].extra["is_network_error"] is True
        assert events[0].extra["is_remote_rejection"] is False
    
    def test_remote_rejection_has_is_remote_rejection_flag(self):
        """测试远程拒绝有 is_remote_rejection 标记"""
        auth_event_emitter.refresh_failed(
            remote_user_id="user123",
            device_id="device456",
            reason_code="revoked",
            is_network_error=False,
            is_remote_rejection=True,
        )
        
        events = auth_event_emitter.get_captured_events()
        assert events[0].extra["is_network_error"] is False
        assert events[0].extra["is_remote_rejection"] is True
    
    def test_all_hard_deny_reasons_are_remote_rejection(self):
        """测试所有硬拒绝原因都是远程拒绝"""
        hard_deny_reasons = ["revoked", "disabled", "device_mismatch"]
        
        for reason in hard_deny_reasons:
            auth_event_emitter.clear_captured_events()
            auth_event_emitter.refresh_failed(
                remote_user_id="user123",
                device_id="device456",
                reason_code=reason,
                is_network_error=False,
                is_remote_rejection=True,
            )
            
            events = auth_event_emitter.get_captured_events()
            assert events[0].extra["is_remote_rejection"] is True, f"Reason {reason} should be remote rejection"


class TestBackgroundStopReasons:
    """测试后台停止原因可见性"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前启动捕获模式"""
        auth_event_emitter.start_capture()
        yield
        auth_event_emitter.stop_capture()
        auth_event_emitter.clear_captured_events()
    
    def test_scheduler_stop_includes_reason_code(self):
        """测试调度器停止包含原因代码"""
        auth_event_emitter.background_stopped_due_to_auth(
            component="task_scheduler",
            auth_state="revoked",
            reason_code="revoked",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert events[0].reason_code == "revoked"
        assert events[0].auth_state == "revoked"
    
    def test_composition_poller_stop_includes_reason_code(self):
        """测试合成轮询器停止包含原因代码"""
        auth_event_emitter.composition_poller_stopped_due_to_auth(
            auth_state="device_mismatch",
            reason_code="device_mismatch",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert events[0].reason_code == "device_mismatch"
    
    def test_publish_task_failure_includes_task_id(self):
        """测试发布任务失败包含任务ID"""
        auth_event_emitter.publish_task_failed_due_to_auth(
            task_id=456,
            auth_state="offline_grace",
            reason_code="offline_grace_restricted",
        )
        
        events = auth_event_emitter.get_captured_events()
        assert events[0].extra["task_id"] == 456


class TestAuthTraceContext:
    """测试 request-scoped trace context 能被注入事件。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        auth_event_emitter.start_capture()
        yield
        auth_event_emitter.stop_capture()
        auth_event_emitter.clear_captured_events()

    def test_event_inherits_trace_context(self):
        with auth_trace_scope(
            build_auth_trace_context(
                request_id="req-123",
                trace_id="trace-123",
                route_name="login_auth",
                method="POST",
                path="/api/auth/login",
            )
        ):
            auth_event_emitter.login_succeeded(
                remote_user_id="user123",
                device_id="device456",
                auth_state="authenticated_active",
            )

        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].trace_id == "trace-123"
        assert events[0].request_id == "req-123"
        assert events[0].route_name == "login_auth"
        assert events[0].method == "POST"
        assert events[0].path == "/api/auth/login"

    def test_trace_context_is_not_leaked_after_scope(self):
        with auth_trace_scope(
            build_auth_trace_context(
                trace_id="trace-ephemeral",
                route_name="refresh_auth",
            )
        ):
            auth_event_emitter.refresh_started(
                remote_user_id="user123",
                device_id="device456",
            )

        auth_event_emitter.clear_captured_events()
        auth_event_emitter.logout_completed(
            remote_user_id="user123",
            device_id="device456",
        )

        events = auth_event_emitter.get_captured_events()
        assert len(events) == 1
        assert events[0].trace_id is None
        assert events[0].route_name is None


class TestEventLoggerIntegration:
    """测试事件日志记录器集成"""
    
    def test_log_auth_event_convenience_function(self):
        """测试便捷函数 log_auth_event"""
        from utils.event_logger import log_auth_event
        
        # This should not raise any exceptions
        log_auth_event(
            "auth_login_succeeded",
            remote_user_id="user123",
            device_id="device456",
            auth_state="authenticated_active",
        )
    
    def test_event_logger_manager_can_start_stop(self):
        """测试事件日志管理器可以启动和停止"""
        from utils.event_logger import EventLoggerManager
        
        manager = EventLoggerManager()
        manager.start()
        assert manager._started is True
        
        manager.stop()
        assert manager._started is False
