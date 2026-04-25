from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.main import create_app


ERROR_RESPONSE_REF = '#/components/schemas/ErrorResponse'
VALIDATION_ERROR_REF = '#/components/schemas/HTTPValidationError'
ERROR_DESCRIPTIONS = {
    '401': 'Unauthorized',
    '403': 'Forbidden',
    '404': 'Not Found',
    '429': 'Too Many Requests',
}
LIST_SCHEMA_NAMES = [
    'AdminUserListResponse',
    'AdminDeviceListResponse',
    'AdminSessionListResponse',
    'AuditLogListResponse',
]


@dataclass(frozen=True)
class OpenApiRouteCase:
    name: str
    path: str
    method: str
    success_ref: str
    response_refs: dict[str, str]


ROUTE_CASES = [
    OpenApiRouteCase(
        name='login',
        path='/login',
        method='post',
        success_ref='#/components/schemas/AuthSuccessResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '429': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='refresh',
        path='/refresh',
        method='post',
        success_ref='#/components/schemas/AuthSuccessResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '429': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='logout',
        path='/logout',
        method='post',
        success_ref='#/components/schemas/LogoutResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='me',
        path='/me',
        method='get',
        success_ref='#/components/schemas/MeResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
        },
    ),
    OpenApiRouteCase(
        name='self_me',
        path='/self/me',
        method='get',
        success_ref='#/components/schemas/SelfMeResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
        },
    ),
    OpenApiRouteCase(
        name='self_devices',
        path='/self/devices',
        method='get',
        success_ref='#/components/schemas/SelfDeviceListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='self_sessions',
        path='/self/sessions',
        method='get',
        success_ref='#/components/schemas/SelfSessionListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='self_activity',
        path='/self/activity',
        method='get',
        success_ref='#/components/schemas/SelfActivityListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='self_revoke_session',
        path='/self/sessions/{session_id}/revoke',
        method='post',
        success_ref='#/components/schemas/SelfSessionRevokeResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_login',
        path='/admin/login',
        method='post',
        success_ref='#/components/schemas/AdminLoginResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '429': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_session',
        path='/admin/session',
        method='get',
        success_ref='#/components/schemas/AdminCurrentSessionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_list_users',
        path='/admin/users',
        method='get',
        success_ref='#/components/schemas/AdminUserListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_get_user',
        path='/admin/users/{user_id}',
        method='get',
        success_ref='#/components/schemas/AdminUserResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_update_user',
        path='/admin/users/{user_id}',
        method='patch',
        success_ref='#/components/schemas/AdminUserResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_revoke_user',
        path='/admin/users/{user_id}/revoke',
        method='post',
        success_ref='#/components/schemas/AdminActionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_restore_user',
        path='/admin/users/{user_id}/restore',
        method='post',
        success_ref='#/components/schemas/AdminActionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_list_devices',
        path='/admin/devices',
        method='get',
        success_ref='#/components/schemas/AdminDeviceListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_get_device',
        path='/admin/devices/{device_id}',
        method='get',
        success_ref='#/components/schemas/AdminDeviceResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_unbind_device',
        path='/admin/devices/{device_id}/unbind',
        method='post',
        success_ref='#/components/schemas/AdminActionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_disable_device',
        path='/admin/devices/{device_id}/disable',
        method='post',
        success_ref='#/components/schemas/AdminActionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_rebind_device',
        path='/admin/devices/{device_id}/rebind',
        method='post',
        success_ref='#/components/schemas/AdminActionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_list_sessions',
        path='/admin/sessions',
        method='get',
        success_ref='#/components/schemas/AdminSessionListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_revoke_session',
        path='/admin/sessions/{session_id}/revoke',
        method='post',
        success_ref='#/components/schemas/AdminActionResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '404': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_audit_logs',
        path='/admin/audit-logs',
        method='get',
        success_ref='#/components/schemas/AuditLogListResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
            '422': VALIDATION_ERROR_REF,
        },
    ),
    OpenApiRouteCase(
        name='admin_metrics_summary',
        path='/admin/metrics/summary',
        method='get',
        success_ref='#/components/schemas/AdminMetricsSummaryResponse',
        response_refs={
            '401': ERROR_RESPONSE_REF,
            '403': ERROR_RESPONSE_REF,
        },
    ),
]


@pytest.fixture(scope='module')
def openapi_schema() -> dict:
    return create_app().openapi()


@pytest.mark.parametrize('case', ROUTE_CASES, ids=[case.name for case in ROUTE_CASES])
def test_openapi_route_responses_match_documented_contract(case: OpenApiRouteCase, openapi_schema: dict) -> None:
    route_spec = openapi_schema['paths'][case.path][case.method]
    responses = route_spec['responses']

    assert set(responses.keys()) == {'200', *case.response_refs.keys()}
    assert responses['200']['content']['application/json']['schema']['$ref'] == case.success_ref

    for status_code, expected_ref in case.response_refs.items():
        response_spec = responses[status_code]
        assert response_spec['content']['application/json']['schema']['$ref'] == expected_ref
        if status_code == '422':
            assert response_spec['description'] == 'Validation Error'
        else:
            assert response_spec['description'] == ERROR_DESCRIPTIONS[status_code]


@pytest.mark.parametrize('schema_name', LIST_SCHEMA_NAMES)
def test_openapi_admin_list_schemas_include_page_metadata(schema_name: str, openapi_schema: dict) -> None:
    schema = openapi_schema['components']['schemas'][schema_name]
    properties = schema['properties']

    assert {'items', 'total', 'page', 'page_size'} <= set(properties.keys())
    assert properties['total']['type'] == 'integer'
    assert properties['page']['type'] == 'integer'
    assert properties['page_size']['type'] == 'integer'
    assert {'items', 'total', 'page', 'page_size'} <= set(schema['required'])
