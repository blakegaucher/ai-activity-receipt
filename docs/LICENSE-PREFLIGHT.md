# Repository License Decision Preflight

> **Status:** Preflight clear; owner decision recorded as **Apache License 2.0**.  
> **Decision date:** 2026-09-21  
> **Copyright holder:** Blake Gaucher  
> This document is a technical/governance inventory, not legal advice or patent clearance.

Issue #44 required an explicit owner decision before the public repository could grant broad reuse rights. Blake Gaucher has now selected Apache-2.0 for covered project-authored public repository material.

## Preflight result

The live repository was rechecked before applying the decision.

- Direct Python requirements exactly match the machine-readable inventory.
- GitHub Action repositories used by the current workflows exactly match the inventory.
- All 21 locked package names exactly match the recorded transitive package-name snapshot.
- Every inventoried direct dependency, Action, and referenced DSSE implementation remains recorded as non-vendored.
- The current tree contains no obvious `vendor/`, `third_party/`, embedded dependency source subtree, or pre-existing project license/notice subtree.
- No new unresolved incompatible or unclear dependency/material issue was identified by this technical inventory check.

This result means the documented inventory did not reveal a new blocker. It does **not** constitute a legal compatibility opinion, patent clearance, or verification of every transitive package's current license text.

## Direct Python dependencies

Observed upstream license files were originally reviewed on 2026-09-19; the live requirement set was rechecked on 2026-09-21.

| Dependency | Current project range | Upstream repository | Observed upstream license | Vendored here? |
| --- | --- | --- | --- | --- |
| `jsonschema` | `jsonschema[format]>=4.23,<5` | `python-jsonschema/jsonschema` | MIT | No |
| `cryptography` | `cryptography>=50.0.1,<51` | `pyca/cryptography` | Apache-2.0 **or** BSD-3-Clause | No |

The exact CI snapshot in `requirements-lock.txt` contains transitive packages. Their package names are recorded in `research/third-party-inventory.json`; their source is not vendored here. Review exact upstream terms before redistributing or vendoring third-party source/assets.

## GitHub Actions dependencies

| Action repository | Repository use | Observed upstream license | Vendored here? |
| --- | --- | --- | --- |
| `actions/checkout` | repository checkout | MIT | No |
| `actions/setup-python` | CI Python setup | MIT | No |
| `actions/upload-artifact` | reproducibility-report upload | MIT | No |
| `github/codeql-action` | CodeQL advanced setup | MIT | No |

The workflows pin immutable commit SHAs. Pinning supports reproducibility and supply-chain discipline; it does not change upstream license obligations.

## DSSE and external specifications

The research DSSE prototype is project-authored code implementing documented DSSE v1 envelope/PAE behavior. The upstream `secure-systems-lab/dsse` repository's observed license is Apache-2.0, and upstream source is not vendored here.

The repository also references external standards/protocols including JSON Schema, W3C PROV / PROV-O, OpenTelemetry / GenAI conventions, Model Context Protocol, Agent2Agent, OAuth RFCs, C2PA, and DSSE.

References and interoperability mappings do not transfer ownership or license rights in those specifications to this project. Do not copy or adapt third-party text/source without checking and preserving applicable terms and notices.

## Owner licensing decision

The repository-wide default for **project-authored public material actually published here** is Apache License 2.0.

Covered material includes source code, validators and research utilities, adapters, benchmark tooling, the offline runner, project documentation, project-authored schemas, examples, synthetic fixtures, and synthetic benchmark material.

The complete standard Apache License 2.0 text is published as top-level `LICENSE`. `NOTICE` records Blake Gaucher's 2026 copyright attribution and the non-trademark/third-party boundary.

## Explicit exclusions and boundaries

Future human-study, participant, reviewer, hidden-analysis, personal, or privacy-sensitive material is **not** automatically authorized for public release by the repository license. Such material remains private unless a separate release, privacy, ethics, and licensing decision is explicitly made.

Third-party material remains governed by its applicable upstream terms and required notices. This repository license does not claim ownership of third-party specifications, libraries, Actions, standards, or adapted material.

Apache-2.0 does not grant trademark rights. Ancient Immortal Art and AI Activity Receipt names/branding are not made freely licensed trademarks or endorsement rights by this decision.

ARC / solver and other competition lanes remain separate. Do not transfer this licensing decision into another repository or competition without checking that lane's current rules.

## Machine-readable preflight

Run:

```bash
python research/validate_third_party_inventory.py
```

The check verifies direct requirements, workflow Action repositories, lock-package names, non-vendoring status, the Apache-2.0 `LICENSE`, `NOTICE` attribution, and the private/third-party/trademark boundaries. The aggregate reproducibility suite also binds `LICENSE` and `NOTICE`.

## Evidence boundary

Publishing Apache-2.0 grants reuse rights to covered public project material subject to the license terms.

It does **not** establish customer validation, commercial readiness, standards conformance, certification, patent clearance, trademark permission, human-study approval, security certification, or competition eligibility.
