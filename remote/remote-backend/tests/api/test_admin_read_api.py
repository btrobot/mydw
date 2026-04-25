from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import admin as admin_api
from app.main import create_app
from app.schemas.admin import (
    AdminCurrentSessionResponse,
    AdminDeviceListResponse,
    AdminDeviceResponse,
    AdminIdentity,
    AdminMetricsSummaryResponse,
    AdminSessionListResponse,
    AdminSessionResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AuditLogListResponse,
    AuditLogResponse,
)
from app.services.admin_service import AdminServiceError
from tests.support.route_contract import (
    ErrorContractCase,
    RecordingRouteService,
    assert_error_response,
    assert_json_model_response,
    assert_single_service_call,
    bearer_headers,
    expected_access_token,
)


@dataclass(frozen=True)
class ReadRouteCase:
    name: str
    path: str
    service_method: str
    success_response: Any
    expected_call: dict[str, Any]
    not_found_details: dict[str, Any] | None = None


UTC = timezone.utc


def _dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


AUDIT_LOG = AuditLogResponse(
    id="audit_1",
    event_type="admin_login_failed",
    actor_type="admin",
    actor_id="admin_1",
    target_user_id="u_1",
    target_device_id="device_1",
    target_session_id="sess_1",
    request_id="req_1",
    trace_id="trace_1",
    created_at=_dt(2026, 4, 25, 10, 30, 0),
    details={"reason": "forbidden"},
)

