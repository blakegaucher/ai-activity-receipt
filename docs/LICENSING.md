# Licensing Status

> **Status:** Governance decision still open.

This repository does not currently include an explicit open-source license.

That means the project should not describe the repository as MIT-, Apache-, CC-, or otherwise open-source licensed until Blake Gaucher / Ancient Immortal Art deliberately selects and publishes a license.

## Decision preflight completed

The factual preflight is now published at [Repository License Decision Preflight](LICENSE-PREFLIGHT.md).

It records:

- direct Python dependencies and observed upstream license files;
- external GitHub Action repositories used by the workflows;
- the exact transitive lock-package name snapshot;
- the DSSE reference implementation boundary;
- standards/specification citation boundaries;
- a machine-readable inventory and drift check.

This reduces the remaining work to an explicit owner/IP decision. It does **not** grant a license or provide legal clearance.

## Why this is kept explicit

The repository is public for research transparency and reproducibility, but public visibility and an open-source license are different things.

Before a broader external-reproduction or contribution phase, the project should decide:

- whether code and documentation use the same or different licenses;
- whether synthetic benchmark fixtures are covered by the code license;
- whether any third-party-derived material requires notices or different terms;
- how future human-study material will be licensed, if released at all.

## License-decision preflight now available

A dated dependency/action/protocol-reference inventory and owner decision checklist are available at [LICENSE-PREFLIGHT.md](LICENSE-PREFLIGHT.md).

The machine-readable inventory is `research/third-party-inventory.json`, with a deterministic drift check at `research/validate_third_party_inventory.py`.

This preparation does **not** select or grant a license. The owner decision remains open.

## Third-party material

References to standards, protocols, specifications, or external projects do not transfer their licenses to this repository.

Any copied or adapted third-party source must retain the notices required by its own license.

## Current project rule

Until an explicit license is published:

- do not state that this repository is licensed under a named open-source license;
- do not imply that public availability is permission for unrestricted reuse;
- track licensing as a release/governance prerequisite rather than silently choosing terms during technical development.

This file records repository status only and is not legal advice.
