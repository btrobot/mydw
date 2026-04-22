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
    assert "docs/governance/policies/generated-artifact-policy.md" in workflow
    assert "docs/governance/standards/schema-parity-checklist.md" in workflow
    assert "docs/governance/policies/manual-http-exceptions.md" in workflow
    assert "npm run generated:check" in workflow


def test_readme_uses_actual_packaged_output_directory() -> None:
    readme = _read("README.md")

    assert "dist-electron" in readme
    assert "docs/governance/verification-baseline.md" in readme
    assert "docs/current/next-phase-kickoff.md" in readme
    assert "frontend/release/" not in readme


def test_documentation_strategy_matches_epic7_authority_model() -> None:
    strategy = _read("docs/governance/standards/documentation-strategy.md")

    assert "docs/current/architecture.md" in strategy
    assert "docs/current/runtime-truth.md" in strategy
    assert "system-architecture.md" in strategy
    assert "唯一来源" not in strategy or "system-architecture.md 是架构的唯一来源" not in strategy


def test_doc_checklist_recognizes_current_vs_archival_docs() -> None:
    checklist = _read("docs/governance/standards/doc-checklist.md")

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
    assert "已经收尾到能做决定" in checklist
    assert "不翻聊天记录，也能讲清“现在做到哪了”" in checklist
    assert "backlog 已压缩到可以支持“只选一条主线”" in checklist
    assert "docs/governance/post-mvp-development-model.md" in checklist
    assert "next-phase PRD" in checklist
    assert "下一阶段有且只有一条主线" in checklist
    assert "MVP 后" in model


def test_post_mvp_closeout_sequence_doc_connects_closeout_route_and_targeted_truth() -> None:
    docs_index = _read("docs/README.md")
    flow = _read("docs/governance/post-mvp-closeout-sequence.md")

    assert "docs/governance/post-mvp-closeout-sequence.md" in docs_index
    assert "先做当前阶段收尾总结" in flow
    assert "再选下一阶段唯一主线" in flow
    assert "围绕主线定向补齐 current truth" in flow
    assert "全局最小基线" in flow
    assert "路线绑定的 current truth" in flow
    assert "docs/governance/post-mvp-development-model.md" in flow
    assert "docs/governance/phase-transition-checklist.md" in flow
    assert "docs/current/next-phase-kickoff.md" in flow


def test_post_mvp_templates_are_indexed_and_connected_to_sequence_doc() -> None:
    docs_index = _read("docs/README.md")
    flow = _read("docs/governance/post-mvp-closeout-sequence.md")
    closeout_template = _read("docs/governance/templates/phase-closeout-template.md")
    selection_template = _read("docs/governance/templates/next-phase-mainline-selection-template.md")

    assert "docs/governance/templates/phase-closeout-template.md" in docs_index
    assert "docs/governance/templates/next-phase-mainline-selection-template.md" in docs_index
    assert "docs/governance/templates/phase-closeout-template.md" in flow
    assert "docs/governance/templates/next-phase-mainline-selection-template.md" in flow
    assert "Remaining risks / Residual risks" in closeout_template
    assert "Exit decision / 阶段退出结论" in closeout_template
    assert "下一阶段唯一主线" in selection_template
    assert "为这条主线必须先补准的 current truth" in selection_template
    assert "kickoff / PRD / test spec / execution breakdown" in selection_template


