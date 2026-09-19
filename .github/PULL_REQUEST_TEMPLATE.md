## Summary

Describe the change and the concrete problem, failure mode, or research need it addresses.

## Evidence boundary

State what this change **does** establish and what it **does not** establish.

## Validation

- [ ] I ran `python research/reproduce.py --output reproducibility-report.json`, or explained why it does not apply.
- [ ] New/changed cross-component behavior has a deterministic test where practical.
- [ ] I did not silently rewrite a frozen benchmark/result.
- [ ] I updated documentation when behavior, evidence status, or claim boundaries changed.

## Data and safety

- [ ] No passwords, API keys, tokens, credentials, private chain-of-thought, identifiable participant data, reviewer exports, or hidden gold/analysis material are included.
- [ ] Any copied/adapted third-party material has appropriate provenance/notices.
- [ ] This PR does not upgrade synthetic/engineering evidence into a human-benefit, compliance, standards-conformance, or institutional-endorsement claim.

## Notes for reviewers

Call out any migration, compatibility, privacy, reproducibility, or licensing concern that deserves special attention.
