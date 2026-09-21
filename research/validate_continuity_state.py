#!/usr/bin/env python3
"""Continuity guard for cross-source project state.

This is intentionally narrow: it protects a few high-risk continuity facts from
silent drift between historical benchmark evidence, current research profiles,
and public claim boundaries.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research" / "project-continuity-state.json"
REPRO = ROOT / "research" / "reproduce.py"
RUNNER_BUNDLE_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "runner-bundle.schema.json"
RUNNER_RESPONSE_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "runner-response.schema.json"
LATEST_CONTINUITY = (
    ROOT
    / "docs"
    / "PROJECT-CONTINUITY-2026-09-21-AR-P003-PRIMARY-ENDPOINT.md"
)
EXPECTED_FREEZE = (
    "8a381f4ae20a5f6824e513c7f96920fdf3cfe6b00b0b8d301127f5e0b659d0fd"
)


def current_repro_suite_version() -> str:
    text = REPRO.read_text(encoding="utf-8")
    match = re.search(r'^SUITE_VERSION\s*=\s*["\\\']([^"\\\']+)["\\\']', text, re.MULTILINE)
    if not match:
        raise ValueError("unable to read SUITE_VERSION from research/reproduce.py")
    return match.group(1)


def schema_const(path: Path, property_name: str) -> str:
    doc = json.loads(path.read_text(encoding="utf-8"))
    value = ((doc.get("properties") or {}).get(property_name) or {}).get("const")
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}: missing string const for {property_name!r}")
    return value


def main() -> int:
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        actual_repro_version = current_repro_suite_version()
        actual_bundle_contract = schema_const(RUNNER_BUNDLE_SCHEMA, "bundle_version")
        actual_response_contract = schema_const(
            RUNNER_RESPONSE_SCHEMA, "response_bundle_version"
        )
        latest_continuity_text = LATEST_CONTINUITY.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: unable to load continuity state: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    if state.get("snapshot_version") != "project-continuity-v0.19":
        errors.append("machine-readable continuity snapshot_version is stale")
    if state.get("snapshot_date") != "2026-09-21":
        errors.append("machine-readable continuity snapshot_date is stale")
    if "**Snapshot date:** 2026-09-21" not in latest_continuity_text:
        errors.append("latest human-readable continuity snapshot date is stale")

    hist = ((state.get("historical") or {}).get("arp003_v0_2_3") or {})
    if hist.get("status") != "frozen_append_only":
        errors.append("AR-P003 v0.2.3 must remain frozen_append_only")
    if hist.get("freeze_id") != EXPECTED_FREEZE:
        errors.append("AR-P003 v0.2.3 freeze_id changed")

    c1 = hist.get("c1_auxiliary") or {}
    expected_counts = {"episodes": 80, "control": 40, "receipt_plus_raw_logs": 40}
    for key, value in expected_counts.items():
        if c1.get(key) != value:
            errors.append(f"C1 historical {key} changed: expected {value!r}")

    if c1.get("timing") != "unavailable":
        errors.append("C1 historical timing must remain unavailable")

    dev = state.get("development") or {}
    if (dev.get("arp003_v0_3") or {}).get("status") != "draft_not_frozen_not_executed":
        errors.append("AR-P003 v0.3 must remain draft until an explicit freeze/execution update")
    if (dev.get("public_record_profile") or {}).get("version") != "candidate-record-v0.1":
        errors.append("current public canonical record profile unexpectedly changed")

    arp003 = dev.get("arp003_v0_3") or {}
    methodology = arp003.get("methodology_decision_ledger") or {}
    if methodology.get("status") != "development_unresolved":
        errors.append(
            "AR-P003 methodology-decision status changed; update continuity "
            "deliberately when preregistration choices are selected"
        )
    if methodology.get("comparison_conditions") != (
        "selected:three_condition_structured_control"
    ):
        errors.append(
            "AR-P003 comparison_conditions must remain explicitly selected as "
            "three_condition_structured_control"
        )
    if methodology.get("protocol_version") != (
        "v0.3-draft-2026-09-21-primary-endpoint-v0.1"
    ):
        errors.append("AR-P003 selected methodology protocol-version continuity is stale")
    if methodology.get("comparison_conditions_freeze_readiness") != "complete":
        errors.append("AR-P003 comparison-condition readiness continuity is stale")

    if methodology.get("challenge_design") != "selected:integrated_challenge_strata":
        errors.append(
            "AR-P003 challenge_design must remain explicitly selected as "
            "integrated_challenge_strata"
        )
    if methodology.get("challenge_strata_freeze_readiness") != "prepared":
        errors.append(
            "AR-P003 challenge-strata freeze-readiness must remain prepared "
            "until counts/allocation/final-corpus review are frozen"
        )

    if methodology.get("reviewer_population") != (
        "selected:relevant_professional_reviewers"
    ):
        errors.append(
            "AR-P003 reviewer_population must remain explicitly selected as "
            "relevant_professional_reviewers"
        )
    if methodology.get("reviewer_population_freeze_readiness") != "complete":
        errors.append("AR-P003 reviewer-population readiness continuity is stale")

    population = methodology.get("reviewer_population_design") or {}
    expected_population = {
        "minimum_relevant_experience_years": 1,
        "experience_bands": [
            "1_to_2_years",
            "3_to_5_years",
            "6_plus_years",
        ],
        "english_proficiency_required": True,
        "degree_certification_or_specific_title_required": False,
        "prior_general_ai_activity_receipt_familiarity": "permitted_and_recorded",
        "external_assistance_during_study_cases": (
            "prohibited_absent_pre_execution_versioned_amendment"
        ),
        "claims_scoped_to_population_actually_recruited": True,
        "recruitment_authorized": False,
    }
    if population != expected_population:
        errors.append("AR-P003 reviewer-population continuity details are stale")

    if methodology.get("primary_endpoint") != (
        "selected:correct_completion_by_180s"
    ):
        errors.append(
            "AR-P003 primary_endpoint must remain explicitly selected as "
            "correct_completion_by_180s"
        )
    if methodology.get("primary_endpoint_freeze_readiness") != "complete":
        errors.append("AR-P003 primary-endpoint readiness continuity is stale")

    endpoint = methodology.get("primary_endpoint_design") or {}
    expected_endpoint = {
        "outcome_type": "binary",
        "deadline_seconds": 180,
        "case_specific_required_judgments": True,
        "case_specific_acceptable_evidence_sets": True,
        "material_fact_failure_semantics": True,
        "deadline_miss_cannot_succeed": True,
        "component_endpoints": "secondary_diagnostic_not_co_primary",
        "critical_false_clearance": "separate_prespecified_safety_endpoint",
        "critical_false_clearance_threshold": (
            "unresolved_effect_precision_target"
        ),
        "primary_timing_clock": "unresolved",
        "development_contingency": (
            "pre_freeze_stop_and_new_owner_decision_no_automatic_fallback"
        ),
        "confirmatory_primary_derivation": "blocked_until_timing_selected",
    }
    if endpoint != expected_endpoint:
        errors.append("AR-P003 primary-endpoint continuity details are stale")

    required_methodology_unresolved = {
        "primary_timing_clock",
        "effect_precision_target",
    }
    for decision_id in required_methodology_unresolved:
        if methodology.get(decision_id) != "unresolved":
            errors.append(
                f"AR-P003 methodology decision {decision_id!r} changed without "
                "a deliberate continuity update"
            )
    if methodology.get("freeze_readiness_crosscheck") is not True:
        errors.append(
            "AR-P003 methodology/freeze-readiness cross-check continuity flag "
            "is not enabled"
        )

    runner = (arp003.get("offline_runner") or {})
    assignment_binding = runner.get("assignment_binding") or {}
    if assignment_binding.get("exact_assignment_sha256") is not True:
        errors.append("AR-P003 exact assignment binding unexpectedly disabled")
    if assignment_binding.get("condition_order_case_verification") is not True:
        errors.append("AR-P003 assignment case/order/condition verification unexpectedly disabled")
    if assignment_binding.get("incomplete_session_rejected") is not True:
        errors.append("AR-P003 incomplete-session scoring guard unexpectedly disabled")
    if assignment_binding.get("bundle_contract") != actual_bundle_contract:
        errors.append(
            "AR-P003 reviewer bundle contract continuity is stale: "
            f"state={assignment_binding.get('bundle_contract')!r}, "
            f"schema={actual_bundle_contract!r}"
        )
    if assignment_binding.get("response_contract") != actual_response_contract:
        errors.append(
            "AR-P003 reviewer response contract continuity is stale: "
            f"state={assignment_binding.get('response_contract')!r}, "
            f"schema={actual_response_contract!r}"
        )
    if assignment_binding.get("assignment_contract") != (
        "AR-P003-v0.3-draft-assignment-v0.3"
    ):
        errors.append("AR-P003 three-condition assignment contract continuity is stale")
    if assignment_binding.get("comparison_design") != (
        "three_condition_structured_control"
    ):
        errors.append("AR-P003 comparison-design runner continuity is stale")
    if assignment_binding.get("analysis_contract") != (
        "AR-P003-v0.3-dev-runner-analysis-v0.4"
    ):
        errors.append("AR-P003 hidden analysis contract continuity is stale")
    if assignment_binding.get("challenge_design") != "integrated_challenge_strata":
        errors.append("AR-P003 challenge-design runner continuity is stale")

    if runner.get("primary_endpoint") != (
        "selected:correct_completion_by_180s"
    ):
        errors.append("AR-P003 endpoint-aware runner continuity is stale")
    if runner.get("primary_endpoint_deadline_seconds") != 180:
        errors.append("AR-P003 primary endpoint deadline continuity is stale")
    if runner.get("primary_timing_clock") != "unresolved":
        errors.append("AR-P003 primary timing clock must remain unresolved")
    if runner.get("confirmatory_primary_derivation") != (
        "blocked_until_primary_timing_clock_selected"
    ):
        errors.append("AR-P003 confirmatory primary derivation must remain blocked")
    if runner.get("primary_endpoint_contract") != (
        "AR-P003-v0.3-primary-endpoint-case-v0.1"
    ):
        errors.append("AR-P003 primary endpoint contract continuity is stale")
    if runner.get("scoring_record_contract") != (
        "AR-P003-v0.3-scoring-record-v0.2"
    ):
        errors.append("AR-P003 scoring-record continuity is stale")
    if assignment_binding.get("dual_clock_preservation") is not True:
        errors.append("AR-P003 dual-clock preservation continuity is stale")
    if assignment_binding.get("primary_endpoint_binding") is not True:
        errors.append("AR-P003 endpoint-binding continuity is stale")

    freeze_manifest = arp003.get("freeze_manifest") or {}
    if freeze_manifest.get("version") != "AR-P003-v0.3-freeze-manifest-v0.2":
        errors.append("AR-P003 freeze-manifest continuity version unexpectedly changed")
    if freeze_manifest.get("status") != "prepared_no_final_manifest":
        errors.append(
            "AR-P003 freeze-manifest evidence status changed without deliberate continuity update"
        )
    if freeze_manifest.get("exact_protocol_binding") is not True:
        errors.append("AR-P003 freeze-manifest protocol binding unexpectedly disabled")
    if freeze_manifest.get("protocol_frozen_gate") is not True:
        errors.append("AR-P003 final-freeze protocol-frozen gate unexpectedly disabled")
    if freeze_manifest.get("deterministic_freeze_content_id") is not True:
        errors.append("AR-P003 deterministic freeze content ID unexpectedly disabled")
    if freeze_manifest.get("final_manifest") != "not_created":
        errors.append(
            "AR-P003 final manifest state changed; update continuity only with final freeze evidence"
        )

    leakage = arp003.get("leakage_validation") or {}
    if leakage.get("status") != "prepared_not_complete":
        errors.append(
            "AR-P003 leakage-validation continuity status changed; update deliberately "
            "only after the final sealed corpus audit/review evidence changes"
        )
    automated_audit = leakage.get("automated_audit") or {}
    if automated_audit.get("status") != "development_only_ci_green":
        errors.append("AR-P003 leakage-audit development status unexpectedly changed")
    if automated_audit.get("final_corpus_audit") != "not_run":
        errors.append(
            "AR-P003 final-corpus leakage-audit state changed without continuity update"
        )
    manual_review = leakage.get("manual_case_review") or {}
    if manual_review.get("checked_in_record") != "not_tested_template_only":
        errors.append("AR-P003 checked-in manual case-review evidence boundary changed")
    if manual_review.get("final_corpus_review") != "not_run":
        errors.append(
            "AR-P003 final-corpus manual case-review state changed without continuity update"
        )

    repro = dev.get("reproducibility_runner") or {}
    if repro.get("suite_version") != actual_repro_version:
        errors.append(
            "reproducibility suite continuity is stale: "
            f"state={repro.get('suite_version')!r}, "
            f"source={actual_repro_version!r}"
        )
    if repro.get("exact_dependency_lock") is not True:
        errors.append("exact dependency-lock continuity flag unexpectedly changed")
    if repro.get("github_actions_commit_pinned") is not True:
        errors.append("GitHub Actions pinning continuity flag unexpectedly changed")

    governance = state.get("repository_governance") or {}
    security = governance.get("security_hardening") or {}
    required_security_flags = {
        "dependabot_version_updates_configured": True,
        "codeowners_present": True,
        "primary_ci_contents_read_only": True,
        "primary_ci_checkout_persist_credentials": False,
        "primary_ci_actions_commit_pinned": True,
        "primary_ci_cancel_stale_runs": True,
        "security_smoke_test": True,
        "offline_runner_strict_csp": True,
        "offline_runner_resource_limits": True,
    }
    for key, expected in required_security_flags.items():
        if security.get(key) is not expected:
            errors.append(
                f"repository security continuity flag {key!r} changed unexpectedly"
            )
    codeql = security.get("codeql_advanced_setup") or {}
    if codeql.get("status") != "main_ci_green":
        errors.append("CodeQL advanced-setup continuity status unexpectedly changed")
    if codeql.get("action_commit_pinned") is not True:
        errors.append("CodeQL immutable Action pin continuity flag unexpectedly changed")
    if set(codeql.get("languages") or []) != {"python", "javascript-typescript"}:
        errors.append("CodeQL language coverage continuity unexpectedly changed")
    if security.get("codeql_default_setup") != "not_used_advanced_setup_selected":
        errors.append("CodeQL setup mode changed without deliberate continuity update")
    if security.get("main_ruleset") != "protect_main_active_verified_2026-09-20":
        errors.append("verified Protect main ruleset continuity is stale")
    verified_admin_flags = {
        "dependabot_alerts_enabled": True,
        "dependabot_security_updates_enabled": True,
        "code_scanning_alerts_enabled": True,
        "secret_scanning_alerts_enabled": True,
        "secret_protection_enabled": True,
        "push_protection_enabled": True,
        "security_advisories_enabled": True,
        "security_policy_enabled": True,
    }
    for key, expected in verified_admin_flags.items():
        if security.get(key) is not expected:
            errors.append(
                f"verified repository-admin security field {key!r} changed unexpectedly"
            )
    if security.get("private_vulnerability_reporting") != (
        "enabled_owner_verified_2026-09-20"
    ):
        errors.append("private vulnerability reporting continuity is stale")
    if codeql.get("remediation_pr") != 72:
        errors.append("CodeQL diagnostic-remediation PR continuity is stale")
    if codeql.get("remediation_merge_commit") != (
        "4788dc4f39a19b01e68e89c2f39a7e7c6dce7fb4"
    ):
        errors.append("CodeQL diagnostic-remediation merge continuity is stale")
    if codeql.get("post_remediation_python") != "success":
        errors.append("post-remediation Python CodeQL status is stale")
    if codeql.get("post_remediation_javascript_typescript") != "success":
        errors.append("post-remediation JavaScript/TypeScript CodeQL status is stale")
    if codeql.get("alert_inventory") != (
        "owner_ui_verified_0_open_2_closed_2026-09-20"
    ):
        errors.append(
            "CodeQL alert-inventory continuity is stale relative to authenticated "
            "owner dashboard evidence"
        )
    if codeql.get("post_remediation_open_high_alert_count") != 0:
        errors.append("CodeQL open-High alert count continuity is stale")
    if codeql.get("open_original_alerts") != []:
        errors.append("CodeQL remaining original-alert continuity is stale")
    if codeql.get("closed_original_alerts") != [1, 2]:
        errors.append("CodeQL closed original-alert continuity is stale")
    if codeql.get("alert_1_post_second_remediation_dashboard_verification") != (
        "owner_ui_verified_closed_after_pr_76_on_main_2026-09-20"
    ):
        errors.append(
            "CodeQL alert #1 final dashboard verification continuity is stale"
        )
    if codeql.get("all_original_alerts_resolved") is not True:
        errors.append("CodeQL original-alert resolution continuity is stale")
    if codeql.get("final_original_alert_state") != "0_open_2_closed":
        errors.append("CodeQL final original-alert state continuity is stale")
    if codeql.get("alert_1_second_remediation_pr") != 75:
        errors.append("CodeQL alert #1 second-remediation PR continuity is stale")
    if codeql.get("alert_1_second_remediation_merge_commit") != (
        "b8e10da52be098fe7bf2b68e065e7fae5dcb6263"
    ):
        errors.append("CodeQL alert #1 second-remediation merge continuity is stale")
    if codeql.get("alert_1_second_remediation_validation_run") != 162:
        errors.append("CodeQL alert #1 second-remediation validation run is stale")
    if codeql.get("alert_1_second_remediation_codeql_run") != 79:
        errors.append("CodeQL alert #1 second-remediation CodeQL run is stale")
    if codeql.get("alert_1_heuristic_followup_branch") != (
        "codeql-alert-1-heuristic-source-hardening"
    ):
        errors.append("CodeQL alert #1 heuristic-followup branch continuity is stale")
    if codeql.get("alert_1_heuristic_followup_strategy") != (
        "remove_sensitive_heuristic_names_from_printable_diagnostic_dataflow"
    ):
        errors.append("CodeQL alert #1 heuristic-followup strategy continuity is stale")
    if codeql.get("alert_1_heuristic_followup_pr") != 76:
        errors.append("CodeQL alert #1 heuristic-followup PR continuity is stale")
    if codeql.get("alert_1_heuristic_followup_merge_commit") != (
        "9c03d91de065511bc7397f93a12e40cb747eb3e7"
    ):
        errors.append("CodeQL alert #1 heuristic-followup merge continuity is stale")
    if codeql.get("alert_1_heuristic_followup_validation_run") != 164:
        errors.append("CodeQL alert #1 heuristic-followup validation run is stale")
    if codeql.get("alert_1_heuristic_followup_codeql_run") != 81:
        errors.append("CodeQL alert #1 heuristic-followup CodeQL run is stale")
    if security.get("security_alert_notifications") != (
        "enabled_owner_verified_2026-09-20"
    ):
        errors.append("owner Security-alert notification continuity is stale")
    if security.get("issue_37") != "closed_completed_2026-09-20":
        errors.append("repository security issue #37 continuity is stale")
    if (dev.get("reproducibility_runner") or {}).get("external_reproduction_handoff") is not True:
        errors.append("external reproduction handoff continuity flag unexpectedly changed")

    if governance.get("explicit_license_status") != "apache-2.0":
        errors.append("repository license status must remain apache-2.0 after issue #44")

    repository_license = governance.get("repository_license") or {}
    required_license = {
        "spdx_id": "Apache-2.0",
        "copyright_holder": "Blake Gaucher",
        "copyright_year": 2026,
        "license_file": "LICENSE",
        "notice_file": "NOTICE",
        "scope": "project_authored_public_repository_material",
        "private_human_study_material_auto_released": False,
        "third_party_terms_preserved": True,
        "trademark_rights_granted": False,
        "cross_competition_lane_transfer": False,
        "issue_44": "closed_completed_2026-09-21",
    }
    for key, expected in required_license.items():
        if repository_license.get(key) != expected:
            errors.append(
                f"repository license continuity field {key!r} changed unexpectedly"
            )

    markdown_integrity = governance.get("markdown_link_integrity") or {}
    if markdown_integrity.get("status") != "ci_and_reproducibility_guard":
        errors.append("Markdown-link integrity continuity status changed unexpectedly")
    if markdown_integrity.get("remote_url_checks") is not False:
        errors.append("Markdown-link guard unexpectedly claims remote URL checking")
    if markdown_integrity.get("local_target_existence") is not True:
        errors.append("Markdown-link local target existence guard unexpectedly disabled")
    if markdown_integrity.get("repository_escape_rejected") is not True:
        errors.append("Markdown-link repository-escape guard unexpectedly disabled")

    json_integrity = governance.get("json_integrity") or {}
    required_json_integrity = {
        "status": "ci_and_reproducibility_guard",
        "utf8_json_required": True,
        "duplicate_keys_rejected": True,
        "declared_draft_2020_12_schemas_meta_validated": True,
        "instance_semantics_delegated_to_specialized_validators": True,
    }
    for key, expected in required_json_integrity.items():
        if json_integrity.get(key) != expected:
            errors.append(
                f"repository JSON-integrity continuity field {key!r} changed unexpectedly"
            )

    license_preflight = governance.get("license_preflight_inventory") or {}
    if license_preflight.get("status") != "clear_owner_decision_applied_not_legal_clearance":
        errors.append("license preflight inventory status changed unexpectedly")
    if license_preflight.get("inventory_version") != "third-party-inventory-v0.2":
        errors.append("third-party inventory version changed unexpectedly")
    if license_preflight.get("direct_dependency_and_action_drift_check") is not True:
        errors.append("license preflight drift check unexpectedly disabled")
    if license_preflight.get("current_preflight_clear") is not True:
        errors.append("license preflight clear-state continuity unexpectedly changed")

    open_governance_gates = state.get("open_project_governance_gates") or []
    if "explicit_repository_license_selection" in open_governance_gates:
        errors.append("resolved repository-license gate is still marked open")

    gates = state.get("claim_gates") or {}
    protected = {
        "human_productivity": "unproven",
        "human_audit_accuracy_advantage": "unproven",
        "real_world_safety": "unproven",
        "legal_compliance": "not_claimed",
        "standards_conformance": "not_claimed",
        "production_signing": "not_claimed",
        "customer_demand": "unproven",
        "institutional_endorsement": "not_claimed",
    }
    for key, value in protected.items():
        if gates.get(key) != value:
            errors.append(
                f"claim gate {key!r} changed without an explicit continuity update"
            )

    boundaries = state.get("cross_project_boundaries") or {}
    if boundaries.get("arc_agi_2") != "separate_lane":
        errors.append("ARC-AGI-2 boundary must remain separate")
    if boundaries.get("julia_dgap_meta_anchor") != "separate_lane":
        errors.append("Julia/DGAP/meta-anchor boundary must remain separate")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "Continuity guard passed: frozen AR-P003 history, current profile status, "
        "claim gates, and cross-project boundaries are internally consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