ROUTE_CASES = [
    ReadRouteCase(
        name="admin_session",
        path="/admin/session",
        service_method="get_session",
        success_response=AdminCurrentSessionResponse(
            session_id="admin_sess_1",
            expires_at=_dt(2026, 5, 1, 0, 0, 0),
            user=AdminIdentity(
                id="admin_1",
                username="admin",
                display_name="Remote Admin",
                role="super_admin",
            ),
        ),
        expected_call={"access_token": "admin_access_token"},
    ),
    ReadRouteCase(
        name="list_users",
        path="/admin/users?q=alice&status=active&license_status=active&limit=10&offset=5",
        service_method="list_users",
        success_response=AdminUserListResponse(
            items=[
                AdminUserResponse(
                    id="u_1",
                    username="alice",
                    display_name="Alice",
                    email="alice@example.com",
                    tenant_id="tenant_1",
                    status="active",
                    license_status="active",
                    license_expires_at=_dt(2026, 5, 25, 0, 0, 0),
                    entitlements=["dashboard:view"],
                    device_count=1,
                    last_seen_at=_dt(2026, 4, 25, 8, 0, 0),
                )
            ],
            total=1,
        ),
        expected_call={
            "access_token": "admin_access_token",
            "q": "alice",
            "status": "active",
            "license_status": "active",
            "limit": 10,
            "offset": 5,
        },
    ),
    ReadRouteCase(
        name="get_user",
        path="/admin/users/u_1",
        service_method="get_user",
        success_response=AdminUserResponse(
            id="u_1",
            username="alice",
            display_name="Alice",
            email="alice@example.com",
            tenant_id="tenant_1",
            status="active",
            license_status="active",
            license_expires_at=_dt(2026, 5, 25, 0, 0, 0),
            entitlements=["dashboard:view"],
            device_count=1,
            last_seen_at=_dt(2026, 4, 25, 8, 0, 0),
        ),
        expected_call={"access_token": "admin_access_token", "user_id": "u_1"},
        not_found_details={"user_id": "u_1"},
    ),
    ReadRouteCase(
        name="list_devices",
        path="/admin/devices?q=mac&device_status=bound&user_id=u_1&limit=10&offset=5",
        service_method="list_devices",
        success_response=AdminDeviceListResponse(
            items=[
                AdminDeviceResponse(
                    device_id="device_1",
                    user_id="u_1",
                    device_status="bound",
                    first_bound_at=_dt(2026, 4, 20, 12, 0, 0),
                    last_seen_at=_dt(2026, 4, 25, 8, 30, 0),
                    client_version="0.3.0",
                )
            ],
            total=1,
        ),
        expected_call={
            "access_token": "admin_access_token",
            "q": "mac",
            "device_status": "bound",
            "user_id": "u_1",
            "limit": 10,
            "offset": 5,
        },
    ),
    ReadRouteCase(
        name="get_device",
        path="/admin/devices/device_1",
        service_method="get_device",
        success_response=AdminDeviceResponse(
            device_id="device_1",
            user_id="u_1",
            device_status="bound",
            first_bound_at=_dt(2026, 4, 20, 12, 0, 0),
            last_seen_at=_dt(2026, 4, 25, 8, 30, 0),
            client_version="0.3.0",
        ),
        expected_call={"access_token": "admin_access_token", "device_id": "device_1"},
        not_found_details={"device_id": "device_1"},
    ),
    ReadRouteCase(
        name="list_sessions",
        path="/admin/sessions?q=alice&auth_state=active&user_id=u_1&device_id=device_1&limit=10&offset=5",
        service_method="list_sessions",
        success_response=AdminSessionListResponse(
            items=[
                AdminSessionResponse(
                    session_id="sess_1",
                    user_id="u_1",
                    device_id="device_1",
                    auth_state="active",
                    issued_at=_dt(2026, 4, 24, 10, 0, 0),
                    expires_at=_dt(2026, 4, 25, 10, 0, 0),
                    last_seen_at=_dt(2026, 4, 25, 9, 45, 0),
                )
            ],
            total=1,
        ),
        expected_call={
            "access_token": "admin_access_token",
            "q": "alice",
            "auth_state": "active",
            "user_id": "u_1",
            "device_id": "device_1",
            "limit": 10,
            "offset": 5,
        },
    ),
    ReadRouteCase(
        name="list_audit_logs",
        path="/admin/audit-logs?event_type=admin_login_failed&actor_id=admin_1&target_user_id=u_1&target_device_id=device_1&target_session_id=sess_1&created_from=2026-04-20T00:00:00Z&created_to=2026-04-21T00:00:00Z&limit=10&offset=5",
        service_method="list_audit_logs",
        success_response=AuditLogListResponse(items=[AUDIT_LOG], total=1),
        expected_call={
            "access_token": "admin_access_token",
            "event_type": "admin_login_failed",
            "actor_id": "admin_1",
            "target_user_id": "u_1",
            "target_device_id": "device_1",
            "target_session_id": "sess_1",
            "created_from": _dt(2026, 4, 20, 0, 0, 0),
            "created_to": _dt(2026, 4, 21, 0, 0, 0),
            "limit": 10,
            "offset": 5,
        },
    ),
    ReadRouteCase(
        name="metrics_summary",
        path="/admin/metrics/summary",
        service_method="get_metrics_summary",
        success_response=AdminMetricsSummaryResponse(
            active_sessions=3,
            login_failures=5,
            device_mismatches=2,
            destructive_actions=4,
            generated_at=_dt(2026, 4, 25, 11, 0, 0),
            recent_failures=[AUDIT_LOG],
            recent_destructive_actions=[],
        ),
        expected_call={"access_token": "admin_access_token"},
    ),
]


