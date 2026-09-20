#!/usr/bin/env python3
"""Deterministically validate repository JSON assets without network access.

Checks:
- every repository JSON file parses as UTF-8 JSON;
- duplicate object keys are rejected at any nesting depth;
- files declaring JSON Schema draft 2020-12 are themselves valid schemas.

This is a repository-integrity check, not validation of every instance against
its corresponding schema.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "private-study-data",
}


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(f"duplicate object key: {key!r}")
        obj[key] = value
    return obj


def json_files(root: Path) -> list[Path]:
    output: list[Path] = []
    for path in root.rglob("*.json"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            output.append(path)
    return sorted(output)


def load_strict(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text, object_pairs_hook=reject_duplicate_keys)


def is_draft_2020_12_schema(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    declaration = value.get("$schema")
    return (
        isinstance(declaration, str)
        and "json-schema.org/draft/2020-12/schema" in declaration
    )


def validate_json_assets(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    files = json_files(root)
    schema_count = 0

    for path in files:
        rel = path.relative_to(root)
        try:
            value = load_strict(path)
        except UnicodeDecodeError as exc:
            errors.append(f"{rel}: not valid UTF-8 ({exc})")
            continue
        except DuplicateKeyError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        except json.JSONDecodeError as exc:
            errors.append(
                f"{rel}: invalid JSON at line {exc.lineno}, "
                f"column {exc.colno}: {exc.msg}"
            )
            continue

        if is_draft_2020_12_schema(value):
            schema_count += 1
            try:
                Draft202012Validator.check_schema(value)
            except SchemaError as exc:
                errors.append(f"{rel}: invalid JSON Schema: {exc.message}")

    return errors, len(files), schema_count


def run_self_test() -> int:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ok.json").write_text(
            json.dumps({"a": 1, "nested": {"b": 2}}),
            encoding="utf-8",
        )
        (root / "schema.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {"x": {"type": "string"}},
                }
            ),
            encoding="utf-8",
        )

        errors, count, schemas = validate_json_assets(root)
        assert not errors, errors
        assert count == 2
        assert schemas == 1

        (root / "duplicate.json").write_text(
            '{"x": 1, "x": 2}\n',
            encoding="utf-8",
        )
        errors, _, _ = validate_json_assets(root)
        assert any("duplicate object key" in error for error in errors)

        (root / "broken.json").write_text(
            '{"x":',
            encoding="utf-8",
        )
        errors, _, _ = validate_json_assets(root)
        assert any("invalid JSON" in error for error in errors)

        (root / "bad-schema.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": 7,
                }
            ),
            encoding="utf-8",
        )
        errors, _, _ = validate_json_assets(root)
        assert any("invalid JSON Schema" in error for error in errors)

    print("Repository JSON-integrity checker self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate repository JSON syntax, duplicate keys, and schemas."
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        try:
            return run_self_test()
        except AssertionError as exc:
            print(f"ERROR: self-test failed: {exc}", file=sys.stderr)
            return 2

    errors, file_count, schema_count = validate_json_assets(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"Repository JSON validation failed: {len(errors)} issue(s) across "
            f"{file_count} JSON files.",
            file=sys.stderr,
        )
        return 1

    print(
        "Repository JSON validation passed: "
        f"{file_count} JSON files, {schema_count} draft-2020-12 schema(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
