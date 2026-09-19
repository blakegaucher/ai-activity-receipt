#!/usr/bin/env python3
"""Validate AR-P003 v0.3 manual methodology-review records.

A completed review must bind to one exact leakage-audit report and its build
manifest hash, cover exactly the same case IDs, contain no unresolved automated
high-risk flags, and mark every reviewed case acceptable across the declared
manual dimensions.

This is development QA, not human-study outcome evidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark" / "arp003_v0_3"
SCHEMA = BENCH / "case-methodology-review.schema.json"
EXAMPLE = BENCH / "case-methodology-review.example.json"
LEAKAGE_SCHEMA = BENCH / "leakage-audit.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def structural_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def semantic_errors(
    review: dict[str, Any],
    leakage: dict[str, Any],
    *,
    leakage_sha256: str,
) -> list[str]:
    errors: list[str] = []

    if review["corpus_build_sha256"] != leakage["build_manifest_sha256"]:
        errors.append(
            "corpus_build_sha256 does not match leakage-audit build_manifest_sha256"
        )
    if review["leakage_audit_sha256"] != leakage_sha256:
        errors.append(
            "leakage_audit_sha256 does not match the supplied leakage-audit file"
        )

    review_cases = review["cases"]
    review_ids = [item["case_id"] for item in review_cases]
    if len(review_ids) != len(set(review_ids)):
        errors.append("manual review contains duplicate case_id values")

    leakage_ids = [item["case_id"] for item in leakage["cases"]]
    if review["status"] == "complete":
        if set(review_ids) != set(leakage_ids):
            missing = sorted(set(leakage_ids) - set(review_ids))
            extra = sorted(set(review_ids) - set(leakage_ids))
            errors.append(
                "complete manual review must cover exactly the leakage-audit cases; "
                f"missing={missing!r}, extra={extra!r}"
            )

        if review["reviewed_at"] is None:
            errors.append("complete manual review requires reviewed_at")

        high_risk = [
            item["case_id"]
            for item in leakage["cases"]
            if item["high_risk_flags"]
        ]
        if high_risk:
            errors.append(
                "complete manual review cannot bind to an audit with unresolved "
                f"high-risk cases: {sorted(high_risk)!r}"
            )

        for index, item in enumerate(review_cases):
            required = {
                "semantic_leakage": "pass",
                "realism": "acceptable",
                "framing_neutrality": "acceptable",
                "answer_option_quality": "acceptable",
                "decision": "accept",
            }
            for field, expected in required.items():
                if item[field] != expected:
                    errors.append(
                        f"cases[{index}] {field} must be {expected!r} for a "
                        f"complete review, got {item[field]!r}"
                    )

    if review["status"] == "not_tested" and review["reviewed_at"] is not None:
        errors.append("not_tested review must not have reviewed_at")

    return errors


def validate(
    review: Any,
    review_schema: dict[str, Any],
    leakage: Any,
    leakage_schema: dict[str, Any],
    *,
    leakage_sha256: str,
) -> list[str]:
    errors = structural_errors(review, review_schema)
    if errors:
        return errors
    leakage_errors = structural_errors(leakage, leakage_schema)
    if leakage_errors:
        return [f"leakage audit invalid: {error}" for error in leakage_errors]
    if not isinstance(review, dict) or not isinstance(leakage, dict):
        return ["review and leakage audit must both be JSON objects"]
    return semantic_errors(review, leakage, leakage_sha256=leakage_sha256)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def clean_leakage() -> dict[str, Any]:
    return {
        "audit_version": "AR-P003-v0.3-leakage-audit-v0.1",
        "status": "development_audit",
        "build_manifest_sha256": "sha256:" + ("1" * 64),
        "analysis_sha256": "sha256:" + ("2" * 64),
        "n_cases": 1,
        "n_high_risk_cases": 0,
        "requires_human_review": True,
        "thresholds": {
            "presentation_expansion_ratio_review": 1.75
        },
        "cases": [
            {
                "case_id": "case-1",
                "stratum": "ordinary",
                "conditions_present": ["control", "receipt"],
                "n_presentations": 2,
                "evidence_sha256": "sha256:" + ("3" * 64),
                "evidence_chars": 300,
                "receipt_chars": 120,
                "presentation_expansion_ratio": 1.4,
                "answer_option_audit": {
                    "material_actions": {
                        "n_gold": 1,
                        "n_options": 3,
                        "n_non_gold_options": 2,
                        "option_set_equals_gold_set": False,
                        "gold_representable": True,
                    },
                    "material_sources": {
                        "n_gold": 1,
                        "n_options": 3,
                        "n_non_gold_options": 2,
                        "option_set_equals_gold_set": False,
                        "gold_representable": True,
                    },
                    "incidents": {
                        "n_gold": 0,
                        "n_options": 2,
                        "n_non_gold_options": 2,
                        "option_set_equals_gold_set": False,
                        "gold_representable": True,
                    },
                },
                "literal_gold_mentions": {
                    "material_actions": ["analyze"],
                    "material_sources": ["source-A"],
                    "incidents": [],
                },
                "high_risk_flags": [],
                "review_flags": [
                    "literal_gold_action_label_present",
                    "literal_gold_source_label_present",
                ],
            }
        ],
        "evidence_boundary": (
            "Synthetic self-test leakage report; no human-study claim."
        ),
    }


def complete_review(leakage_sha256: str) -> dict[str, Any]:
    return {
        "review_version": "AR-P003-v0.3-case-methodology-review-v0.1",
        "status": "complete",
        "corpus_build_sha256": "sha256:" + ("1" * 64),
        "leakage_audit_sha256": leakage_sha256,
        "reviewer_id": "synthetic-methodology-reviewer",
        "reviewed_at": "2026-09-19T12:00:00Z",
        "cases": [
            {
                "case_id": "case-1",
                "semantic_leakage": "pass",
                "realism": "acceptable",
                "framing_neutrality": "acceptable",
                "answer_option_quality": "acceptable",
                "decision": "accept",
                "notes": "Synthetic self-test review only.",
            }
        ],
        "evidence_boundary": (
            "Synthetic self-test review only; not participant data or human-study evidence."
        ),
    }


def run_self_test() -> int:
    review_schema = load_json(SCHEMA)
    leakage_schema = load_json(LEAKAGE_SCHEMA)
    Draft202012Validator.check_schema(review_schema)
    Draft202012Validator.check_schema(leakage_schema)

    template = load_json(EXAMPLE)
    template_structural = structural_errors(template, review_schema)
    assert not template_structural, template_structural
    assert template["status"] == "not_tested"

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        leakage_path = root / "leakage.json"
        leakage = clean_leakage()
        write_json(leakage_path, leakage)
        leakage_sha = sha256_file(leakage_path)

        review = complete_review(leakage_sha)
        errors = validate(
            review,
            review_schema,
            leakage,
            leakage_schema,
            leakage_sha256=leakage_sha,
        )
        assert not errors, errors

        bad_hash = copy.deepcopy(review)
        bad_hash["leakage_audit_sha256"] = "sha256:" + ("9" * 64)
        errors = validate(
            bad_hash,
            review_schema,
            leakage,
            leakage_schema,
            leakage_sha256=leakage_sha,
        )
        assert any("does not match the supplied leakage-audit file" in e for e in errors)

        missing_case = copy.deepcopy(review)
        missing_case["cases"] = []
        errors = validate(
            missing_case,
            review_schema,
            leakage,
            leakage_schema,
            leakage_sha256=leakage_sha,
        )
        assert any("must cover exactly" in e for e in errors)

        incomplete_dimension = copy.deepcopy(review)
        incomplete_dimension["cases"][0]["realism"] = "revise"
        errors = validate(
            incomplete_dimension,
            review_schema,
            leakage,
            leakage_schema,
            leakage_sha256=leakage_sha,
        )
        assert any("realism must be 'acceptable'" in e for e in errors)

        risky_leakage = copy.deepcopy(leakage)
        risky_leakage["n_high_risk_cases"] = 1
        risky_leakage["cases"][0]["high_risk_flags"] = [
            "literal_gold_incident_label_in_control_evidence"
        ]
        risky_path = root / "risky.json"
        write_json(risky_path, risky_leakage)
        risky_sha = sha256_file(risky_path)
        risky_review = complete_review(risky_sha)
        errors = validate(
            risky_review,
            review_schema,
            risky_leakage,
            leakage_schema,
            leakage_sha256=risky_sha,
        )
        assert any("unresolved high-risk cases" in e for e in errors)

    print(
        "AR-P003 case-methodology-review self-test passed: complete review "
        "requires exact audit binding, full case coverage, no unresolved "
        "high-risk leakage flags, and acceptable manual review dimensions."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate AR-P003 manual case methodology review."
    )
    parser.add_argument(
        "review",
        nargs="?",
        default=str(EXAMPLE),
        help="Case methodology review JSON file.",
    )
    parser.add_argument(
        "--leakage-audit",
        help="Leakage-audit JSON report that the review is bound to.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit non-zero unless the review status is complete.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            return run_self_test()

        review_schema = load_json(SCHEMA)
        leakage_schema = load_json(LEAKAGE_SCHEMA)
        Draft202012Validator.check_schema(review_schema)
        Draft202012Validator.check_schema(leakage_schema)
        review = load_json(Path(args.review))

        if not args.leakage_audit:
            if review.get("status") == "not_tested" and not args.require_complete:
                errors = structural_errors(review, review_schema)
                if errors:
                    for error in errors:
                        print(f"ERROR: {error}", file=sys.stderr)
                    return 1
                print(
                    "AR-P003 case methodology review template is structurally valid "
                    "and remains not_tested."
                )
                return 0
            parser.error("--leakage-audit is required for in_progress/complete review validation")

        leakage_path = Path(args.leakage_audit)
        leakage = load_json(leakage_path)
        errors = validate(
            review,
            review_schema,
            leakage,
            leakage_schema,
            leakage_sha256=sha256_file(leakage_path),
        )
    except (OSError, json.JSONDecodeError, SchemaError, AssertionError, ValueError) as exc:
        print(f"ERROR: case methodology review validation failed: {exc}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.require_complete and review["status"] != "complete":
        print(
            "ERROR: case methodology review is not complete.",
            file=sys.stderr,
        )
        return 1

    print(
        "AR-P003 case methodology review is internally valid: "
        f"status={review['status']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
