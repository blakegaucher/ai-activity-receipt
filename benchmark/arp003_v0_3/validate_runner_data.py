#!/usr/bin/env python3
"""Validate AR-P003 v0.3 development offline-runner bundles/exports.

The runner bundle is deliberately reviewer-facing only. Hidden gold labels,
challenge strata, and analysis-only metadata must not be embedded in it.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "runner-bundle.schema.json"
RESPONSE_SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "runner-response.schema.json"
EXAMPLE_BUNDLE = ROOT / "benchmark" / "arp003_v0_3" / "runner-bundle.example.json"
RUNNER_HTML = ROOT / "benchmark" / "arp003_v0_3" / "offline_runner.html"

PROHIBITED_REVIEWER_KEYS = {
    "gold",
    "gold_labels",
    "analysis_files",
    "analysis_only",
    "hidden_stratum",
    "stratum",
    "receipt_state",
    "expected_answer",
    "answer_key",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def structural_errors(doc: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(doc),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def prohibited_key_paths(value: Any, prefix: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{prefix}.{key}"
            if key in PROHIBITED_REVIEWER_KEYS:
                errors.append(current)
            errors.extend(prohibited_key_paths(item, current))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(prohibited_key_paths(item, f"{prefix}[{index}]"))
    return errors


def bundle_semantic_errors(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    case_ids = [case["case_id"] for case in doc["cases"]]
    if len(case_ids) != len(set(case_ids)):
        errors.append("case_id values must be unique within a runner bundle")

    prohibited = prohibited_key_paths(doc)
    if prohibited:
        errors.append(
            "reviewer-facing bundle contains prohibited analysis key(s): "
            + ", ".join(prohibited)
        )

    for index, case in enumerate(doc["cases"]):
        labels = [artifact["label"] for artifact in case["evidence"]]
        if len(labels) != len(set(labels)):
            errors.append(
                f"cases[{index}] evidence labels must be unique within the case"
            )

        receipt = case["receipt"]
        if receipt is not None and receipt["label"] in labels:
            errors.append(
                f"cases[{index}] receipt label duplicates an evidence label"
            )

    return errors


def validate_bundle(doc: Any, schema: dict[str, Any]) -> list[str]:
    errors = structural_errors(doc, schema)
    if errors:
        return errors
    if not isinstance(doc, dict):
        return ["$: runner bundle must be an object"]
    return bundle_semantic_errors(doc)


def validate_response(doc: Any, schema: dict[str, Any]) -> list[str]:
    errors = structural_errors(doc, schema)
    if errors:
        return errors
    if not isinstance(doc, dict):
        return ["$: runner response export must be an object"]

    case_ids = [case["case_id"] for case in doc["cases"]]
    if len(case_ids) != len(set(case_ids)):
        errors.append("response export contains duplicate case_id values")

    for index, case in enumerate(doc["cases"]):
        if case["elapsed_active_seconds"] > case["elapsed_wall_seconds"] + 0.01:
            errors.append(
                f"cases[{index}] active elapsed time exceeds wall elapsed time"
            )

    return errors


def runner_static_errors() -> list[str]:
    try:
        html = RUNNER_HTML.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unable to read offline runner: {exc}"]

    errors: list[str] = []
    required = [
        "default-src 'none'",
        "connect-src 'none'",
        "worker-src 'none'",
        "const MAX_BUNDLE_BYTES",
        "const MAX_CASES",
        "const MAX_ARTIFACT_CHARS",
        "file.size > MAX_BUNDLE_BYTES",
        'id="pauseBtn"',
        'id="downloadFinalBtn"',
        "visibilitychange",
        "beforeunload",
        "URL.createObjectURL",
        "textContent = artifact.content",
        "assignment_version: bundle.assignment_version",
        "assignment_sha256: bundle.assignment_sha256",
    ]
    for marker in required:
        if marker not in html:
            errors.append(f"offline runner missing required marker: {marker}")

    forbidden = [
        "<script src=",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "sendBeacon",
        "https://",
        "http://",
    ]
    for marker in forbidden:
        if marker in html:
            errors.append(f"offline runner contains network/external marker: {marker}")

    return errors


def run_self_test() -> int:
    bundle_schema = load_json(BUNDLE_SCHEMA)
    response_schema = load_json(RESPONSE_SCHEMA)
    Draft202012Validator.check_schema(bundle_schema)
    Draft202012Validator.check_schema(response_schema)

    runner_errors = runner_static_errors()
    assert not runner_errors, runner_errors

    bundle = load_json(EXAMPLE_BUNDLE)
    errors = validate_bundle(bundle, bundle_schema)
    assert not errors, errors

    duplicate = copy.deepcopy(bundle)
    duplicate["cases"][1]["case_id"] = duplicate["cases"][0]["case_id"]
    errors = validate_bundle(duplicate, bundle_schema)
    assert any("case_id values must be unique" in error for error in errors)

    leaked_gold = copy.deepcopy(bundle)
    leaked_gold["cases"][0]["gold"] = {"authorization_violation": True}
    errors = validate_bundle(leaked_gold, bundle_schema)
    assert errors
    assert any("Additional properties are not allowed" in error for error in errors)

    nested_hidden = copy.deepcopy(bundle)
    nested_hidden["cases"][0]["evidence"][0]["content"] = (
        "The literal word gold inside reviewer evidence is allowed."
    )
    errors = validate_bundle(nested_hidden, bundle_schema)
    assert not errors, errors

    duplicate_label = copy.deepcopy(bundle)
    duplicate_label["cases"][0]["evidence"].append(
        copy.deepcopy(duplicate_label["cases"][0]["evidence"][0])
    )
    errors = validate_bundle(duplicate_label, bundle_schema)
    assert any("evidence labels must be unique" in error for error in errors)

    oversized_content = copy.deepcopy(bundle)
    oversized_content["cases"][0]["evidence"][0]["content"] = "x" * 2_000_001
    errors = validate_bundle(oversized_content, bundle_schema)
    assert errors
    assert any("too long" in error for error in errors)

    too_many_cases = copy.deepcopy(bundle)
    prototype = copy.deepcopy(bundle["cases"][0])
    too_many_cases["cases"] = []
    for index in range(513):
        item = copy.deepcopy(prototype)
        item["case_id"] = f"DEV-LIMIT-{index:04d}"
        too_many_cases["cases"].append(item)
    errors = validate_bundle(too_many_cases, bundle_schema)
    assert errors
    assert any("too long" in error for error in errors)

    sample_response = {
        "response_bundle_version": "AR-P003-v0.3-dev-runner-response-v0.2",
        "protocol_version": bundle["protocol_version"],
        "assignment_version": bundle["assignment_version"],
        "assignment_sha256": bundle["assignment_sha256"],
        "reviewer_id": bundle["reviewer_id"],
        "session_started_at": "2026-09-18T12:00:00Z",
        "session_completed_at": "2026-09-18T12:03:00Z",
        "cases": [
            {
                "case_id": bundle["cases"][0]["case_id"],
                "condition": "control",
                "started_at": "2026-09-18T12:00:00Z",
                "submitted_at": "2026-09-18T12:01:00Z",
                "elapsed_wall_seconds": 60.0,
                "elapsed_active_seconds": 55.0,
                "events": [
                    {
                        "event": "pause_started",
                        "at": "2026-09-18T12:00:30Z",
                        "reason": "manual",
                    },
                    {
                        "event": "pause_ended",
                        "at": "2026-09-18T12:00:35Z",
                        "reason": "manual",
                    },
                ],
                "technical_issue": False,
                "answer": {
                    "material_actions": ["analyze"],
                    "authorization_violation": False,
                    "material_sources": ["source-1"],
                    "incidents": [],
                    "verification_state": "not_required",
                    "missing_evidence": False,
                    "confidence": 4,
                },
            }
        ],
    }
    errors = validate_response(sample_response, response_schema)
    assert not errors, errors

    bad_assignment_binding = copy.deepcopy(sample_response)
    bad_assignment_binding["assignment_sha256"] = "sha256:" + "z" * 64
    errors = validate_response(bad_assignment_binding, response_schema)
    assert errors

    impossible_timing = copy.deepcopy(sample_response)
    impossible_timing["cases"][0]["elapsed_active_seconds"] = 61.0
    errors = validate_response(impossible_timing, response_schema)
    assert any("active elapsed time exceeds wall" in error for error in errors)

    duplicate_response = copy.deepcopy(sample_response)
    duplicate_response["cases"].append(
        copy.deepcopy(duplicate_response["cases"][0])
    )
    errors = validate_response(duplicate_response, response_schema)
    assert any("duplicate case_id" in error for error in errors)

    event_overflow = copy.deepcopy(sample_response)
    event_overflow["cases"][0]["events"] = [
        {
            "event": "pause_started",
            "at": "2026-09-18T12:00:30Z",
            "reason": "manual",
        }
        for _ in range(4097)
    ]
    errors = validate_response(event_overflow, response_schema)
    assert errors
    assert any("too long" in error for error in errors)

    print(
        "AR-P003 offline runner validation self-test passed: "
        "strict offline/no-network static checks, reviewer-bundle separation, "
        "resource bounds, and response timing checks."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate AR-P003 development offline-runner data."
    )
    parser.add_argument("path", nargs="?", help="Bundle or response JSON file")
    parser.add_argument(
        "--kind",
        choices=["bundle", "response"],
        default="bundle",
        help="Document kind to validate.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            return run_self_test()

        if not args.path:
            parser.error("provide a JSON file or use --self-test")

        schema_path = BUNDLE_SCHEMA if args.kind == "bundle" else RESPONSE_SCHEMA
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        doc = load_json(Path(args.path))
        errors = (
            validate_bundle(doc, schema)
            if args.kind == "bundle"
            else validate_response(doc, schema)
        )
    except (OSError, json.JSONDecodeError, SchemaError, AssertionError) as exc:
        print(f"ERROR: runner validation failed: {exc}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"AR-P003 {args.kind} is structurally and semantically valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
