from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.main import create_app
from app.schemas.auth import LogoutRequest, LogoutResponse, MeResponse, UserIdentity
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


class FakeAuthSessionService(RecordingRouteService):
    def __init__(
        self,
        *,
        logout_response: LogoutResponse | None = None,
        me_response: MeResponse | None = None,
    ) -> None:
        responses = {}
        if logout_response is not None:
            responses["logout"] = logout_response
        if me_response is not None:
            responses["me"] = me_response
        super().__init__(responses)

    def logout(self, payload: LogoutRequest) -> LogoutResponse:
        return self.handle(
            "logout",
            refresh_token=payload.refresh_token,
            device_id=payload.device_id,
        )

    def me(self, access_token: str) -> MeResponse:
        return self.handle("me", access_token=access_token)


@pytest.fixture
def app():
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def _make_me_response() -> MeResponse:
    return MeResponse(
        user=UserIdentity(
            id="u_1",
            username="alice",
            display_name="Alice",
            tenant_id="tenant_1",
        ),
        license_status="active",
        entitlements=["dashboard:view"],
        device_id="device_1",
        device_status="bound",
        offline_grace_until=datetime(2026, 5, 2, 0, 0, 0),
        minimum_supported_version="0.2.0",
    )


def test_logout_returns_success_payload_and_forwards_request_payload(app) -> None:
    service = FakeAuthSessionService(logout_response=LogoutResponse(success=True))
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/logout",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert_single_service_call(
        service.calls,
        method="logout",
        refresh_token="refresh_token",
        device_id="device_1",
    )


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_body"),
    [
        (
            AuthServiceError(
                "token_expired",
                "Refresh token expired or invalid",
                status_code=401,
                details={"reason": "token_expired"},
            ),
            401,
            {
                "error_code": "token_expired",
                "message": "Refresh token expired or invalid",
                "details": {"reason": "token_expired"},
            },
        ),
        (
            AuthServiceError(
                "revoked",
                "Remote authorization revoked",
                status_code=403,
                details={"reason": "revoked"},
            ),
            403,
            {
                "error_code": "revoked",
                "message": "Remote authorization revoked",
                "details": {"reason": "revoked"},
            },
        ),
    ],
    ids=["401", "403"],
)
def test_logout_surfaces_service_error_semantics(
    app,
    error: AuthServiceError,
    expected_status: int,
    expected_body: dict[str, object],
) -> None:
    service = FakeAuthSessionService(logout_response=LogoutResponse(success=True))
    service.errors["logout"] = error
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/logout",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
            },
        )

    assert_error_response(
        response,
        ErrorContractCase(
            status=expected_status,
            error_code=expected_body["error_code"],
            message=expected_body["message"],
            details=expected_body["details"],
        ),
    )
    assert_single_service_call(
        service.calls,
        method="logout",
        refresh_token="refresh_token",
        device_id="device_1",
    )


def test_me_returns_success_payload_and_extracts_bearer_token(app) -> None:
    service = FakeAuthSessionService(me_response=_make_me_response())
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            "/me",
            headers=bearer_headers("access_token"),
        )

    assert_json_model_response(response, _make_me_response())
    assert_single_service_call(
        service.calls,
        method="me",
        access_token="access_token",
    )


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_body"),
    [
        (
            AuthServiceError(
                "token_expired",
                "Access token expired or invalid",
                status_code=401,
                details={"reason": "token_expired"},
            ),
            401,
            {
                "error_code": "token_expired",
                "message": "Access token expired or invalid",
                "details": {"reason": "token_expired"},
            },
        ),
        (
            AuthServiceError(
                "revoked",
                "Remote authorization revoked",
                status_code=403,
                details={"reason": "revoked"},
            ),
            403,
            {
                "error_code": "revoked",
                "message": "Remote authorization revoked",
                "details": {"reason": "revoked"},
            },
        ),
    ],
    ids=["401", "403"],
)
def test_me_surfaces_service_error_semantics(
    app,
    error: AuthServiceError,
    expected_status: int,
    expected_body: dict[str, object],
) -> None:
    service = FakeAuthSessionService(me_response=_make_me_response())
    service.errors["me"] = error
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            "/me",
            headers=bearer_headers(None if expected_status == 401 else "access_token"),
        )

    assert_error_response(
        response,
        ErrorContractCase(
            status=expected_status,
            error_code=expected_body["error_code"],
            message=expected_body["message"],
            details=expected_body["details"],
        ),
    )
    assert_single_service_call(
        service.calls,
        method="me",
        access_token=expected_access_token(expected_status, "access_token"),
    )
