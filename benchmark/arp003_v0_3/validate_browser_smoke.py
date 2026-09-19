#!/usr/bin/env python3
"""Validate AR-P003 manual browser/device smoke-test records.

This validator checks record completeness and internal consistency only. It
cannot perform the manual browser actions or convert an unrun template into
evidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "browser-smoke-record.schema.json"
EXAMPLE = ROOT / "benchmark" / "arp003_v0_3" / "browser-smoke-record.example.json"
RUNNER = ROOT / "benchmark" / "arp003_v0_3" / "offline_runner.html"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return "sha256:" + digest


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


def semantic_errors(
    doc: dict[str, Any],
    *,
    require_current_runner_hash: bool,
) -> list[str]:
    errors: list[str] = []

    try:
        started = parse_time(doc["started_at"])
        completed = parse_time(doc["completed_at"])
        if completed < started:
            errors.append("completed_at occurs before started_at")
    except ValueError as exc:
        errors.append(f"invalid timestamp: {exc}")

    statuses = [item["status"] for item in doc["checks"].values()]
    failed = statuses.count("fail")
    not_tested = statuses.count("not_tested")

    if doc["overall_status"] == "pass":
        if failed or not_tested:
            errors.append(
                "overall_status='pass' requires every manual check to pass"
            )
        if doc["defects"]:
            blocking_or_major = [
                d for d in doc["defects"] if d["severity"] in {"major", "blocking"}
            ]
            if blocking_or_major:
                errors.append(
                    "overall_status='pass' cannot contain major/blocking defects"
                )

    if doc["overall_status"] == "incomplete" and not not_tested:
        errors.append(
            "overall_status='incomplete' requires at least one not_tested check"
        )

    if doc["overall_status"] == "fail":
        if not failed and not doc["defects"]:
            errors.append(
                "overall_status='fail' requires a failed check or recorded defect"
            )

    if require_current_runner_hash:
        expected = sha256_file(RUNNER)
        if doc["runner_sha256"] != expected:
            errors.append(
                "runner_sha256 does not match the current offline_runner.html"
            )

    return errors


def validate(
    doc: Any,
    schema: dict[str, Any],
    *,
    require_current_runner_hash: bool,
) -> list[str]:
    errors = structural_errors(doc, schema)
    if errors:
        return errors
    if not isinstance(doc, dict):
        return ["$: smoke record must be an object"]
    return semantic_errors(
        doc,
        require_current_runner_hash=require_current_runner_hash,
    )


def run_self_test() -> int:
    schema = load_json(SCHEMA)
    example = load_json(EXAMPLE)
    Draft202012Validator.check_schema(schema)

    errors = validate(example, schema, require_current_runner_hash=False)
    assert not errors, errors

    fake_pass = copy.deepcopy(example)
    fake_pass["overall_status"] = "pass"
    errors = validate(fake_pass, schema, require_current_runner_hash=False)
    assert any("requires every manual check to pass" in error for error in errors)

    full_pass = copy.deepcopy(example)
    full_pass["overall_status"] = "pass"
    full_pass["runner_sha256"] = sha256_file(RUNNER)
    for item in full_pass["checks"].values():
        item["status"] = "pass"
        item["notes"] = "Synthetic self-test pass marker only."
    errors = validate(full_pass, schema, require_current_runner_hash=True)
    assert not errors, errors

    reversed_time = copy.deepcopy(example)
    reversed_time["started_at"] = "2026-09-19T01:00:00Z"
    reversed_time["completed_at"] = "2026-09-19T00:00:00Z"
    errors = validate(reversed_time, schema, require_current_runner_hash=False)
    assert any("completed_at occurs before" in error for error in errors)

    failing_without_basis = copy.deepcopy(example)
    failing_without_basis["overall_status"] = "fail"
    for item in failing_without_basis["checks"].values():
        item["status"] = "pass"
    errors = validate(
        failing_without_basis,
        schema,
        require_current_runner_hash=False,
    )
    assert any("requires a failed check or recorded defect" in error for error in errors)

    print(
        "AR-P003 browser-smoke record self-test passed: incomplete templates "
        "cannot masquerade as passing manual evidence."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an AR-P003 manual browser smoke-test record."
    )
    parser.add_argument(
        "record",
        nargs="?",
        default=str(EXAMPLE),
        help="Smoke-test record JSON.",
    )
    parser.add_argument(
        "--require-current-runner-hash",
        action="store_true",
        help="Require runner_sha256 to match the current offline_runner.html.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        schema = load_json(SCHEMA)
        Draft202012Validator.check_schema(schema)
        record = load_json(Path(args.record))
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load smoke record/schema: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        return run_self_test()

    errors = validate(
        record,
        schema,
        require_current_runner_hash=args.require_current_runner_hash,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "AR-P003 browser-smoke record is structurally and semantically valid; "
        f"overall_status={record['overall_status']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
