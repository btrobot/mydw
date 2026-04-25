from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import admin as admin_api
from app.main import create_app
from app.schemas.admin import AdminActionResponse, AdminDeviceRebindRequest
from app.services.admin_service import AdminServiceError


@dataclass(frozen=True)
class DestructiveRouteCase:
    name: str
    path: str
    service_method: str
    resource_key: str
    resource_value: str
    payload: dict[str, Any] | None = None


ROUTE_CASES = [
    DestructiveRouteCase(
        name="revoke_user",
        path="/admin/users/u_1/revoke",
        service_method="revoke_user",
        resource_key="user_id",
        resource_value="u_1",
    ),
    DestructiveRouteCase(
        name="restore_user",
        path="/admin/users/u_1/restore",
        service_method="restore_user",
        resource_key="user_id",
        resource_value="u_1",
    ),
    DestructiveRouteCase(
        name="unbind_device",
        path="/admin/devices/device_1/unbind",
        service_method="unbind_device",
        resource_key="device_id",
        resource_value="device_1",
    ),
    DestructiveRouteCase(
        name="disable_device",
        path="/admin/devices/device_1/disable",
        service_method="disable_device",
        resource_key="device_id",
        resource_value="device_1",
    ),
    DestructiveRouteCase(
        name="rebind_device",
        path="/admin/devices/device_1/rebind",
        service_method="rebind_device",
        resource_key="device_id",
        resource_value="device_1",
        payload={"user_id": "u_2", "client_version": "0.3.0"},
    ),
    DestructiveRouteCase(
        name="revoke_session",
        path="/admin/sessions/sess_1/revoke",
        service_method="revoke_session",
        resource_key="session_id",
        resource_value="sess_1",
    ),
]


class FakeAdminDestructiveService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.errors: dict[str, AdminServiceError] = {}

    def _handle(self, method: str, access_token: str, resource_value: str, payload: dict[str, Any] | None = None) -> AdminActionResponse:
        self.calls.append(
            {
                "method": method,
                "access_token": access_token,
                "resource_value": resource_value,
                "payload": payload,
            }
        )
        error = self.errors.get(method)
        if error is not None:
            raise error
        return AdminActionResponse(success=True)

    def revoke_user(self, access_token: str, user_id: str) -> AdminActionResponse:
        return self._handle("revoke_user", access_token, user_id)

    def restore_user(self, access_token: str, user_id: str) -> AdminActionResponse:
        return self._handle("restore_user", access_token, user_id)

    def unbind_device(self, access_token: str, device_id: str) -> AdminActionResponse:
        return self._handle("unbind_device", access_token, device_id)

    def disable_device(self, access_token: str, device_id: str) -> AdminActionResponse:
        return self._handle("disable_device", access_token, device_id)

    def rebind_device(self, access_token: str, device_id: str, payload: AdminDeviceRebindRequest) -> AdminActionResponse:
        return self._handle("rebind_device", access_token, device_id, payload.model_dump())

    def revoke_session(self, access_token: str, session_id: str) -> AdminActionResponse:
        return self._handle("revoke_session", access_token, session_id)


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
        response = client.post(
            case.path,
            headers={"Authorization": "Bearer admin_access_token"},
            json=case.payload,
        )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert service.calls == [
        {
            "method": case.service_method,
            "access_token": "admin_access_token",
            "resource_value": case.resource_value,
            "payload": case.payload,
        }
    ]


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
    service = FakeAdminDestructiveService()
    service.errors[case.service_method] = AdminServiceError(
        expected_error_code,
        expected_message,
        status_code=expected_status,
        details=expected_details if expected_details is not None else {case.resource_key: case.resource_value},
    )
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    headers = None if expected_status == 401 else {"Authorization": "Bearer admin_access_token"}

    with TestClient(app) as client:
        response = client.post(
            case.path,
            headers=headers,
            json=case.payload,
        )

    assert response.status_code == expected_status
    assert response.json() == {
        "error_code": expected_error_code,
        "message": expected_message,
        "details": expected_details if expected_details is not None else {case.resource_key: case.resource_value},
    }
    assert service.calls == [
        {
            "method": case.service_method,
            "access_token": "" if expected_status == 401 else "admin_access_token",
            "resource_value": case.resource_value,
            "payload": case.payload,
        }
    ]
