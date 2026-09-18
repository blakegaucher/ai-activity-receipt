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
