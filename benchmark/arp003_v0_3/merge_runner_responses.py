#!/usr/bin/env python3
"""Merge reviewer-side offline-runner exports with hidden analysis labels.

Gold labels/strata stay outside the browser runner. Reviewer-reported condition
labels are not trusted by themselves: the response is bound to the exact frozen
assignment file and checked against that assignment before scorer input is
created.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
RUNNER_RESPONSE_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "runner-response.schema.json"
ANALYSIS_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "runner-analysis.schema.json"
SCORING_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "response-record.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def errors_for(doc: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in validator.iter_errors(doc)]


def expected_rows_for_reviewer(
    assignment: dict[str, Any],
    reviewer_id: str,
) -> list[dict[str, Any]]:
    version = assignment.get("assignment_version")
    if not isinstance(version, str) or not version:
        raise ValueError("assignment file has no valid assignment_version")

    rows = assignment.get("assignments")
    if not isinstance(rows, list) or not rows:
        raise ValueError("assignment file has no non-empty assignments list")

    selected: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("assignment rows must be objects")
        if row.get("reviewer_id") == reviewer_id:
            selected.append(row)

    if not selected:
        raise ValueError(
            f"reviewer {reviewer_id!r} is not present in the assignment file"
        )

    orders: set[int] = set()
    cases: set[str] = set()
    for row in selected:
        order = row.get("order")
        case_id = row.get("case_id")
        condition = row.get("condition")
        stratum = row.get("stratum")

        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise ValueError(
                f"assignment row for reviewer {reviewer_id!r} has invalid order"
            )
        if order in orders:
            raise ValueError(
                f"assignment duplicates order {order} for reviewer {reviewer_id!r}"
            )
        orders.add(order)

        if not isinstance(case_id, str) or not case_id:
            raise ValueError("assignment row has invalid case_id")
        if case_id in cases:
            raise ValueError(
                f"assignment repeats case {case_id!r} for reviewer {reviewer_id!r}"
            )
        cases.add(case_id)

        if condition not in {"raw", "structured", "receipt"}:
            raise ValueError(
                f"assignment condition for case {case_id!r} is invalid"
            )
        if not isinstance(stratum, str) or not stratum:
            raise ValueError(
                f"assignment stratum for case {case_id!r} is invalid"
            )

    return sorted(selected, key=lambda row: row["order"])


def merge(
    response: dict[str, Any],
    analysis: dict[str, Any],
    assignment: dict[str, Any],
    *,
    assignment_sha256: str,
    timing: str,
) -> list[dict[str, Any]]:
    if response["session_completed_at"] is None:
        raise ValueError("response export is incomplete; session_completed_at is null")

    comprehension = response.get("comprehension")
    if not isinstance(comprehension, dict):
        raise ValueError("response export has no comprehension-gate record")
    if comprehension.get("gate_version") != "AR-P003-v0.3-comprehension-v0.1":
        raise ValueError("response comprehension gate version is unsupported")
    attempts = comprehension.get("attempts")
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
        raise ValueError("response comprehension gate was not passed")

    practice = response.get("practice")
    if not isinstance(practice, dict):
        raise ValueError("response export has no practice-gate record")
    if practice.get("practice_version") != "AR-P003-v0.3-practice-v0.1":
        raise ValueError("response practice gate version is unsupported")
    practice_attempts = practice.get("attempts")
    if (
        not isinstance(practice_attempts, int)
        or isinstance(practice_attempts, bool)
        or practice_attempts < 1
    ):
        raise ValueError("response practice gate was not passed")

    if response["protocol_version"] != analysis["protocol_version"]:
        raise ValueError("response and analysis protocol_version values differ")
    if response.get("comparison_design") != "three_condition_structured_control":
        raise ValueError("response comparison_design is unsupported")
    if analysis.get("comparison_design") != "three_condition_structured_control":
        raise ValueError("analysis comparison_design is unsupported")
    if analysis.get("challenge_design") != "integrated_challenge_strata":
        raise ValueError("analysis challenge_design is unsupported")

    assignment_version = assignment.get("assignment_version")
    if response["assignment_version"] != assignment_version:
        raise ValueError(
            "response assignment_version does not match the assignment file"
        )
    if response["assignment_sha256"] != assignment_sha256:
        raise ValueError(
            "response assignment_sha256 does not match the exact assignment file"
        )

    expected = expected_rows_for_reviewer(assignment, response["reviewer_id"])

    response_cases = response["cases"]
    if len(response_cases) != len(expected):
        raise ValueError(
            "response case count does not match the reviewer's frozen assignment"
        )

    analysis_by_id: dict[str, dict[str, Any]] = {}
    for item in analysis["cases"]:
        case_id = item["case_id"]
        if case_id in analysis_by_id:
            raise ValueError(f"analysis bundle duplicates case_id {case_id!r}")
        analysis_by_id[case_id] = item

    timing_key = (
        "elapsed_active_seconds"
        if timing == "active"
        else "elapsed_wall_seconds"
    )
    records: list[dict[str, Any]] = []

    for position, (item, expected_row) in enumerate(
        zip(response_cases, expected, strict=True),
        start=1,
    ):
        case_id = item["case_id"]
        expected_case_id = expected_row["case_id"]
        if case_id != expected_case_id:
            raise ValueError(
                f"response case/order mismatch at position {position}: "
                f"expected {expected_case_id!r}, got {case_id!r}"
            )

        expected_condition = expected_row["condition"]
        if item["condition"] != expected_condition:
            raise ValueError(
                f"response condition mismatch for case {case_id!r}: "
                f"expected {expected_condition!r}, got {item['condition']!r}"
            )

        hidden = analysis_by_id.get(case_id)
        if hidden is None:
            raise ValueError(
                f"response case {case_id!r} has no hidden analysis record"
            )
        if hidden["stratum"] != expected_row["stratum"]:
            raise ValueError(
                f"hidden analysis stratum for case {case_id!r} does not match "
                "the frozen assignment"
            )

        records.append(
            {
                "reviewer_id": response["reviewer_id"],
                "case_id": case_id,
                "condition": expected_condition,
                "stratum": hidden["stratum"],
                "elapsed_seconds": item[timing_key],
                "gold": hidden["gold"],
                "answer": item["answer"],
            }
        )

    return records


def run_self_test() -> int:
    response_schema = load_json(RUNNER_RESPONSE_SCHEMA)
    analysis_schema = load_json(ANALYSIS_SCHEMA)
    scoring_schema = load_json(SCORING_SCHEMA)
    for schema in (response_schema, analysis_schema, scoring_schema):
        Draft202012Validator.check_schema(schema)

    reconstruction = {
        "material_actions": ["analyze"],
        "authorization_violation": False,
        "material_sources": ["source-1"],
        "incidents": [],
        "verification_state": "not_required",
        "missing_evidence": False,
    }

    assignment = {
        "assignment_version": "AR-P003-v0.3-draft-assignment-v0.3",
        "assignments": [
            {
                "reviewer_id": "dev-reviewer-001",
                "case_id": "DEV-RUNNER-001",
                "stratum": "ordinary",
                "order": 1,
                "condition": "raw",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmp:
        assignment_path = Path(tmp) / "assignment.json"
        assignment_path.write_text(
            json.dumps(assignment, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assignment_digest = sha256_file(assignment_path)

        response = {
            "response_bundle_version": "AR-P003-v0.3-dev-runner-response-v0.5",
            "protocol_version": "v0.3-draft-2026-09-20-three-condition-v0.1",
            "comparison_design": "three_condition_structured_control",
            "assignment_version": assignment["assignment_version"],
            "assignment_sha256": assignment_digest,
            "reviewer_id": "dev-reviewer-001",
            "session_started_at": "2026-09-18T12:00:00Z",
            "session_completed_at": "2026-09-18T12:02:00Z",
            "comprehension": {
                "gate_version": "AR-P003-v0.3-comprehension-v0.1",
                "attempts": 1,
                "passed_at": "2026-09-18T11:59:00Z",
            },
            "practice": {
                "practice_version": "AR-P003-v0.3-practice-v0.1",
                "attempts": 1,
                "passed_at": "2026-09-18T12:00:00Z",
            },
            "cases": [
                {
                    "case_id": "DEV-RUNNER-001",
                    "condition": "raw",
                    "started_at": "2026-09-18T12:00:00Z",
                    "submitted_at": "2026-09-18T12:01:00Z",
                    "elapsed_wall_seconds": 60.0,
                    "elapsed_active_seconds": 55.0,
                    "events": [],
                    "technical_issue": False,
                    "answer": {**reconstruction, "confidence": 4},
                }
            ],
        }
        analysis = {
            "analysis_bundle_version": "AR-P003-v0.3-dev-runner-analysis-v0.3",
            "protocol_version": "v0.3-draft-2026-09-20-three-condition-v0.1",
            "comparison_design": "three_condition_structured_control",
            "challenge_design": "integrated_challenge_strata",
            "cases": [
                {
                    "case_id": "DEV-RUNNER-001",
                    "stratum": "ordinary",
                    "gold": reconstruction,
                }
            ],
        }

        assert not errors_for(response, response_schema)
        assert not errors_for(analysis, analysis_schema)

        active = merge(
            response,
            analysis,
            assignment,
            assignment_sha256=assignment_digest,
            timing="active",
        )
        wall = merge(
            response,
            analysis,
            assignment,
            assignment_sha256=assignment_digest,
            timing="wall",
        )
        assert active[0]["elapsed_seconds"] == 55.0
        assert wall[0]["elapsed_seconds"] == 60.0
        assert active[0]["stratum"] == "ordinary"
        assert not errors_for(active[0], scoring_schema)

        missing_comprehension = json.loads(json.dumps(response))
        missing_comprehension.pop("comprehension")
        try:
            merge(
                missing_comprehension,
                analysis,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "comprehension-gate" in str(exc)
        else:
            raise AssertionError("response without comprehension evidence was accepted")

        missing_practice = json.loads(json.dumps(response))
        missing_practice.pop("practice")
        try:
            merge(
                missing_practice,
                analysis,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "practice-gate" in str(exc)
        else:
            raise AssertionError("response without practice evidence was accepted")

        bad_condition = json.loads(json.dumps(response))
        bad_condition["cases"][0]["condition"] = "receipt"
        try:
            merge(
                bad_condition,
                analysis,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "condition mismatch" in str(exc)
        else:
            raise AssertionError("tampered response condition was accepted")

        bad_hash = json.loads(json.dumps(response))
        bad_hash["assignment_sha256"] = "sha256:" + "0" * 64
        try:
            merge(
                bad_hash,
                analysis,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "assignment_sha256" in str(exc)
        else:
            raise AssertionError("wrong assignment hash was accepted")

        incomplete = json.loads(json.dumps(response))
        incomplete["session_completed_at"] = None
        try:
            merge(
                incomplete,
                analysis,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "incomplete" in str(exc)
        else:
            raise AssertionError("incomplete session was accepted for scoring")

        reordered = json.loads(json.dumps(response))
        reordered["cases"][0]["case_id"] = "OTHER"
        try:
            merge(
                reordered,
                analysis,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "case/order mismatch" in str(exc)
        else:
            raise AssertionError("wrong assigned case was accepted")

        bad_protocol = dict(analysis)
        bad_protocol["protocol_version"] = "other"
        try:
            merge(
                response,
                bad_protocol,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "protocol_version" in str(exc)
        else:
            raise AssertionError("protocol mismatch was accepted")

        missing_case = {**analysis, "cases": []}
        try:
            merge(
                response,
                missing_case,
                assignment,
                assignment_sha256=assignment_digest,
                timing="active",
            )
        except ValueError as exc:
            assert "no hidden analysis record" in str(exc)
        else:
            raise AssertionError("missing hidden case was accepted")

    print(
        "AR-P003 runner merge self-test passed: exact assignment binding, "
        "condition/order integrity, and hidden-label separation are enforced."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Join AR-P003 offline-runner responses to hidden analysis labels "
            "while checking the exact frozen assignment."
        )
    )
    parser.add_argument("responses", nargs="?", help="Runner response JSON export")
    parser.add_argument("analysis", nargs="?", help="Hidden analysis JSON bundle")
    parser.add_argument("assignment", nargs="?", help="Exact frozen assignment JSON")
    parser.add_argument(
        "--timing",
        choices=["active", "wall"],
        help="Explicit timing field to map into scorer elapsed_seconds.",
    )
    parser.add_argument("--output", help="Output JSONL path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            return run_self_test()

        if (
            not args.responses
            or not args.analysis
            or not args.assignment
            or not args.timing
        ):
            parser.error(
                "provide responses, analysis, assignment, and "
                "--timing active|wall, or use --self-test"
            )

        response_schema = load_json(RUNNER_RESPONSE_SCHEMA)
        analysis_schema = load_json(ANALYSIS_SCHEMA)
        scoring_schema = load_json(SCORING_SCHEMA)
        for schema in (response_schema, analysis_schema, scoring_schema):
            Draft202012Validator.check_schema(schema)

        response = load_json(Path(args.responses))
        analysis = load_json(Path(args.analysis))
        assignment_path = Path(args.assignment)
        assignment = load_json(assignment_path)

        response_errors = errors_for(response, response_schema)
        analysis_errors = errors_for(analysis, analysis_schema)
        if response_errors or analysis_errors:
            for error in response_errors:
                print(f"ERROR response: {error}", file=sys.stderr)
            for error in analysis_errors:
                print(f"ERROR analysis: {error}", file=sys.stderr)
            return 1

        records = merge(
            response,
            analysis,
            assignment,
            assignment_sha256=sha256_file(assignment_path),
            timing=args.timing,
        )
        for index, record in enumerate(records):
            record_errors = errors_for(record, scoring_schema)
            if record_errors:
                for error in record_errors:
                    print(
                        f"ERROR merged record {index}: {error}",
                        file=sys.stderr,
                    )
                return 1

        rendered = "".join(
            json.dumps(record, sort_keys=True) + "\n" for record in records
        )
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, json.JSONDecodeError, SchemaError, ValueError) as exc:
        print(f"ERROR: runner response merge failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
