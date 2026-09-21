#!/usr/bin/env python3
"""Render the AR-P003 neutral structured-control event table.

The renderer consumes a valid candidate Activity Record and exposes only
mechanical event organization: event ID, time, actor, operation, execution
status, and source references.

It deliberately does not expose record materiality, consequentiality,
authorization classification, verification summaries, incidents, Receipt
fields, or gold labels. Those are part of the semantic/audit layer that the
structured-control condition is intended to distinguish from generic
organization.

This is development-only study infrastructure. A deterministic rendering does
not by itself prove that the canonical record is complete or faithful to the
underlying heterogeneous evidence; final case methodology review must assess
that evidence-symmetry claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from derive_receipt import record_semantic_errors, validate_record_structure  # noqa: E402

SCHEMA = ROOT / "activity-record.schema.json"
RENDERER_VERSION = "AR-P003-v0.3-neutral-event-table-v0.1"
COLUMNS = ("event_id", "occurred_at", "actor_id", "operation", "status", "source_refs")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _cell(value: Any) -> str:
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value)
    elif value is None:
        text = ""
    else:
        text = str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_record(record: dict[str, Any]) -> str:
    schema = load_json(SCHEMA)
    structural = validate_record_structure(record, schema)
    if structural:
        raise ValueError("record is structurally invalid: " + "; ".join(structural))
    semantic = record_semantic_errors(record)
    if semantic:
        raise ValueError("record is semantically invalid: " + "; ".join(semantic))

    lines = [
        "| event_id | occurred_at | actor_id | operation | status | source_refs |",
        "|---|---|---|---|---|---|",
    ]
    for event in record["events"]:
        values = [
            event.get("event_id"),
            event.get("occurred_at"),
            event.get("actor_id"),
            event.get("operation"),
            event.get("status"),
            event.get("source_refs") or [],
        ]
        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")
    return "\n".join(lines) + "\n"


def render_file(path: Path) -> str:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError("canonical record must contain a JSON object")
    return render_record(value)


def run_self_test() -> int:
    record = load_json(ROOT / "examples" / "canonical-record.json")
    rendered = render_record(record)

    assert "event-debug" in rendered
    assert "event-1" in rendered
    assert "internal_cache_lookup" in rendered
    assert "send_email" in rendered
    assert "src-A" in rendered

    # These interpretive fields exist in the canonical record but are
    # intentionally absent from the neutral presentation.
    for prohibited in (
        "material",
        "consequential",
        "authorization",
        "verification",
        "incident",
        "approved",
    ):
        assert prohibited not in rendered.lower()

    assert rendered == render_record(record)

    bad = json.loads(json.dumps(record))
    bad["events"][0]["event_id"] = ""
    try:
        render_record(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid canonical record was rendered")

    print(
        "AR-P003 neutral structured-control renderer self-test passed: "
        "deterministic event organization without Receipt/audit semantic fields."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a neutral AR-P003 event table from a canonical Activity Record."
    )
    parser.add_argument("record", nargs="?", help="Canonical Activity Record JSON")
    parser.add_argument("--output", help="Optional Markdown output path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if not args.record:
        parser.error("provide a canonical record JSON file or use --self-test")

    try:
        rendered = render_file(Path(args.record))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: structured-control rendering failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
