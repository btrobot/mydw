from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REMOTE_README = ROOT / 'remote' / 'README.md'
ENV_TEMPLATE = ROOT / 'remote' / '.env.example'
ENV_MATRIX_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'remote-full-system-env-config-matrix-v1.md'
STAGING_DRY_RUN_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'staging-env-dry-run-artifact-v1.md'


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


def test_remote_env_matrix_docs_exist_and_are_referenced() -> None:
    assert ENV_MATRIX_DOC.exists()
    assert STAGING_DRY_RUN_DOC.exists()

    matrix = ENV_MATRIX_DOC.read_text(encoding='utf-8')
    dry_run = STAGING_DRY_RUN_DOC.read_text(encoding='utf-8')
    readme = REMOTE_README.read_text(encoding='utf-8')

    assert 'remote-backend' in matrix
    assert 'remote-admin' in matrix
    assert 'remote-portal' in matrix
    assert 'Required secrets' in matrix
    assert 'Required non-secret runtime config' in matrix
    assert 'Optional dev-only config' in matrix
    assert '## 2. Backend' in matrix
    assert '## 3. Admin frontend' in matrix
    assert '## 4. Planned portal frontend' in matrix
    assert '## 5. Compatibility / release smoke' in matrix
    assert 'A0 / B0 boundary note' in matrix
    assert 'does **not** freeze' in matrix

    assert 'staging env dry-run artifact' in dry_run.lower()
    assert 'REMOTE_BACKEND_APP_ENV=staging' in dry_run
    assert 'bootstrap password overridden from dev placeholder' in dry_run.lower()
    assert 'At least one such dry-run artifact must exist' in dry_run

    assert 'remote-full-system-env-config-matrix-v1.md' in readme
    assert 'staging-env-dry-run-artifact-v1.md' in readme


def test_remote_env_template_exposes_a0_2_canonical_keys_and_placeholder_discipline() -> None:
    template_text = ENV_TEMPLATE.read_text(encoding='utf-8')
    env = _parse_env_template(template_text)

    for key in [
        'REMOTE_ENV',
        'REMOTE_STAGING_PUBLIC_BASE_URL',
        'REMOTE_STAGING_ADMIN_BASE_URL',
        'REMOTE_STAGING_PORTAL_BASE_URL',
        'REMOTE_BACKEND_APP_ENV',
        'REMOTE_BACKEND_HOST',
        'REMOTE_BACKEND_PORT',
        'REMOTE_BACKEND_DATABASE_URL',
        'REMOTE_BACKEND_CORS_ALLOW_ORIGINS',
        'REMOTE_BACKEND_ADMIN_BOOTSTRAP_USERNAME',
        'REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD',
        'REMOTE_ADMIN_PORT',
        'REMOTE_ADMIN_API_BASE_URL',
        'REMOTE_PORTAL_PORT',
        'REMOTE_PORTAL_API_BASE_URL',
        'REMOTE_PORTAL_PUBLIC_BASE_URL',
        'REMOTE_COMPAT_BASE_URL',
        'REMOTE_COMPAT_USERNAME',
        'REMOTE_COMPAT_PASSWORD',
        'REMOTE_COMPAT_DEVICE_ID',
        'REMOTE_COMPAT_ADMIN_USERNAME',
        'REMOTE_COMPAT_ADMIN_PASSWORD',
    ]:
        assert key in env

    assert env['REMOTE_PORTAL_PORT'] == '4174'
    assert env['REMOTE_PORTAL_API_BASE_URL'] == 'http://127.0.0.1:8100'
    assert env['REMOTE_PORTAL_PUBLIC_BASE_URL'] == 'http://127.0.0.1:4174'

    assert 'Override these in staging/prod' in template_text
    assert 'do not keep' in template_text
    assert 'dev-style bootstrap secrets outside local environments' in template_text
