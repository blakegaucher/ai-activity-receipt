#!/usr/bin/env python3
"""Validate repository-local Markdown links without network access.

This checker is intentionally narrow and deterministic:
- scans Markdown files present in the checkout;
- ignores external URLs, mailto links, sandbox links, and anchor-only links;
- resolves relative and repository-root-relative local paths;
- ignores fenced code blocks;
- validates ordinary inline links/images and reference-style definitions.

It does not attempt to validate remote URLs or Markdown anchor slugs.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}

INLINE_RE = re.compile(r"!?\\[[^\\]]*\\]\\(([^)]+)\\)")
REFERENCE_RE = re.compile(r"^\\s*\\[[^\\]]+\\]:\\s*(\\S+)")
FENCE_RE = re.compile(r"^\\s*(```|~~~)")


def markdown_files(root: Path) -> list[Path]:
    output: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            output.append(path)
    readme = root / "README.md"
    if readme.is_file() and readme not in output:
        output.append(readme)
    return sorted(set(output))


def strip_fenced_code(text: str) -> str:
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif token == fence:
                fence = None
            continue
        if fence is None:
            kept.append(line)
    return "\n".join(kept)


def normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]

    if not raw.strip().startswith("<"):
        for marker in (' "', " '"):
            if marker in target:
                target = target.split(marker, 1)[0].strip()
                break
    return target


def extract_targets(text: str) -> list[str]:
    cleaned = strip_fenced_code(text)
    targets = [normalize_target(match.group(1)) for match in INLINE_RE.finditer(cleaned)]
    for line in cleaned.splitlines():
        match = REFERENCE_RE.match(line)
        if match:
            targets.append(normalize_target(match.group(1)))
    return [target for target in targets if target]


def is_external_or_nonfile(target: str) -> bool:
    lowered = target.lower()
    if target.startswith("#"):
        return True
    if lowered.startswith(("mailto:", "tel:", "data:", "javascript:", "sandbox:")):
        return True

    parsed = urlsplit(target)
    return bool(parsed.scheme or parsed.netloc)


def resolve_local(source: Path, target: str, root: Path) -> Path | None:
    if is_external_or_nonfile(target):
        return None

    parsed = urlsplit(target)
    path_text = unquote(parsed.path)
    if not path_text:
        return None

    if path_text.startswith("/"):
        candidate = root / path_text.lstrip("/")
    else:
        candidate = source.parent / path_text

    return candidate.resolve()


def validate_links(root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    docs = markdown_files(root)
    local_count = 0

    root_resolved = root.resolve()
    for source in docs:
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(
                f"{source.relative_to(root)}: Markdown file is not UTF-8"
            )
            continue

        for target in extract_targets(text):
            resolved = resolve_local(source, target, root)
            if resolved is None:
                continue

            local_count += 1
            try:
                resolved.relative_to(root_resolved)
            except ValueError:
                errors.append(
                    f"{source.relative_to(root)} -> {target!r}: "
                    "local link escapes repository root"
                )
                continue

            if not resolved.exists():
                errors.append(
                    f"{source.relative_to(root)} -> {target!r}: target does not exist"
                )

    return errors, len(docs), local_count


def run_self_test() -> int:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        (root / "README.md").write_text(
            """# Demo

[Good](docs/GOOD.md)
[External](https://example.com/x)
[Anchor](#demo)
[Mail](mailto:test@example.com)
[Encoded](docs/with%20space.md)

~~~text
[Ignored broken](docs/nope.md)
~~~

[ref]: docs/GOOD.md
""",
            encoding="utf-8",
        )
        (root / "docs" / "GOOD.md").write_text(
            "[Back](../README.md)\n",
            encoding="utf-8",
        )
        (root / "docs" / "with space.md").write_text(
            "# ok\n",
            encoding="utf-8",
        )

        errors, docs, local = validate_links(root)
        assert not errors, errors
        assert docs == 3
        assert local == 4

        (root / "docs" / "BROKEN.md").write_text(
            "[Missing](missing.md)\n",
            encoding="utf-8",
        )
        errors, _, _ = validate_links(root)
        assert any("target does not exist" in error for error in errors)

        (root / "docs" / "ESCAPE.md").write_text(
            "[Outside](../../outside.md)\n",
            encoding="utf-8",
        )
        errors, _, _ = validate_links(root)
        assert any("escapes repository root" in error for error in errors)

    print("Repository Markdown-link checker self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate repository-local Markdown link targets."
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        try:
            return run_self_test()
        except AssertionError as exc:
            print(f"ERROR: self-test failed: {exc}", file=sys.stderr)
            return 2

    errors, doc_count, local_count = validate_links(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"Markdown link validation failed: {len(errors)} issue(s) across "
            f"{doc_count} Markdown files.",
            file=sys.stderr,
        )
        return 1

    print(
        "Markdown link validation passed: "
        f"{doc_count} Markdown files, {local_count} local link target(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
