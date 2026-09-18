#!/usr/bin/env python3
"""Merge reviewer-side offline-runner exports with hidden analysis labels.

Gold labels/strata stay outside the browser runner. This utility performs the
analysis-side join and writes JSONL records accepted by score_responses.py.
"""

from __future__ import annotations

import argparse
import json
import sys
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


def errors_for(doc: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in validator.iter_errors(doc)]


def merge(
    response: dict[str, Any],
    analysis: dict[str, Any],
    *,
    timing: str,
) -> list[dict[str, Any]]:
    if response["protocol_version"] != analysis["protocol_version"]:
        raise ValueError("response and analysis protocol_version values differ")

    analysis_by_id: dict[str, dict[str, Any]] = {}
    for item in analysis["cases"]:
        case_id = item["case_id"]
        if case_id in analysis_by_id:
            raise ValueError(f"analysis bundle duplicates case_id {case_id!r}")
        analysis_by_id[case_id] = item

    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    timing_key = (
        "elapsed_active_seconds"
        if timing == "active"
        else "elapsed_wall_seconds"
    )

    for item in response["cases"]:
        case_id = item["case_id"]
        if case_id in seen:
            raise ValueError(f"response export duplicates case_id {case_id!r}")
        seen.add(case_id)

        hidden = analysis_by_id.get(case_id)
        if hidden is None:
            raise ValueError(
                f"response case {case_id!r} has no hidden analysis record"
            )

        records.append(
            {
                "reviewer_id": response["reviewer_id"],
                "case_id": case_id,
                "condition": item["condition"],
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
    response = {
        "response_bundle_version": "AR-P003-v0.3-dev-runner-response-v0.1",
        "protocol_version": "v0.3-development-only",
        "reviewer_id": "dev-reviewer-001",
        "session_started_at": "2026-09-18T12:00:00Z",
        "session_completed_at": "2026-09-18T12:02:00Z",
        "cases": [
            {
                "case_id": "DEV-RUNNER-001",
                "condition": "control",
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
        "analysis_bundle_version": "AR-P003-v0.3-dev-runner-analysis-v0.1",
        "protocol_version": "v0.3-development-only",
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

    active = merge(response, analysis, timing="active")
    wall = merge(response, analysis, timing="wall")
    assert active[0]["elapsed_seconds"] == 55.0
    assert wall[0]["elapsed_seconds"] == 60.0
    assert active[0]["stratum"] == "ordinary"
    assert not errors_for(active[0], scoring_schema)

    bad_protocol = dict(analysis)
    bad_protocol["protocol_version"] = "other"
    try:
        merge(response, bad_protocol, timing="active")
    except ValueError as exc:
        assert "protocol_version" in str(exc)
    else:
        raise AssertionError("protocol mismatch was accepted")

    missing_case = {**analysis, "cases": []}
    try:
        merge(response, missing_case, timing="active")
    except ValueError as exc:
        assert "no hidden analysis record" in str(exc)
    else:
        raise AssertionError("missing hidden case was accepted")

    print(
        "AR-P003 runner merge self-test passed: hidden analysis labels remain "
        "separate until scoring-side join."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Join AR-P003 offline-runner responses to hidden analysis labels."
    )
    parser.add_argument("responses", nargs="?", help="Runner response JSON export")
    parser.add_argument("analysis", nargs="?", help="Hidden analysis JSON bundle")
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

        if not args.responses or not args.analysis or not args.timing:
            parser.error(
                "provide responses, analysis, and --timing active|wall, "
                "or use --self-test"
            )

        response_schema = load_json(RUNNER_RESPONSE_SCHEMA)
        analysis_schema = load_json(ANALYSIS_SCHEMA)
        scoring_schema = load_json(SCORING_SCHEMA)
        for schema in (response_schema, analysis_schema, scoring_schema):
            Draft202012Validator.check_schema(schema)

        response = load_json(Path(args.responses))
        analysis = load_json(Path(args.analysis))

        response_errors = errors_for(response, response_schema)
        analysis_errors = errors_for(analysis, analysis_schema)
        if response_errors or analysis_errors:
            for error in response_errors:
                print(f"ERROR response: {error}", file=sys.stderr)
            for error in analysis_errors:
                print(f"ERROR analysis: {error}", file=sys.stderr)
            return 1

        records = merge(response, analysis, timing=args.timing)
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
