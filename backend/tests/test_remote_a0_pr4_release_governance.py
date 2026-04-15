from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / 'remote' / 'remote-shared' / 'docs'
REMOTE_README = ROOT / 'remote' / 'README.md'
WORKFLOW = ROOT / '.github' / 'workflows' / 'remote-phase4-release-gate.yml'


def test_remote_a0_pr4_governance_docs_exist_and_are_cross_referenced() -> None:
    for path in [
        DOCS_ROOT / 'phase4-release-gate.md',
        DOCS_ROOT / 'staging-promotion-checklist.md',
        DOCS_ROOT / 'rollback-runbook.md',
        DOCS_ROOT / 'restore-recovery-runbook.md',
        DOCS_ROOT / 'release-governance-tabletop-record-v1.md',
        REMOTE_README,
        WORKFLOW,
    ]:
        assert path.exists(), str(path)

    phase4 = (DOCS_ROOT / 'phase4-release-gate.md').read_text(encoding='utf-8')
    promotion = (DOCS_ROOT / 'staging-promotion-checklist.md').read_text(encoding='utf-8')
    rollback = (DOCS_ROOT / 'rollback-runbook.md').read_text(encoding='utf-8')
    restore = (DOCS_ROOT / 'restore-recovery-runbook.md').read_text(encoding='utf-8')
    tabletop = (DOCS_ROOT / 'release-governance-tabletop-record-v1.md').read_text(encoding='utf-8')
    readme = REMOTE_README.read_text(encoding='utf-8')

    assert 'Required release evidence bundle' in phase4
    assert 'portal smoke placeholder for Program B' in phase4
    assert 'restore-recovery-runbook.md' in phase4
    assert 'candidate build / environment identifier' in phase4
    assert 'prod promotion baseline' in phase4.lower()

    assert 'candidate identifier / build reference' in promotion
    assert 'release evidence bundle is attached or linked' in promotion
    assert 'restore-recovery-runbook.md' in promotion
    assert 'deployment smoke' in promotion.lower()

    assert 'restore-recovery-runbook.md' in rollback
    assert 'Post-rollback validation checklist' in rollback
    assert 'last known-good build / commit / deployment identifier' in rollback

    assert 'Backup ownership baseline' in restore
    assert 'Restore verification expectations' in restore
    assert 'Post-rollback / post-restore validation checklist' in restore
    assert 'not release-ready' in restore

    assert 'Scenario 1 - Bad release rollback path' in tabletop
    assert 'Scenario 2 - Restore-needed recovery path' in tabletop
    assert 'Scenario 3 - Release evidence checklist completion' in tabletop
    assert 'portal smoke placeholder noted for Program B' in tabletop

    assert 'restore-recovery-runbook.md' in readme
    assert 'release-governance-tabletop-record-v1.md' in readme


def test_remote_a0_pr4_workflow_enforces_a0_governance_baseline() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))
    on_block = workflow.get('on', workflow.get(True))
    pr_paths = on_block['pull_request']['paths']
    regression_step = next(
        step
        for step in workflow['jobs']['remote-backend-phase4-gate']['steps']
        if step.get('name') == 'Run backend regression through phase4'
    )

    assert 'backend/tests/test_remote_a0_pr*.py' in pr_paths
    for test_name in [
        'test_remote_a0_pr1_operating_model.py',
        'test_remote_a0_pr2_env_discipline.py',
        'test_remote_a0_pr3_topology_health.py',
        'test_remote_a0_pr4_release_governance.py',
    ]:
        assert test_name in regression_step['run']
