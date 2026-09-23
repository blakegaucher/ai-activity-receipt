# Public Exposure Gate

This public repository now has a second repository-hygiene layer in addition to the existing high-confidence secret scanner.

The gate fails when a change introduces:

- common credential/private-key/wallet/database/backup file types;
- high-confidence private-key or supported credential patterns in tracked text;
- a new path whose name suggests private/customer/participant/consent/hidden-gold/finance/medical/backup material unless that exact path is explicitly reviewed in the baseline.

The gate deliberately prints only the **path and category**, never the matched secret or source text.

Two current paths are explicitly approved because they are intentionally public methodology/negative-fixture artifacts:

- `docs/AR-P003-V0.3-RECRUITMENT-ELIGIBILITY.md`;
- `examples/invalid-private-reasoning-field.json`.

Approval of a filename is not approval to place real participant, customer, consent, private-reasoning, credential, or hidden-analysis data there.

The gate complements, rather than replaces, GitHub secret scanning/push protection and manual privacy/licensing review. If a real credential is ever exposed publicly, rotate or revoke it first; deleting the file later does not make the old credential safe.