class FakeAdminReadService(RecordingRouteService):
    def __init__(self) -> None:
        super().__init__({case.service_method: case.success_response for case in ROUTE_CASES})

    def get_session(self, access_token: str) -> AdminCurrentSessionResponse:
        return self.handle("get_session", access_token=access_token)

    def list_users(
        self,
        access_token: str,
        *,
        q: str | None = None,
        status: str | None = None,
        license_status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> AdminUserListResponse:
        return self.handle(
            "list_users",
            access_token=access_token,
            q=q,
            status=status,
            license_status=license_status,
            limit=limit,
            offset=offset,
        )

    def get_user(self, access_token: str, user_id: str) -> AdminUserResponse:
        return self.handle("get_user", access_token=access_token, user_id=user_id)

    def list_devices(
        self,
        access_token: str,
        *,
        q: str | None = None,
        device_status: str | None = None,
        user_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> AdminDeviceListResponse:
        return self.handle(
            "list_devices",
            access_token=access_token,
            q=q,
            device_status=device_status,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def get_device(self, access_token: str, device_id: str) -> AdminDeviceResponse:
        return self.handle("get_device", access_token=access_token, device_id=device_id)

    def list_sessions(
        self,
        access_token: str,
        *,
        q: str | None = None,
        auth_state: str | None = None,
        user_id: str | None = None,
        device_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> AdminSessionListResponse:
        return self.handle(
            "list_sessions",
            access_token=access_token,
            q=q,
            auth_state=auth_state,
            user_id=user_id,
            device_id=device_id,
            limit=limit,
            offset=offset,
        )

    def list_audit_logs(
        self,
        access_token: str,
        *,
        event_type: str | None = None,
        actor_id: str | None = None,
        target_user_id: str | None = None,
        target_device_id: str | None = None,
        target_session_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        return self.handle(
            "list_audit_logs",
            access_token=access_token,
            event_type=event_type,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_device_id=target_device_id,
            target_session_id=target_session_id,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )

    def get_metrics_summary(self, access_token: str) -> AdminMetricsSummaryResponse:
        return self.handle("get_metrics_summary", access_token=access_token)


@pytest.fixture
def app():
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.mark.parametrize("case", ROUTE_CASES, ids=[case.name for case in ROUTE_CASES])
def test_admin_read_routes_forward_bearer_token_and_query_params(case: ReadRouteCase, app) -> None:
    service = FakeAdminReadService()
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            case.path,
            headers=bearer_headers("admin_access_token"),
        )

    assert_json_model_response(response, case.success_response)
    assert_single_service_call(
        service.calls,
        method=case.service_method,
        **case.expected_call,
    )


@pytest.mark.parametrize("case", [case for case in ROUTE_CASES if case.not_found_details is None], ids=[case.name for case in ROUTE_CASES if case.not_found_details is None])
@pytest.mark.parametrize(
    ("expected_status", "expected_error_code", "expected_message", "expected_details"),
    [
        (401, "token_expired", "Access token expired or invalid", {"reason": "token_expired"}),
        (403, "forbidden", "Admin access forbidden", {"reason": "forbidden"}),
    ],
    ids=["401", "403"],
)
def test_admin_read_routes_surface_401_403_semantics(
    case: ReadRouteCase,
    expected_status: int,
    expected_error_code: str,
    expected_message: str,
    expected_details: dict[str, Any],
    app,
) -> None:
    error_case = ErrorContractCase(
        status=expected_status,
        error_code=expected_error_code,
        message=expected_message,
        details=expected_details,
    )
    service = FakeAdminReadService()
    service.errors[case.service_method] = AdminServiceError(
        error_case.error_code,
        error_case.message,
        status_code=error_case.status,
        details=error_case.details,
    )
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            case.path,
            headers=bearer_headers(None if expected_status == 401 else "admin_access_token"),
        )

    assert_error_response(response, error_case)
    expected_call = dict(case.expected_call, access_token=expected_access_token(expected_status, "admin_access_token"))
    assert_single_service_call(service.calls, method=case.service_method, **expected_call)


@pytest.mark.parametrize("case", [case for case in ROUTE_CASES if case.not_found_details is not None], ids=[case.name for case in ROUTE_CASES if case.not_found_details is not None])
@pytest.mark.parametrize(
    ("expected_status", "expected_error_code", "expected_message", "expected_details"),
    [
        (401, "token_expired", "Access token expired or invalid", {"reason": "token_expired"}),
        (403, "forbidden", "Admin access forbidden", {"reason": "forbidden"}),
        (404, "not_found", "Requested admin resource missing", None),
    ],
    ids=["401", "403", "404"],
)
def test_admin_read_detail_routes_surface_401_403_404_semantics(
    case: ReadRouteCase,
    expected_status: int,
    expected_error_code: str,
    expected_message: str,
    expected_details: dict[str, Any] | None,
    app,
) -> None:
    error_case = ErrorContractCase(
        status=expected_status,
        error_code=expected_error_code,
        message=expected_message,
        details=expected_details if expected_details is not None else case.not_found_details or {},
    )
    service = FakeAdminReadService()
    service.errors[case.service_method] = AdminServiceError(
        error_case.error_code,
        error_case.message,
        status_code=error_case.status,
        details=error_case.details,
    )
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            case.path,
            headers=bearer_headers(None if expected_status == 401 else "admin_access_token"),
        )

    assert_error_response(response, error_case)
    expected_call = dict(case.expected_call, access_token=expected_access_token(expected_status, "admin_access_token"))
    assert_single_service_call(service.calls, method=case.service_method, **expected_call)
