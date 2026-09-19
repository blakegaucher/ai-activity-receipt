#!/usr/bin/env python3
"""Heuristic pre-freeze leakage/presentation audit for AR-P003 v0.3.

This tool operates analysis-side on generated development reviewer bundles plus
hidden gold labels. It reports obvious literal-label leakage, answer-option
degeneracy, presentation asymmetry, and reviewer-evidence drift.

It is deliberately conservative and heuristic. Passing it is not proof that a
case is free of semantic clues, framing effects, or other human-study bias.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark" / "arp003_v0_3"
REPORT_SCHEMA = BENCH / "leakage-audit.schema.json"

AUDIT_VERSION = "AR-P003-v0.3-leakage-audit-v0.1"
PRESENTATION_EXPANSION_RATIO_REVIEW = 1.75


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized_text(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return " ".join(tokens)


def literal_mentions(labels: list[str], evidence_text: str) -> list[str]:
    haystack = " " + normalized_text(evidence_text) + " "
    hits: list[str] = []
    for label in labels:
        needle = normalized_text(label)
        if len(needle.replace(" ", "")) < 4:
            continue
        if f" {needle} " in haystack:
            hits.append(label)
    return sorted(set(hits))


def reviewer_visible_evidence(case: dict[str, Any]) -> tuple[str, int]:
    parts: list[str] = []
    chars = 0
    for artifact in case["evidence"]:
        label = str(artifact["label"])
        content = str(artifact["content"])
        parts.extend([label, content])
        chars += len(label) + len(content)
    return "\n".join(parts), chars


def receipt_chars(case: dict[str, Any]) -> int:
    receipt = case.get("receipt")
    if not isinstance(receipt, dict):
        return 0
    return len(str(receipt["label"])) + len(str(receipt["content"]))


def canonical_evidence_blob(case: dict[str, Any]) -> bytes:
    normalized = [
        {
            "label": artifact["label"],
            "media_type": artifact["media_type"],
            "content": artifact["content"],
        }
        for artifact in case["evidence"]
    ]
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def index_gold(analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in analysis["cases"]:
        case_id = item["case_id"]
        if case_id in result:
            raise ValueError(f"hidden analysis duplicates case_id {case_id!r}")
        result[case_id] = item
    return result


def audit_build(build_dir: Path) -> dict[str, Any]:
    manifest_path = build_dir / "build-manifest.json"
    manifest = load_json(manifest_path)

    hidden_rel = manifest["hidden_analysis"]["path"]
    hidden_path = build_dir / hidden_rel
    analysis = load_json(hidden_path)
    gold_by_id = index_gold(analysis)

    option_audits = {
        item["case_id"]: item
        for item in manifest.get("answer_option_audit") or []
    }

    presentations: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for summary in manifest["reviewer_bundles"]:
        bundle_path = build_dir / summary["path"]
        bundle = load_json(bundle_path)
        for case in bundle["cases"]:
            condition = "receipt" if case.get("receipt") is not None else "control"
            presentations.setdefault(case["case_id"], []).append((condition, case))

    cases_out: list[dict[str, Any]] = []
    high_risk_count = 0

    for case_id in sorted(gold_by_id):
        hidden = gold_by_id[case_id]
        gold = hidden["gold"]
        rows = presentations.get(case_id) or []
        if not rows:
            raise ValueError(f"case {case_id!r} has hidden gold but no reviewer presentation")

        evidence_hashes = {
            sha256_bytes(canonical_evidence_blob(case))
            for _, case in rows
        }
        if len(evidence_hashes) != 1:
            raise ValueError(
                f"case {case_id!r} reviewer evidence differs across presentations"
            )

        evidence_text, evidence_char_count = reviewer_visible_evidence(rows[0][1])
        receipt_sizes = [receipt_chars(case) for _, case in rows if case.get("receipt") is not None]
        receipt_char_count = max(receipt_sizes) if receipt_sizes else 0

        if evidence_char_count == 0:
            ratio = 1.0 if receipt_char_count == 0 else float("inf")
        else:
            ratio = (evidence_char_count + receipt_char_count) / evidence_char_count

        mentions = {
            endpoint: literal_mentions(list(gold[endpoint]), evidence_text)
            for endpoint in ("material_actions", "material_sources", "incidents")
        }

        audit = option_audits.get(case_id)
        if not isinstance(audit, dict):
            raise ValueError(f"case {case_id!r} has no answer_option_audit entry")

        high_risk: list[str] = []
        review: list[str] = []

        if mentions["incidents"]:
            high_risk.append("literal_gold_incident_label_in_control_evidence")

        for endpoint in ("material_actions", "material_sources", "incidents"):
            endpoint_audit = audit.get(endpoint) or {}
            if (
                endpoint_audit.get("n_options", 0) > 0
                and endpoint_audit.get("option_set_equals_gold_set") is True
            ):
                high_risk.append(f"{endpoint}_options_equal_gold_set")

        if ratio > PRESENTATION_EXPANSION_RATIO_REVIEW:
            review.append("large_receipt_presentation_expansion")

        if mentions["material_actions"]:
            review.append("literal_gold_action_label_present")
        if mentions["material_sources"]:
            review.append("literal_gold_source_label_present")

        conditions = sorted({condition for condition, _ in rows})
        if conditions != ["control", "receipt"]:
            review.append("case_not_observed_in_both_conditions")

        if high_risk:
            high_risk_count += 1

        cases_out.append(
            {
                "case_id": case_id,
                "stratum": hidden["stratum"],
                "conditions_present": conditions,
                "n_presentations": len(rows),
                "evidence_sha256": next(iter(evidence_hashes)),
                "evidence_chars": evidence_char_count,
                "receipt_chars": receipt_char_count,
                "presentation_expansion_ratio": round(ratio, 6),
                "answer_option_audit": {
                    endpoint: audit[endpoint]
                    for endpoint in ("material_actions", "material_sources", "incidents")
                },
                "literal_gold_mentions": mentions,
                "high_risk_flags": sorted(set(high_risk)),
                "review_flags": sorted(set(review)),
            }
        )

    return {
        "audit_version": AUDIT_VERSION,
        "status": "development_audit",
        "build_manifest_sha256": sha256_file(manifest_path),
        "analysis_sha256": sha256_file(hidden_path),
        "n_cases": len(cases_out),
        "n_high_risk_cases": high_risk_count,
        "requires_human_review": any(
            item["high_risk_flags"] or item["review_flags"] for item in cases_out
        ),
        "thresholds": {
            "presentation_expansion_ratio_review": PRESENTATION_EXPANSION_RATIO_REVIEW
        },
        "cases": cases_out,
        "evidence_boundary": (
            "Heuristic development audit only. Absence of flags does not prove "
            "absence of semantic leakage, framing effects, realism problems, or "
            "other human-study bias."
        ),
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def make_self_test_build(root: Path) -> Path:
    build = root / "built"
    (build / "reviewer_bundles").mkdir(parents=True)
    (build / "analysis").mkdir()

    control_case = {
        "case_id": "case-1",
        "evidence": [
            {
                "label": "Synthetic event log",
                "media_type": "text/plain",
                "content": (
                    "The agent performed analysis on source-A. "
                    "Incident classification: authorization_violation."
                ),
            }
        ],
        "receipt": None,
        "answer_options": {
            "material_actions": ["analyze", "send_email"],
            "material_sources": ["source-A", "source-B"],
            "incidents": ["authorization_violation", "tool_failure"],
        },
    }
    receipt_case = json.loads(json.dumps(control_case))
    receipt_case["receipt"] = {
        "label": "Activity Receipt",
        "media_type": "application/json",
        "content": json.dumps(
            {
                "material_actions": [{"operation": "analyze"}],
                "incidents": [{"type": "authorization_violation"}],
            },
            indent=2,
        ),
    }

    for reviewer, case in (("R1", control_case), ("R2", receipt_case)):
        write_json(
            build / "reviewer_bundles" / f"{reviewer}.json",
            {
                "bundle_version": "self-test",
                "protocol_version": "self-test",
                "reviewer_id": reviewer,
                "cases": [case],
            },
        )

    gold = {
        "material_actions": ["analyze"],
        "authorization_violation": True,
        "material_sources": ["source-A"],
        "incidents": ["authorization_violation"],
        "verification_state": "confirmed",
        "missing_evidence": False,
    }
    write_json(
        build / "analysis" / "runner-analysis.json",
        {
            "analysis_bundle_version": "self-test",
            "protocol_version": "self-test",
            "cases": [
                {
                    "case_id": "case-1",
                    "stratum": "ordinary",
                    "gold": gold,
                }
            ],
        },
    )

    manifest = {
        "build_output_version": "self-test",
        "hidden_analysis": {
            "path": "analysis/runner-analysis.json",
        },
        "reviewer_bundles": [
            {"reviewer_id": "R1", "path": "reviewer_bundles/R1.json"},
            {"reviewer_id": "R2", "path": "reviewer_bundles/R2.json"},
        ],
        "answer_option_audit": [
            {
                "case_id": "case-1",
                "material_actions": {
                    "n_gold": 1,
                    "n_options": 2,
                    "n_non_gold_options": 1,
                    "option_set_equals_gold_set": False,
                    "gold_representable": True,
                },
                "material_sources": {
                    "n_gold": 1,
                    "n_options": 2,
                    "n_non_gold_options": 1,
                    "option_set_equals_gold_set": False,
                    "gold_representable": True,
                },
                "incidents": {
                    "n_gold": 1,
                    "n_options": 2,
                    "n_non_gold_options": 1,
                    "option_set_equals_gold_set": False,
                    "gold_representable": True,
                },
            }
        ],
    }
    write_json(build / "build-manifest.json", manifest)
    return build


def run_self_test() -> int:
    schema = load_json(REPORT_SCHEMA)
    Draft202012Validator.check_schema(schema)

    with tempfile.TemporaryDirectory() as tmp:
        build = make_self_test_build(Path(tmp))
        report = audit_build(build)
        errors = list(Draft202012Validator(schema).iter_errors(report))
        assert not errors, [error.message for error in errors]
        assert report["n_cases"] == 1
        assert report["n_high_risk_cases"] == 1
        case = report["cases"][0]
        assert "authorization_violation" in case["literal_gold_mentions"]["incidents"]
        assert (
            "literal_gold_incident_label_in_control_evidence"
            in case["high_risk_flags"]
        )
        assert "literal_gold_action_label_present" in case["review_flags"]
        assert "literal_gold_source_label_present" in case["review_flags"]
        assert case["conditions_present"] == ["control", "receipt"]

        drift = load_json(build / "reviewer_bundles" / "R2.json")
        drift["cases"][0]["evidence"][0]["content"] += " changed"
        write_json(build / "reviewer_bundles" / "R2.json", drift)
        try:
            audit_build(build)
        except ValueError as exc:
            assert "reviewer evidence differs" in str(exc)
        else:
            raise AssertionError("reviewer-evidence drift was accepted")

    print(
        "AR-P003 leakage-audit self-test passed: literal incident leakage was "
        "flagged and cross-presentation evidence drift was rejected."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit AR-P003 development build output for obvious leakage/asymmetry."
    )
    parser.add_argument(
        "build_dir",
        nargs="?",
        help="Directory containing build-manifest.json and generated bundles.",
    )
    parser.add_argument("--output", help="Optional JSON report path.")
    parser.add_argument(
        "--fail-on-high-risk",
        action="store_true",
        help="Exit non-zero when one or more high-risk flags are present.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            return run_self_test()
        if not args.build_dir:
            parser.error("provide build_dir or use --self-test")
        report = audit_build(Path(args.build_dir))
        schema = load_json(REPORT_SCHEMA)
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(report))
        if errors:
            for error in errors:
                print(f"ERROR: {error.message}", file=sys.stderr)
            return 2
    except (OSError, json.JSONDecodeError, SchemaError, ValueError, AssertionError) as exc:
        print(f"ERROR: leakage audit failed: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    if args.fail_on_high_risk and report["n_high_risk_cases"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
