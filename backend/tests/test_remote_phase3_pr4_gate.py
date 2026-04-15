from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REMOTE_BACKEND_ROOT = ROOT / 'remote' / 'remote-backend'
if str(REMOTE_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(REMOTE_BACKEND_ROOT))

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.repositories.admin import AdminRepository
from app.services.admin_service import AdminService
from app.migrations.runner import upgrade
from app.models import AdminUser


PHASE3_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'phase3-release-gate.md'
BOOTSTRAP_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'admin-bootstrap-runbook.md'
STAGING_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'staging-deploy-checklist.md'
SUPPORT_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'support-runbook.md'
REMOTE_README = ROOT / 'remote' / 'README.md'
REMOTE_ENV = ROOT / 'remote' / '.env.example'
BACKEND_README = ROOT / 'remote' / 'remote-backend' / 'README.md'
ADMIN_README = ROOT / 'remote' / 'remote-admin' / 'README.md'
WORKFLOW_PATH = ROOT / '.github' / 'workflows' / 'remote-phase3-release-gate.yml'
BOOTSTRAP_SCRIPT = ROOT / 'remote' / 'remote-backend' / 'scripts' / 'bootstrap_admin.py'


def run_bootstrap(db_path: Path, *, username: str, password: str, display_name: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env['REMOTE_BACKEND_DATABASE_URL'] = f"sqlite:///{db_path.as_posix()}"
    env['BOOTSTRAP_ADMIN_PASSWORD'] = password
    return subprocess.run(
        [
            sys.executable,
            str(BOOTSTRAP_SCRIPT),
            '--migrate',
            '--username',
            username,
            '--password-env',
            'BOOTSTRAP_ADMIN_PASSWORD',
            '--role',
            'super_admin',
            '--display-name',
            display_name,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_phase3_release_docs_and_workflow_exist() -> None:
    for path in [PHASE3_DOC, BOOTSTRAP_DOC, STAGING_DOC, SUPPORT_DOC, REMOTE_README, REMOTE_ENV, BACKEND_README, ADMIN_README, BOOTSTRAP_SCRIPT]:
        assert path.exists(), str(path)

    phase3_text = PHASE3_DOC.read_text(encoding='utf-8')
    assert 'Bootstrap an admin account' in phase3_text
    assert 'staging-deploy-checklist.md' in phase3_text
    assert 'support-runbook.md' in phase3_text
    assert 'Workflow green alone is insufficient' in phase3_text

    bootstrap_text = BOOTSTRAP_DOC.read_text(encoding='utf-8')
    assert 'bootstrap_admin.py' in bootstrap_text
    assert 'created' in bootstrap_text
    assert 'updated' in bootstrap_text
    assert '--password-env' in bootstrap_text

    staging_text = STAGING_DOC.read_text(encoding='utf-8')
    assert 'REMOTE_BACKEND_DATABASE_URL' in staging_text
    assert 'validate_phase1_gate.py' in staging_text
    assert 'override all development/bootstrap defaults' in staging_text

    support_text = SUPPORT_DOC.read_text(encoding='utf-8')
    assert 'device_mismatch' in support_text
    assert 'support_readonly' in support_text

    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding='utf-8'))
    assert workflow['name'] == 'remote-phase3-release-gate'
    assert 'remote-backend-phase3-gate' in workflow['jobs']
    assert 'remote-admin-phase3-gate' in workflow['jobs']
    bootstrap_step = next(step for step in workflow['jobs']['remote-backend-phase3-gate']['steps'] if step.get('name') == 'Bootstrap admin smoke')
    assert 'bootstrap_admin.py' in bootstrap_step['run']
    assert bootstrap_step['env']['BOOTSTRAP_ADMIN_PASSWORD'] == 'ci-secret'


def test_bootstrap_admin_script_creates_and_updates_admin_user(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / 'remote_pr34.sqlite3'

    created = run_bootstrap(db_path, username='staging-admin', password='first-secret', display_name='Staging Admin')
    assert created.returncode == 0, created.stderr
    created_payload = json.loads(created.stdout)
    assert created_payload['result'] == 'created'

    monkeypatch.setenv('REMOTE_BACKEND_DATABASE_URL', f"sqlite:///{db_path.as_posix()}")
    reset_settings_cache()
    reset_db_state()
    with session_scope() as session:
        admin_user = session.query(AdminUser).filter_by(username='staging-admin').one()
        assert admin_user.display_name == 'Staging Admin'
        assert admin_user.role == 'super_admin'

    updated = run_bootstrap(db_path, username='staging-admin', password='second-secret', display_name='Rotated Admin')
    assert updated.returncode == 0, updated.stderr
    updated_payload = json.loads(updated.stdout)
    assert updated_payload['result'] == 'updated'

    reset_settings_cache()
    reset_db_state()
    with session_scope() as session:
        admin_user = session.query(AdminUser).filter_by(username='staging-admin').one()
        assert admin_user.display_name == 'Rotated Admin'


def test_staging_env_does_not_auto_seed_admins(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / 'remote_pr34_staging.sqlite3'
    monkeypatch.setenv('REMOTE_BACKEND_DATABASE_URL', f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv('REMOTE_BACKEND_APP_ENV', 'staging')
    reset_settings_cache()
    reset_db_state()
    upgrade()
    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        service.ensure_seed_admin()
        assert session.query(AdminUser).count() == 0
