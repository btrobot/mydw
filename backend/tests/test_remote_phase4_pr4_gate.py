from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / 'remote' / 'remote-shared' / 'docs'
WORKFLOW = ROOT / '.github' / 'workflows' / 'remote-phase4-release-gate.yml'
REMOTE_README = ROOT / 'remote' / 'README.md'


def test_phase4_release_docs_and_workflow_exist() -> None:
    for path in [
        DOCS_ROOT / 'phase4-release-gate.md',
        DOCS_ROOT / 'staging-promotion-checklist.md',
        DOCS_ROOT / 'rollback-runbook.md',
        DOCS_ROOT / 'staging-deploy-checklist.md',
        DOCS_ROOT / 'support-runbook.md',
        WORKFLOW,
    ]:
        assert path.exists(), str(path)

    phase4 = (DOCS_ROOT / 'phase4-release-gate.md').read_text(encoding='utf-8')
    assert 'Required release evidence' in phase4
    assert 'Automation is necessary but not sufficient' in phase4
    assert 'rollback-runbook.md' in phase4

    promotion = (DOCS_ROOT / 'staging-promotion-checklist.md').read_text(encoding='utf-8')
    assert 'Environment confirmation' in promotion
    assert 'Sign-off' in promotion
    assert 'Do not promote' in promotion

    rollback = (DOCS_ROOT / 'rollback-runbook.md').read_text(encoding='utf-8')
    assert 'Trigger conditions' in rollback
    assert 'Record the rollback' in rollback

    workflow = yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))
    assert workflow['name'] == 'remote-phase4-release-gate'
    assert 'remote-backend-phase4-gate' in workflow['jobs']
    assert 'remote-admin-phase4-gate' in workflow['jobs']


def test_phase4_workflow_and_readme_reference_phase4_gate_assets() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))
    backend_steps = workflow['jobs']['remote-backend-phase4-gate']['steps']

    compat_step = next(step for step in backend_steps if step.get('name') == 'Run compatibility/export gate')
    assert 'build_phase0_manifest.py' in compat_step['run']
    assert 'validate_phase0_gate.py' in compat_step['run']
    assert 'validate_phase1_gate.py' in compat_step['run']

    regression_step = next(step for step in backend_steps if step.get('name') == 'Run backend regression through phase4')
    assert 'test_remote_phase4_pr1_contract_hardening.py' in regression_step['run']
    assert 'test_remote_phase4_pr2_runtime_reliability.py' in regression_step['run']
    assert 'test_remote_phase4_pr4_gate.py' in regression_step['run']

    readme = REMOTE_README.read_text(encoding='utf-8')
    assert 'phase3-release-gate.md' in readme or 'phase4-release-gate.md' in readme