def test_governance_readme_classifies_core_policies_inventory_standards_and_templates() -> None:
    governance_index = _read("docs/governance/README.md")
    docs_index = _read("docs/README.md")

    assert "docs/governance/README.md" in docs_index
    assert "Core" in governance_index
    assert "Policies" in governance_index
    assert "Inventory" in governance_index
    assert "Standards" in governance_index
    assert "Templates" in governance_index
    assert "docs/governance/policies/generated-artifact-policy.md" in governance_index
    assert "docs/governance/policies/manual-http-exceptions.md" in governance_index
    assert "docs/governance/inventory/inventory-ledger.md" in governance_index
    assert "docs/governance/inventory/current-project-mvp-closeout-checklist.md" in governance_index
    assert "docs/governance/inventory/current-project-mvp-closeout-execution.md" in governance_index
    assert "docs/governance/inventory/current-project-phase-transition-decision.md" in governance_index
    assert "docs/governance/inventory/post-mvp-doc-governance-closeout.md" in governance_index
    assert "docs/governance/standards/documentation-strategy.md" in governance_index
    assert "docs/governance/standards/docs-directory-placement-rules.md" in governance_index
    assert "docs/governance/standards/domains-architecture-governance-boundary.md" in governance_index
    assert "docs/governance/standards/schema-parity-checklist.md" in governance_index
    assert "docs/governance/templates/phase-closeout-template.md" in governance_index
    assert "按场景的阅读顺序" in governance_index
    assert "场景 B：我想知道 MVP 后怎么继续推进" in governance_index
    assert "这 4 份核心文档的关系" in governance_index
    assert "model 讲为什么，sequence 讲顺序，checklist 讲门槛，kickoff 讲起点" in governance_index
    assert "post-mvp-development-model" in governance_index
    assert "post-mvp-closeout-sequence" in governance_index
    assert "phase-transition-checklist" in governance_index
    assert "current/next-phase-kickoff" in governance_index
    assert "新文档落点规则" in governance_index
    assert "应该留在 root 的文档" in governance_index
    assert "应该放进 `policies/` 的文档" in governance_index
    assert "应该放进 `inventory/` 的文档" in governance_index
    assert "应该放进 `standards/` 的文档" in governance_index
    assert "应该放进 `templates/` 的文档" in governance_index
    assert "文档放置决策表（5 秒判断版）" in governance_index
    assert "高频入口 / 阶段切换入口 / 推荐阅读路径中的高频文档" in governance_index
    assert "规则 / 边界 / retention / artifact policy" in governance_index
    assert "盘点 / triage / ledger / stale/version/parity checklist" in governance_index
    assert "长期规范 / strategy / guide / checklist / system spec" in governance_index
    assert "可复制复用的模板 / skeleton / starter" in governance_index


def test_formal_doc_governance_closeout_artifact_is_indexed_and_summarizes_current_state() -> None:
    docs_index = _read("docs/README.md")
    governance_index = _read("docs/governance/README.md")
    ledger = _read("docs/governance/inventory/inventory-ledger.md")
    closeout = _read("docs/governance/inventory/post-mvp-doc-governance-closeout.md")

    assert "docs/governance/inventory/post-mvp-doc-governance-closeout.md" in docs_index
    assert "docs/governance/inventory/post-mvp-doc-governance-closeout.md" in governance_index
    assert "docs/governance/inventory/post-mvp-doc-governance-closeout.md" in ledger
    assert "formal closeout artifact" in closeout
    assert "docs/` 根层现在只保留默认入口文档：`docs/README.md` 与 `docs/runtime-truth.md`" in closeout
    assert "docs/governance/post-mvp-development-model.md" in closeout
    assert "docs/governance/post-mvp-closeout-sequence.md" in closeout
    assert "docs/governance/phase-transition-checklist.md" in closeout
    assert "docs/current/next-phase-kickoff.md" in closeout
    assert "model 讲为什么，sequence 讲顺序，checklist 讲门槛，kickoff 讲起点" in closeout
    assert "不是新的长期规范，而是本轮治理工作的" in closeout


def test_current_project_mvp_closeout_checklist_is_indexed_and_covers_six_closeout_areas() -> None:
    docs_index = _read("docs/README.md")
    governance_index = _read("docs/governance/README.md")
    sequence = _read("docs/governance/post-mvp-closeout-sequence.md")
    transition = _read("docs/governance/phase-transition-checklist.md")
    checklist = _read("docs/governance/inventory/current-project-mvp-closeout-checklist.md")

    assert "docs/governance/inventory/current-project-mvp-closeout-checklist.md" in docs_index
    assert "docs/governance/inventory/current-project-mvp-closeout-checklist.md" in governance_index
    assert "docs/governance/inventory/current-project-mvp-closeout-checklist.md" in sequence
    assert "docs/governance/inventory/current-project-mvp-closeout-checklist.md" in transition
    assert "实现状态收口" in checklist
    assert "系统边界收口" in checklist
    assert "文档体系收口" in checklist
    assert "验证基线收口" in checklist
    assert "Planning / 历史产物收口" in checklist
    assert "下一阶段决策收口" in checklist
    assert "Creative-first" in checklist
    assert "local_ffmpeg V1" in checklist
    assert ".omx/plans" in checklist


