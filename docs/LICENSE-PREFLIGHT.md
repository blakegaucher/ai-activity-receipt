# Repository License Decision Preflight

> **Status:** Preparation only — no repository license has been selected.  
> **Snapshot:** 2026-09-19  
> This document is a technical/governance inventory, not legal advice.

The repository is public, but public visibility is not the same as an open-source license.

Issue #44 intentionally keeps the owner decision open. This preflight reduces the factual work needed before Blake Gaucher / Ancient Immortal Art chooses terms.

## Current repository status

- no top-level `LICENSE` file is present;
- `docs/LICENSING.md` explicitly records that no open-source license has been selected;
- the repository should not currently be described as MIT-, MIT-0-, Apache-, BSD-, CC-, or otherwise open-source licensed;
- technical reviewers may inspect the public repository, but broad reuse/redistribution permission should not be inferred from public visibility.

## Direct Python dependencies

Observed upstream license files were reviewed on 2026-09-19.

| Dependency | Current project range | Upstream repository | Observed upstream license | Vendored here? |
| --- | --- | --- | --- | --- |
| `jsonschema` | `jsonschema[format]>=4.23,<5` | `python-jsonschema/jsonschema` | MIT | No |
| `cryptography` | `cryptography>=50.0.1,<51` | `pyca/cryptography` | Apache-2.0 **or** BSD-3-Clause | No |

The exact CI snapshot in `requirements-lock.txt` also contains transitive packages.

Their names are captured in `research/third-party-inventory.json`, but this pass did **not** individually reverify every transitive package's current license text because their source is not vendored in this repository.

Before vendoring or redistributing third-party package source/assets, review the exact upstream terms for that material.

## GitHub Actions dependencies

The committed workflows currently reference these external Action repositories:

| Action repository | Repository use | Observed upstream license | Vendored here? |
| --- | --- | --- | --- |
| `actions/checkout` | repository checkout | MIT | No |
| `actions/setup-python` | CI Python setup | MIT | No |
| `actions/upload-artifact` | reproducibility-report upload | MIT | No |
| `github/codeql-action` | CodeQL advanced setup | MIT | No |

The workflows pin immutable commit SHAs. Pinning improves reproducibility/supply-chain discipline; it does not change upstream license obligations.

## DSSE reference implementation

The research DSSE prototype is project code implementing the documented DSSE v1 envelope/PAE behavior.

The upstream `secure-systems-lab/dsse` repository's observed license is Apache-2.0.

The upstream source package is not vendored in this repository.

The project documentation cites the protocol and upstream implementation for comparison/test-vector context. Any future direct copying/adaptation of source must preserve whatever notices the applicable upstream license requires.

## Standards and specifications referenced

The repository also references external standards/protocols such as:

- JSON Schema;
- W3C PROV / PROV-O;
- OpenTelemetry / GenAI conventions;
- Model Context Protocol;
- Agent2Agent;
- OAuth RFCs;
- C2PA;
- DSSE.

A citation or interoperability mapping is not the same thing as incorporating the standard's source code or relicensing its text.

Do not copy large specification text into the repository without checking the applicable publication/license terms.

## Repository-tree observation

At this snapshot, the repository tree contains project code, schemas, examples, documentation, workflows, and benchmark/research artifacts.

No `vendor/`, `third_party/`, embedded package source tree, or other obvious vendored dependency subtree is present.

That observation reduces one licensing risk, but it is not a legal originality opinion.

## Candidate owner choices

The project owner still needs to choose the repository's licensing model deliberately.

Common permissive options to consider include:

| Option | Practical characteristic | Decision consideration |
| --- | --- | --- |
| **MIT-0** | very short permissive software license without an attribution condition | low-friction reuse; no express patent grant |
| **MIT** | short permissive software license with notice preservation | familiar and broadly used |
| **Apache-2.0** | permissive license with explicit patent terms and notice requirements | stronger patent language; more compliance text |
| **BSD-3-Clause** | permissive software license with notice and non-endorsement terms | familiar alternative to MIT |
| **CC0** | public-domain dedication/fallback-license approach | often considered for data/fixtures; software use should be chosen deliberately |

This table does **not** recommend or select a license.

## Scope decisions the owner should make

Before closing the license-governance issue, decide separately what covers:

1. **Project-authored source code**
   - validators;
   - adapters;
   - research utilities;
   - benchmark tooling;
   - offline runner.

2. **Project documentation**
   - README/docs;
   - architecture notes;
   - research writeups.

3. **Synthetic schemas/examples/fixtures**
   - JSON Schemas;
   - synthetic Receipt/record examples;
   - synthetic benchmark material.

4. **Future human-study material**
   - participant/reviewer responses should remain private unless a separate ethics/privacy/release decision is made;
   - a repository code license should not automatically be assumed to authorize publication of human-participant data.

5. **Competition reuse**
   - ARC/competition work is a separate project lane;
   - if code from this repository is ever reused in a competition entry, check that competition's current license/open-source rules at that time rather than silently transferring assumptions between lanes.

## Machine-readable preflight

Run:

```bash
python research/validate_third_party_inventory.py
```

The check verifies only repository consistency:

- each direct Python requirement is listed;
- each external GitHub Action repository used by current workflows is listed;
- the exact lock-package names match the transitive snapshot list;
- current inventory entries state that upstream source is not vendored;
- `docs/LICENSING.md` still records the no-license state.

It does **not** determine legal compatibility or choose terms.

## Recommended decision sequence

1. Review this preflight and issue #44.
2. Decide whether code/docs/fixtures use one license or separate licenses.
3. If needed, obtain legal advice for patent, Indigenous IP/cultural material, commercial, or contributor questions.
4. Publish the selected license file(s).
5. Update `docs/LICENSING.md`, README, CONTRIBUTING, CITATION, continuity state, and issue #44.
6. Re-run CI, CodeQL, and the aggregate reproducibility suite.
7. Only then describe the repository using the selected license name.

## Evidence boundary

Completing this preflight means the project has a documented dependency/action inventory and a clearer owner decision path.

It does **not** grant permission, provide legal clearance, certify third-party-license compatibility, or make the repository open source.
