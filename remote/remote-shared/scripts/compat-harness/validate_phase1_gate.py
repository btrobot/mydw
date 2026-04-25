from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient

from build_phase1_manifest import OUTPUT as MANIFEST_OUTPUT, build_manifest
from export_phase1_openapi import OUTPUT as RUNTIME_SPEC_OUTPUT, build_runtime_spec


ROOT = Path(__file__).resolve().parents[4]
ARTIFACT_ROOT = ROOT / "remote" / "remote-shared"
FIXTURE_ROOT = ARTIFACT_ROOT / "scripts" / "compat-harness" / "fixtures"
SOURCE_SPEC_PATH = ARTIFACT_ROOT / "openapi" / "remote-auth-v1.yaml"
REMOTE_BACKEND_ROOT = ROOT / "remote" / "remote-backend"
ERROR_CODES_PATH = ARTIFACT_ROOT / "scripts" / "compat-harness" / "error-codes.json"


def fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def assert_required_keys(payload: dict[str, Any], required: list[str], name: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise AssertionError(f"{name} missing required keys: {missing}")


def assert_error_response(payload: dict[str, Any], expected: dict[str, Any], name: str) -> None:
    assert_required_keys(payload, ["error_code", "message"], name)
    if payload["error_code"] != expected["error_code"]:
        raise AssertionError(f"{name} error_code drifted: {payload['error_code']} != {expected['error_code']}")
    if payload["message"] != expected["message"]:
        raise AssertionError(f"{name} message drifted: {payload['message']} != {expected['message']}")


def load_source_spec() -> dict:
    return yaml.safe_load(SOURCE_SPEC_PATH.read_text(encoding="utf-8"))


def validate_openapi_drift(source_spec: dict, runtime_spec: dict) -> None:
    phase1_paths = {
        "/login",
        "/refresh",
        "/logout",
        "/me",
        "/self/me",
        "/self/devices",
        "/self/sessions",
        "/self/activity",
        "/self/sessions/{session_id}/revoke",
        "/admin/login",
        "/admin/session",
    }
    for path in phase1_paths:
        if path not in source_spec["paths"]:
            raise AssertionError(f"source OpenAPI missing expected Phase 1 path: {path}")
        if path not in runtime_spec["paths"]:
            raise AssertionError(f"runtime OpenAPI missing expected Phase 1 path: {path}")

    schema_names = [
        "LoginRequest",
        "RefreshRequest",
        "LogoutRequest",
        "AuthSuccessResponse",
        "MeResponse",
        "LogoutResponse",
        "ErrorResponse",
        "AdminLoginRequest",
        "AdminIdentity",
        "AdminLoginResponse",
        "AdminCurrentSessionResponse",
        "SelfUserIdentity",
        "SelfMeResponse",
        "SelfDeviceResponse",
        "SelfDeviceListResponse",
        "SelfSessionResponse",
        "SelfSessionListResponse",
        "SelfActivityResponse",
        "SelfActivityListResponse",
        "SelfSessionRevokeResponse",
    ]
    for name in schema_names:
        source_schema = source_spec["components"]["schemas"][name]
        runtime_schema = runtime_spec["components"]["schemas"].get(name)
        if runtime_schema is None:
            raise AssertionError(f"runtime OpenAPI missing schema: {name}")

        source_required = sorted(source_schema.get("required", []))
        runtime_required = sorted(runtime_schema.get("required", []))
        if source_required != runtime_required:
            raise AssertionError(f"schema required mismatch for {name}: {source_required} != {runtime_required}")

        source_properties = sorted(source_schema.get("properties", {}).keys())
        runtime_properties = sorted(runtime_schema.get("properties", {}).keys())
        if source_properties != runtime_properties:
            raise AssertionError(f"schema property mismatch for {name}: {source_properties} != {runtime_properties}")

    source_security = source_spec["components"].get("securitySchemes", {})
    runtime_security = runtime_spec["components"].get("securitySchemes", {})
    if source_security != runtime_security:
        raise AssertionError("runtime OpenAPI securitySchemes drifted from source contract")

    endpoint_responses = {
        "/login": ["200", "401", "403", "429"],
        "/refresh": ["200", "401", "403", "429"],
        "/logout": ["200", "401", "403"],
        "/me": ["200", "401", "403"],
        "/self/me": ["200", "401", "403"],
        "/self/devices": ["200", "401", "403"],
        "/self/sessions": ["200", "401", "403"],
        "/self/activity": ["200", "401", "403"],
        "/self/sessions/{session_id}/revoke": ["200", "401", "403", "404"],
        "/admin/login": ["200", "401", "403", "429"],
        "/admin/session": ["200", "401", "403"],
    }
    for path, response_codes in endpoint_responses.items():
        operation = next(iter(source_spec["paths"][path]))
        source_codes = sorted(source_spec["paths"][path][operation]["responses"].keys())
        source_codes = [code for code in source_codes if code != "422"]
        runtime_codes = sorted(
            code
            for code in runtime_spec["paths"][path][operation]["responses"].keys()
            if code != "422"
        )
        if sorted(response_codes) != source_codes:
            raise AssertionError(f"source OpenAPI response codes changed for {path}: {source_codes}")
        if sorted(response_codes) != runtime_codes:
            raise AssertionError(f"runtime OpenAPI response codes drifted for {path}: {runtime_codes}")

    secure_paths = ["/me", "/self/me", "/self/devices", "/self/sessions", "/self/activity", "/self/sessions/{session_id}/revoke", "/admin/session"]
    for path in secure_paths:
        operation = next(iter(source_spec["paths"][path]))
        source_security_requirement = source_spec["paths"][path][operation].get("security")
        runtime_security_requirement = runtime_spec["paths"][path][operation].get("security")
        if source_security_requirement != runtime_security_requirement:
            raise AssertionError(f"runtime OpenAPI security requirement drifted for {path}")


def validate_runtime_artifact_reproducibility(runtime_spec: dict) -> None:
    checked_in = json.loads(RUNTIME_SPEC_OUTPUT.read_text(encoding="utf-8"))
    if checked_in != runtime_spec:
        raise AssertionError("runtime OpenAPI drift detected; regenerate with export_phase1_openapi.py")


def validate_fixtures(source_spec: dict) -> None:
    schemas = source_spec["components"]["schemas"]
    success_fixture_map = {
        "login-success.json": schemas["AuthSuccessResponse"]["required"],
        "refresh-success.json": schemas["AuthSuccessResponse"]["required"],
        "logout-success.json": schemas["LogoutResponse"]["required"],
        "me-success.json": schemas["MeResponse"]["required"],
        "self-me-success.json": schemas["SelfMeResponse"]["required"],
        "self-devices-success.json": schemas["SelfDeviceListResponse"]["required"],
        "self-sessions-success.json": schemas["SelfSessionListResponse"]["required"],
        "self-activity-success.json": schemas["SelfActivityListResponse"]["required"],
        "self-session-revoke-success.json": schemas["SelfSessionRevokeResponse"]["required"],
    }
    for filename, required in success_fixture_map.items():
        payload = fixture(filename)
        assert_required_keys(payload, required, filename)

    self_me_payload = fixture("self-me-success.json")
    if "tenant_id" in self_me_payload["user"]:
        raise AssertionError("self-me-success.json must not expose tenant_id")

    allowed_event_types = {
        "login_succeeded",
        "login_failed",
        "session_refreshed",
        "session_revoked",
        "device_bound",
        "device_unbound",
    }
    for event in fixture("self-activity-success.json")["items"]:
        assert_required_keys(event, ["id", "event_type", "created_at", "summary"], "self-activity event")
        if event["event_type"] not in allowed_event_types:
            raise AssertionError(f"self-activity fixture uses unsupported event type {event['event_type']}")

    self_revoke_fixture = fixture("self-session-revoke-success.json")
    if self_revoke_fixture["success"] is not True:
        raise AssertionError("self-session-revoke-success.json must freeze success=true")
    if self_revoke_fixture["auth_state"] != "revoked":
        raise AssertionError("self-session-revoke-success.json must freeze auth_state=revoked")
    if self_revoke_fixture["already_revoked"] is not False:
        raise AssertionError("self-session-revoke-success.json must freeze already_revoked=false for the first revoke")

    error_codes = set(json.loads(ERROR_CODES_PATH.read_text(encoding="utf-8"))["error_codes"])
    for path in sorted(FIXTURE_ROOT.glob("error-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert_required_keys(payload, ["error_code", "message"], path.name)
        if payload["error_code"] not in error_codes:
            raise AssertionError(f"{path.name} uses unknown error code {payload['error_code']}")


class CompatHarness:
    def request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
        raise NotImplementedError

    def seed_admin_password(self) -> str:
        return os.environ.get("REMOTE_COMPAT_ADMIN_PASSWORD", "admin-secret")

    def managed_username(self) -> str:
        return os.environ.get("REMOTE_COMPAT_USERNAME", "alice")

    def managed_password(self) -> str:
        return os.environ.get("REMOTE_COMPAT_PASSWORD", "secret")

    def managed_device(self) -> str:
        return os.environ.get("REMOTE_COMPAT_DEVICE_ID", "device_compat")

    def admin_username(self) -> str:
        return os.environ.get("REMOTE_COMPAT_ADMIN_USERNAME", "admin")

    def cleanup(self) -> None:
        return None

    def reset_rate_limits(self) -> None:
        return None

    @property
    def supports_db_mutation(self) -> bool:
        return False

    def set_license_status(self, status: str) -> None:
        raise RuntimeError("license mutation is unavailable for external compatibility mode")


class LocalCompatHarness(CompatHarness):
    def __init__(self) -> None:
        if str(REMOTE_BACKEND_ROOT) not in sys.path:
            sys.path.insert(0, str(REMOTE_BACKEND_ROOT))

        from app.api.admin import admin_login_rate_limiter  # noqa: WPS433
        from app.api.auth import login_rate_limiter, refresh_rate_limiter  # noqa: WPS433
        from app.core.config import reset_settings_cache  # noqa: WPS433
        from app.core.db import reset_db_state  # noqa: WPS433
        from app.migrations.alembic import ensure_database_on_head  # noqa: WPS433
        from app.main import create_app  # noqa: WPS433

        self._previous_db_url = os.environ.get("REMOTE_BACKEND_DATABASE_URL")
        self._temp_dir = tempfile.TemporaryDirectory()
        os.environ["REMOTE_BACKEND_DATABASE_URL"] = f"sqlite:///{(Path(self._temp_dir.name) / 'phase1_gate.sqlite3').as_posix()}"
        reset_settings_cache()
        reset_db_state()
        self.login_rate_limiter = login_rate_limiter
        self.refresh_rate_limiter = refresh_rate_limiter
        self.admin_login_rate_limiter = admin_login_rate_limiter
        self.reset_rate_limits()
        ensure_database_on_head()
        self.client = TestClient(create_app())

    def request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
        response = self.client.request(method, path, json=json_body, headers=headers)
        payload = response.json()
        return response.status_code, payload, dict(response.headers)

    @property
    def supports_db_mutation(self) -> bool:
        return True

    def reset_rate_limits(self) -> None:
        self.login_rate_limiter.reset()
        self.refresh_rate_limiter.reset()
        self.admin_login_rate_limiter.reset()

    def set_license_status(self, status: str) -> None:
        from app.core.db import session_scope  # noqa: WPS433
        from app.models import License, User  # noqa: WPS433

        with session_scope() as session:
            user = session.query(User).filter_by(username=self.managed_username()).one()
            license_row = session.query(License).filter_by(user_id=user.id).one()
            license_row.license_status = status

    def cleanup(self) -> None:
        from app.core.config import reset_settings_cache  # noqa: WPS433
        from app.core.db import reset_db_state  # noqa: WPS433

        if self._previous_db_url is None:
            os.environ.pop("REMOTE_BACKEND_DATABASE_URL", None)
        else:
            os.environ["REMOTE_BACKEND_DATABASE_URL"] = self._previous_db_url
        reset_settings_cache()
        reset_db_state()
        self._temp_dir.cleanup()


class ExternalCompatHarness(CompatHarness):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
        data = None
        request_headers = {"Content-Type": "application/json"} if json_body is not None else {}
        if headers:
            request_headers.update(headers)
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
        request = urllib.request.Request(f"{self.base_url}{path}", method=method, data=data, headers=request_headers)
        try:
            with urllib.request.urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return response.status, payload, dict(response.headers)
        except urllib.error.HTTPError as error:
            payload = json.loads(error.read().decode("utf-8"))
            return error.code, payload, dict(error.headers)


def build_harness() -> CompatHarness:
    base_url = os.environ.get("REMOTE_COMPAT_BASE_URL")
    if base_url:
        return ExternalCompatHarness(base_url)
    return LocalCompatHarness()


def post_json(harness: CompatHarness, path: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
    return harness.request("POST", path, json_body=payload, headers=headers)


def get_json(harness: CompatHarness, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
    return harness.request("GET", path, headers=headers)


def validate_runtime_contract() -> None:
    harness = build_harness()
    try:
        login_fixture = fixture("login-success.json")
        refresh_fixture = fixture("refresh-success.json")
        me_fixture = fixture("me-success.json")
        self_me_fixture = fixture("self-me-success.json")
        self_devices_fixture = fixture("self-devices-success.json")
        self_sessions_fixture = fixture("self-sessions-success.json")
        self_activity_fixture = fixture("self-activity-success.json")
        self_revoke_fixture = fixture("self-session-revoke-success.json")
        logout_fixture = fixture("logout-success.json")
        invalid_fixture = fixture("error-invalid-credentials.json")
        disabled_fixture = fixture("error-disabled.json")
        revoked_fixture = fixture("error-revoked.json")
        mismatch_fixture = fixture("error-device-mismatch.json")
        min_version_fixture = fixture("error-minimum-version-required.json")
        not_found_fixture = fixture("error-not-found.json")
        rate_limit_fixture = fixture("error-too-many-requests.json")

        invalid_login = post_json(
            harness,
            "/login",
            {"username": harness.managed_username(), "password": "wrong", "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if invalid_login[0] != 401:
            raise AssertionError(f"invalid credentials path drifted: {invalid_login[0]} {invalid_login[1]}")
        assert_error_response(invalid_login[1], invalid_fixture, "runtime invalid credentials")

        for _ in range(5):
            status, _, _ = post_json(
                harness,
                "/login",
                {"username": "ghost-user", "password": "wrong", "device_id": harness.managed_device(), "client_version": "0.2.0"},
            )
            if status != 401:
                raise AssertionError(f"rate-limit warmup drifted: {status}")
        blocked_login = post_json(
            harness,
            "/login",
            {"username": "ghost-user", "password": "wrong", "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if blocked_login[0] != 429:
            raise AssertionError(f"too_many_requests path drifted: {blocked_login[0]} {blocked_login[1]}")
        assert_error_response(blocked_login[1], rate_limit_fixture, "runtime too many requests")

        login = post_json(
            harness,
            "/login",
            {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if login[0] != 200:
            raise AssertionError(f"compat login failed: {login[0]} {login[1]}")
        login_payload = login[1]
        assert_required_keys(login_payload, list(login_fixture.keys()), "runtime login payload")
        if login_payload["license_status"] != login_fixture["license_status"]:
            raise AssertionError("runtime login payload drifted on license_status")

        refresh = post_json(
            harness,
            "/refresh",
            {"refresh_token": login_payload["refresh_token"], "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if refresh[0] != 200:
            raise AssertionError(f"compat refresh failed: {refresh[0]} {refresh[1]}")
        refresh_payload = refresh[1]
        assert_required_keys(refresh_payload, list(refresh_fixture.keys()), "runtime refresh payload")

        revoked_refresh = post_json(
            harness,
            "/refresh",
            {"refresh_token": login_payload["refresh_token"], "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if revoked_refresh[0] != 403:
            raise AssertionError(f"refresh revoked path drifted: {revoked_refresh[0]} {revoked_refresh[1]}")
        assert_error_response(revoked_refresh[1], revoked_fixture, "runtime revoked refresh")

        me = get_json(harness, "/me", headers={"Authorization": f"Bearer {refresh_payload['access_token']}"})
        if me[0] != 200:
            raise AssertionError(f"compat me failed: {me[0]} {me[1]}")
        me_payload = me[1]
        assert_required_keys(me_payload, list(me_fixture.keys()), "runtime me payload")

        self_me = get_json(harness, "/self/me", headers={"Authorization": f"Bearer {refresh_payload['access_token']}"})
        if self_me[0] != 200:
            raise AssertionError(f"compat self/me failed: {self_me[0]} {self_me[1]}")
        self_me_payload = self_me[1]
        assert_required_keys(self_me_payload, list(self_me_fixture.keys()), "runtime self/me payload")
        if "tenant_id" in self_me_payload["user"]:
            raise AssertionError("runtime /self/me payload must not expose tenant_id")

        self_devices = get_json(harness, "/self/devices", headers={"Authorization": f"Bearer {refresh_payload['access_token']}"})
        if self_devices[0] != 200:
            raise AssertionError(f"compat self/devices failed: {self_devices[0]} {self_devices[1]}")
        self_devices_payload = self_devices[1]
        assert_required_keys(self_devices_payload, list(self_devices_fixture.keys()), "runtime self/devices payload")
        if not self_devices_payload["items"]:
            raise AssertionError("runtime /self/devices returned no items for authenticated user")

        self_sessions = get_json(harness, "/self/sessions", headers={"Authorization": f"Bearer {refresh_payload['access_token']}"})
        if self_sessions[0] != 200:
            raise AssertionError(f"compat self/sessions failed: {self_sessions[0]} {self_sessions[1]}")
        self_sessions_payload = self_sessions[1]
        assert_required_keys(self_sessions_payload, list(self_sessions_fixture.keys()), "runtime self/sessions payload")
        if not self_sessions_payload["items"]:
            raise AssertionError("runtime /self/sessions returned no items for authenticated user")

        second_login = post_json(
            harness,
            "/login",
            {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if second_login[0] != 200:
            raise AssertionError(f"compat second login failed: {second_login[0]} {second_login[1]}")
        second_login_payload = second_login[1]

        second_sessions = get_json(harness, "/self/sessions", headers={"Authorization": f"Bearer {second_login_payload['access_token']}"})
        if second_sessions[0] != 200:
            raise AssertionError(f"compat second self/sessions failed: {second_sessions[0]} {second_sessions[1]}")
        target_session_id = next((item["session_id"] for item in second_sessions[1]["items"] if not item["is_current"]), None)
        if target_session_id is None:
            raise AssertionError("compat self/sessions did not expose a non-current session for revoke testing")

        revoke = post_json(
            harness,
            f"/self/sessions/{target_session_id}/revoke",
            {},
            headers={"Authorization": f"Bearer {second_login_payload['access_token']}"},
        )
        if revoke[0] != 200:
            raise AssertionError(f"compat self revoke failed: {revoke[0]} {revoke[1]}")
        revoke_payload = revoke[1]
        assert_required_keys(revoke_payload, list(self_revoke_fixture.keys()), "runtime self revoke payload")
        if revoke_payload["success"] is not True:
            raise AssertionError("runtime self revoke must return success=true")
        if revoke_payload["session_id"] != target_session_id:
            raise AssertionError("runtime self revoke must echo the revoked session_id")
        if revoke_payload["auth_state"] != "revoked":
            raise AssertionError("runtime self revoke must freeze auth_state=revoked")
        if revoke_payload["already_revoked"]:
            raise AssertionError("runtime self revoke should not report already_revoked on first revoke")

        repeat_revoke = post_json(
            harness,
            f"/self/sessions/{target_session_id}/revoke",
            {},
            headers={"Authorization": f"Bearer {second_login_payload['access_token']}"},
        )
        if repeat_revoke[0] != 200:
            raise AssertionError(f"compat repeated self revoke failed: {repeat_revoke[0]} {repeat_revoke[1]}")
        if repeat_revoke[1].get("success") is not True:
            raise AssertionError("runtime repeated self revoke must return success=true")
        if repeat_revoke[1].get("session_id") != target_session_id:
            raise AssertionError("runtime repeated self revoke must echo the revoked session_id")
        if repeat_revoke[1].get("auth_state") != "revoked":
            raise AssertionError("runtime repeated self revoke must freeze auth_state=revoked")
        if repeat_revoke[1].get("already_revoked") is not True:
            raise AssertionError("runtime self revoke should be idempotent with already_revoked=true")

        if harness.supports_db_mutation:
            from app.core.db import session_scope  # noqa: WPS433
            from app.models import AuditLog  # noqa: WPS433

            with session_scope() as session:
                audits = (
                    session.query(AuditLog)
                    .filter_by(event_type="self_session_revoked", target_session_id=target_session_id)
                    .order_by(AuditLog.id.desc())
                    .limit(2)
                    .all()
                )
                if len(audits) != 2:
                    raise AssertionError("runtime self revoke must emit two audit rows across first and repeated revoke")
                latest_details = json.loads(audits[0].details_json or "{}")
                previous_details = json.loads(audits[1].details_json or "{}")
                if audits[0].actor_type != "user" or audits[1].actor_type != "user":
                    raise AssertionError("runtime self revoke audit rows must use actor_type=user")
                if audits[0].target_session_id != target_session_id or audits[1].target_session_id != target_session_id:
                    raise AssertionError("runtime self revoke audit rows must link the target_session_id")
                if latest_details.get("already_revoked") is not True:
                    raise AssertionError("runtime repeated self revoke audit row must persist already_revoked=true")
                if previous_details.get("already_revoked") is not False:
                    raise AssertionError("runtime first self revoke audit row must persist already_revoked=false")

        revoked_refresh = post_json(
            harness,
            "/refresh",
            {"refresh_token": refresh_payload["refresh_token"], "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if revoked_refresh[0] != 403:
            raise AssertionError(f"revoked refresh path drifted: {revoked_refresh[0]} {revoked_refresh[1]}")
        assert_error_response(revoked_refresh[1], revoked_fixture, "runtime revoked refresh after self revoke")

        foreign_revoke = post_json(
            harness,
            "/self/sessions/sess_foreign/revoke",
            {},
            headers={"Authorization": f"Bearer {second_login_payload['access_token']}"},
        )
        if foreign_revoke[0] != 404:
            raise AssertionError(f"foreign self revoke drifted: {foreign_revoke[0]} {foreign_revoke[1]}")
        assert_error_response(foreign_revoke[1], not_found_fixture, "runtime self revoke not found")

        logout = post_json(
            harness,
            "/logout",
            {"refresh_token": second_login_payload["refresh_token"], "device_id": harness.managed_device()},
        )
        if logout[0] != 200:
            raise AssertionError(f"compat logout failed: {logout[0]} {logout[1]}")
        assert_required_keys(logout[1], list(logout_fixture.keys()), "runtime logout payload")

        revoked_self_revoke = post_json(
            harness,
            f"/self/sessions/{target_session_id}/revoke",
            {},
            headers={"Authorization": f"Bearer {second_login_payload['access_token']}"},
        )
        if revoked_self_revoke[0] != 403:
            raise AssertionError(f"revoked self revoke drifted: {revoked_self_revoke[0]} {revoked_self_revoke[1]}")
        assert_error_response(revoked_self_revoke[1], revoked_fixture, "runtime self revoke after logout")

        relogin = post_json(
            harness,
            "/login",
            {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": harness.managed_device(), "client_version": "0.2.0"},
        )
        if relogin[0] != 200:
            raise AssertionError(f"compat re-login failed: {relogin[0]} {relogin[1]}")
        self_activity = get_json(harness, "/self/activity", headers={"Authorization": f"Bearer {relogin[1]['access_token']}"})
        if self_activity[0] != 200:
            raise AssertionError(f"compat self/activity failed: {self_activity[0]} {self_activity[1]}")
        self_activity_payload = self_activity[1]
        assert_required_keys(self_activity_payload, list(self_activity_fixture.keys()), "runtime self/activity payload")
        allowed_activity_keys = {"id", "event_type", "created_at", "summary", "device_id", "session_id"}
        allowed_event_types = {
            "login_succeeded",
            "login_failed",
            "session_refreshed",
            "session_revoked",
            "device_bound",
            "device_unbound",
        }
        event_types = set()
        for item in self_activity_payload["items"]:
            assert_required_keys(item, ["id", "event_type", "created_at", "summary"], "runtime self/activity item")
            if set(item.keys()) - allowed_activity_keys:
                raise AssertionError(f"runtime /self/activity exposed unexpected keys: {sorted(set(item.keys()) - allowed_activity_keys)}")
            if item["event_type"] not in allowed_event_types:
                raise AssertionError(f"runtime /self/activity exposed unsupported event type: {item['event_type']}")
            event_types.add(item["event_type"])
        if "session_revoked" not in event_types:
            raise AssertionError("runtime /self/activity did not project the session_revoked event")

        harness.reset_rate_limits()

        min_version = post_json(
            harness,
            "/login",
            {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": harness.managed_device(), "client_version": "0.1.0"},
        )
        if min_version[0] != 403:
            raise AssertionError(f"minimum version path drifted: {min_version[0]} {min_version[1]}")
        assert_error_response(min_version[1], min_version_fixture, "runtime minimum version")

        mismatch = post_json(
            harness,
            "/login",
            {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": "device_other", "client_version": "0.2.0"},
        )
        if mismatch[0] != 403:
            raise AssertionError(f"device mismatch path drifted: {mismatch[0]} {mismatch[1]}")
        assert_error_response(mismatch[1], mismatch_fixture, "runtime device mismatch")

        if harness.supports_db_mutation:
            harness.reset_rate_limits()
            harness.set_license_status("disabled")
            disabled = post_json(
                harness,
                "/login",
                {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": harness.managed_device(), "client_version": "0.2.0"},
            )
            if disabled[0] != 403:
                raise AssertionError(f"disabled path drifted: {disabled[0]} {disabled[1]}")
            assert_error_response(disabled[1], disabled_fixture, "runtime disabled")
            harness.set_license_status("active")

            harness.reset_rate_limits()
            harness.set_license_status("revoked")
            revoked_login = post_json(
                harness,
                "/login",
                {"username": harness.managed_username(), "password": harness.managed_password(), "device_id": harness.managed_device(), "client_version": "0.2.0"},
            )
            if revoked_login[0] != 403:
                raise AssertionError(f"revoked login path drifted: {revoked_login[0]} {revoked_login[1]}")
            assert_error_response(revoked_login[1], revoked_fixture, "runtime revoked login")
            harness.set_license_status("active")

        admin_login = post_json(
            harness,
            "/admin/login",
            {"username": harness.admin_username(), "password": harness.seed_admin_password()},
        )
        if admin_login[0] != 200:
            raise AssertionError(f"admin compat login failed: {admin_login[0]} {admin_login[1]}")
        admin_session = get_json(harness, "/admin/session", headers={"Authorization": f"Bearer {admin_login[1]['access_token']}"})
        if admin_session[0] != 200:
            raise AssertionError(f"admin compat session failed: {admin_session[0]} {admin_session[1]}")
    finally:
        harness.cleanup()


def validate_manifest_reproducibility() -> None:
    current = build_manifest()
    checked_in = json.loads(MANIFEST_OUTPUT.read_text(encoding="utf-8"))
    if current != checked_in:
        raise AssertionError("phase1 manifest drift detected; regenerate with build_phase1_manifest.py")


def main() -> None:
    source_spec = load_source_spec()
    runtime_spec = build_runtime_spec()
    validate_openapi_drift(source_spec, runtime_spec)
    validate_runtime_artifact_reproducibility(runtime_spec)
    validate_fixtures(source_spec)
    validate_runtime_contract()
    validate_manifest_reproducibility()
    print("phase1 compatibility gate: PASS")


if __name__ == "__main__":
    main()