def test_current_project_mvp_closeout_execution_record_is_indexed_and_tracks_residual_planning_risk() -> None:
    docs_index = _read("docs/README.md")
    governance_index = _read("docs/governance/README.md")
    ledger = _read("docs/governance/inventory/inventory-ledger.md")
    execution = _read("docs/governance/inventory/current-project-mvp-closeout-execution.md")

    assert "docs/governance/inventory/current-project-mvp-closeout-execution.md" in docs_index
    assert "docs/governance/inventory/current-project-mvp-closeout-execution.md" in governance_index
    assert "docs/governance/inventory/current-project-mvp-closeout-execution.md" in ledger
    assert "A. 实现状态收口" in execution
    assert "B. 系统边界收口" in execution
    assert "C. 文档体系收口" in execution
    assert "D. 验证基线收口" in execution
    assert "E. Planning / 历史产物收口" in execution
    assert "F. 下一阶段决策收口" in execution
    assert "completed" in execution
    assert "pending-manual-review 文件，已在本轮 follow-up 中继续归档清理" in execution
    assert "Creative-first 稳定化 / UI-UX 收口主线" in execution
    assert "可以进入下一阶段持续开发" in execution


def test_current_project_phase_transition_decision_is_indexed_and_approves_next_phase_entry() -> None:
    docs_index = _read("docs/README.md")
    governance_index = _read("docs/governance/README.md")
    ledger = _read("docs/governance/inventory/inventory-ledger.md")
    decision = _read("docs/governance/inventory/current-project-phase-transition-decision.md")

    assert "docs/governance/inventory/current-project-phase-transition-decision.md" in docs_index
    assert "docs/governance/inventory/current-project-phase-transition-decision.md" in governance_index
    assert "docs/governance/inventory/current-project-phase-transition-decision.md" in ledger
    assert "Part A：当前阶段已收口" in decision
    assert "Part B：下一阶段已准备好启动" in decision
    assert "Creative-first 稳定化 / UI-UX 收口主线" in decision
    assert "Approved / 允许切换阶段" in decision
    assert "PR-1：Workbench 可管理性收口" in decision


def test_domains_architecture_governance_boundary_doc_is_indexed_and_explains_split() -> None:
    docs_index = _read("docs/README.md")
    governance_index = _read("docs/governance/README.md")
    split_doc = _read("docs/governance/standards/domains-architecture-governance-boundary.md")

    assert "docs/governance/standards/domains-architecture-governance-boundary.md" in docs_index
    assert "docs/governance/standards/domains-architecture-governance-boundary.md" in governance_index
    assert "`domains/` = **业务是什么，业务真相是什么**" in split_doc
    assert "`architecture/` = **系统现在如何被设计成这样**" in split_doc
    assert "`governance/` = **这些真相和设计，平时如何被维护、更新、约束、收口**" in split_doc
    assert "governance 不是“项目管理杂项”" in split_doc


