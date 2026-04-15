from __future__ import annotations

from pathlib import Path

import json
import yaml


ROOT = Path(__file__).resolve().parents[2]
PHASE2_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'phase2-release-gate.md'
PHASE2_WORKFLOW = ROOT / '.github' / 'workflows' / 'remote-phase2-release-gate.yml'
OPENAPI_SOURCE = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-v1.yaml'
OPENAPI_RUNTIME = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-runtime.json'


def test_phase2_release_gate_assets_exist() -> None:
    assert PHASE2_DOC.exists()
    text = PHASE2_DOC.read_text(encoding='utf-8')
    assert 'supportability gate' in text
    assert '/admin/audit-logs' in text
    assert '/admin/metrics/summary' in text

    workflow = yaml.safe_load(PHASE2_WORKFLOW.read_text(encoding='utf-8'))
    assert workflow['name'] == 'remote-phase2-release-gate'
    assert 'remote-backend-phase2-gate' in workflow['jobs']
    assert 'remote-admin-phase2-gate' in workflow['jobs']


def test_phase2_audit_logs_422_contract_alignment() -> None:
    source = yaml.safe_load(OPENAPI_SOURCE.read_text(encoding='utf-8'))
    runtime = json.loads(OPENAPI_RUNTIME.read_text(encoding='utf-8'))
    source_ref = source['paths']['/admin/audit-logs']['get']['responses']['422']['content']['application/json']['schema']['$ref']
    runtime_ref = runtime['paths']['/admin/audit-logs']['get']['responses']['422']['content']['application/json']['schema']['$ref']
    assert source_ref == '#/components/schemas/HTTPValidationError'
    assert runtime_ref == source_ref
