#!/usr/bin/env python3
"""Build AR-P003 v0.3 reviewer bundles from assignments + case packages.

This is analysis-side development tooling. It validates each case package,
constructs reviewer-facing bundles without gold/stratum data, and emits a
separate hidden analysis bundle for later scoring-side joins.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark" / "arp003_v0_3"
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from lint_case_packages import lint_package, safe_relative_file  # noqa: E402
from validate_runner_data import validate_bundle  # noqa: E402
from render_structured_control import RENDERER_VERSION, render_file  # noqa: E402

CASE_SCHEMA = BENCH / "case-package.schema.json"
BUILD_SCHEMA = BENCH / "runner-build-config.schema.json"
BUNDLE_SCHEMA = BENCH / "runner-bundle.schema.json"
ANALYSIS_SCHEMA = BENCH / "runner-analysis.schema.json"

ASSIGNMENT_VERSION_PREFIX = "AR-P003-v0.3-draft-assignment-"
BUILD_OUTPUT_VERSION = "AR-P003-v0.3-dev-runner-build-output-v0.4"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def schema_errors(doc: Any, schema: dict[str, Any]) -> list[str]:
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def safe_config_file(config_root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute() or any(
        part in {"", ".", ".."} for part in candidate.parts
    ):
        raise ValueError(f"unsafe config-relative path: {raw!r}")

    root = config_root.resolve()
    resolved = (config_root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes build-config root: {raw!r}") from exc
    if not resolved.is_file():
        raise ValueError(f"referenced file does not exist: {raw!r}")
    return resolved


def media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "application/json"
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    return "text/plain"


def read_text_artifact(path: Path, *, label: str) -> dict[str, str]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"offline runner currently supports UTF-8 text artifacts only: {path}"
        ) from exc
    return {
        "label": label,
        "media_type": media_type(path),
        "content": content,
    }


def canonical_reconstruction(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    required = {
        "material_actions",
        "authorization_violation",
        "material_sources",
        "incidents",
        "verification_state",
        "missing_evidence",
    }
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        raise ValueError(
            f"{label} reconstruction keys mismatch; missing={missing!r}, "
            f"extra={extra!r}"
        )
    return value


def validate_answer_options(
    gold: dict[str, Any],
    options: dict[str, Any],
    *,
    case_id: str,
) -> dict[str, Any]:
    """Ensure every set-valued gold answer can be expressed by the UI.

    This is a representability guard, not a non-leakage guarantee. A case can
    still have answer-option leakage even when every gold label is representable.
    The returned counts are therefore retained for analysis-side pre-freeze review.
    """

    audit: dict[str, Any] = {"case_id": case_id}
    for endpoint in ("material_actions", "material_sources", "incidents"):
        gold_set = set(gold[endpoint])
        option_set = set(options[endpoint])
        missing = sorted(gold_set - option_set)
        if missing:
            raise ValueError(
                f"case {case_id!r} gold {endpoint} cannot be represented by "
                f"answer_options; missing={missing!r}"
            )

        audit[endpoint] = {
            "n_gold": len(gold_set),
            "n_options": len(option_set),
            "n_non_gold_options": len(option_set - gold_set),
            "option_set_equals_gold_set": option_set == gold_set,
            "gold_representable": True,
        }

    return audit


def build(
    assignment: dict[str, Any],
    config: dict[str, Any],
    *,
    config_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    version = assignment.get("assignment_version")
    if (
        not isinstance(version, str)
        or not version.startswith(ASSIGNMENT_VERSION_PREFIX)
    ):
        raise ValueError("unrecognized assignment_version")

    assignments = assignment.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        raise ValueError("assignment file must contain non-empty assignments")

    assignment_source = Path(assignment["_source_path"])
    assignment_sha256 = sha256_file(assignment_source)

    config_root = config_path.parent
    case_schema = load_json(CASE_SCHEMA)
    bundle_schema = load_json(BUNDLE_SCHEMA)
    analysis_schema = load_json(ANALYSIS_SCHEMA)
    for schema in (case_schema, bundle_schema, analysis_schema):
        Draft202012Validator.check_schema(schema)

    config_by_id: dict[str, dict[str, Any]] = {}
    for item in config["cases"]:
        case_id = item["case_id"]
        if case_id in config_by_id:
            raise ValueError(f"build config duplicates case_id {case_id!r}")
        config_by_id[case_id] = item

    used_case_ids = {row.get("case_id") for row in assignments}
    if None in used_case_ids:
        raise ValueError("assignment row is missing case_id")

    missing_config = sorted(used_case_ids - set(config_by_id))
    if missing_config:
        raise ValueError(
            f"assignment references case(s) absent from build config: {missing_config!r}"
        )

    prepared: dict[str, dict[str, Any]] = {}
    hidden_cases: list[dict[str, Any]] = []
    answer_option_audits: list[dict[str, Any]] = []
    structured_control_audits: list[dict[str, Any]] = []

    for case_id in sorted(used_case_ids):
        item = config_by_id[case_id]
        manifest_path = safe_config_file(config_root, item["manifest"])
        lint_errors, _ = lint_package(manifest_path, case_schema)
        if lint_errors:
            raise ValueError(
                f"case {case_id!r} failed package lint: " + "; ".join(lint_errors)
            )

        manifest = load_json(manifest_path)
        if manifest["case_id"] != case_id:
            raise ValueError(
                f"build config case_id {case_id!r} does not match manifest "
                f"{manifest['case_id']!r}"
            )

        package_root = manifest_path.parent
        evidence: list[dict[str, str]] = []
        labels = item.get("evidence_labels") or {}
        for raw in manifest["reviewer_evidence_files"]:
            path, error = safe_relative_file(package_root, raw)
            if error or path is None:
                raise ValueError(error or f"unable to resolve evidence {raw!r}")
            label = labels.get(raw) or Path(raw).name
            evidence.append(read_text_artifact(path, label=label))

        structured_path, error = safe_relative_file(
            package_root,
            manifest["structured_control_file"],
        )
        if error or structured_path is None:
            raise ValueError(error or "unable to resolve structured-control file")
        structured_record_path, error = safe_relative_file(
            package_root,
            manifest["structured_control_record_file"],
        )
        if error or structured_record_path is None:
            raise ValueError(error or "unable to resolve structured-control record")
        expected_structured = render_file(structured_record_path)
        actual_structured = structured_path.read_text(encoding="utf-8")
        if actual_structured != expected_structured:
            raise ValueError(
                f"case {case_id!r} structured-control table does not match "
                "the deterministic canonical-record rendering"
            )
        structured_artifact = read_text_artifact(
            structured_path,
            label="Neutral structured event table",
        )
        structured_control_audits.append(
            {
                "case_id": case_id,
                "renderer_version": RENDERER_VERSION,
                "canonical_record_sha256": sha256_file(structured_record_path),
                "structured_table_sha256": sha256_file(structured_path),
                "exact_renderer_match": True,
            }
        )

        receipt_path, error = safe_relative_file(
            package_root,
            manifest["receipt_file"],
        )
        if error or receipt_path is None:
            raise ValueError(error or "unable to resolve receipt file")
        receipt_artifact = read_text_artifact(
            receipt_path,
            label=item.get("receipt_label") or "Activity Receipt",
        )

        gold_raw = item["gold_file"]
        if gold_raw not in set(manifest["analysis_files"]):
            raise ValueError(
                f"case {case_id!r} gold_file must be listed in manifest.analysis_files"
            )
        gold_path, error = safe_relative_file(package_root, gold_raw)
        if error or gold_path is None:
            raise ValueError(error or "unable to resolve gold file")
        gold = canonical_reconstruction(
            load_json(gold_path),
            label=f"case {case_id!r} gold_file",
        )
        answer_option_audits.append(
            validate_answer_options(
                gold,
                item["answer_options"],
                case_id=case_id,
            )
        )

        prepared[case_id] = {
            "manifest": manifest,
            "evidence": evidence,
            "structured_event_table": structured_artifact,
            "receipt": receipt_artifact,
            "answer_options": item["answer_options"],
        }
        hidden_cases.append(
            {
                "case_id": case_id,
                "stratum": manifest["stratum"],
                "gold": gold,
            }
        )

    reviewer_rows: dict[str, list[dict[str, Any]]] = {}
    for row in assignments:
        reviewer = row.get("reviewer_id")
        case_id = row.get("case_id")
        condition = row.get("condition")
        order = row.get("order")
        stratum = row.get("stratum")

        if not isinstance(reviewer, str) or not reviewer:
            raise ValueError("assignment reviewer_id must be non-empty string")
        if condition not in {"raw", "structured", "receipt"}:
            raise ValueError(
                f"assignment condition for {case_id!r} is invalid: {condition!r}"
            )
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise ValueError("assignment order must be positive integer")

        manifest = prepared[case_id]["manifest"]
        if stratum != manifest["stratum"]:
            raise ValueError(
                f"assignment stratum for {case_id!r} does not match case manifest"
            )

        reviewer_rows.setdefault(reviewer, []).append(row)

    reviewer_dir = output_dir / "reviewer_bundles"
    analysis_dir = output_dir / "analysis"
    reviewer_dir.mkdir(parents=True, exist_ok=False)
    analysis_dir.mkdir(parents=True, exist_ok=False)

    generated: list[Path] = []
    reviewer_summaries: list[dict[str, Any]] = []
    used_reviewer_filenames: set[str] = set()

    for reviewer, rows in sorted(reviewer_rows.items()):
        orders = [row["order"] for row in rows]
        if len(orders) != len(set(orders)):
            raise ValueError(f"reviewer {reviewer!r} has duplicate order values")
        rows = sorted(rows, key=lambda row: row["order"])

        cases: list[dict[str, Any]] = []
        for row in rows:
            case_id = row["case_id"]
            material = prepared[case_id]
            cases.append(
                {
                    "case_id": case_id,
                    "evidence": material["evidence"],
                    "structured_event_table": (
                        material["structured_event_table"]
                        if row["condition"] == "structured"
                        else None
                    ),
                    "receipt": (
                        material["receipt"]
                        if row["condition"] == "receipt"
                        else None
                    ),
                    "answer_options": material["answer_options"],
                }
            )

        bundle = {
            "bundle_version": "AR-P003-v0.3-dev-runner-bundle-v0.3",
            "protocol_version": config["protocol_version"],
            "comparison_design": "three_condition_structured_control",
            "assignment_version": assignment["assignment_version"],
            "assignment_sha256": assignment_sha256,
            "reviewer_id": reviewer,
            "cases": cases,
        }
        bundle_errors = validate_bundle(bundle, bundle_schema)
        if bundle_errors:
            raise ValueError(
                f"generated reviewer bundle {reviewer!r} is invalid: "
                + "; ".join(bundle_errors)
            )

        safe_reviewer = "".join(
            char if char.isalnum() or char in "._-" else "_"
            for char in reviewer
        )
        if not safe_reviewer:
            raise ValueError("reviewer ID cannot be converted to safe filename")
        filename = f"{safe_reviewer}.json"
        if filename in used_reviewer_filenames:
            raise ValueError(
                "two reviewer IDs collapse to the same safe output filename: "
                f"{filename!r}"
            )
        used_reviewer_filenames.add(filename)
        path = reviewer_dir / filename
        path.write_text(
            json.dumps(bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        generated.append(path)
        reviewer_summaries.append(
            {
                "reviewer_id": reviewer,
                "path": str(path.relative_to(output_dir)),
                "n_cases": len(cases),
                "sha256": sha256_file(path),
            }
        )

    analysis_bundle = {
        "analysis_bundle_version": "AR-P003-v0.3-dev-runner-analysis-v0.3",
        "protocol_version": config["protocol_version"],
        "comparison_design": "three_condition_structured_control",
        "challenge_design": "integrated_challenge_strata",
        "cases": hidden_cases,
    }
    analysis_errors = schema_errors(analysis_bundle, analysis_schema)
    if analysis_errors:
        raise ValueError(
            "generated hidden analysis bundle is invalid: "
            + "; ".join(analysis_errors)
        )

    analysis_path = analysis_dir / "runner-analysis.json"
    analysis_path.write_text(
        json.dumps(analysis_bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated.append(analysis_path)

    build_manifest = {
        "build_output_version": BUILD_OUTPUT_VERSION,
        "assignment_version": assignment["assignment_version"],
        "protocol_version": config["protocol_version"],
        "inputs": {
            "assignment_sha256": assignment_sha256,
            "build_config_sha256": sha256_file(config_path),
        },
        "reviewer_bundles": reviewer_summaries,
        "hidden_analysis": {
            "path": str(analysis_path.relative_to(output_dir)),
            "sha256": sha256_file(analysis_path),
            "n_cases": len(hidden_cases),
        },
        "answer_option_audit": answer_option_audits,
        "structured_control_audit": structured_control_audits,
        "evidence_boundary": (
            "Development-only build output. Reviewer bundles contain no gold "
            "labels or hidden strata; analysis output must remain access-controlled."
        ),
    }
    manifest_path = output_dir / "build-manifest.json"
    manifest_path.write_text(
        json.dumps(build_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated.append(manifest_path)

    return build_manifest


def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases_root = root / "cases"
        case_dir = cases_root / "case-1"
        (case_dir / "evidence").mkdir(parents=True)
        (case_dir / "structured").mkdir()
        (case_dir / "receipt").mkdir()
        (case_dir / "analysis").mkdir()

        (case_dir / "evidence" / "events.json").write_text(
            json.dumps(
                {
                    "event_id": "event-1",
                    "operation": "analyze",
                    "status": "completed",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        canonical_record = load_json(ROOT / "examples" / "canonical-record.json")
        (case_dir / "analysis" / "canonical-record.json").write_text(
            json.dumps(canonical_record, indent=2) + "\n",
            encoding="utf-8",
        )
        (case_dir / "structured" / "events-table.md").write_text(
            render_file(case_dir / "analysis" / "canonical-record.json"),
            encoding="utf-8",
        )
        (case_dir / "receipt" / "receipt.json").write_text(
            '{"receipt_id":"dev-case-1"}\n',
            encoding="utf-8",
        )
        gold = {
            "material_actions": ["analyze"],
            "authorization_violation": False,
            "material_sources": [],
            "incidents": [],
            "verification_state": "not_required",
            "missing_evidence": False,
        }
        (case_dir / "analysis" / "gold.json").write_text(
            json.dumps(gold, indent=2) + "\n",
            encoding="utf-8",
        )

        case_manifest = {
            "package_version": "AR-P003-v0.3-dev-case-v0.2",
            "case_id": "case-1",
            "stratum": "ordinary",
            "condition_contract": "same_evidence_plus_neutral_structured_or_receipt_v1",
            "reviewer_evidence_files": ["evidence/events.json"],
            "structured_control_file": "structured/events-table.md",
            "structured_control_record_file": "analysis/canonical-record.json",
            "receipt_file": "receipt/receipt.json",
            "analysis_files": [
                "analysis/gold.json",
                "analysis/canonical-record.json",
            ],
            "receipt_state": "current",
            "forbidden_reviewer_markers": ["GOLD_ONLY_MARKER"],
        }
        case_manifest_path = case_dir / "case.json"
        case_manifest_path.write_text(
            json.dumps(case_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        config = {
            "build_config_version": "AR-P003-v0.3-dev-runner-build-v0.2",
            "protocol_version": "v0.3-draft-2026-09-20-three-condition-v0.1",
            "cases": [
                {
                    "case_id": "case-1",
                    "manifest": "cases/case-1/case.json",
                    "gold_file": "analysis/gold.json",
                    "answer_options": {
                        "material_actions": ["analyze"],
                        "material_sources": [],
                        "incidents": [],
                    },
                    "evidence_labels": {
                        "evidence/events.json": "Synthetic event log"
                    },
                }
            ],
        }
        config_path = root / "build-config.json"
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8",
        )

        assignment = {
            "assignment_version": "AR-P003-v0.3-draft-assignment-v0.3",
            "assignments": [
                {
                    "reviewer_id": "R-raw",
                    "case_id": "case-1",
                    "stratum": "ordinary",
                    "order": 1,
                    "condition": "raw",
                },
                {
                    "reviewer_id": "R-structured",
                    "case_id": "case-1",
                    "stratum": "ordinary",
                    "order": 1,
                    "condition": "structured",
                },
                {
                    "reviewer_id": "R-receipt",
                    "case_id": "case-1",
                    "stratum": "ordinary",
                    "order": 1,
                    "condition": "receipt",
                },
            ],
        }
        assignment_path = root / "assignment.json"
        assignment_path.write_text(
            json.dumps(assignment, indent=2) + "\n",
            encoding="utf-8",
        )

        build_schema = load_json(BUILD_SCHEMA)
        Draft202012Validator.check_schema(build_schema)
        assert not schema_errors(config, build_schema)

        assignment["_source_path"] = str(assignment_path)
        output_dir = root / "output"
        result = build(
            assignment,
            config,
            config_path=config_path,
            output_dir=output_dir,
        )
        assert len(result["reviewer_bundles"]) == 3
        assert result["answer_option_audit"][0]["material_actions"]["gold_representable"]
        assert result["structured_control_audit"][0]["exact_renderer_match"] is True
        assert result["structured_control_audit"][0]["renderer_version"] == RENDERER_VERSION
        assert result["answer_option_audit"][0]["material_actions"]["option_set_equals_gold_set"]
        # The equality above is allowed in this tiny smoke fixture. It is surfaced
        # for pre-freeze leakage review rather than silently treated as safe.
        print("gold representability guard accepted the valid smoke case")

        try:
            validate_answer_options(
                gold,
                {
                    "material_actions": [],
                    "material_sources": [],
                    "incidents": [],
                },
                case_id="case-1",
            )
        except ValueError as exc:
            assert "cannot be represented" in str(exc)
        else:
            raise AssertionError("unrepresentable gold answer was accepted")

        raw = load_json(output_dir / "reviewer_bundles" / "R-raw.json")
        structured = load_json(output_dir / "reviewer_bundles" / "R-structured.json")
        receipt = load_json(output_dir / "reviewer_bundles" / "R-receipt.json")
        hidden = load_json(output_dir / "analysis" / "runner-analysis.json")

        assert raw["assignment_version"] == assignment["assignment_version"]
        assert raw["assignment_sha256"] == sha256_file(assignment_path)
        assert structured["assignment_sha256"] == sha256_file(assignment_path)
        assert receipt["assignment_sha256"] == sha256_file(assignment_path)
        assert raw["comparison_design"] == "three_condition_structured_control"
        assert raw["cases"][0]["structured_event_table"] is None
        assert raw["cases"][0]["receipt"] is None
        assert structured["cases"][0]["structured_event_table"]["label"] == "Neutral structured event table"
        assert structured["cases"][0]["receipt"] is None
        assert receipt["cases"][0]["structured_event_table"] is None
        assert receipt["cases"][0]["receipt"]["label"] == "Activity Receipt"
        assert raw["cases"][0]["evidence"] == structured["cases"][0]["evidence"]
        assert raw["cases"][0]["evidence"] == receipt["cases"][0]["evidence"]
        assert "gold" not in json.dumps(raw)
        assert "stratum" not in json.dumps(raw)
        assert hidden["cases"][0]["gold"] == gold
        assert hidden["cases"][0]["stratum"] == "ordinary"

        bad_assignment = json.loads(
            json.dumps({k: v for k, v in assignment.items() if k != "_source_path"})
        )
        bad_assignment["assignments"][0]["stratum"] = "conflicting_receipt"
        bad_assignment_path = root / "bad-assignment.json"
        bad_assignment_path.write_text(
            json.dumps(bad_assignment, indent=2) + "\n",
            encoding="utf-8",
        )
        bad_assignment["_source_path"] = str(bad_assignment_path)
        try:
            build(
                bad_assignment,
                config,
                config_path=config_path,
                output_dir=root / "bad-output",
            )
        except ValueError as exc:
            assert "does not match case manifest" in str(exc)
        else:
            raise AssertionError("assignment/manifest stratum mismatch accepted")

    print(
        "AR-P003 runner-bundle builder self-test passed: "
        "three-condition evidence symmetry, hidden-label separation, and build hashes."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build AR-P003 development reviewer bundles from frozen-style inputs."
    )
    parser.add_argument("assignment", nargs="?", help="Assignment JSON file")
    parser.add_argument("config", nargs="?", help="Runner build-config JSON file")
    parser.add_argument("--output-dir", help="New output directory")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            return run_self_test()

        if not args.assignment or not args.config or not args.output_dir:
            parser.error(
                "provide assignment, config, --output-dir, or use --self-test"
            )

        assignment_path = Path(args.assignment)
        config_path = Path(args.config)
        output_dir = Path(args.output_dir)
        if output_dir.exists():
            raise ValueError(
                "output directory already exists; use a new path to avoid "
                "silently overwriting a reviewer package"
            )

        build_schema = load_json(BUILD_SCHEMA)
        Draft202012Validator.check_schema(build_schema)
        config = load_json(config_path)
        config_errors = schema_errors(config, build_schema)
        if config_errors:
            raise ValueError(
                "build config is invalid: " + "; ".join(config_errors)
            )

        assignment = load_json(assignment_path)
        if not isinstance(assignment, dict):
            raise ValueError("assignment file must contain a JSON object")
        assignment["_source_path"] = str(assignment_path)

        output_dir.mkdir(parents=True, exist_ok=False)
        try:
            result = build(
                assignment,
                config,
                config_path=config_path,
                output_dir=output_dir,
            )
        except Exception:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise

        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (
        OSError,
        json.JSONDecodeError,
        SchemaError,
        ValueError,
        AssertionError,
    ) as exc:
        print(f"ERROR: runner bundle build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
