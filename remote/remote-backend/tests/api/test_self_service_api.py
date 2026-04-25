from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import self_service as self_api
from app.main import create_app
from app.schemas.auth import (
    SelfActivityListResponse,
    SelfActivityResponse,
    SelfDeviceListResponse,
    SelfDeviceResponse,
    SelfMeResponse,
    SelfSessionListResponse,
    SelfSessionResponse,
    SelfSessionRevokeResponse,
    SelfUserIdentity,
)
from app.services.auth_service import AuthServiceError
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
class SelfReadRouteCase:
    name: str
    path: str
    service_method: str
    success_response: Any
    expected_call: dict[str, Any]


UTC = timezone.utc


def _dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


SELF_READ_ROUTE_CASES = [
    SelfReadRouteCase(
        name="self_me",
        path="/self/me",
        service_method="self_me",
        success_response=SelfMeResponse(
            user=SelfUserIdentity(
                id="u_1",
                username="alice",
                display_name="Alice",
            ),
            license_status="active",
            entitlements=["dashboard:view"],
            device_id="device_1",
            device_status="bound",
            offline_grace_until=_dt(2026, 5, 2, 0, 0, 0),
            minimum_supported_version="0.2.0",
        ),
        expected_call={"access_token": "access_token"},
    ),
    SelfReadRouteCase(
        name="self_devices",
        path="/self/devices?limit=10&offset=5",
        service_method="list_self_devices",
        success_response=SelfDeviceListResponse(
            items=[
                SelfDeviceResponse(
                    device_id="device_1",
                    device_status="bound",
                    client_version="0.3.0",
                    first_bound_at=_dt(2026, 4, 20, 12, 0, 0),
                    last_seen_at=_dt(2026, 4, 25, 10, 0, 0),
                    is_current=True,
                )
            ],
            total=1,
            page=1,
            page_size=10,
        ),
        expected_call={"access_token": "access_token", "limit": 10, "offset": 5},
    ),
    SelfReadRouteCase(
        name="self_sessions",
        path="/self/sessions?limit=10&offset=5",
        service_method="list_self_sessions",
        success_response=SelfSessionListResponse(
            items=[
                SelfSessionResponse(
                    session_id="sess_1",
                    device_id="device_1",
                    auth_state="active",
                    issued_at=_dt(2026, 4, 24, 10, 0, 0),
                    expires_at=_dt(2026, 4, 25, 10, 0, 0),
                    last_seen_at=_dt(2026, 4, 25, 9, 45, 0),
                    is_current=True,
                )
            ],
            total=1,
            page=1,
            page_size=10,
        ),
        expected_call={"access_token": "access_token", "limit": 10, "offset": 5},
    ),
    SelfReadRouteCase(
        name="self_activity",
        path="/self/activity?limit=10&offset=5",
        service_method="list_self_activity",
        success_response=SelfActivityListResponse(
            items=[
                SelfActivityResponse(
                    id="activity_1",
                    event_type="login_succeeded",
                    created_at=_dt(2026, 4, 25, 10, 30, 0),
                    summary="Signed in successfully",
                    device_id="device_1",
                    session_id="sess_1",
                )
            ],
            total=1,
            page=1,
            page_size=10,
        ),
        expected_call={"access_token": "access_token", "limit": 10, "offset": 5},
    ),
]


