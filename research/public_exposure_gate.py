#!/usr/bin/env python3
"""Fail closed on accidental public-repository exposure classes.

This is a repository hygiene gate, not a full DLP scanner. It never prints
matched secret values or source text.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "research" / "public-exposure-baseline.json"

SKIP_PARTS = {".git", ".venv", "venv", "__pycache__"}
TEXT_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".html", ".txt", ".toml", ".cff", ".sh"}

BLOCK_FILENAMES = {
    ".env", ".npmrc", ".pypirc", ".netrc",
    "credentials.json", "service-account.json", "wallet.dat",
    "id_rsa", "id_ed25519",
}
BLOCK_SUFFIXES = {".key", ".p12", ".pfx", ".jks", ".keystore", ".seed", ".mnemonic", ".kdbx", ".sqlite", ".sqlite3", ".db", ".dump", ".bak"}
REVIEW_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".tgz", ".gz", ".bz2", ".xz"}
REVIEW_TOKENS = {"private", "participant", "consent", "customer", "billing", "invoice", "finance", "medical", "personal", "hidden", "gold", "recruitment", "backup", "export", "dump", "wallet", "credential"}

PATTERNS = [
    ("private_key_material", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b")),
    ("github_fine_grained_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]

def baseline_paths() -> set[str]:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    return set(data.get("approved_review_paths", []))

def review_path(path: Path) -> bool:
    tokens = {p.lower() for p in path.parts}
    tokens |= set(re.split(r"[^a-z0-9]+", path.stem.lower()))
    return bool(tokens & REVIEW_TOKENS)

def main() -> int:
    approved = baseline_paths()
    block_findings: list[tuple[str, str]] = []
    review_findings: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        rel = str(path.relative_to(ROOT))
        lower_name = path.name.lower()
        suffix = path.suffix.lower()

        if lower_name in BLOCK_FILENAMES or suffix in BLOCK_SUFFIXES:
            block_findings.append((rel, "sensitive_file_type"))
            continue
        if suffix == ".pem" and not lower_name.endswith(".pub.pem"):
            block_findings.append((rel, "private_or_ambiguous_pem"))
            continue
        if suffix in REVIEW_SUFFIXES or review_path(path):
            review_findings.append(rel)

        if suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for category, pattern in PATTERNS:
            if pattern.search(text):
                block_findings.append((rel, category))

    new_review = sorted(set(review_findings) - approved)
    stale_baseline = sorted(approved - set(review_findings))

    if block_findings:
        for rel, category in sorted(set(block_findings)):
            print(f"ERROR: public exposure block: {rel} [{category}]", file=sys.stderr)
    if new_review:
        for rel in new_review:
            print(f"ERROR: new public-exposure review path is not approved in baseline: {rel}", file=sys.stderr)
    if stale_baseline:
        for rel in stale_baseline:
            print(f"NOTE: approved review path no longer matches and can be removed from baseline: {rel}")

    if block_findings or new_review:
        return 1

    print(
        "Public exposure gate passed: no blocked secret/private file classes and "
        f"{len(set(review_findings))} approved review-path finding(s)."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
