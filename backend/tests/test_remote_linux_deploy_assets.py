from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REMOTE_ROOT = ROOT / 'remote'
DEPLOY_ROOT = REMOTE_ROOT / 'remote-shared' / 'deploy'
README = REMOTE_ROOT / 'README.md'
LINUX_RUNBOOK = REMOTE_ROOT / 'remote-shared' / 'docs' / 'linux-deployment-runbook.md'
LINUX_ENV = REMOTE_ROOT / '.env.linux.example'


def _parse_env_template(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, value = line.partition('=')
        assert key and _, f'invalid env template line: {raw_line!r}'
        parsed[key] = value
    return parsed


def test_remote_linux_env_template_and_scripts_exist() -> None:
    assert LINUX_ENV.exists()
    env = _parse_env_template(LINUX_ENV.read_text(encoding='utf-8'))

    for key in [
        'REMOTE_DEPLOY_BRANCH',
        'REMOTE_DEPLOY_TLS_MODE',
        'REMOTE_DEPLOY_SERVER_NAME',
        'REMOTE_DEPLOY_HTTP_PORT',
        'REMOTE_DEPLOY_HTTPS_PORT',
        'REMOTE_NGINX_RUNTIME_IMAGE',
        'REMOTE_PYTHON_BASE_IMAGE',
        'REMOTE_NODE_BASE_IMAGE',
        'REMOTE_NGINX_BASE_IMAGE',
        'REMOTE_PIP_INDEX_URL',
        'REMOTE_NPM_REGISTRY',
        'REMOTE_ADMIN_API_BASE_URL',
        'REMOTE_BACKEND_DATABASE_URL',
    ]:
        assert key in env

    assert env['REMOTE_DEPLOY_TLS_MODE'] == 'http'
    assert env['REMOTE_NGINX_RUNTIME_IMAGE'] == 'mirror.ccs.tencentyun.com/library/nginx:1.27-alpine'
    assert env['REMOTE_PYTHON_BASE_IMAGE'] == 'mirror.ccs.tencentyun.com/library/python:3.12-slim'
    assert env['REMOTE_NODE_BASE_IMAGE'] == 'mirror.ccs.tencentyun.com/library/node:20-alpine'
    assert env['REMOTE_NGINX_BASE_IMAGE'] == 'mirror.ccs.tencentyun.com/library/nginx:1.27-alpine'
    assert env['REMOTE_PIP_INDEX_URL'] == 'https://mirrors.cloud.tencent.com/pypi/simple'
    assert env['REMOTE_NPM_REGISTRY'] == 'https://registry.npmmirror.com'
    assert env['REMOTE_ADMIN_API_BASE_URL'] == '/api'
    assert env['REMOTE_BACKEND_DATABASE_URL'] == 'sqlite:////data/remote_auth.db'

    for rel in [
        'common.sh',
        'deploy.sh',
        'upgrade.sh',
        'rollback.sh',
        'nginx.remote-full-system-https.conf.template',
        'certs/README.md',
    ]:
        assert (DEPLOY_ROOT / rel).exists(), rel


def test_remote_linux_compose_and_https_template_capture_expected_shape() -> None:
    compose = yaml.safe_load((DEPLOY_ROOT / 'docker-compose.linux.yml').read_text(encoding='utf-8'))
    reverse_proxy = compose['services']['reverse-proxy']
    backend = compose['services']['remote-backend']
    admin = compose['services']['remote-admin']

    assert './nginx.remote-full-system.generated.conf:/etc/nginx/conf.d/default.conf:ro' in reverse_proxy['volumes']
    assert './certs:/etc/nginx/certs:ro' in reverse_proxy['volumes']
    assert reverse_proxy['image'] == '${REMOTE_NGINX_RUNTIME_IMAGE:-nginx:1.27-alpine}'
    assert '${REMOTE_DEPLOY_HTTP_PORT:-80}:80' in reverse_proxy['ports']
    assert '${REMOTE_DEPLOY_HTTPS_PORT:-443}:443' in reverse_proxy['ports']
    assert backend['env_file'][0]['path'] == '../../../remote/.env.linux.example'
    assert backend['env_file'][0]['required'] is True
    assert backend['env_file'][1]['path'] == '../../../.env'
    assert backend['env_file'][1]['required'] is False
    assert backend['build']['args']['REMOTE_PYTHON_BASE_IMAGE'] == '${REMOTE_PYTHON_BASE_IMAGE:-python:3.12-slim}'
    assert backend['build']['args']['REMOTE_PIP_INDEX_URL'] == '${REMOTE_PIP_INDEX_URL:-https://pypi.org/simple}'
    assert backend['build']['args']['REMOTE_PIP_TRUSTED_HOST'] == '${REMOTE_PIP_TRUSTED_HOST:-}'
    assert admin['build']['args']['REMOTE_NODE_BASE_IMAGE'] == '${REMOTE_NODE_BASE_IMAGE:-node:20-alpine}'
    assert admin['build']['args']['REMOTE_NGINX_BASE_IMAGE'] == '${REMOTE_NGINX_BASE_IMAGE:-nginx:1.27-alpine}'
    assert admin['build']['args']['REMOTE_NPM_REGISTRY'] == '${REMOTE_NPM_REGISTRY:-https://registry.npmjs.org}'

    https_template = (DEPLOY_ROOT / 'nginx.remote-full-system-https.conf.template').read_text(encoding='utf-8')
    assert '__REMOTE_SERVER_NAME__' in https_template
    assert 'ssl_certificate /etc/nginx/certs/fullchain.pem;' in https_template
    assert 'ssl_certificate_key /etc/nginx/certs/privkey.pem;' in https_template
    assert 'return 301 https://$host$request_uri;' in https_template


def test_remote_linux_docs_reference_env_scripts_and_https_assets() -> None:
    readme = README.read_text(encoding='utf-8')
    runbook = LINUX_RUNBOOK.read_text(encoding='utf-8')
    service = (DEPLOY_ROOT / 'remote-compose.service').read_text(encoding='utf-8')

    for marker in [
        '.env.linux.example',
        'deploy.sh',
        'upgrade.sh',
        'rollback.sh',
        'nginx.remote-full-system-https.conf.template',
        'mirror.ccs.tencentyun.com/library/nginx:1.27-alpine',
        'mirrors.cloud.tencent.com/pypi/simple',
        'registry.npmmirror.com',
    ]:
        assert marker in readme
        assert marker in runbook

    assert 'REMOTE_DEPLOY_TLS_MODE=https' in runbook
    assert 'certs/fullchain.pem' in runbook
    assert 'certs/privkey.pem' in runbook
    assert 'ExecStart=/opt/mydw/remote/remote-shared/deploy/deploy.sh' in service
    assert 'ExecReload=/opt/mydw/remote/remote-shared/deploy/upgrade.sh' in service
