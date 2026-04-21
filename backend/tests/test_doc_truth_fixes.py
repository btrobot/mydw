"""
Code-review remediation PR-A: documentation truth-fix checks.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_openapi_workflow_describes_tracked_generated_snapshot_correctly() -> None:
    workflow = _read("docs/guides/openapi-generation-workflow.md")

    assert "frontend/openapi.local.json" in workflow
    assert "tracked generated artifact" in workflow
    assert "docs/governance/generated-artifact-policy.md" in workflow
    assert "npm run generated:check" in workflow


def test_readme_uses_actual_packaged_output_directory() -> None:
    readme = _read("README.md")

    assert "dist-electron" in readme
    assert "docs/governance/verification-baseline.md" in readme
    assert "docs/current/next-phase-kickoff.md" in readme
    assert "frontend/release/" not in readme


def test_documentation_strategy_matches_epic7_authority_model() -> None:
    strategy = _read("docs/governance/documentation-strategy.md")

    assert "docs/current/architecture.md" in strategy
    assert "docs/current/runtime-truth.md" in strategy
    assert "system-architecture.md" in strategy
    assert "唯一来源" not in strategy or "system-architecture.md 是架构的唯一来源" not in strategy


def test_doc_checklist_recognizes_current_vs_archival_docs() -> None:
    checklist = _read("docs/governance/doc-checklist.md")

    assert "docs/current/architecture.md" in checklist
    assert "docs/current/runtime-truth.md" in checklist
    assert "stale" in checklist or "archival" in checklist or "过时" in checklist
    assert "system-architecture.md" in checklist


def test_post_mvp_model_and_phase_transition_checklist_are_indexed_and_connected() -> None:
    docs_index = _read("docs/README.md")
    model = _read("docs/governance/post-mvp-development-model.md")
    checklist = _read("docs/governance/phase-transition-checklist.md")

    assert "docs/governance/post-mvp-development-model.md" in docs_index
    assert "docs/governance/phase-transition-checklist.md" in docs_index

    assert "Part A：当前阶段收口检查" in checklist
    assert "Part B：下一阶段启动检查" in checklist
    assert "docs/governance/post-mvp-development-model.md" in checklist
    assert "next-phase PRD" in checklist
    assert "下一阶段有且只有一条主线" in checklist
    assert "MVP 后" in model


def test_task_domain_doc_matches_local_ffmpeg_v1_truth() -> None:
    doc = _read("docs/domains/tasks/task-management-domain-model.md")

    assert "local_ffmpeg V1" in doc
    assert "不走 `CompositionPoller`" in doc
    assert "1 个视频输入" in doc
    assert "0/1 个音频输入" in doc
    assert "multi-video montage" in doc
    assert "本地同步执行" in doc


def test_task_semantics_doc_no_longer_claims_broad_local_ffmpeg_inputs() -> None:
    doc = _read("docs/domains/tasks/task-semantics.md")

    assert "local_ffmpeg V1" in doc
    assert "broader composition inputs surface" in doc
    assert "submit_composition()" in doc
    assert "final_video_path" in doc
    assert "CompositionPoller" in doc
    assert "broader composition inputs 仍然允许" not in doc


def test_local_ffmpeg_closeout_doc_lists_support_limits_and_regression_commands() -> None:
    doc = _read("docs/domains/publishing/local-ffmpeg-composition.md")

    assert "PR-4 docs + regression closeout" in doc
    assert "1 个视频输入" in doc
    assert "0/1 个音频输入" in doc
    assert "multi-video montage" in doc
    assert "pytest tests/test_local_ffmpeg_composition.py" in doc
    assert "npm run typecheck" in doc


def test_project_introduction_uses_canonical_dev_baseline_and_electron_ts_entry() -> None:
    intro = _read("docs/specs/project-introduction.md")

    assert "frontend/electron/main.ts" in intro
    assert "frontend/electron/main.js" not in intro
    assert "Node 22+" in intro
    assert "Python 3.11+" in intro
    assert "FFmpeg 6+" in intro
    assert "docs/guides/startup-protocol.md" in intro


def test_verification_baseline_doc_defines_daily_and_release_layers() -> None:
    baseline = _read("docs/governance/verification-baseline.md")

    assert "最小可信回归基线" in baseline
    assert "日常开发必跑" in baseline
    assert "阶段发布必跑" in baseline
    assert "auth-routing.spec.ts" in baseline
    assert "creative-main-entry.spec.ts" in baseline
    assert "publish-pool.spec.ts" in baseline
    assert "test_auth_router_gates_pr3.py" in baseline
    assert "test_creative_workflow_contract.py" in baseline
    assert "test_local_ffmpeg_contract.py" in baseline
    assert "test_openapi_contract_parity.py" in baseline
    assert "test_remote_phase4_pr4_gate.py" in baseline
    assert "phase4-release-gate.md" in baseline


def test_dev_guide_links_to_verification_baseline() -> None:
    guide = _read("docs/guides/dev-guide.md")

    assert "docs/governance/verification-baseline.md" in guide
    assert "当前最小验证基线" in guide


def test_root_doc_triage_classifies_uncategorized_docs() -> None:
    triage = _read("docs/governance/root-doc-triage.md")

    assert "根层文档分诊表" in triage
    assert "docs/backup-scope.md" in triage
    assert "docs/chat-req.md" in triage
    assert "docs/init-req.md" in triage
    assert "docs/manual-axios-exceptions.md" in triage
    assert "docs/schema-parity-checklist.md" in triage
    assert "删除候选" in triage
    assert "docs/frontend-ui-ux-closeout-ralplan-command.md" in triage


def test_omx_plan_retention_distinguishes_active_archive_and_pending_plan_sets() -> None:
    retention = _read("docs/governance/omx-plan-retention.md")

    assert ".omx/plans" in retention
    assert ".omx/plans/archive/" in retention
    assert "Keep active in `.omx/plans/`" in retention
    assert "Archive now to `.omx/plans/archive/`" in retention
    assert "Keep in `.omx/plans/` pending manual review" in retention
    assert "prd-remote-full-system.md" in retention
    assert "prd-remote-auth.md" in retention
    assert "prd-creative-progressive-rebuild-roadmap.md" in retention
    assert "prd-frontend-ui-ux-closeout-phase-e-pr-plan.md" in retention
    assert "prd-local-ffmpeg-composition-pr-plan.md" in retention
    assert "prd-login-ux-closeout-pr-plan.md" in retention
    assert "prd-release-hardening-runtime-acceptance-closeout.md" in retention
    assert "prd-remote-system-mvp.md" in retention
    assert "remote-admin-platform-ui-pr-sequence-2026-04-16.md" in retention
    assert "prd-product-create-name-share-text.md" in retention
    assert "test-spec-product-create-name-share-text.md" in retention
    assert "product-create-dual-field-ralplan-2026-04-16.md" in retention
    assert "ralplan-login-bs-alignment-2026-04-20.md" in retention
    assert "ralplan-task-management-filters-2026-04-19.md" in retention
    assert "ralplan-task-management-page-closeout-2026-04-19.md" in retention
    assert "ralplan-work-driven-creative-flow-2026-04-20.md" in retention


def test_product_docs_match_current_name_share_text_parse_and_delete_truth() -> None:
    redesign = _read("docs/domains/products/redesign.md")
    requirements = _read("docs/domains/products/requirements.md")
    list_doc = _read("docs/specs/page-specs/product-list.md")
    detail_doc = _read("docs/specs/page-specs/product-detail.md")
    spec = _read("docs/specs/requirements-spec.md")
    guide = _read("docs/guides/user-guide.md")

    for doc in [redesign, requirements]:
        assert "share_text" in doc
        assert "product.name" in doc
        assert "不会覆盖" in doc
        assert "PUT /api/products/{id}" in doc
        assert "DELETE /api/products/{id}" in doc

    assert "解绑关联素材" in redesign
    assert "/material/product" in list_doc
    assert "分享文本" in list_doc
    assert "解析状态" in list_doc
    assert "批量删除" in list_doc
    assert "商品链接" not in list_doc

    assert "/material/product/:id" in detail_doc
    assert "得物链接" in detail_doc
    assert "解析素材" in detail_doc
    assert "封面" in detail_doc
    assert "话题" in detail_doc
    assert "商品链接" not in detail_doc

    assert "商品名称、分享文本" in spec
    assert "填写商品名称和分享文本" in guide
    assert "关联商品" in guide


def test_product_plan_retention_moves_product_create_prd_and_test_spec_out_of_pending_review() -> None:
    retention = _read("docs/governance/omx-plan-retention.md")

    assert "product-create 双字段规划已经被正式商品域文档" in retention
    assert "prd-product-create-name-share-text.md" in retention
    assert "test-spec-product-create-name-share-text.md" in retention

    pending_section = retention.split("## 3.3 Keep in `.omx/plans/` pending manual review", maxsplit=1)[1]
    assert "prd-product-create-name-share-text.md" not in pending_section
    assert "test-spec-product-create-name-share-text.md" not in pending_section


def test_closeout_docs_point_to_archived_omx_plan_sources() -> None:
    creative_summary = _read("docs/domains/creative/progressive-rebuild-final-summary.md")
    creative_audit = _read("docs/domains/creative/progressive-rebuild-completion-audit.md")
    phase_a = _read("docs/domains/creative/phase-a-acceptance-checklist.md")
    frontend_summary = _read("docs/frontend-ui-ux-closeout-final-summary.md")

    for doc in [creative_summary, creative_audit, phase_a, frontend_summary]:
        assert ".omx/plans/archive/" in doc

    assert ".omx/plans/prd-creative-progressive-rebuild-roadmap.md" not in creative_summary
    assert ".omx/plans/prd-creative-progressive-rebuild-phase-a-pr-plan.md" not in creative_audit
    assert ".omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md" not in frontend_summary


def test_closeout_reports_point_to_archived_second_batch_omx_plan_sources() -> None:
    local_ffmpeg = _read("reports/local-ffmpeg-plan-closeout-2026-04-20.md")
    login_ux = _read("reports/login-ux-closeout-stage-summary-2026-04-19.md")
    release_tail = _read("reports/release-hardening-tail-triage-2026-04-20.md")
    runtime_acceptance = _read("reports/runtime-acceptance-local-ffmpeg-and-random-account-2026-04-20.md")
    flaky = _read("reports/flaky-e2e-convergence-2026-04-20.md")

    assert ".omx/plans/archive/prd-local-ffmpeg-composition-pr-plan.md" in local_ffmpeg
    assert ".omx/plans/archive/prd-login-ux-closeout-pr-plan.md" in login_ux
    assert ".omx/plans/archive/test-spec-login-ux-closeout-pr-plan.md" in login_ux
    assert ".omx/plans/archive/prd-release-hardening-runtime-acceptance-closeout.md" in release_tail
    assert ".omx/plans/archive/prd-release-hardening-runtime-acceptance-closeout.md" in runtime_acceptance
    assert ".omx/plans/archive/test-spec-release-hardening-runtime-acceptance-closeout.md" in runtime_acceptance
    assert ".omx/plans/archive/prd-release-hardening-runtime-acceptance-closeout.md" in flaky
    assert ".omx/plans/archive/test-spec-release-hardening-runtime-acceptance-closeout.md" in flaky


def test_next_phase_backlog_compresses_open_issues_into_prioritized_lanes() -> None:
    backlog = _read("docs/governance/next-phase-backlog.md")

    assert "下一阶段 Backlog" in backlog
    assert "Open Questions" in backlog
    assert "P0" in backlog
    assert "P1" in backlog
    assert "P2" in backlog
    assert "Creative Workbench 可用性收口" in backlog
    assert "业务层 vs 诊断层彻底分层" in backlog
    assert "AIClip workflow 产品化" in backlog
    assert "docs/governance/root-doc-triage.md" in backlog


def test_next_phase_kickoff_links_completion_boundary_baseline_and_launch_artifacts() -> None:
    kickoff = _read("docs/current/next-phase-kickoff.md")

    assert "下一阶段启动包" in kickoff
    assert "本文件是“下一阶段启动包”的总入口" in kickoff
    assert "docs/governance/phase-transition-checklist.md" in kickoff
    assert "这份启动包怎么用" in kickoff
    assert "当前完成度" in kickoff
    assert "当前边界" in kickoff
    assert "当前验证基线" in kickoff
    assert "当前 backlog 入口" in kickoff
    assert "下一阶段第一条主线" in kickoff
    assert "单主线推进 + 多 PR sequence" in kickoff
    assert "docs/governance/verification-baseline.md" in kickoff
    assert "docs/governance/next-phase-backlog.md" in kickoff
    assert "docs/governance/next-phase-prd.md" in kickoff
    assert "docs/governance/next-phase-test-spec.md" in kickoff
    assert "docs/governance/next-phase-execution-breakdown.md" in kickoff


def test_next_phase_launch_bundle_docs_define_scope_tests_and_execution() -> None:
    prd = _read("docs/governance/next-phase-prd.md")
    test_spec = _read("docs/governance/next-phase-test-spec.md")
    breakdown = _read("docs/governance/next-phase-execution-breakdown.md")

    assert "Creative-first 稳定化 / UI-UX 收口主线" in prd
    assert "在启动包中的角色" in prd
    assert "docs/current/next-phase-kickoff.md" in prd
    assert "docs/governance/phase-transition-checklist.md" in prd
    assert "成功标准" in prd
    assert "PRD 负责锁范围，test spec 负责锁验证，execution breakdown 负责锁顺序" in prd
    assert "在启动包中的角色" in test_spec
    assert "docs/governance/verification-baseline.md" in test_spec
    assert "必跑 frontend E2E baseline" in test_spec
    assert "与 PR Sequence 的映射" in test_spec
    assert "PR-4 — 回归补强与阶段收口" in test_spec
    assert "CreativeWorkbench" in test_spec
    assert "在启动包中的角色" in breakdown
    assert "docs/governance/phase-transition-checklist.md" in breakdown
    assert "PR Sequence" in breakdown
    assert "PR-1 — Workbench 可管理性收口" in breakdown
    assert "PR-4 — 回归补强与阶段收口" in breakdown
    assert "需要同步更新" in breakdown
