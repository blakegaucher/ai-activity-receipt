#!/usr/bin/env python3
"""Lint AR-P003 v0.3 development case packages.

This tool enforces file separation, path safety, condition symmetry, stratum/
receipt-state consistency, neutral structured-control separation, and exact forbidden-marker scans. It does not prove
that a case is unbiased, realistic, or suitable for confirmatory human study.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parent
DEFAULT_SCHEMA = ROOT / "case-package.schema.json"

EXPECTED_RECEIPT_STATE = {
    "ordinary": "current",
    "stale_receipt": "stale",
    "incomplete_receipt": "incomplete",
    "conflicting_receipt": "conflicting",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def safe_relative_file(package_root: Path, raw: str) -> tuple[Path | None, str | None]:
    candidate = Path(raw)
    if candidate.is_absolute():
        return None, f"absolute paths are not allowed: {raw!r}"
    if any(part in {"", ".", ".."} for part in candidate.parts):
        return None, f"path must be a clean relative path without traversal: {raw!r}"

    root_resolved = package_root.resolve()
    resolved = (package_root / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        return None, f"path escapes the case package root: {raw!r}"

    if not resolved.is_file():
        return None, f"referenced file does not exist: {raw!r}"

    return resolved, None


def schema_errors(manifest: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(manifest),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def lint_package(
    manifest_path: Path,
    schema: dict[str, Any],
) -> tuple[list[str], dict[str, Any] | None]:
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{manifest_path}: unable to load manifest: {exc}"], None

    errors = schema_errors(manifest, schema)
    if errors or not isinstance(manifest, dict):
        return [f"{manifest_path}: {error}" for error in errors], None

    package_root = manifest_path.parent
    case_id = manifest["case_id"]

    expected_state = EXPECTED_RECEIPT_STATE.get(manifest["stratum"])
    if manifest["receipt_state"] != expected_state:
        errors.append(
            f"{manifest_path}: receipt_state {manifest['receipt_state']!r} does not "
            f"match stratum {manifest['stratum']!r}; expected {expected_state!r}"
        )

    reviewer_raw = list(manifest["reviewer_evidence_files"])
    structured_raw = manifest["structured_control_file"]
    receipt_raw = manifest["receipt_file"]
    analysis_raw = list(manifest["analysis_files"])

    reviewer_set = set(reviewer_raw)
    analysis_set = set(analysis_raw)

    if structured_raw in reviewer_set:
        errors.append(
            f"{manifest_path}: structured_control_file must be separate from "
            "reviewer_evidence_files"
        )
    if structured_raw == receipt_raw:
        errors.append(
            f"{manifest_path}: structured_control_file must be separate from receipt_file"
        )
    if structured_raw in analysis_set:
        errors.append(
            f"{manifest_path}: structured_control_file must be separate from analysis_files"
        )
    if receipt_raw in reviewer_set:
        errors.append(
            f"{manifest_path}: receipt_file must be separate from "
            "reviewer_evidence_files"
        )
    if receipt_raw in analysis_set:
        errors.append(
            f"{manifest_path}: receipt_file must be separate from analysis_files"
        )
    overlap = reviewer_set & analysis_set
    if overlap:
        errors.append(
            f"{manifest_path}: reviewer and analysis files overlap: "
            f"{sorted(overlap)!r}"
        )

    resolved: dict[str, Path] = {}
    for raw in reviewer_raw + [structured_raw, receipt_raw] + analysis_raw:
        path, error = safe_relative_file(package_root, raw)
        if error:
            errors.append(f"{manifest_path}: {error}")
        elif path is not None:
            resolved[raw] = path

    if errors:
        return errors, None

    reviewer_visible = reviewer_raw + [structured_raw, receipt_raw]
    markers = manifest["forbidden_reviewer_markers"]

    for marker in markers:
        needle = marker.encode("utf-8")
        for raw in reviewer_visible:
            data = resolved[raw].read_bytes()
            if needle in data:
                errors.append(
                    f"{manifest_path}: forbidden reviewer marker {marker!r} "
                    f"appears in reviewer-facing file {raw!r}"
                )

    if errors:
        return errors, None

    report = {
        "case_id": case_id,
        "stratum": manifest["stratum"],
        "receipt_state": manifest["receipt_state"],
        "condition_contract": manifest["condition_contract"],
        "reviewer_evidence": [
            {
                "path": raw,
                "sha256": sha256_file(resolved[raw]),
                "size_bytes": resolved[raw].stat().st_size,
            }
            for raw in reviewer_raw
        ],
        "structured_control": {
            "path": structured_raw,
            "sha256": sha256_file(resolved[structured_raw]),
            "size_bytes": resolved[structured_raw].stat().st_size,
        },
        "receipt": {
            "path": receipt_raw,
            "sha256": sha256_file(resolved[receipt_raw]),
            "size_bytes": resolved[receipt_raw].stat().st_size,
        },
        "analysis_files": [
            {
                "path": raw,
                "sha256": sha256_file(resolved[raw]),
                "size_bytes": resolved[raw].stat().st_size,
            }
            for raw in analysis_raw
        ],
        "forbidden_marker_count": len(markers),
    }
    return [], report


def run_self_test(schema: dict[str, Any]) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "evidence").mkdir()
        (root / "structured").mkdir()
        (root / "receipt").mkdir()
        (root / "analysis").mkdir()

        (root / "evidence" / "events.log").write_text(
            "2026-09-18T08:00:00Z tool=send_email status=completed\n",
            encoding="utf-8",
        )
        (root / "structured" / "events-table.md").write_text(
            "| time | operation | status |\\n|---|---|---|\\n|08:00|send_email|completed|\\n",
            encoding="utf-8",
        )
        (root / "receipt" / "receipt.json").write_text(
            '{"receipt_id":"dev-smoke","status":"current"}\n',
            encoding="utf-8",
        )
        (root / "analysis" / "gold.json").write_text(
            '{"gold":"GOLD_ONLY_MARKER"}\n',
            encoding="utf-8",
        )

        manifest = {
            "package_version": "AR-P003-v0.3-dev-case-v0.2",
            "case_id": "dev-smoke-ordinary",
            "stratum": "ordinary",
            "condition_contract": "same_evidence_plus_neutral_structured_or_receipt_v1",
            "reviewer_evidence_files": ["evidence/events.log"],
            "structured_control_file": "structured/events-table.md",
            "receipt_file": "receipt/receipt.json",
            "analysis_files": ["analysis/gold.json"],
            "receipt_state": "current",
            "forbidden_reviewer_markers": ["GOLD_ONLY_MARKER"],
            "notes": "Development-only smoke case.",
        }
        manifest_path = root / "case.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        errors, report = lint_package(manifest_path, schema)
        assert not errors, errors
        assert report is not None
        assert report["case_id"] == "dev-smoke-ordinary"
        assert report["reviewer_evidence"][0]["sha256"].startswith("sha256:")
        assert report["structured_control"]["sha256"].startswith("sha256:")

        # Gold/analysis material cannot be reviewer-facing.
        overlap = dict(manifest)
        overlap["reviewer_evidence_files"] = [
            "evidence/events.log",
            "analysis/gold.json",
        ]
        manifest_path.write_text(
            json.dumps(overlap, indent=2) + "\n",
            encoding="utf-8",
        )
        errors, _ = lint_package(manifest_path, schema)
        assert any("overlap" in error for error in errors)

        # Structured-control material must remain distinct from raw evidence.
        structured_overlap = dict(manifest)
        structured_overlap["structured_control_file"] = "evidence/events.log"
        manifest_path.write_text(
            json.dumps(structured_overlap, indent=2) + "\n",
            encoding="utf-8",
        )
        errors, _ = lint_package(manifest_path, schema)
        assert any("structured_control_file must be separate" in error for error in errors)

        # Path traversal must be rejected.
        traversal = dict(manifest)
        traversal["analysis_files"] = ["../outside.json"]
        manifest_path.write_text(
            json.dumps(traversal, indent=2) + "\n",
            encoding="utf-8",
        )
        errors, _ = lint_package(manifest_path, schema)
        assert any("traversal" in error for error in errors)

        # Exact leakage markers cannot appear in reviewer-facing files.
        leaked = dict(manifest)
        (root / "receipt" / "receipt.json").write_text(
            '{"receipt_id":"dev-smoke","leak":"GOLD_ONLY_MARKER"}\n',
            encoding="utf-8",
        )
        manifest_path.write_text(
            json.dumps(leaked, indent=2) + "\n",
            encoding="utf-8",
        )
        errors, _ = lint_package(manifest_path, schema)
        assert any("forbidden reviewer marker" in error for error in errors)

        # Restore clean receipt.
        (root / "receipt" / "receipt.json").write_text(
            '{"receipt_id":"dev-smoke","status":"current"}\n',
            encoding="utf-8",
        )

        # Stratum and declared Receipt state must agree.
        wrong_state = dict(manifest)
        wrong_state["stratum"] = "stale_receipt"
        manifest_path.write_text(
            json.dumps(wrong_state, indent=2) + "\n",
            encoding="utf-8",
        )
        errors, _ = lint_package(manifest_path, schema)
        assert any("does not match stratum" in error for error in errors)

        # Missing files fail closed.
        missing = dict(manifest)
        missing["receipt_file"] = "receipt/no-such-file.json"
        manifest_path.write_text(
            json.dumps(missing, indent=2) + "\n",
            encoding="utf-8",
        )
        errors, _ = lint_package(manifest_path, schema)
        assert any("does not exist" in error for error in errors)

    print("AR-P003 case-package linter self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint AR-P003 v0.3 development case-package manifests."
    )
    parser.add_argument(
        "manifests",
        nargs="*",
        help="One or more case.json package manifests.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
        help="Path to case-package JSON Schema.",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON report path.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic development smoke tests.",
    )
    args = parser.parse_args()

    try:
        schema = load_json(Path(args.schema))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load case-package schema: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        return run_self_test(schema)

    if not args.manifests:
        parser.error("provide at least one case manifest or use --self-test")

    reports: list[dict[str, Any]] = []
    all_errors: list[str] = []

    for raw in args.manifests:
        errors, report = lint_package(Path(raw), schema)
        all_errors.extend(errors)
        if report is not None:
            reports.append(report)

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    output = {
        "lint_version": "AR-P003-v0.3-case-lint-v0.1",
        "n_cases": len(reports),
        "cases": reports,
    }
    rendered = json.dumps(output, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
