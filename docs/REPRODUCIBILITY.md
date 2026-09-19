# One-Command Reproducibility Suite

> **Status:** Public engineering/research reproducibility helper.  
> **Snapshot:** 2026-09-19  
> Passing this suite does not convert synthetic or development evidence into a human-study result, standards certificate, production security audit, or proof of real-world benefit.

The repository now exposes one command that runs the current deterministic and synthetic checks in a fixed order and emits a machine-readable report:

```bash
python research/reproduce.py --output reproducibility-report.json
```

The runner is intended to make it easier for another developer, reviewer, competition judge, or collaborator to reproduce the repository-local claims without first reconstructing the GitHub Actions workflow by hand.

## What it runs

The suite currently executes:

- public Receipt fixture validation;
- canonical-record derivation self-test;
- OpenTelemetry GenAI adapter self-test;
- MCP 2026-07-28 adapter self-test;
- cross-adapter normalization parity;
- machine-readable interoperability mapping validation;
- standalone delegation-chain prototype;
- candidate-record-v0.2 multi-hop migration/derivation tests;
- heterogeneous synthetic workflow pilot;
- external evidence-reference / C2PA reference checks;
- attestation trust-policy validation;
- research-only DSSE signing/verification checks;
- AR-P003 scorer tests;
- AR-P003 assignment balance tests;
- AR-P003 case-package linting;
- AR-P003 sample-size/precision planning tests;
- AR-P003 offline-runner data and no-network checks;
- AR-P003 response/gold merge tests;
- AR-P003 assignment-to-runner bundle-builder tests;
- AR-P003 end-to-end assignment → bundle → merge → scoring smoke test;
- AR-P003 freeze-manifest tests;
- repository security smoke checks for workflow permissions, immutable Action refs, checkout credentials, Dependabot/CODEOWNERS metadata, offline-runner boundaries, private-study ignore rules, and high-confidence secret markers.

The AR-P003 protocol JSON is also parsed explicitly before the suite runs.

## Machine-readable report

The JSON report records:

- suite version;
- Python implementation/version;
- check ID;
- command arguments;
- exit code;
- pass/fail state;
- captured stdout/stderr;
- SHA-256 and byte size for the scripts, schemas, fixtures, protocol files, supported-range requirements, exact tested dependency lock, ignore rules, and CI workflow used by the suite;
- the explicit evidence boundary.

This gives a reviewer both the execution result and a content manifest of the important artifacts that were actually used.

## Why the artifact manifest matters

A statement such as:

```text
17/17 checks passed
```

is incomplete if the reader cannot tell which versions of the validators and schemas were used.

The reproducibility report therefore binds the result to a deterministic set of repository artifacts through SHA-256 file hashes.

It is still not a signed release manifest or trusted timestamp. It is a reproducibility aid.

## Failure behavior

Every check runs as a separate child Python process.

The suite:

- continues through all checks so one failure does not hide later failures;
- records stdout and stderr for each check;
- exits non-zero when any check fails;
- exits with setup error when required artifacts/protocol files are missing or malformed.

GitHub Actions runs this aggregate suite in addition to the individually named CI steps. The duplication is deliberate during this research phase: the individual steps remain easy to diagnose, while the aggregate runner tests the exact workflow an external reviewer can use.

## Reproduce locally

From the repository root, the closest reproduction of the currently tested CI environment is:

```bash
python -m pip install -r requirements-lock.txt
python research/reproduce.py --output reproducibility-report.json
```

The CI snapshot is pinned to CPython **3.12.14**. `requirements-lock.txt` records the exact dependency versions observed in the tested GitHub Actions environment.

For ordinary development against the project's supported version ranges instead of the exact snapshot:

```bash
python -m pip install -r requirements.txt
```

A successful run prints a concise per-check summary.

For JSON-only output to standard output:

```bash
python research/reproduce.py --quiet
```

## CI hardening

The public workflow pins checkout/setup/upload Actions to exact commit SHAs, limits the primary workflow token to `contents: read`, disables checkout credential persistence, applies a 20-minute job timeout, cancels obsolete in-progress runs for the same ref, pins CPython 3.12.14, installs the exact dependency snapshot, runs the repository security smoke test, and uploads the machine-readable reproducibility report as a workflow artifact.

Current tested dependency/action refresh (2026-09-19): `cryptography==50.0.1`, checkout 7.0.1, setup-python 7.0.0, and upload-artifact 7.0.1. The Actions are still referenced by full immutable commit SHA in the workflow; version numbers here are readability metadata.

The repository also publishes weekly Dependabot version-update configuration for pip and GitHub Actions, plus CODEOWNERS metadata for security/evidence-sensitive paths.

This reduces avoidable environment and repository-governance drift. It does not make GitHub-hosted infrastructure or the dependency supply chain independently trusted, and it does not replace CodeQL, secret scanning, private vulnerability reporting, or branch/ruleset administration.

---

## What this does not establish

A green report does not establish:

- human audit benefit;
- statistical significance;
- external standards conformance;
- complete real-world telemetry capture;
- production authorization correctness;
- production cryptographic trust;
- legal/regulatory compliance;
- independent external reproduction.

The last item matters: a project-authored reproducibility harness is preparation for external evaluation, not external evaluation itself.

## External-evaluation next step

The practical next step is to give an independent person or organization:

1. a clean repository checkout;
2. the one-command instructions above;
3. no undocumented setup help beyond ordinary dependency installation;
4. a place to record any mismatch, ambiguity, or missing assumption.

Phase 6 should only be marked complete after at least one independent party actually performs that work.

For outside reproduction attempts, the repository now provides a dedicated GitHub **reproducibility issue form** that asks for the exact commit, Python version, dependency path, commands, outcome, and environment while explicitly prohibiting secrets or participant/hidden-analysis data.


---

## Independent reviewer handoff

A public clean-room handoff is available at [EXTERNAL-REPRODUCTION-HANDOFF.md](EXTERNAL-REPRODUCTION-HANDOFF.md).

It asks an independent reviewer to record the exact commit/environment, install the exact dependency lock, run the aggregate suite without undocumented project help, preserve favorable or unfavorable results, and report the first mismatch or hidden prerequisite.

The first independent reproduction remains an **external gate**. Publishing the handoff does not satisfy it.
