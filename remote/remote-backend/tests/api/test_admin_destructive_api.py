from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import admin as admin_api
from app.main import create_app
from app.schemas.admin import AdminActionResponse, AdminDeviceRebindRequest, AdminUserResponse
from app.services.admin_service import AdminServiceError
from tests.support.route_contract import (
    ErrorContractCase,
    RecordingRouteService,
    assert_error_response,
    assert_single_service_call,
    bearer_headers,
    expected_access_token,
)


@dataclass(frozen=True)
class DestructiveRouteCase:
    name: str
    path: str
    http_method: str
    service_method: str
    resource_key: str
    resource_value: str
    payload: dict[str, Any] | None = None


ROUTE_CASES = [
    DestructiveRouteCase(
        name="revoke_user",
        path="/admin/users/u_1/revoke",
        http_method="post",
        service_method="revoke_user",
        resource_key="user_id",
        resource_value="u_1",
    ),
    DestructiveRouteCase(
        name="restore_user",
        path="/admin/users/u_1/restore",
        http_method="post",
        service_method="restore_user",
        resource_key="user_id",
        resource_value="u_1",
    ),
    DestructiveRouteCase(
        name="unbind_device",
        path="/admin/devices/device_1/unbind",
        http_method="post",
        service_method="unbind_device",
        resource_key="device_id",
        resource_value="device_1",
    ),
    DestructiveRouteCase(
        name="disable_device",
        path="/admin/devices/device_1/disable",
        http_method="post",
        service_method="disable_device",
        resource_key="device_id",
        resource_value="device_1",
    ),
    DestructiveRouteCase(
        name="rebind_device",
        path="/admin/devices/device_1/rebind",
        http_method="post",
        service_method="rebind_device",
        resource_key="device_id",
        resource_value="device_1",
        payload={"user_id": "u_2", "client_version": "0.3.0"},
    ),
    DestructiveRouteCase(
        name="revoke_session",
        path="/admin/sessions/sess_1/revoke",
        http_method="post",
        service_method="revoke_session",
        resource_key="session_id",
        resource_value="sess_1",
    ),
]


class FakeAdminDestructiveService(RecordingRouteService):
    def __init__(self) -> None:
        super().__init__()

    def _handle(
        self,
        method: str,
        access_token: str,
        resource_value: str,
        payload: dict[str, Any] | None = None,
        *,
        step_up_token: str | None = None,
    ) -> AdminActionResponse:
        self.handle(
            method,
            access_token=access_token,
            resource_value=resource_value,
            payload=payload,
            step_up_token=step_up_token,
        )
        return AdminActionResponse(success=True)

    def revoke_user(self, access_token: str, user_id: str, *, step_up_token: str | None = None) -> AdminActionResponse:
        return self._handle("revoke_user", access_token, user_id, step_up_token=step_up_token)

    def restore_user(self, access_token: str, user_id: str, *, step_up_token: str | None = None) -> AdminActionResponse:
        return self._handle("restore_user", access_token, user_id, step_up_token=step_up_token)

    def unbind_device(self, access_token: str, device_id: str, *, step_up_token: str | None = None) -> AdminActionResponse:
        return self._handle("unbind_device", access_token, device_id, step_up_token=step_up_token)

    def disable_device(self, access_token: str, device_id: str, *, step_up_token: str | None = None) -> AdminActionResponse:
        return self._handle("disable_device", access_token, device_id, step_up_token=step_up_token)

    def rebind_device(
        self,
        access_token: str,
        device_id: str,
        payload: AdminDeviceRebindRequest,
        *,
        step_up_token: str | None = None,
    ) -> AdminActionResponse:
        return self._handle("rebind_device", access_token, device_id, payload.model_dump(), step_up_token=step_up_token)

    def revoke_session(self, access_token: str, session_id: str, *, step_up_token: str | None = None) -> AdminActionResponse:
        return self._handle("revoke_session", access_token, session_id, step_up_token=step_up_token)


@pytest.fixture
def app():
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.mark.parametrize("case", ROUTE_CASES, ids=[case.name for case in ROUTE_CASES])
def test_destructive_routes_forward_bearer_token_and_payload(case: DestructiveRouteCase, app) -> None:
    service = FakeAdminDestructiveService()
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = getattr(client, case.http_method)(
            case.path,
            headers={**(bearer_headers("admin_access_token") or {}), "X-Step-Up-Token": "step-up-token"},
            json=case.payload,
        )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert_single_service_call(
        service.calls,
        method=case.service_method,
        access_token="admin_access_token",
        resource_value=case.resource_value,
        payload=case.payload,
        step_up_token="step-up-token",
    )


@pytest.mark.parametrize("case", ROUTE_CASES, ids=[case.name for case in ROUTE_CASES])
@pytest.mark.parametrize(
    ("expected_status", "expected_error_code", "expected_message", "expected_details"),
    [
        (401, "token_expired", "Access token expired or invalid", {"reason": "token_expired"}),
        (403, "forbidden", "Admin access forbidden", {"reason": "forbidden"}),
        (404, "not_found", "Requested admin resource missing", None),
    ],
    ids=["401", "403", "404"],
)
def test_destructive_routes_surface_401_403_404_semantics(
    case: DestructiveRouteCase,
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
        details=expected_details if expected_details is not None else {case.resource_key: case.resource_value},
    )
    service = FakeAdminDestructiveService()
    service.errors[case.service_method] = AdminServiceError(
        error_case.error_code,
        error_case.message,
        status_code=error_case.status,
        details=error_case.details,
    )
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = getattr(client, case.http_method)(
            case.path,
            headers=(
                None
                if expected_status == 401
                else {**(bearer_headers("admin_access_token") or {}), "X-Step-Up-Token": "step-up-token"}
            ),
            json=case.payload,
        )

    assert_error_response(response, error_case)
    assert_single_service_call(
        service.calls,
        method=case.service_method,
        access_token=expected_access_token(expected_status, "admin_access_token"),
        resource_value=case.resource_value,
        payload=case.payload,
        step_up_token=None if expected_status == 401 else "step-up-token",
    )


def test_update_user_route_forwards_step_up_token(app) -> None:
    class FakeAdminUpdateUserService(RecordingRouteService):
        def update_user(self, access_token: str, user_id: str, payload, *, step_up_token: str | None = None) -> AdminUserResponse:
            self.handle(
                "update_user",
                access_token=access_token,
                resource_value=user_id,
                payload=payload.model_dump(),
                step_up_token=step_up_token,
            )
            return AdminUserResponse(
                id=user_id,
                username="alice",
                display_name="Alice",
                entitlements=["dashboard:view"],
            )

    service = FakeAdminUpdateUserService()
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.patch(
            "/admin/users/u_1",
            headers={**(bearer_headers("admin_access_token") or {}), "X-Step-Up-Token": "step-up-token"},
            json={"entitlements": ["dashboard:view"]},
        )

    assert response.status_code == 200
    assert response.json()["id"] == "u_1"
    assert_single_service_call(
        service.calls,
        method="update_user",
        access_token="admin_access_token",
        resource_value="u_1",
        payload={
            "display_name": None,
            "license_status": None,
            "license_expires_at": None,
            "entitlements": ["dashboard:view"],
        },
        step_up_token="step-up-token",
    )