def test_docs_directory_placement_rules_doc_is_indexed_and_explains_four_way_split() -> None:
    docs_index = _read("docs/README.md")
    governance_index = _read("docs/governance/README.md")
    split_doc = _read("docs/governance/standards/docs-directory-placement-rules.md")

    assert "docs/governance/standards/docs-directory-placement-rules.md" in docs_index
    assert "docs/governance/standards/docs-directory-placement-rules.md" in governance_index
    assert "`docs/current/` = **当前真相 / 当前默认入口**" in split_doc
    assert "`docs/domains/` = **业务领域真相**" in split_doc
    assert "`docs/governance/` = **治理规则 / 收口规则 / 阶段推进规则**" in split_doc
    assert "`docs/guides/` = **操作指南 / 实施手册 / how-to**" in split_doc


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
    triage = _read("docs/governance/inventory/root-doc-triage.md")

    assert "根层文档分诊表" in triage
    assert "优先按 current / domains / governance / guides 四分法收口" in triage
    assert "Batch 1 已完成" in triage
    assert "Batch 2 已完成" in triage
    assert "Batch 3 已完成" in triage
    assert "docs/domains/system/backup-scope.md" in triage
    assert "docs/governance/policies/manual-http-exceptions.md" in triage
    assert "docs/governance/standards/schema-parity-checklist.md" in triage
    assert "docs/specs/requirements-sources/chat-req.md" in triage
    assert "docs/specs/requirements-sources/init-req.md" in triage
    assert "docs/domains/creative/workbench-ui-issues.md" in triage
    assert "删除候选" in triage
    assert "docs/frontend-ui-ux-closeout-ralplan-command.md" in triage
    assert "docs/archive/history/frontend-ui-ux-closeout-final-summary.md" in triage
    assert "当前根目录只保留" in triage
    assert "docs/runtime-truth.md" in triage


def test_batch1_low_risk_docs_have_moved_out_of_docs_root() -> None:
    moved_pairs = [
        ("docs/backup-scope.md", "docs/domains/system/backup-scope.md"),
        ("docs/dewu-page-structure.md", "docs/domains/products/dewu-page-structure.md"),
        ("docs/manual-axios-exceptions.md", "docs/governance/policies/manual-http-exceptions.md"),
        ("docs/schema-parity-checklist.md", "docs/governance/standards/schema-parity-checklist.md"),
    ]

    for old_path, new_path in moved_pairs:
        assert not (REPO_ROOT / old_path).exists(), f"file should no longer stay in docs root: {old_path}"
        assert (REPO_ROOT / new_path).exists(), f"missing moved file: {new_path}"


def test_batch2_docs_have_moved_out_of_docs_root() -> None:
    moved_pairs = [
        ("docs/init-req.md", "docs/specs/requirements-sources/init-req.md"),
        ("docs/chat-req.md", "docs/specs/requirements-sources/chat-req.md"),
        ("docs/frontend-ui-issues-and-improvements.md", "docs/domains/creative/workbench-ui-issues.md"),
    ]

    for old_path, new_path in moved_pairs:
        assert not (REPO_ROOT / old_path).exists(), f"file should no longer stay in docs root: {old_path}"
        assert (REPO_ROOT / new_path).exists(), f"missing moved file: {new_path}"


def test_omx_plan_retention_distinguishes_active_archive_and_pending_plan_sets() -> None:
    retention = _read("docs/governance/policies/omx-plan-retention.md")

    assert ".omx/plans" in retention
    assert ".omx/plans/archive/" in retention
    assert "Keep active in `.omx/plans/`" in retention
    assert "Archive now to `.omx/plans/archive/`" in retention
    assert "Pending manual review set" in retention
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
    assert "docs/archive/history/frontend-ui-ux-closeout-final-summary.md" in retention
    assert "product-create-dual-field-ralplan-2026-04-16.md" in retention
    assert "ralplan-login-bs-alignment-2026-04-20.md" in retention
    assert "ralplan-task-management-filters-2026-04-19.md" in retention
    assert "ralplan-task-management-page-closeout-2026-04-19.md" in retention
    assert "ralplan-work-driven-creative-flow-2026-04-20.md" in retention
    assert "prd-login-bs-alignment-pr-plan.md" in retention
    assert "prd-task-management-page-closeout.md" in retention
    assert "prd-work-driven-creative-flow-refactor.md" in retention


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
    retention = _read("docs/governance/policies/omx-plan-retention.md")

    assert "product-create 双字段规划已经被正式商品域文档" in retention
    assert "prd-product-create-name-share-text.md" in retention
    assert "test-spec-product-create-name-share-text.md" in retention

    pending_section = retention.split("## 3.3 Pending manual review set", maxsplit=1)[1]
    assert "prd-product-create-name-share-text.md" not in pending_section
    assert "test-spec-product-create-name-share-text.md" not in pending_section
    assert "prd-login-bs-alignment-pr-plan.md" not in pending_section
    assert "prd-task-management-page-closeout.md" not in pending_section
    assert "prd-work-driven-creative-flow-refactor.md" not in pending_section


