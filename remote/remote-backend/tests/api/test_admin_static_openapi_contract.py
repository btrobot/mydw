from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
SOURCE_SPEC_PATH = ROOT / 'remote-shared' / 'openapi' / 'remote-auth-v1.yaml'
RUNTIME_SPEC_PATH = ROOT / 'remote-shared' / 'openapi' / 'remote-auth-runtime.json'


def load_source_spec() -> dict:
    return yaml.safe_load(SOURCE_SPEC_PATH.read_text(encoding='utf-8'))


def load_runtime_spec() -> dict:
    return json.loads(RUNTIME_SPEC_PATH.read_text(encoding='utf-8'))


def test_static_openapi_includes_admin_create_user_route() -> None:
    source_spec = load_source_spec()
    runtime_spec = load_runtime_spec()

    for spec in (source_spec, runtime_spec):
        assert '/admin/users' in spec['paths']
        assert 'post' in spec['paths']['/admin/users']

    source_post = source_spec['paths']['/admin/users']['post']
    runtime_post = runtime_spec['paths']['/admin/users']['post']

    assert source_post['requestBody']['content']['application/json']['schema']['$ref'] == '#/components/schemas/AdminUserCreateRequest'
    assert runtime_post['requestBody']['content']['application/json']['schema']['$ref'] == '#/components/schemas/AdminUserCreateRequest'
    assert source_post['responses']['200']['content']['application/json']['schema']['$ref'] == '#/components/schemas/AdminUserResponse'
    assert runtime_post['responses']['200']['content']['application/json']['schema']['$ref'] == '#/components/schemas/AdminUserResponse'


def test_static_openapi_includes_admin_user_create_schema() -> None:
    source_spec = load_source_spec()
    runtime_spec = load_runtime_spec()

    source_schema = source_spec['components']['schemas']['AdminUserCreateRequest']
    runtime_schema = runtime_spec['components']['schemas']['AdminUserCreateRequest']

    assert sorted(source_schema['required']) == ['password', 'username']
    assert sorted(runtime_schema['required']) == ['password', 'username']
    assert sorted(source_schema['properties'].keys()) == [
        'display_name',
        'email',
        'entitlements',
        'license_expires_at',
        'license_status',
        'password',
        'tenant_id',
        'username',
    ]
    assert sorted(runtime_schema['properties'].keys()) == sorted(source_schema['properties'].keys())


def test_static_openapi_keeps_paginated_list_contract_in_sync() -> None:
    source_spec = load_source_spec()
    runtime_spec = load_runtime_spec()

    schema_names = [
        'SelfDeviceListResponse',
        'SelfSessionListResponse',
        'SelfActivityListResponse',
        'AdminUserListResponse',
        'AdminDeviceListResponse',
        'AdminSessionListResponse',
        'AuditLogListResponse',
    ]
    expected_required = ['items', 'page', 'page_size', 'total']
    expected_properties = ['items', 'page', 'page_size', 'total']

    for name in schema_names:
        source_schema = source_spec['components']['schemas'][name]
        runtime_schema = runtime_spec['components']['schemas'][name]

        assert sorted(source_schema['required']) == expected_required
        assert sorted(runtime_schema['required']) == expected_required
        assert sorted(source_schema['properties'].keys()) == expected_properties
        assert sorted(runtime_schema['properties'].keys()) == expected_properties