class FakeSelfService(RecordingRouteService):
    def __init__(self) -> None:
        responses = {case.service_method: case.success_response for case in SELF_READ_ROUTE_CASES}
        responses["revoke_self_session"] = SelfSessionRevokeResponse(
            success=True,
            session_id="sess_2",
            auth_state="revoked",
            already_revoked=False,
        )
        super().__init__(responses)

    def self_me(self, access_token: str) -> SelfMeResponse:
        return self.handle("self_me", access_token=access_token)

    def list_self_devices(self, access_token: str, *, limit: int = 20, offset: int = 0) -> SelfDeviceListResponse:
        return self.handle("list_self_devices", access_token=access_token, limit=limit, offset=offset)

    def list_self_sessions(self, access_token: str, *, limit: int = 20, offset: int = 0) -> SelfSessionListResponse:
        return self.handle("list_self_sessions", access_token=access_token, limit=limit, offset=offset)

    def list_self_activity(self, access_token: str, *, limit: int = 20, offset: int = 0) -> SelfActivityListResponse:
        return self.handle("list_self_activity", access_token=access_token, limit=limit, offset=offset)

    def revoke_self_session(self, access_token: str, session_id: str) -> SelfSessionRevokeResponse:
        return self.handle("revoke_self_session", access_token=access_token, session_id=session_id)


@pytest.fixture
def app():
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.mark.parametrize("case", SELF_READ_ROUTE_CASES, ids=[case.name for case in SELF_READ_ROUTE_CASES])
def test_self_service_read_routes_forward_bearer_token_and_query_params(case: SelfReadRouteCase, app) -> None:
    service = FakeSelfService()
    app.dependency_overrides[self_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            case.path,
            headers=bearer_headers("access_token"),
        )

    assert_json_model_response(response, case.success_response)
    assert_single_service_call(service.calls, method=case.service_method, **case.expected_call)


@pytest.mark.parametrize("case", SELF_READ_ROUTE_CASES, ids=[case.name for case in SELF_READ_ROUTE_CASES])
@pytest.mark.parametrize(
    ("expected_status", "expected_error_code", "expected_message", "expected_details"),
    [
        (401, "token_expired", "Access token expired or invalid", {"reason": "token_expired"}),
        (403, "revoked", "Remote authorization revoked", {"reason": "revoked"}),
    ],
    ids=["401", "403"],
)
def test_self_service_read_routes_surface_401_403_semantics(
    case: SelfReadRouteCase,
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
    service = FakeSelfService()
    service.errors[case.service_method] = AuthServiceError(
        error_case.error_code,
        error_case.message,
        status_code=error_case.status,
        details=error_case.details,
    )
    app.dependency_overrides[self_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            case.path,
            headers=bearer_headers(None if expected_status == 401 else "access_token"),
        )

    assert_error_response(response, error_case)
    expected_call = dict(case.expected_call, access_token=expected_access_token(expected_status, "access_token"))
    assert_single_service_call(service.calls, method=case.service_method, **expected_call)


def test_self_session_revoke_forwards_bearer_token_and_session_id(app) -> None:
    service = FakeSelfService()
    app.dependency_overrides[self_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/self/sessions/sess_2/revoke",
            headers=bearer_headers("access_token"),
        )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "session_id": "sess_2",
        "auth_state": "revoked",
        "already_revoked": False,
    }
    assert_single_service_call(
        service.calls,
        method="revoke_self_session",
        access_token="access_token",
        session_id="sess_2",
    )


@pytest.mark.parametrize(
    ("expected_status", "expected_error_code", "expected_message", "expected_details"),
    [
        (401, "token_expired", "Access token expired or invalid", {"reason": "token_expired"}),
        (403, "revoked", "Remote authorization revoked", {"reason": "revoked"}),
        (404, "not_found", "Requested resource was not found.", {"session_id": "sess_2"}),
    ],
    ids=["401", "403", "404"],
)
def test_self_session_revoke_surfaces_401_403_404_semantics(
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
    service = FakeSelfService()
    service.errors["revoke_self_session"] = AuthServiceError(
        error_case.error_code,
        error_case.message,
        status_code=error_case.status,
        details=error_case.details,
    )
    app.dependency_overrides[self_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/self/sessions/sess_2/revoke",
            headers=bearer_headers(None if expected_status == 401 else "access_token"),
        )

    assert_error_response(response, error_case)
    assert_single_service_call(
        service.calls,
        method="revoke_self_session",
        access_token=expected_access_token(expected_status, "access_token"),
        session_id="sess_2",
    )