def test_followup_archive_batch_moves_remaining_pending_omx_plans_out_of_active_set() -> None:
    moved_pairs = [
        (".omx/plans/prd-login-bs-alignment-pr-plan.md", ".omx/plans/archive/prd-login-bs-alignment-pr-plan.md"),
        (".omx/plans/test-spec-login-bs-alignment-pr-plan.md", ".omx/plans/archive/test-spec-login-bs-alignment-pr-plan.md"),
        (".omx/plans/prd-task-management-page-closeout.md", ".omx/plans/archive/prd-task-management-page-closeout.md"),
        (".omx/plans/test-spec-task-management-page-closeout.md", ".omx/plans/archive/test-spec-task-management-page-closeout.md"),
        (".omx/plans/prd-work-driven-creative-flow-refactor.md", ".omx/plans/archive/prd-work-driven-creative-flow-refactor.md"),
        (".omx/plans/test-spec-work-driven-creative-flow-refactor.md", ".omx/plans/archive/test-spec-work-driven-creative-flow-refactor.md"),
    ]

    for old_path, new_path in moved_pairs:
        assert not (REPO_ROOT / old_path).exists(), f"file should no longer be active: {old_path}"
        assert (REPO_ROOT / new_path).exists(), f"missing archived file: {new_path}"


def test_closeout_docs_point_to_archived_omx_plan_sources() -> None:
    creative_summary = _read("docs/domains/creative/progressive-rebuild-final-summary.md")
    creative_audit = _read("docs/domains/creative/progressive-rebuild-completion-audit.md")
    phase_a = _read("docs/domains/creative/phase-a-acceptance-checklist.md")
    frontend_summary = _read("docs/archive/history/frontend-ui-ux-closeout-final-summary.md")

    for doc in [creative_summary, creative_audit, phase_a, frontend_summary]:
        assert ".omx/plans/archive/" in doc

    assert ".omx/plans/prd-creative-progressive-rebuild-roadmap.md" not in creative_summary
    assert ".omx/plans/prd-creative-progressive-rebuild-phase-a-pr-plan.md" not in creative_audit
    assert ".omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md" not in frontend_summary


def test_batch3_historical_docs_are_archived_or_deleted_from_docs_root() -> None:
    moved_pairs = [
        ("docs/coze-integration.md", "docs/archive/reference/coze-integration.md"),
        ("docs/domain-model-analysis.md", "docs/archive/analysis/domain-model-analysis.md"),
        (
            "docs/frontend-ui-ux-closeout-final-summary.md",
            "docs/archive/history/frontend-ui-ux-closeout-final-summary.md",
        ),
    ]

    for old_path, new_path in moved_pairs:
        assert not (REPO_ROOT / old_path).exists(), f"file should no longer stay in docs root: {old_path}"
        assert (REPO_ROOT / new_path).exists(), f"missing archived file: {new_path}"

    assert not (REPO_ROOT / "docs/frontend-ui-ux-closeout-ralplan-command.md").exists()


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
    assert "docs/governance/inventory/root-doc-triage.md" in backlog


def test_next_phase_kickoff_links_completion_boundary_baseline_and_launch_artifacts() -> None:
    kickoff = _read("docs/current/next-phase-kickoff.md")

    assert "下一阶段启动包" in kickoff
    assert "本文件是“下一阶段启动包”的总入口" in kickoff
    assert "先收尾到“能做决定”" in kickoff
    assert "再选线到“只剩一条主线”" in kickoff
    assert "再补文档到“这条主线不再被误导”" in kickoff
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
