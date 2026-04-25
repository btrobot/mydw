from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core.rate_limit import InMemoryRateLimiter
from app.main import create_app
from app.schemas.auth import AuthSuccessResponse, RefreshRequest, UserIdentity
from app.services.auth_service import AuthServiceError
from tests.support.route_contract import (
    ErrorContractCase,
    RecordingRouteService,
    assert_error_response,
    assert_json_model_response,
    assert_single_service_call,
)


class FakeAuthRefreshService(RecordingRouteService):
    def __init__(self, *, response: AuthSuccessResponse | None = None, error: AuthServiceError | None = None) -> None:
        super().__init__({"refresh": response} if response is not None else {})
        if error is not None:
            self.errors["refresh"] = error

    def refresh(self, payload: RefreshRequest, *, client_ip: str) -> AuthSuccessResponse:
        return self.handle(
            "refresh",
            refresh_token=payload.refresh_token,
            device_id=payload.device_id,
            client_version=payload.client_version,
            client_ip=client_ip,
        )


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    app = create_app()
    monkeypatch.setattr(
        auth_api,
        "refresh_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=5),
    )
    yield app
    app.dependency_overrides.clear()


def _make_success_response() -> AuthSuccessResponse:
    return AuthSuccessResponse(
        access_token="access_token_next",
        refresh_token="refresh_token_next",
        expires_at=datetime(2026, 5, 1, 0, 0, 0),
        token_type="Bearer",
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
        offline_grace_until=None,
        minimum_supported_version="0.2.0",
    )


def test_refresh_returns_success_payload_and_forwards_client_context(app) -> None:
    service = FakeAuthRefreshService(response=_make_success_response())
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/refresh",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
                "client_version": "0.2.0",
            },
        )

    assert_json_model_response(response, _make_success_response())
    assert_single_service_call(
        service.calls,
        method="refresh",
        refresh_token="refresh_token",
        device_id="device_1",
        client_version="0.2.0",
        client_ip="testclient",
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
def test_refresh_surfaces_service_error_semantics(
    app,
    error: AuthServiceError,
    expected_status: int,
    expected_body: dict[str, object],
) -> None:
    error_case = ErrorContractCase(
        status=expected_status,
        error_code=expected_body["error_code"],
        message=expected_body["message"],
        details=expected_body["details"],
    )
    service = FakeAuthRefreshService(error=error)
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/refresh",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
                "client_version": "0.2.0",
            },
        )

    assert_error_response(response, error_case)
    assert_single_service_call(
        service.calls,
        method="refresh",
        refresh_token="refresh_token",
        device_id="device_1",
        client_version="0.2.0",
        client_ip="testclient",
    )


def test_refresh_returns_429_before_calling_service_when_rate_limit_bucket_is_full(app, monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeAuthRefreshService(response=_make_success_response())
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service
    monkeypatch.setattr(
        auth_api,
        "refresh_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=1),
    )

    with TestClient(app) as client:
        first_response = client.post(
            "/refresh",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
                "client_version": "0.2.0",
            },
        )
        second_response = client.post(
            "/refresh",
            json={
                "refresh_token": "refresh_token",
                "device_id": "device_1",
                "client_version": "0.2.0",
            },
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json() == {
        "error_code": "too_many_requests",
        "message": "Too many refresh attempts, please retry later.",
        "details": {},
    }
    assert_single_service_call(
        service.calls,
        method="refresh",
        refresh_token="refresh_token",
        device_id="device_1",
        client_version="0.2.0",
        client_ip="testclient",
    )
