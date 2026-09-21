#!/usr/bin/env python3
"""End-to-end development smoke test for the AR-P003 v0.3 study pipeline.

Exercises:
assignment generation -> case-package lint/build -> reviewer bundles ->
reviewer-side response shape -> hidden-label merge -> scorer.

This is synthetic engineering validation only, not human-study evidence.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark" / "arp003_v0_3"
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from build_runner_bundles import build  # noqa: E402
from generate_assignment import generate  # noqa: E402
from merge_runner_responses import merge  # noqa: E402
from render_structured_control import render_record  # noqa: E402
from score_responses import score_record, summarize  # noqa: E402


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_case(
    root: Path,
    *,
    case_id: str,
    stratum: str,
    receipt_state: str,
    gold: dict[str, Any],
    evidence_text: str,
) -> tuple[Path, dict[str, Any]]:
    case_dir = root / "cases" / case_id
    (case_dir / "evidence").mkdir(parents=True)
    (case_dir / "structured").mkdir()
    (case_dir / "receipt").mkdir()
    (case_dir / "analysis").mkdir()

    (case_dir / "evidence" / "events.txt").write_text(
        evidence_text + "\n",
        encoding="utf-8",
    )
    source_ids = list(gold["material_sources"])
    actor_id = "agent-pipeline"
    principal_id = "user-pipeline"
    events = []
    for index, operation in enumerate(gold["material_actions"], start=1):
        events.append(
            {
                "event_id": f"{case_id}-event-{index}",
                "occurred_at": f"2026-09-18T12:{index:02d}:00Z",
                "actor_id": actor_id,
                "operation": operation,
                "status": "completed",
                "authorization": "approved",
                "authorization_decided_at": f"2026-09-18T12:{index-1:02d}:30Z",
                "consequential": True,
                "material": True,
                "source_refs": source_ids,
            }
        )
    canonical_record = {
        "record_id": f"record-{case_id}",
        "record_schema_version": "candidate-record-v0.1",
        "trace_id": f"trace-{case_id}",
        "system": {"agent_id": actor_id, "version": "pipeline-smoke"},
        "actors": [
            {"actor_id": principal_id, "kind": "human", "role": "principal"},
            {"actor_id": actor_id, "kind": "agent", "role": "delegate"},
        ],
        "authority": {
            "principal": principal_id,
            "delegate": actor_id,
            "scope": list(gold["material_actions"]) or ["read"],
            "prohibited": [],
            "valid_from": "2026-09-18T12:00:00Z",
            "valid_until": "2026-09-18T13:00:00Z",
        },
        "sources": [
            {"source_id": source_id, "role": "supports_result", "material": True}
            for source_id in source_ids
        ],
        "events": events,
        "verification": {"state": "not_required", "evidence_refs": []},
        "incidents": [],
        "integrity": {"generated_at": "2026-09-18T12:30:00Z"},
        "notes": "Synthetic pipeline smoke canonical record.",
    }
    write_json(case_dir / "analysis" / "canonical-record.json", canonical_record)
    (case_dir / "structured" / "events-table.md").write_text(
        render_record(canonical_record),
        encoding="utf-8",
    )
    write_json(
        case_dir / "receipt" / "receipt.json",
        {
            "receipt_id": f"receipt-{case_id}",
            "state": receipt_state,
            "note": "Synthetic development-only Receipt artifact.",
        },
    )
    write_json(case_dir / "analysis" / "gold.json", gold)

    manifest = {
        "package_version": "AR-P003-v0.3-dev-case-v0.2",
        "case_id": case_id,
        "stratum": stratum,
        "condition_contract": "same_evidence_plus_neutral_structured_or_receipt_v1",
        "reviewer_evidence_files": ["evidence/events.txt"],
        "structured_control_file": "structured/events-table.md",
        "structured_control_record_file": "analysis/canonical-record.json",
        "receipt_file": "receipt/receipt.json",
        "analysis_files": [
            "analysis/gold.json",
            "analysis/canonical-record.json",
        ],
        "receipt_state": receipt_state,
        "forbidden_reviewer_markers": [f"HIDDEN_{case_id.upper()}"],
        "notes": "Synthetic end-to-end pipeline smoke case.",
    }
    manifest_path = case_dir / "case.json"
    write_json(manifest_path, manifest)

    options = {
        "material_actions": sorted(set(gold["material_actions"]) | {"distractor_action"}),
        "material_sources": sorted(set(gold["material_sources"]) | {"distractor_source"}),
        "incidents": sorted(set(gold["incidents"]) | {"distractor_incident"}),
    }
    return manifest_path, options


def perfect_answer(gold: dict[str, Any]) -> dict[str, Any]:
    return {
        "material_actions": list(gold["material_actions"]),
        "authorization_violation": gold["authorization_violation"],
        "material_sources": list(gold["material_sources"]),
        "incidents": list(gold["incidents"]),
        "verification_state": gold["verification_state"],
        "missing_evidence": gold["missing_evidence"],
        "confidence": 4,
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        gold_ordinary = {
            "material_actions": ["analyze"],
            "authorization_violation": False,
            "material_sources": ["source-A"],
            "incidents": [],
            "verification_state": "confirmed",
            "missing_evidence": False,
        }
        gold_conflict = {
            "material_actions": ["send_email"],
            "authorization_violation": True,
            "material_sources": ["source-B"],
            "incidents": ["authorization_violation"],
            "verification_state": "uncertain",
            "missing_evidence": False,
        }

        manifest_a, options_a = make_case(
            root,
            case_id="case-ordinary",
            stratum="ordinary",
            receipt_state="current",
            gold=gold_ordinary,
            evidence_text=(
                "Synthetic evidence: source-A was analyzed under valid authority "
                "and verification was confirmed."
            ),
        )
        manifest_b, options_b = make_case(
            root,
            case_id="case-conflict",
            stratum="conflicting_receipt",
            receipt_state="conflicting",
            gold=gold_conflict,
            evidence_text=(
                "Synthetic evidence: send_email completed outside the delegated "
                "scope; source-B supports the event."
            ),
        )

        assignment_config = {
            "reviewers": ["reviewer-1", "reviewer-2"],
            "cases": [
                {"case_id": "case-ordinary", "stratum": "ordinary"},
                {"case_id": "case-conflict", "stratum": "conflicting_receipt"},
            ],
            "cases_per_reviewer": 2,
            "seed": 73917,
        }
        assignment = generate(assignment_config)
        assignment_path = root / "assignment.json"
        write_json(assignment_path, assignment)

        build_config = {
            "build_config_version": "AR-P003-v0.3-dev-runner-build-v0.2",
            "protocol_version": "v0.3-draft-2026-09-21-integrated-challenge-v0.1",
            "cases": [
                {
                    "case_id": "case-ordinary",
                    "manifest": str(manifest_a.relative_to(root)),
                    "gold_file": "analysis/gold.json",
                    "answer_options": options_a,
                    "evidence_labels": {
                        "evidence/events.txt": "Synthetic ordinary evidence"
                    },
                },
                {
                    "case_id": "case-conflict",
                    "manifest": str(manifest_b.relative_to(root)),
                    "gold_file": "analysis/gold.json",
                    "answer_options": options_b,
                    "evidence_labels": {
                        "evidence/events.txt": "Synthetic conflicting evidence"
                    },
                },
            ],
        }
        build_config_path = root / "build-config.json"
        write_json(build_config_path, build_config)

        assignment_for_build = json.loads(json.dumps(assignment))
        assignment_for_build["_source_path"] = str(assignment_path)
        output_dir = root / "built"
        build_manifest = build(
            assignment_for_build,
            build_config,
            config_path=build_config_path,
            output_dir=output_dir,
        )

        assert len(build_manifest["reviewer_bundles"]) == 2
        assert len(build_manifest["answer_option_audit"]) == 2
        for audit in build_manifest["answer_option_audit"]:
            for endpoint in ("material_actions", "material_sources", "incidents"):
                assert audit[endpoint]["gold_representable"] is True
                assert audit[endpoint]["n_non_gold_options"] >= 1

        hidden = json.loads(
            (output_dir / "analysis" / "runner-analysis.json").read_text(
                encoding="utf-8"
            )
        )
        hidden_by_id = {item["case_id"]: item for item in hidden["cases"]}

        merged_records: list[dict[str, Any]] = []
        conditions: list[str] = []

        for reviewer_summary in build_manifest["reviewer_bundles"]:
            bundle_path = output_dir / reviewer_summary["path"]
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            rendered_bundle = json.dumps(bundle)
            assert '"gold"' not in rendered_bundle
            assert '"stratum"' not in rendered_bundle

            response_cases: list[dict[str, Any]] = []
            for index, case in enumerate(bundle["cases"], start=1):
                condition = (
                    "receipt"
                    if case["receipt"] is not None
                    else (
                        "structured"
                        if case["structured_event_table"] is not None
                        else "raw"
                    )
                )
                conditions.append(condition)
                gold = hidden_by_id[case["case_id"]]["gold"]
                response_cases.append(
                    {
                        "case_id": case["case_id"],
                        "condition": condition,
                        "started_at": f"2026-09-18T12:0{index}:00Z",
                        "submitted_at": f"2026-09-18T12:0{index}:12Z",
                        "elapsed_wall_seconds": 12.0,
                        "elapsed_active_seconds": 10.0,
                        "events": [
                            {
                                "event": "pause_started",
                                "at": f"2026-09-18T12:0{index}:05Z",
                                "reason": "manual",
                            },
                            {
                                "event": "pause_ended",
                                "at": f"2026-09-18T12:0{index}:07Z",
                                "reason": "manual",
                            },
                        ],
                        "technical_issue": False,
                        "answer": perfect_answer(gold),
                    }
                )

            response = {
                "response_bundle_version": "AR-P003-v0.3-dev-runner-response-v0.5",
                "protocol_version": bundle["protocol_version"],
                "comparison_design": bundle["comparison_design"],
                "assignment_version": bundle["assignment_version"],
                "assignment_sha256": bundle["assignment_sha256"],
                "reviewer_id": bundle["reviewer_id"],
                "session_started_at": "2026-09-18T12:00:00Z",
                "session_completed_at": "2026-09-18T12:10:00Z",
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
                "cases": response_cases,
            }
            merged_records.extend(
                merge(
                    response,
                    hidden,
                    assignment,
                    assignment_sha256=bundle["assignment_sha256"],
                    timing="active",
                )
            )

        condition_counts = {
            condition: conditions.count(condition)
            for condition in ("raw", "structured", "receipt")
        }
        assert sum(condition_counts.values()) == 4
        assert all(count >= 1 for count in condition_counts.values())
        assert max(condition_counts.values()) - min(condition_counts.values()) <= 1
        assert len(merged_records) == 4
        assert all(record["elapsed_seconds"] == 10.0 for record in merged_records)

        scored = [score_record(record) for record in merged_records]
        for row in scored:
            assert row["material_actions_f1"] == 1.0
            assert row["material_sources_f1"] == 1.0
            assert row["incidents_f1"] == 1.0
            assert row["authorization_violation_accuracy"] == 1.0
            assert row["verification_state_accuracy"] == 1.0
            assert row["missing_evidence_accuracy"] == 1.0

        summary = summarize(scored)
        assert summary["n_records"] == 4
        for condition, expected in condition_counts.items():
            assert summary["by_condition"][condition]["n"] == expected

        # Analysis-side merge must not trust a reviewer-edited condition field.
        first_bundle_path = output_dir / build_manifest["reviewer_bundles"][0]["path"]
        first_bundle = json.loads(first_bundle_path.read_text(encoding="utf-8"))
        first_case = first_bundle["cases"][0]
        true_condition = (
            "receipt"
            if first_case["receipt"] is not None
            else (
                "structured"
                if first_case["structured_event_table"] is not None
                else "raw"
            )
        )
        tampered_condition = next(
            condition
            for condition in ("raw", "structured", "receipt")
            if condition != true_condition
        )
        hidden_gold = hidden_by_id[first_case["case_id"]]["gold"]
        tampered_response = {
            "response_bundle_version": "AR-P003-v0.3-dev-runner-response-v0.5",
            "protocol_version": first_bundle["protocol_version"],
            "comparison_design": first_bundle["comparison_design"],
            "assignment_version": first_bundle["assignment_version"],
            "assignment_sha256": first_bundle["assignment_sha256"],
            "reviewer_id": first_bundle["reviewer_id"],
            "session_started_at": "2026-09-18T13:00:00Z",
            "session_completed_at": "2026-09-18T13:01:00Z",
            "comprehension": {
                "gate_version": "AR-P003-v0.3-comprehension-v0.1",
                "attempts": 1,
                "passed_at": "2026-09-18T12:59:00Z",
            },
            "practice": {
                "practice_version": "AR-P003-v0.3-practice-v0.1",
                "attempts": 1,
                "passed_at": "2026-09-18T13:00:00Z",
            },
            "cases": [
                {
                    "case_id": first_case["case_id"],
                    "condition": tampered_condition,
                    "started_at": "2026-09-18T13:00:00Z",
                    "submitted_at": "2026-09-18T13:00:10Z",
                    "elapsed_wall_seconds": 10.0,
                    "elapsed_active_seconds": 10.0,
                    "events": [],
                    "technical_issue": False,
                    "answer": perfect_answer(hidden_gold),
                }
            ],
        }
        try:
            merge(
                tampered_response,
                hidden,
                assignment,
                assignment_sha256=first_bundle["assignment_sha256"],
                timing="active",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("tampered reviewer condition was accepted")

    print(
        "AR-P003 end-to-end pipeline smoke test passed: assignment -> build -> "
        "reviewer export -> hidden-label merge -> scoring."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
