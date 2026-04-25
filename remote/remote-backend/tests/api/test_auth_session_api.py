from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.main import create_app
from app.schemas.auth import LogoutRequest, LogoutResponse, MeResponse, UserIdentity
from app.services.auth_service import AuthServiceError


class FakeAuthSessionService:
    def __init__(
        self,
        *,
        logout_response: LogoutResponse | None = None,
        me_response: MeResponse | None = None,
    ) -> None:
        self.logout_response = logout_response
        self.me_response = me_response
        self.logout_error: AuthServiceError | None = None
        self.me_error: AuthServiceError | None = None
        self.logout_calls: list[dict[str, str]] = []
        self.me_calls: list[dict[str, str]] = []

    def logout(self, payload: LogoutRequest) -> LogoutResponse:
        self.logout_calls.append(
            {
                "refresh_token": payload.refresh_token,
                "device_id": payload.device_id,
            }
        )
        if self.logout_error is not None:
            raise self.logout_error
        assert self.logout_response is not None
        return self.logout_response

    def me(self, access_token: str) -> MeResponse:
        self.me_calls.append({"access_token": access_token})
        if self.me_error is not None:
            raise self.me_error
        assert self.me_response is not None
        return self.me_response


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
    assert service.logout_calls == [
        {
            "refresh_token": "refresh_token",
            "device_id": "device_1",
        }
    ]


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
    service.logout_error = error
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/logout",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
            },
        )

    assert response.status_code == expected_status
    assert response.json() == expected_body
    assert service.logout_calls == [
        {
            "refresh_token": "refresh_token",
            "device_id": "device_1",
        }
    ]


def test_me_returns_success_payload_and_extracts_bearer_token(app) -> None:
    service = FakeAuthSessionService(me_response=_make_me_response())
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer access_token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "user": {
            "id": "u_1",
            "username": "alice",
            "display_name": "Alice",
            "tenant_id": "tenant_1",
        },
        "license_status": "active",
        "entitlements": ["dashboard:view"],
        "device_id": "device_1",
        "device_status": "bound",
        "offline_grace_until": "2026-05-02T00:00:00",
        "minimum_supported_version": "0.2.0",
    }
    assert service.me_calls == [{"access_token": "access_token"}]


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
    service.me_error = error
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    headers = None if expected_status == 401 else {"Authorization": "Bearer access_token"}

    with TestClient(app) as client:
        response = client.get("/me", headers=headers)

    assert response.status_code == expected_status
    assert response.json() == expected_body
    assert service.me_calls == [
        {"access_token": "" if expected_status == 401 else "access_token"}
    ]
