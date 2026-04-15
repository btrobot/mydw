from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REMOTE_README = ROOT / 'remote' / 'README.md'
OPERATING_MODEL_DOC = ROOT / 'remote' / 'remote-shared' / 'docs' / 'remote-full-system-operating-model-v1.md'
FULL_SYSTEM_PRD = ROOT / '.omx' / 'plans' / 'prd-remote-full-system.md'


def test_remote_full_system_operating_model_doc_exists_and_is_referenced() -> None:
    assert OPERATING_MODEL_DOC.exists()
    text = OPERATING_MODEL_DOC.read_text(encoding='utf-8')
    readme = REMOTE_README.read_text(encoding='utf-8')

    assert 'single-tenant productionized remote platform' in text
    assert '`remote-backend`' in text
    assert '`remote-admin`' in text
    assert '`remote-portal`' in text
    assert 'dev' in text
    assert 'staging' in text
    assert 'prod' in text
    assert 'public' in text.lower()
    assert 'internal' in text.lower()
    assert 'multi-tenant runtime behavior' in text
    assert 'SSO providers' in text
    assert 'MFA flows' in text
    assert 'A0 owns' in text
    assert 'B0 owns' in text
    assert 'reviewer should be able to answer' in text.lower()

    assert 'remote-full-system-operating-model-v1.md' in readme


def test_full_system_prd_and_operating_model_are_consistent_on_scope() -> None:
    prd = FULL_SYSTEM_PRD.read_text(encoding='utf-8')
    operating = OPERATING_MODEL_DOC.read_text(encoding='utf-8')

    assert 'single-tenant' in prd.lower()
    assert 'Platform Expansion' in prd
    assert 'Out of Scope' in prd

    for marker in [
        'remote-backend',
        'remote-admin',
        'remote-portal',
        'single-tenant',
    ]:
        assert marker in operating
