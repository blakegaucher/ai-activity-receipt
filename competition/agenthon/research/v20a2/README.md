# Agenthon Track 4: source-only v20a.2 manifest-hardening review

**DRAFT / NOT INTEGRATED / NO DOCKER / NO PUBLIC IMAGE / NO OFFICIAL SCORE.**

This separate version addresses a concrete parser discrepancy discovered when reviewing the already preserved v20a.1 PR [#119](https://github.com/blakegaucher/ai-activity-receipt/pull/119). Never rewrite, delete, merge, relabel or retroactively alter v20a.1 evidence.

## Authority and pinned dependencies

AIAR branch parent `21c6ae6536c8fb8727521789d4e4c9f74b9d82b0`. Official public Track 4 `Agenthon-2026/track4-analysis-public@5d3b726a49b8ea218543e4d24319895874dcff6e`; toolkit/scorer `Agenthon-2026/Agenthon2026-public@bd01548e34d21fd660d88fd06157078fb25ece4e` (v2.6.0). Historical v20 Docker smoke [#38191311123](https://github.com/blakegaucher/ai-activity-receipt/actions/runs/38191311123) tested the **unmodified baseline**, not this source-only candidate.

## Source overlay and new security/validity checks

Create a **fresh temporary copy** of the official pinned `baselines/baseline_agent/`. Overlay only `overlay/baseline_agent/cli.py` (the unchanged v20a.1 CLI file) and `overlay/baseline_agent/entity_filter.py` (new v20a.2 version). Never copy into a live release workflow without fresh authorization.

The overlay follows the task-declared `manifest.json` (official exemplar) or `corpus/manifest.json` (ten practice units), selects only documents admitting the entity through `entity_ids` or `shared`, filters both retrieval and fallback, and refuses fabricated fallback citation when no eligible evidence exists.

**Versioned differences from v20a.1:** explicitly reject `shared: false`, documents both `shared:true` and nonempty `entity_ids`, duplicate or empty entity labels, corpus filename/ID mismatches, malformed dates, missing or altered manifest SHA-256 digests, symlinked/missing corpus files and invalid corpus path structures. These additional constraints follow the published official scorer's manifest policy; if a hidden organizer unit diverges, report a refusal, not a guaranteed hidden-unit success.

## Evidence (SOURCE-ONLY, NOT A CodaBench score)

- 10 public practice units, 77 roster entities: original official deterministic rail **17 wrong-entity findings**, this candidate **0**; no date/span failures.
- Both sides report **10 `claim_tokens_unchecked`** notices: current-source judge tokenizer/NLI unavailable.
- 11 public outputs passed pinned `analysis.schema.json` (10 practice + 1 exemplar).
- Public worked exemplar output remained byte-exact frozen SHA-256 `e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2`.
- **8/8** new synthetic local adversarial tests pass (`tests/test_guard.py`), explicitly exercising the three v20a.1-to-scorer divergences, digest tampering, malformed dates and wrong document IDs.
- Raw per-unit results, source hashes and test metadata: `evidence/V20A2_SOURCE_ONLY_VALIDATION.json`. Original older results in v20a.1 preserved unmodified.

## Reproduction / protected boundary

```sh
TRACK=/path/to/pinned/official-track4
REVIEW=/path/to/this/competition/agenthon/research/v20a2
SCRATCH=$(mktemp -d)
cp -R "$TRACK/baselines/baseline_agent" "$SCRATCH/baseline_agent"
cp "$REVIEW/overlay/baseline_agent/cli.py" "$SCRATCH/baseline_agent/cli.py"
cp "$REVIEW/overlay/baseline_agent/entity_filter.py" "$SCRATCH/baseline_agent/entity_filter.py"
PYTHONPATH="$SCRATCH" python -m unittest discover -s "$REVIEW/tests" -v
```

**No official NLI faithfulness, 400-token cap, ranking, forecast calibration, hidden units, exploitability risk acceptance, inherited GPL/LGPL/MPL notices or v20 image license-release decision is established.** The retained v20 image had **55 High** scanner matches. No code signing, Team Key use, Docker run, new OCI build, registry publish, CodaBench upload, registration or merge is approved. Controlled issue [#93](https://github.com/blakegaucher/ai-activity-receipt/issues/93) governs the CONDITIONAL/NO-GO decision.
