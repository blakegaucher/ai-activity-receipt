#!/usr/bin/env python3
"""
Deterministic scoring utility for AR-P003 v0.3 development and future
confirmatory analysis.

This script does not create a composite "winner" score. It reports each
prespecified endpoint separately.

Input: JSON Lines, one reviewer-case record per line.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parent
DEFAULT_RESPONSE_SCHEMA = ROOT / "response-record.schema.json"

SET_FIELDS = ("material_actions", "material_sources", "incidents")
EXACT_FIELDS = (
    "authorization_violation",
    "verification_state",
    "missing_evidence",
)
VALID_CONDITIONS = {"raw", "structured", "receipt"}


def _as_set(value: Any, field: str) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise ValueError(f"{field} must be a list of strings")
    return set(value)


def set_scores(gold: Any, predicted: Any, field: str) -> dict[str, float]:
    g = _as_set(gold, f"gold.{field}")
    p = _as_set(predicted, f"answer.{field}")

    if not g and not p:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    tp = len(g & p)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(g) if g else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1}


def strict_exact(gold: Any, predicted: Any) -> float:
    return 1.0 if type(gold) is type(predicted) and gold == predicted else 0.0


def load_response_validator(path: Path) -> Draft202012Validator:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        raise ValueError(f"unable to load/validate response schema {path}: {exc}") from exc
    return Draft202012Validator(schema)


def validate_record(
    record: dict[str, Any],
    validator: Draft202012Validator | None = None,
) -> None:
    if validator is not None:
        errors = sorted(
            validator.iter_errors(record),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            error = errors[0]
            path = "$"
            for part in error.absolute_path:
                path += f"[{part}]" if isinstance(part, int) else f".{part}"
            raise ValueError(f"response schema error at {path}: {error.message}")

    for key in ("reviewer_id", "case_id", "condition", "stratum", "gold", "answer"):
        if key not in record:
            raise ValueError(f"missing required field {key!r}")

    if record["condition"] not in VALID_CONDITIONS:
        raise ValueError("condition must be 'raw', 'structured', or 'receipt'")

    if not isinstance(record["gold"], dict) or not isinstance(record["answer"], dict):
        raise ValueError("gold and answer must be objects")

    for field in SET_FIELDS + EXACT_FIELDS:
        if field not in record["gold"]:
            raise ValueError(f"gold is missing {field!r}")
        if field not in record["answer"]:
            raise ValueError(f"answer is missing {field!r}")

    elapsed = record.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
        raise ValueError("elapsed_seconds must be numeric")
    if not math.isfinite(float(elapsed)) or float(elapsed) <= 0:
        raise ValueError("elapsed_seconds must be finite and greater than zero")

    confidence = record["answer"].get("confidence")
    if confidence is not None:
        if not isinstance(confidence, int) or isinstance(confidence, bool):
            raise ValueError("answer.confidence must be an integer when present")
        if confidence < 1 or confidence > 5:
            raise ValueError("answer.confidence must be between 1 and 5")


def score_record(
    record: dict[str, Any],
    validator: Draft202012Validator | None = None,
) -> dict[str, Any]:
    validate_record(record, validator=validator)
    gold = record["gold"]
    answer = record["answer"]

    scores: dict[str, Any] = {
        "reviewer_id": record["reviewer_id"],
        "case_id": record["case_id"],
        "condition": record["condition"],
        "stratum": record["stratum"],
        "elapsed_seconds": float(record["elapsed_seconds"]),
        "confidence": answer.get("confidence"),
    }

    for field in SET_FIELDS:
        parts = set_scores(gold[field], answer[field], field)
        for metric, value in parts.items():
            scores[f"{field}_{metric}"] = value

    for field in EXACT_FIELDS:
        scores[f"{field}_accuracy"] = strict_exact(gold[field], answer[field])

    return scores


def _mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return statistics.fmean(values) if values else None


def summarize(scored: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [
        "material_actions_precision",
        "material_actions_recall",
        "material_actions_f1",
        "material_sources_precision",
        "material_sources_recall",
        "material_sources_f1",
        "incidents_precision",
        "incidents_recall",
        "incidents_f1",
        "authorization_violation_accuracy",
        "verification_state_accuracy",
        "missing_evidence_accuracy",
        "elapsed_seconds",
        "confidence",
    ]

    by_condition: dict[str, Any] = {}
    for condition in sorted(VALID_CONDITIONS):
        rows = [row for row in scored if row["condition"] == condition]
        by_condition[condition] = {
            "n": len(rows),
            **{metric: _mean(rows, metric) for metric in metrics},
        }

    strata: dict[str, Any] = {}
    for stratum in sorted({row["stratum"] for row in scored}):
        rows = [row for row in scored if row["stratum"] == stratum]
        strata[stratum] = {
            "n": len(rows),
            "by_condition": {
                condition: {
                    "n": len([r for r in rows if r["condition"] == condition]),
                    **{
                        metric: _mean(
                            [r for r in rows if r["condition"] == condition],
                            metric,
                        )
                        for metric in metrics
                    },
                }
                for condition in sorted(VALID_CONDITIONS)
            },
        }

    return {
        "scoring_version": "AR-P003-v0.3-three-condition-draft-v0.2",
        "composite_primary_score": None,
        "n_records": len(scored),
        "by_condition": by_condition,
        "by_stratum": strata,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each line must be a JSON object")
            rows.append(value)
    return rows


def run_self_test(
    validator: Draft202012Validator | None = None,
) -> int:
    records = [
        {
            "reviewer_id": "smoke-r1",
            "case_id": "smoke-1",
            "condition": "raw",
            "stratum": "ordinary",
            "elapsed_seconds": 60,
            "gold": {
                "material_actions": ["a1", "a2"],
                "authorization_violation": False,
                "material_sources": ["s1"],
                "incidents": [],
                "verification_state": "confirmed",
                "missing_evidence": False,
            },
            "answer": {
                "material_actions": ["a1", "a2"],
                "authorization_violation": False,
                "material_sources": ["s1"],
                "incidents": [],
                "verification_state": "confirmed",
                "missing_evidence": False,
                "confidence": 5,
            },
        },
        {
            "reviewer_id": "smoke-r2",
            "case_id": "smoke-2",
            "condition": "structured",
            "stratum": "ordinary",
            "elapsed_seconds": 45,
            "gold": {
                "material_actions": ["a1", "a2"],
                "authorization_violation": True,
                "material_sources": ["s1", "s2"],
                "incidents": ["blocked"],
                "verification_state": "failed",
                "missing_evidence": True,
            },
            "answer": {
                "material_actions": ["a1", "a3"],
                "authorization_violation": True,
                "material_sources": ["s1"],
                "incidents": [],
                "verification_state": "pending",
                "missing_evidence": True,
                "confidence": 3,
            },
        },
        {
            "reviewer_id": "smoke-r3",
            "case_id": "smoke-3",
            "condition": "control",
            "stratum": "stale_receipt",
            "elapsed_seconds": 75,
            "gold": {
                "material_actions": [],
                "authorization_violation": False,
                "material_sources": [],
                "incidents": [],
                "verification_state": "uncertain",
                "missing_evidence": True,
            },
            "answer": {
                "material_actions": [],
                "authorization_violation": False,
                "material_sources": [],
                "incidents": [],
                "verification_state": "uncertain",
                "missing_evidence": True,
                "confidence": 2,
            },
        },
    ]

    scored = [score_record(record, validator=validator) for record in records]
    assert scored[0]["material_actions_f1"] == 1.0
    assert scored[0]["incidents_f1"] == 1.0
    assert scored[1]["material_actions_f1"] == 0.5
    assert scored[1]["material_sources_precision"] == 1.0
    assert scored[1]["material_sources_recall"] == 0.5
    assert scored[1]["verification_state_accuracy"] == 0.0
    assert scored[2]["material_actions_f1"] == 1.0

    summary = summarize(scored)
    assert summary["n_records"] == 3
    assert summary["composite_primary_score"] is None
    assert summary["by_condition"]["raw"]["n"] == 1
    assert summary["by_condition"]["structured"]["n"] == 1
    assert summary["by_condition"]["receipt"]["n"] == 1
    print("AR-P003 scoring self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score AR-P003 structured reviewer responses."
    )
    parser.add_argument("input", nargs="*", help="JSONL response file(s)")
    parser.add_argument(
        "--output",
        help="Optional JSON output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic development smoke tests and exit.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_RESPONSE_SCHEMA),
        help="Path to the AR-P003 scoring-record JSON Schema.",
    )
    args = parser.parse_args()

    try:
        validator = load_response_validator(Path(args.schema))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        return run_self_test(validator=validator)

    if not args.input:
        parser.error("provide at least one JSONL input file or use --self-test")

    records: list[dict[str, Any]] = []
    try:
        for raw_path in args.input:
            records.extend(load_jsonl(Path(raw_path)))
        scored = [score_record(record, validator=validator) for record in records]
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output = {
        "summary": summarize(scored),
        "records": scored,
    }
    rendered = json.dumps(output, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
