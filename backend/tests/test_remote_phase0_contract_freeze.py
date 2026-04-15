from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "remote" / "remote-shared" / "docs"
OPENAPI_PATH = ROOT / "remote" / "remote-shared" / "openapi" / "remote-auth-v1.yaml"


def test_phase0_contract_docs_exist() -> None:
    expected = [
        "auth-domain-boundaries.md",
        "token-session-model.md",
        "error-code-matrix.md",
        "contract-versioning-policy.md",
        "offline-grace-boundary.md",
        "schema-freeze-migration-policy.md",
        "end-user-auth-api-contract-v1.md",
        "admin-mvp-api-contract-v1.md",
        "db-schema-draft.md",
    ]
    for filename in expected:
        assert (DOCS_ROOT / filename).exists(), f"missing contract freeze doc: {filename}"


def test_domain_boundaries_freeze_managed_and_admin_auth_separation() -> None:
    text = (DOCS_ROOT / "auth-domain-boundaries.md").read_text(encoding="utf-8")
    assert "Managed-user auth domain" in text
    assert "Admin-operator auth domain" in text
    assert "must not" in text.lower()
    assert "runtime-import business logic" in text


def test_token_session_model_freezes_session_types() -> None:
    text = (DOCS_ROOT / "token-session-model.md").read_text(encoding="utf-8")
    assert "Access token" in text
    assert "Refresh token" in text
    assert "End-user remote session" in text
    assert "Admin session" in text


def test_error_code_matrix_contains_phase0_required_codes() -> None:
    text = (DOCS_ROOT / "error-code-matrix.md").read_text(encoding="utf-8")
    for code in [
        "invalid_credentials",
        "token_expired",
        "revoked",
        "disabled",
        "device_mismatch",
        "minimum_version_required",
        "network_timeout",
    ]:
        assert code in text


def test_versioning_and_migration_policy_are_explicit() -> None:
    versioning = (DOCS_ROOT / "contract-versioning-policy.md").read_text(encoding="utf-8")
    migration_policy = (DOCS_ROOT / "schema-freeze-migration-policy.md").read_text(encoding="utf-8")
    assert "v1" in versioning
    assert "breaking change" in versioning.lower()
    assert "Phase 0 does not generate final business migrations" in migration_policy
    assert "Phase 1" in migration_policy


def test_openapi_v1_artifact_parses_and_contains_minimum_paths() -> None:
    data = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert data["openapi"] == "3.1.0"
    assert data["info"]["version"] == "v1"
    for path in [
        "/login",
        "/refresh",
        "/logout",
        "/me",
        "/admin/users",
        "/admin/users/{user_id}",
        "/admin/devices",
        "/admin/devices/{device_id}",
        "/admin/sessions",
        "/admin/sessions/{session_id}/revoke",
        "/admin/audit-logs",
    ]:
        assert path in data["paths"], f"missing path in OpenAPI artifact: {path}"


def test_openapi_freezes_auth_request_response_shapes_and_error_responses() -> None:
    data = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    schemas = data["components"]["schemas"]
    login_request = schemas["LoginRequest"]
    auth_success = schemas["AuthSuccessResponse"]
    error_response = schemas["ErrorResponse"]

    assert login_request["required"] == ["username", "password", "device_id", "client_version"]
    assert "access_token" in auth_success["properties"]
    assert "refresh_token" in auth_success["properties"]
    assert "license_status" in auth_success["properties"]
    assert "device_status" in auth_success["properties"]
    assert error_response["required"] == ["error_code", "message"]
    assert "401" in data["paths"]["/login"]["post"]["responses"]
    assert "403" in data["paths"]["/refresh"]["post"]["responses"]


def test_db_schema_draft_describes_table_responsibilities_and_relationships() -> None:
    text = (DOCS_ROOT / "db-schema-draft.md").read_text(encoding="utf-8")
    for table_name in [
        "users",
        "user_credentials",
        "licenses",
        "user_entitlements",
        "devices",
        "user_devices",
        "sessions",
        "refresh_tokens",
        "admin_users",
        "admin_roles",
        "audit_logs",
    ]:
        assert f"`{table_name}`" in text
    assert "Key responsibility" in text
    assert "Key relationships" in text
    assert "`sessions.user_id` references a managed user" in text
