#!/usr/bin/env python3
"""Continuity guard for cross-source project state.

This is intentionally narrow: it protects a few high-risk continuity facts from
silent drift between historical benchmark evidence, current research profiles,
and public claim boundaries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research" / "project-continuity-state.json"
EXPECTED_FREEZE = (
    "8a381f4ae20a5f6824e513c7f96920fdf3cfe6b00b0b8d301127f5e0b659d0fd"
)


def main() -> int:
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load continuity state: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

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
    required_methodology_unresolved = {
        "comparison_conditions",
        "primary_endpoint",
        "primary_timing_clock",
        "challenge_design",
        "reviewer_population",
        "effect_precision_target",
    }
    for decision_id in required_methodology_unresolved:
        if methodology.get(decision_id) != "unresolved":
            errors.append(
                f"AR-P003 methodology decision {decision_id!r} changed without "
                "a deliberate continuity update"
            )

    runner = (arp003.get("offline_runner") or {})
    assignment_binding = runner.get("assignment_binding") or {}
    if assignment_binding.get("exact_assignment_sha256") is not True:
        errors.append("AR-P003 exact assignment binding unexpectedly disabled")
    if assignment_binding.get("condition_order_case_verification") is not True:
        errors.append("AR-P003 assignment case/order/condition verification unexpectedly disabled")
    if assignment_binding.get("incomplete_session_rejected") is not True:
        errors.append("AR-P003 incomplete-session scoring guard unexpectedly disabled")

    repro = dev.get("reproducibility_runner") or {}
    if repro.get("suite_version") != "ai-activity-receipt-repro-v0.8":
        errors.append("reproducibility suite version unexpectedly changed")
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
    if security.get("main_ruleset") != "not_configured_detected_via_api":
        errors.append(
            "main ruleset status changed; update continuity deliberately after "
            "repository-admin verification"
        )
    if (dev.get("reproducibility_runner") or {}).get("external_reproduction_handoff") is not True:
        errors.append("external reproduction handoff continuity flag unexpectedly changed")

    if governance.get("explicit_license_status") != "not_selected":
        errors.append(
            "repository license status changed; update continuity deliberately "
            "before changing public licensing claims"
        )

    license_preflight = governance.get("license_preflight_inventory") or {}
    if license_preflight.get("status") != "prepared_not_legal_clearance":
        errors.append("license preflight inventory status changed unexpectedly")
    if license_preflight.get("inventory_version") != "third-party-inventory-v0.1":
        errors.append("third-party inventory version changed unexpectedly")
    if license_preflight.get("direct_dependency_and_action_drift_check") is not True:
        errors.append("license preflight drift check unexpectedly disabled")

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
