from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
OPENAPI_SOURCE = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-v1.yaml'
OPENAPI_RUNTIME = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-runtime.json'
DOCS_ROOT = ROOT / 'remote' / 'remote-shared' / 'docs'


def _source() -> dict:
    return yaml.safe_load(OPENAPI_SOURCE.read_text(encoding='utf-8'))


def _runtime() -> dict:
    return json.loads(OPENAPI_RUNTIME.read_text(encoding='utf-8'))


def test_admin_list_query_parameters_are_source_runtime_aligned() -> None:
    source = _source()
    runtime = _runtime()

    checks = {
        ('/admin/users', 'get'): ['q', 'status', 'license_status', 'limit', 'offset'],
        ('/admin/devices', 'get'): ['q', 'device_status', 'user_id', 'limit', 'offset'],
        ('/admin/sessions', 'get'): ['q', 'auth_state', 'user_id', 'device_id', 'limit', 'offset'],
        ('/admin/audit-logs', 'get'): ['event_type', 'actor_id', 'target_user_id', 'target_device_id', 'target_session_id', 'created_from', 'created_to', 'limit', 'offset'],
    }

    for (path, method), expected in checks.items():
        source_names = [param['name'] for param in source['paths'][path][method]['parameters']]
        runtime_names = [param['name'] for param in runtime['paths'][path][method]['parameters']]
        assert source_names == expected
        assert runtime_names == expected


def test_validation_error_contract_is_explicit_for_validation_backed_routes() -> None:
    source = _source()
    runtime = _runtime()

    checks = [
        ('/login', 'post'),
        ('/refresh', 'post'),
        ('/logout', 'post'),
        ('/admin/login', 'post'),
        ('/admin/users', 'get'),
        ('/admin/devices', 'get'),
        ('/admin/sessions', 'get'),
        ('/admin/audit-logs', 'get'),
    ]

    for path, method in checks:
        source_ref = source['paths'][path][method]['responses']['422']['content']['application/json']['schema']['$ref']
        runtime_ref = runtime['paths'][path][method]['responses']['422']['content']['application/json']['schema']['$ref']
        assert source_ref == '#/components/schemas/HTTPValidationError'
        assert runtime_ref == source_ref


def test_additive_audit_and_metrics_fields_are_documented_in_openapi() -> None:
    source = _source()
    runtime = _runtime()

    source_audit_props = source['components']['schemas']['AuditLogResponse']['properties']
    runtime_audit_props = runtime['components']['schemas']['AuditLogResponse']['properties']
    for key in ['request_id', 'trace_id']:
        assert key in source_audit_props
        assert key in runtime_audit_props

    source_metrics = source['components']['schemas']['AdminMetricsSummaryResponse']
    runtime_metrics = runtime['components']['schemas']['AdminMetricsSummaryResponse']
    for key in ['generated_at', 'recent_failures', 'recent_destructive_actions']:
        assert key in source_metrics['properties']
        assert key in runtime_metrics['properties']
    assert 'generated_at' in source_metrics['required']
    assert 'generated_at' in runtime_metrics['required']


def test_contract_docs_capture_validation_and_additive_v1_rules() -> None:
    error_matrix = (DOCS_ROOT / 'error-code-matrix.md').read_text(encoding='utf-8')
    versioning = (DOCS_ROOT / 'contract-versioning-policy.md').read_text(encoding='utf-8')
    gate_doc = (DOCS_ROOT / 'compatibility-gate.md').read_text(encoding='utf-8')
    admin_contract = (DOCS_ROOT / 'admin-mvp-api-contract-v1.md').read_text(encoding='utf-8')

    assert '422' in error_matrix
    assert 'required_permission' in error_matrix
    assert 'optional query parameters' in versioning
    assert 'Phase 4 contract-hardening rule' in gate_doc
    assert 'GET /admin/users' in admin_contract
    assert 'target_session_id' in admin_contract
