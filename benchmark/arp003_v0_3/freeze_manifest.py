#!/usr/bin/env python3
"""Create a SHA-256 freeze manifest for AR-P003 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_manifest(paths: list[Path], root: Path) -> dict:
    artifacts = []
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_file():
            raise ValueError(f"not a file: {path}")
        try:
            relative = resolved.relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"artifact is outside root {root}: {path}") from exc
        artifacts.append(
            {
                "path": relative,
                "bytes": resolved.stat().st_size,
                "sha256": sha256_file(resolved),
            }
        )

    artifacts.sort(key=lambda item: item["path"])
    return {
        "manifest_version": "1",
        "protocol_id": "AR-P003",
        "protocol_version": "v0.3-draft",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "hash_algorithm": "sha256",
        "artifacts": artifacts,
    }


def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sample = root / "sample.txt"
        sample.write_bytes(b"abc")
        manifest = make_manifest([sample], root)
        entry = manifest["artifacts"][0]
        assert entry["path"] == "sample.txt"
        assert entry["bytes"] == 3
        assert (
            entry["sha256"]
            == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )
    print("AR-P003 freeze-manifest self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a SHA-256 manifest for frozen AR-P003 artifacts."
    )
    parser.add_argument("files", nargs="*", help="Files to include in the manifest")
    parser.add_argument(
        "--root",
        default=".",
        help="Root used for relative manifest paths (default: repository cwd)",
    )
    parser.add_argument("--output", help="Write manifest JSON to this path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.files:
        parser.error("provide one or more files, or use --self-test")

    try:
        manifest = make_manifest([Path(item) for item in args.files], Path(args.root))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
