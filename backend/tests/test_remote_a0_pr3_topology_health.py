from __future__ import annotations

import sys
from pathlib import Path

import yaml
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
REMOTE_README = ROOT / 'remote' / 'README.md'
OPERATING_MODEL_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'remote-full-system-operating-model-v1.md'
TOPOLOGY_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'remote-full-system-deployment-topology-v1.md'
DEPLOY_COMPOSE = ROOT / 'remote' / 'remote-shared' / 'deploy' / 'docker-compose.a0-baseline.yml'
DEPLOY_PROXY = ROOT / 'remote' / 'remote-shared' / 'deploy' / 'nginx.remote-full-system-a0.conf'
REMOTE_BACKEND_ROOT = ROOT / 'remote' / 'remote-backend'
if str(REMOTE_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(REMOTE_BACKEND_ROOT))

from app.main import create_app


def test_remote_a0_pr3_topology_doc_and_templates_exist() -> None:
    for path in [TOPOLOGY_DOC, DEPLOY_COMPOSE, DEPLOY_PROXY]:
        assert path.exists(), str(path)

    topology = TOPOLOGY_DOC.read_text(encoding='utf-8')
    readme = REMOTE_README.read_text(encoding='utf-8')
    operating = OPERATING_MODEL_DOC.read_text(encoding='utf-8')
    proxy = DEPLOY_PROXY.read_text(encoding='utf-8')

    for marker in [
        'remote-backend',
        'remote-admin',
        'remote-portal',
        'Reverse proxy / TLS termination layer',
        'Authoritative backing database',
        'Runtime Health Contract',
        'Liveness / health',
        'Readiness',
        'Startup ordering expectations',
        'Healthy vs ready',
        'operator-gated condition',
        'GET /health',
        'why is `/health` insufficient as a readiness or release signal?',
    ]:
        assert marker in topology

    assert 'remote-full-system-deployment-topology-v1.md' in readme
    assert 'remote-full-system-deployment-topology-v1.md' in operating
    assert 'location = /health' in proxy
    assert 'location /api/' in proxy
    assert 'location /admin/' in proxy
    assert 'B0-owned' in proxy


def test_remote_a0_pr3_compose_template_parses_and_captures_service_shape() -> None:
    compose = yaml.safe_load(DEPLOY_COMPOSE.read_text(encoding='utf-8'))
    services = compose['services']

    assert compose['version'] == '3.9'
    for service in ['reverse-proxy', 'remote-backend', 'remote-admin', 'remote-portal']:
        assert service in services

    reverse_proxy = services['reverse-proxy']
    assert 'remote-backend' in reverse_proxy['depends_on']
    assert 'remote-admin' in reverse_proxy['depends_on']

    backend = services['remote-backend']
    assert '../../../.env' in backend['env_file']
    assert backend['environment']['REMOTE_BACKEND_HOST'] == '0.0.0.0'
    assert '8100' in backend['expose']

    portal = services['remote-portal']
    assert portal['profiles'] == ['portal']


def test_remote_backend_health_probe_matches_a0_pr3_baseline() -> None:
    client = TestClient(create_app())
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
