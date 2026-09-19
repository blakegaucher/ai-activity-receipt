#!/usr/bin/env python3
"""One-command reproducibility runner for the public research repository.

Runs the repository's deterministic/synthetic validation and research checks in
a fixed order, then emits a machine-readable report with SHA-256 hashes for the
executed scripts/schemas/protocol artifacts.

This is a reproducibility convenience layer. It does not upgrade synthetic or
engineering evidence into human-study, standards-conformance, production, or
real-world claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUITE_VERSION = "ai-activity-receipt-repro-v0.4"

CHECKS: list[dict[str, Any]] = [
    {
        "id": "receipt-fixtures",
        "argv": ["validate_receipts.py"],
        "artifacts": [
            "validate_receipts.py",
            "activity-receipt.schema.json",
        ],
    },
    {
        "id": "canonical-record-derivation",
        "argv": ["derive_receipt.py", "--self-test"],
        "artifacts": [
            "derive_receipt.py",
            "activity-record.schema.json",
            "activity-receipt.schema.json",
            "examples/canonical-record.json",
            "examples/derived-receipt.json",
        ],
    },
    {
        "id": "otel-genai-adapter",
        "argv": ["adapters/otel_genai.py", "--self-test"],
        "artifacts": [
            "adapters/otel_genai.py",
            "examples/otel-genai-traces.json",
            "examples/otel-adapter-context.json",
        ],
    },
    {
        "id": "mcp-2026-adapter",
        "argv": ["adapters/mcp_2026.py", "--self-test"],
        "artifacts": [
            "adapters/mcp_2026.py",
            "examples/mcp-2026-capture.json",
            "examples/mcp-adapter-context.json",
        ],
    },
    {
        "id": "cross-adapter-parity",
        "argv": ["adapters/cross_adapter_parity.py"],
        "artifacts": ["adapters/cross_adapter_parity.py"],
    },
    {
        "id": "interoperability-mappings",
        "argv": ["mappings/validate_mappings.py"],
        "artifacts": [
            "mappings/validate_mappings.py",
            "mappings/interoperability-v0.1.json",
            "mappings/interoperability-map.schema.json",
        ],
    },
    {
        "id": "delegation-chain-prototype",
        "argv": ["research/delegation_chain.py", "--self-test"],
        "artifacts": [
            "research/delegation_chain.py",
            "research/delegation-chain.schema.json",
            "research/delegation-chain-example.json",
        ],
    },
    {
        "id": "multi-hop-v0.2",
        "argv": ["research/multi_hop_v02.py"],
        "artifacts": [
            "research/multi_hop_v02.py",
            "research/candidate-record-v0.2.schema.json",
            "research/candidate-receipt-v0.3.schema.json",
            "research/candidate-record-v0.2.example.json",
        ],
    },
    {
        "id": "continuity-guard",
        "argv": ["research/validate_continuity_state.py"],
        "artifacts": [
            "research/validate_continuity_state.py",
            "research/project-continuity-state.json",
            "docs/PROJECT-CONTINUITY-2026-09-18.md",
            "docs/AR-P003-V0.2.3-HISTORICAL-BASELINE.md",
        ],
    },
    {
        "id": "repository-security-smoke",
        "argv": ["research/security_smoke_test.py"],
        "artifacts": [
            "research/security_smoke_test.py",
            ".github/dependabot.yml",
            ".github/CODEOWNERS",
            ".github/workflows/validate-receipts.yml",
            "SECURITY.md",
            "docs/SECURITY-HARDENING.md",
            "benchmark/arp003_v0_3/offline_runner.html",
            "benchmark/arp003_v0_3/runner-bundle.schema.json",
            "benchmark/arp003_v0_3/runner-response.schema.json",
            "benchmark/arp003_v0_3/runner-analysis.schema.json",
        ],
    },
    {
        "id": "heterogeneous-workflow-pilot",
        "argv": ["research/workflow_pilot.py"],
        "artifacts": [
            "research/workflow_pilot.py",
            "research/workflow-pilot/manifest.json",
        ],
    },
    {
        "id": "external-evidence-references",
        "argv": ["research/validate_external_evidence.py", "--self-test"],
        "artifacts": [
            "research/validate_external_evidence.py",
            "research/external-evidence-reference.schema.json",
            "research/external-evidence-reference.example.json",
        ],
    },
    {
        "id": "attestation-trust-policy",
        "argv": ["research/validate_attestation_policy.py", "--self-test"],
        "artifacts": [
            "research/validate_attestation_policy.py",
            "research/attestation-trust-policy.schema.json",
            "research/attestation-trust-policy.example.json",
        ],
    },
    {
        "id": "dsse-research-prototype",
        "argv": ["research/dsse_prototype.py"],
        "artifacts": [
            "research/dsse_prototype.py",
            "research/dsse-envelope.schema.json",
            "research/attestation-trust-policy.schema.json",
            "research/attestation-trust-policy.example.json",
        ],
    },
    {
        "id": "arp003-scorer",
        "argv": ["benchmark/arp003_v0_3/score_responses.py", "--self-test"],
        "artifacts": [
            "benchmark/arp003_v0_3/score_responses.py",
            "benchmark/arp003_v0_3/response-record.schema.json",
        ],
    },
    {
        "id": "arp003-assignment",
        "argv": ["benchmark/arp003_v0_3/generate_assignment.py", "--self-test"],
        "artifacts": ["benchmark/arp003_v0_3/generate_assignment.py"],
    },
    {
        "id": "arp003-case-package-lint",
        "argv": ["benchmark/arp003_v0_3/lint_case_packages.py", "--self-test"],
        "artifacts": [
            "benchmark/arp003_v0_3/lint_case_packages.py",
            "benchmark/arp003_v0_3/case-package.schema.json",
        ],
    },
    {
        "id": "arp003-planning",
        "argv": ["benchmark/arp003_v0_3/plan_sample_size.py", "--self-test"],
        "artifacts": [
            "benchmark/arp003_v0_3/plan_sample_size.py",
            "benchmark/arp003_v0_3/planning-scenarios.example.json",
        ],
    },
    {
        "id": "arp003-offline-runner-data",
        "argv": ["benchmark/arp003_v0_3/validate_runner_data.py", "--self-test"],
        "artifacts": [
            "benchmark/arp003_v0_3/validate_runner_data.py",
            "benchmark/arp003_v0_3/runner-bundle.schema.json",
            "benchmark/arp003_v0_3/runner-response.schema.json",
            "benchmark/arp003_v0_3/runner-bundle.example.json",
            "benchmark/arp003_v0_3/offline_runner.html",
        ],
    },
    {
        "id": "arp003-runner-merge",
        "argv": ["benchmark/arp003_v0_3/merge_runner_responses.py", "--self-test"],
        "artifacts": [
            "benchmark/arp003_v0_3/merge_runner_responses.py",
            "benchmark/arp003_v0_3/runner-analysis.schema.json",
            "benchmark/arp003_v0_3/runner-response.schema.json",
            "benchmark/arp003_v0_3/response-record.schema.json",
        ],
    },
    {
        "id": "arp003-runner-bundle-builder",
        "argv": ["benchmark/arp003_v0_3/build_runner_bundles.py", "--self-test"],
        "artifacts": [
            "benchmark/arp003_v0_3/build_runner_bundles.py",
            "benchmark/arp003_v0_3/runner-build-config.schema.json",
            "benchmark/arp003_v0_3/case-package.schema.json",
            "benchmark/arp003_v0_3/runner-bundle.schema.json",
            "benchmark/arp003_v0_3/runner-analysis.schema.json",
        ],
    },
    {
        "id": "arp003-pipeline-smoke",
        "argv": ["benchmark/arp003_v0_3/pipeline_smoke_test.py"],
        "artifacts": [
            "benchmark/arp003_v0_3/pipeline_smoke_test.py",
            "benchmark/arp003_v0_3/build_runner_bundles.py",
            "benchmark/arp003_v0_3/generate_assignment.py",
            "benchmark/arp003_v0_3/merge_runner_responses.py",
            "benchmark/arp003_v0_3/score_responses.py",
            "benchmark/arp003_v0_3/runner-build-config.schema.json",
            "benchmark/arp003_v0_3/runner-bundle.schema.json",
            "benchmark/arp003_v0_3/runner-analysis.schema.json",
            "benchmark/arp003_v0_3/runner-response.schema.json",
            "benchmark/arp003_v0_3/response-record.schema.json",
        ],
    },
    {
        "id": "arp003-freeze-manifest",
        "argv": ["benchmark/arp003_v0_3/freeze_manifest.py", "--self-test"],
        "artifacts": ["benchmark/arp003_v0_3/freeze_manifest.py"],
    },
]

BASE_ARTIFACTS = [
    "requirements.txt",
    "requirements-lock.txt",
    ".gitignore",
    ".github/dependabot.yml",
    ".github/CODEOWNERS",
    ".github/workflows/validate-receipts.yml",
    "SECURITY.md",
    "benchmark/arp003_v0_3/protocol.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def artifact_manifest() -> list[dict[str, Any]]:
    paths = set(BASE_ARTIFACTS)
    for check in CHECKS:
        paths.update(check["artifacts"])

    output: list[dict[str, Any]] = []
    for raw in sorted(paths):
        path = ROOT / raw
        if not path.is_file():
            raise FileNotFoundError(f"repro artifact is missing: {raw}")
        output.append(
            {
                "path": raw,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return output


def run_check(check: dict[str, Any]) -> dict[str, Any]:
    command = [sys.executable, *check["argv"]]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "id": check["id"],
        "argv": check["argv"],
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_suite() -> dict[str, Any]:
    # Validate protocol JSON explicitly; the individual benchmark utilities may
    # not all read it during self-test.
    protocol_path = ROOT / "benchmark" / "arp003_v0_3" / "protocol.json"
    with protocol_path.open("r", encoding="utf-8") as handle:
        protocol = json.load(handle)
    if not isinstance(protocol, dict):
        raise ValueError("AR-P003 protocol.json must contain a JSON object")

    results = [run_check(check) for check in CHECKS]
    passed = all(item["passed"] for item in results)

    return {
        "suite_version": SUITE_VERSION,
        "status": "passed" if passed else "failed",
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "n_checks": len(results),
        "n_passed": sum(1 for item in results if item["passed"]),
        "n_failed": sum(1 for item in results if not item["passed"]),
        "checks": results,
        "artifact_manifest": artifact_manifest(),
        "evidence_boundary": (
            "This report reproduces repository-local deterministic/synthetic "
            "checks only. It is not a human-study result, standards certificate, "
            "production security audit, or proof of real-world effectiveness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the AI Activity Receipt repository reproducibility suite."
    )
    parser.add_argument(
        "--output",
        help="Optional path for the machine-readable JSON report.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-check terminal summaries; JSON output is unchanged.",
    )
    args = parser.parse_args()

    try:
        report = run_suite()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: reproducibility suite setup failed: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        for item in report["checks"]:
            status = "PASS" if item["passed"] else "FAIL"
            print(f"{status}: {item['id']}")
            if not item["passed"]:
                if item["stdout"]:
                    print(item["stdout"], file=sys.stderr, end="")
                if item["stderr"]:
                    print(item["stderr"], file=sys.stderr, end="")

        print(
            f"Reproducibility suite: {report['n_passed']}/"
            f"{report['n_checks']} checks passed."
        )

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    elif args.quiet:
        sys.stdout.write(rendered)

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
