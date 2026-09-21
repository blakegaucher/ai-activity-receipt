#!/usr/bin/env python3
"""Deterministic scoring utility for AR-P003 v0.3 development.

The selected confirmatory primary endpoint is evidence-supported correct audit
completion by 180 seconds. The primary timing clock remains unresolved, so this
development scorer preserves both clocks, derives the frozen content semantics,
and reports clock-conditional development diagnostics without emitting a
confirmatory primary success value.

Component outcomes remain prespecified secondary diagnostics. Critical false
clearance remains a separate safety endpoint. No post-hoc composite is created.

Input: JSON Lines, one reviewer-case scoring record per line.
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

SCORING_VERSION = "AR-P003-v0.3-primary-endpoint-v0.4"
PRIMARY_ENDPOINT_ID = "correct_completion_by_180s"
PRIMARY_DEADLINE_SECONDS = 180.0
PRIMARY_TIMING_CLOCK = "unresolved"

SET_FIELDS = ("material_actions", "material_sources", "incidents")
EXACT_FIELDS = (
    "authorization_violation",
    "verification_state",
    "missing_evidence",
)
VALID_CONDITIONS = {"raw", "structured", "receipt"}
ADVERSE_VERIFICATION_STATES = {"pending", "failed", "uncertain"}
CLEAR_VERIFICATION_STATES = {"confirmed", "not_required"}


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

    for key in (
        "record_version",
        "reviewer_id",
        "case_id",
        "condition",
        "stratum",
        "elapsed_wall_seconds",
        "elapsed_active_seconds",
        "primary_endpoint_contract",
        "gold",
        "answer",
    ):
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

    for field in ("elapsed_wall_seconds", "elapsed_active_seconds"):
        elapsed = record.get(field)
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
            raise ValueError(f"{field} must be numeric")
        if not math.isfinite(float(elapsed)) or float(elapsed) < 0:
            raise ValueError(f"{field} must be finite and nonnegative")

    if (
        float(record["elapsed_active_seconds"])
        > float(record["elapsed_wall_seconds"]) + 0.01
    ):
        raise ValueError("elapsed_active_seconds cannot exceed elapsed_wall_seconds")

    contract = record["primary_endpoint_contract"]
    if contract.get("case_id") != record["case_id"]:
        raise ValueError("primary_endpoint_contract.case_id must match record case_id")
    if contract.get("endpoint_id") != PRIMARY_ENDPOINT_ID:
        raise ValueError("primary endpoint contract has unexpected endpoint_id")
    if float(contract.get("deadline_seconds", -1)) != PRIMARY_DEADLINE_SECONDS:
        raise ValueError("primary endpoint contract must use the selected 180-second deadline")

    required = contract.get("required_judgments")
    if not isinstance(required, dict) or not required:
        raise ValueError("primary endpoint contract requires case-specific judgments")
    for field, spec in required.items():
        if field not in SET_FIELDS + EXACT_FIELDS:
            raise ValueError(f"unknown required judgment {field!r}")
        expected_rule = "set_exact" if field in SET_FIELDS else "exact"
        if spec.get("comparison_rule") != expected_rule:
            raise ValueError(
                f"required judgment {field!r} must use comparison_rule={expected_rule!r}"
            )
        support = (spec.get("acceptable_evidence_sets") or {}).get(record["condition"])
        if not isinstance(support, list) or not support:
            raise ValueError(
                f"required judgment {field!r} has no acceptable support set "
                f"for condition {record['condition']!r}"
            )

    confidence = record["answer"].get("confidence")
    if confidence is not None:
        if not isinstance(confidence, int) or isinstance(confidence, bool):
            raise ValueError("answer.confidence must be an integer when present")
        if confidence < 1 or confidence > 5:
            raise ValueError("answer.confidence must be between 1 and 5")


def evaluate_primary_content(record: dict[str, Any]) -> dict[str, Any]:
    gold = record["gold"]
    answer = record["answer"]
    contract = record["primary_endpoint_contract"]
    required = contract["required_judgments"]

    judgment_results: dict[str, bool] = {}
    evidence_support_valid = True
    extra_material_facts: dict[str, list[str]] = {}

    for field, spec in required.items():
        support_sets = spec["acceptable_evidence_sets"][record["condition"]]
        evidence_support_valid = evidence_support_valid and bool(support_sets)

        if field in SET_FIELDS:
            expected = _as_set(gold[field], f"gold.{field}")
            submitted = _as_set(answer[field], f"answer.{field}")
            judgment_results[field] = expected == submitted
            extras = sorted(submitted - expected)
            if extras:
                extra_material_facts[field] = extras
        else:
            judgment_results[field] = bool(strict_exact(gold[field], answer[field]))

    authorization_state_mismatch = (
        "authorization_violation" in required
        and not judgment_results["authorization_violation"]
    )
    material_fact_failure = bool(extra_material_facts) or authorization_state_mismatch
    all_required_correct = all(judgment_results.values())
    content_success = (
        all_required_correct
        and evidence_support_valid
        and not material_fact_failure
    )

    return {
        "all_required_judgments_correct": all_required_correct,
        "evidence_support_contract_valid": evidence_support_valid,
        "material_fact_failure": material_fact_failure,
        "extra_material_facts": extra_material_facts,
        "authorization_state_mismatch": authorization_state_mismatch,
        "judgment_results": judgment_results,
        "content_success": content_success,
    }


def critical_false_clearance(record: dict[str, Any]) -> dict[str, Any]:
    gold = record["gold"]
    answer = record["answer"]
    checks = record["primary_endpoint_contract"]["critical_false_clearance_checks"]

    applicable: list[str] = []
    triggered: list[str] = []

    for check in checks:
        field = check["field"]
        rule = check["rule"]

        if rule == "boolean_true_to_false":
            if gold[field] is True:
                applicable.append(field)
                if answer[field] is False:
                    triggered.append(field)

        elif rule == "nonempty_set_to_empty":
            gold_values = _as_set(gold[field], f"gold.{field}")
            submitted = _as_set(answer[field], f"answer.{field}")
            if gold_values:
                applicable.append(field)
                if not submitted:
                    triggered.append(field)

        elif rule == "adverse_verification_to_clear":
            if gold[field] in ADVERSE_VERIFICATION_STATES:
                applicable.append(field)
                if answer[field] in CLEAR_VERIFICATION_STATES:
                    triggered.append(field)

        else:
            raise ValueError(f"unsupported critical false-clearance rule {rule!r}")

    return {
        "applicable": bool(applicable),
        "event": bool(triggered),
        "applicable_checks": applicable,
        "triggered_checks": triggered,
    }


def derive_primary_endpoint(record: dict[str, Any]) -> dict[str, Any]:
    content = evaluate_primary_content(record)
    deadline = float(record["primary_endpoint_contract"]["deadline_seconds"])
    active_timeout = float(record["elapsed_active_seconds"]) > deadline
    wall_timeout = float(record["elapsed_wall_seconds"]) > deadline

    active_success = content["content_success"] and not active_timeout
    wall_success = content["content_success"] and not wall_timeout

    return {
        "endpoint_id": PRIMARY_ENDPOINT_ID,
        "deadline_seconds": deadline,
        "primary_timing_clock": PRIMARY_TIMING_CLOCK,
        "confirmatory_status": "not_estimable_primary_timing_clock_unresolved",
        "success": None,
        "content": content,
        "timeout_if_active_time_primary": active_timeout,
        "timeout_if_wall_deadline_primary": wall_timeout,
        "development_if_active_time_primary_success": active_success,
        "development_if_wall_deadline_primary_success": wall_success,
    }


def score_record(
    record: dict[str, Any],
    validator: Draft202012Validator | None = None,
) -> dict[str, Any]:
    validate_record(record, validator=validator)
    gold = record["gold"]
    answer = record["answer"]
    primary = derive_primary_endpoint(record)
    safety = critical_false_clearance(record)

    scores: dict[str, Any] = {
        "reviewer_id": record["reviewer_id"],
        "case_id": record["case_id"],
        "condition": record["condition"],
        "stratum": record["stratum"],
        "elapsed_wall_seconds": float(record["elapsed_wall_seconds"]),
        "elapsed_active_seconds": float(record["elapsed_active_seconds"]),
        "confidence": answer.get("confidence"),
        "primary_endpoint_success": primary["success"],
        "primary_endpoint_status": primary["confirmatory_status"],
        "primary_content_success": 1.0 if primary["content"]["content_success"] else 0.0,
        "development_if_active_time_primary_success": (
            1.0 if primary["development_if_active_time_primary_success"] else 0.0
        ),
        "development_if_wall_deadline_primary_success": (
            1.0 if primary["development_if_wall_deadline_primary_success"] else 0.0
        ),
        "critical_false_clearance_applicable": safety["applicable"],
        "critical_false_clearance": (
            1.0 if safety["event"] else 0.0
        ) if safety["applicable"] else None,
        "critical_false_clearance_triggered_checks": safety["triggered_checks"],
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


def _safety_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    applicable = [
        row for row in rows if row.get("critical_false_clearance_applicable") is True
    ]
    events = [
        row for row in applicable if row.get("critical_false_clearance") == 1.0
    ]
    return {
        "applicable_n": len(applicable),
        "event_n": len(events),
        "rate": (len(events) / len(applicable)) if applicable else None,
    }


def summarize(scored: list[dict[str, Any]]) -> dict[str, Any]:
    secondary_metrics = [
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
        "elapsed_wall_seconds",
        "elapsed_active_seconds",
        "confidence",
    ]

    by_condition: dict[str, Any] = {}
    for condition in sorted(VALID_CONDITIONS):
        rows = [row for row in scored if row["condition"] == condition]
        by_condition[condition] = {
            "n": len(rows),
            **{metric: _mean(rows, metric) for metric in secondary_metrics},
            "critical_false_clearance": _safety_summary(rows),
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
                        for metric in secondary_metrics
                    },
                }
                for condition in sorted(VALID_CONDITIONS)
            },
        }

    case_classes: dict[str, Any] = {}
    for case_class in ("ordinary", "challenge"):
        rows = [
            row
            for row in scored
            if (
                (case_class == "ordinary" and row["stratum"] == "ordinary")
                or (case_class == "challenge" and row["stratum"] != "ordinary")
            )
        ]
        case_classes[case_class] = {
            "n": len(rows),
            "by_condition": {
                condition: {
                    "n": len([r for r in rows if r["condition"] == condition]),
                    **{
                        metric: _mean(
                            [r for r in rows if r["condition"] == condition],
                            metric,
                        )
                        for metric in secondary_metrics
                    },
                }
                for condition in sorted(VALID_CONDITIONS)
            },
        }

    return {
        "scoring_version": SCORING_VERSION,
        "challenge_design": "integrated_challenge_strata",
        "component_endpoints_role": "secondary_diagnostic_not_co_primary",
        "composite_primary_score": None,
        "n_records": len(scored),
        "primary_endpoint": {
            "endpoint_id": PRIMARY_ENDPOINT_ID,
            "outcome_type": "binary",
            "deadline_seconds": PRIMARY_DEADLINE_SECONDS,
            "primary_timing_clock": PRIMARY_TIMING_CLOCK,
            "status": "not_estimable_until_primary_timing_clock_selected",
            "success_rate": None,
            "development_clock_sensitivity": {
                "active_time_primary_success_rate": _mean(
                    scored, "development_if_active_time_primary_success"
                ),
                "wall_deadline_primary_success_rate": _mean(
                    scored, "development_if_wall_deadline_primary_success"
                ),
            },
        },
        "critical_false_clearance": {
            "role": "separate_prespecified_safety_endpoint",
            **_safety_summary(scored),
            "threshold_status": "unresolved_effect_precision_target",
        },
        "by_condition": by_condition,
        "by_case_class": case_classes,
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


def _support_sets() -> dict[str, list[list[str]]]:
    return {
        condition: [["evidence/events.json"]]
        for condition in ("raw", "structured", "receipt")
    }


def _contract(case_id: str) -> dict[str, Any]:
    return {
        "contract_version": "AR-P003-v0.3-primary-endpoint-case-v0.1",
        "case_id": case_id,
        "endpoint_id": PRIMARY_ENDPOINT_ID,
        "deadline_seconds": 180,
        "required_judgments": {
            field: {
                "comparison_rule": "set_exact" if field in SET_FIELDS else "exact",
                "acceptable_evidence_sets": _support_sets(),
            }
            for field in SET_FIELDS + EXACT_FIELDS
        },
        "critical_false_clearance_checks": [
            {
                "field": "authorization_violation",
                "rule": "boolean_true_to_false",
            },
            {"field": "incidents", "rule": "nonempty_set_to_empty"},
            {
                "field": "verification_state",
                "rule": "adverse_verification_to_clear",
            },
            {"field": "missing_evidence", "rule": "boolean_true_to_false"},
        ],
    }


def _record(
    *,
    case_id: str,
    condition: str,
    wall: float,
    active: float,
    gold: dict[str, Any],
    answer: dict[str, Any] | None = None,
    stratum: str = "ordinary",
) -> dict[str, Any]:
    return {
        "record_version": "AR-P003-v0.3-scoring-record-v0.2",
        "reviewer_id": "smoke-reviewer",
        "case_id": case_id,
        "condition": condition,
        "stratum": stratum,
        "elapsed_wall_seconds": wall,
        "elapsed_active_seconds": active,
        "primary_endpoint_contract": _contract(case_id),
        "gold": gold,
        "answer": answer or {**gold, "confidence": 4},
    }


def run_self_test(
    validator: Draft202012Validator | None = None,
) -> int:
    clear_gold = {
        "material_actions": ["a1", "a2"],
        "authorization_violation": False,
        "material_sources": ["s1"],
        "incidents": [],
        "verification_state": "confirmed",
        "missing_evidence": False,
    }
    adverse_gold = {
        "material_actions": ["send_email"],
        "authorization_violation": True,
        "material_sources": ["s2"],
        "incidents": ["authorization_violation"],
        "verification_state": "failed",
        "missing_evidence": True,
    }

    perfect = _record(
        case_id="perfect",
        condition="raw",
        wall=120,
        active=100,
        gold=clear_gold,
    )
    exact_deadline = _record(
        case_id="deadline",
        condition="structured",
        wall=180,
        active=180,
        gold=clear_gold,
    )
    over_wall = _record(
        case_id="over-wall",
        condition="receipt",
        wall=181,
        active=179,
        gold=clear_gold,
        stratum="stale_receipt",
    )

    perfect_score = score_record(perfect, validator=validator)
    deadline_score = score_record(exact_deadline, validator=validator)
    over_wall_score = score_record(over_wall, validator=validator)

    assert perfect_score["primary_endpoint_success"] is None
    assert perfect_score["primary_content_success"] == 1.0
    assert perfect_score["development_if_active_time_primary_success"] == 1.0
    assert perfect_score["development_if_wall_deadline_primary_success"] == 1.0
    assert deadline_score["development_if_active_time_primary_success"] == 1.0
    assert deadline_score["development_if_wall_deadline_primary_success"] == 1.0
    assert over_wall_score["development_if_active_time_primary_success"] == 1.0
    assert over_wall_score["development_if_wall_deadline_primary_success"] == 0.0

    wrong_answer = {**clear_gold, "verification_state": "failed", "confidence": 3}
    wrong = _record(
        case_id="wrong",
        condition="raw",
        wall=20,
        active=20,
        gold=clear_gold,
        answer=wrong_answer,
    )
    wrong_primary = derive_primary_endpoint(wrong)
    assert wrong_primary["content"]["all_required_judgments_correct"] is False
    assert wrong_primary["development_if_active_time_primary_success"] is False

    extra_answer = {
        **clear_gold,
        "material_actions": ["a1", "a2", "fabricated-action"],
        "confidence": 2,
    }
    extra = _record(
        case_id="extra",
        condition="raw",
        wall=20,
        active=20,
        gold=clear_gold,
        answer=extra_answer,
    )
    extra_primary = derive_primary_endpoint(extra)
    assert extra_primary["content"]["material_fact_failure"] is True
    assert extra_primary["development_if_active_time_primary_success"] is False

    false_clear_answer = {
        **adverse_gold,
        "authorization_violation": False,
        "incidents": [],
        "verification_state": "confirmed",
        "missing_evidence": False,
        "confidence": 1,
    }
    false_clear = _record(
        case_id="false-clear",
        condition="receipt",
        wall=30,
        active=25,
        gold=adverse_gold,
        answer=false_clear_answer,
        stratum="conflicting_receipt",
    )
    false_clear_score = score_record(false_clear, validator=validator)
    assert false_clear_score["primary_content_success"] == 0.0
    assert false_clear_score["critical_false_clearance_applicable"] is True
    assert false_clear_score["critical_false_clearance"] == 1.0
    assert set(false_clear_score["critical_false_clearance_triggered_checks"]) == {
        "authorization_violation",
        "incidents",
        "verification_state",
        "missing_evidence",
    }

    clear_score = score_record(perfect, validator=validator)
    assert clear_score["critical_false_clearance_applicable"] is False
    assert clear_score["critical_false_clearance"] is None

    summary = summarize(
        [perfect_score, deadline_score, over_wall_score, false_clear_score]
    )
    assert summary["n_records"] == 4
    assert summary["composite_primary_score"] is None
    assert summary["component_endpoints_role"] == "secondary_diagnostic_not_co_primary"
    assert summary["primary_endpoint"]["success_rate"] is None
    assert summary["primary_endpoint"]["primary_timing_clock"] == "unresolved"
    assert summary["critical_false_clearance"]["applicable_n"] == 1
    assert summary["critical_false_clearance"]["event_n"] == 1
    assert summary["critical_false_clearance"]["rate"] == 1.0
    assert summary["critical_false_clearance"]["threshold_status"] == (
        "unresolved_effect_precision_target"
    )

    bad_support = json.loads(json.dumps(perfect))
    bad_support["primary_endpoint_contract"]["required_judgments"][
        "material_actions"
    ]["acceptable_evidence_sets"]["raw"] = []
    try:
        score_record(bad_support, validator=validator)
    except ValueError as exc:
        assert "schema error" in str(exc) or "acceptable support" in str(exc)
    else:
        raise AssertionError("empty acceptable-evidence set was accepted")

    print(
        "AR-P003 scoring self-test passed: binary content semantics, exact 180s "
        "boundary, dual-clock deadline diagnostics, material-fact failures, "
        "separate critical false clearance, and unresolved-clock fail-close."
    )
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
        try:
            return run_self_test(validator=validator)
        except (AssertionError, ValueError) as exc:
            print(f"ERROR: scoring self-test failed: {exc}", file=sys.stderr)
            return 1

    if not args.input:
        parser.error("provide at least one JSONL input file or use --self-test")

    records: list[dict[str, Any]] = []
    try:
        for raw_path in args.input:
            records.extend(load_jsonl(Path(raw_path)))
        scored = [score_record(record, validator=validator) for record in records]
    except (OSError, ValueError) as exc:
        print(f"ERROR: scoring failed: {exc}", file=sys.stderr)
        return 1

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
