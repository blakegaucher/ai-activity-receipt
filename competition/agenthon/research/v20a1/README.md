# Agenthon Track 4 — manifest-bound citation repair v20a.1 (DRAFT REVIEW ONLY)

**DO NOT MERGE, BUILD, PUBLISH OR SUBMIT without separate explicit owner authorization.** This is an isolated, source-only **overlay**, not the live v20 container or a complete runnable package. It does not import private AI Activity Receipt study data or change AR-P003.

## Exact frozen sources

- Base AIAR main at branch creation: `21c6ae6536c8fb8727521789d4e4c9f74b9d82b0`.
- Organizer Track 4 reference: `Agenthon-2026/track4-analysis-public@5d3b726a49b8ea218543e4d24319895874dcff6e`.
- Toolkit/scorer tag `v2.6.0`: `Agenthon-2026/Agenthon2026-public@bd01548e34d21fd660d88fd06157078fb25ece4e`.
- Historical v20 Docker smoke [#38191311123](https://github.com/blakegaucher/ai-activity-receipt/actions/runs/38191311123): one-exemplar pass, **not** this overlay.
- Controls and immutable audits: [AIAR issue #93](https://github.com/blakegaucher/ai-activity-receipt/issues/93).

## Proposal and application boundary

Copy the **unchanged pinned organizer** `baselines/baseline_agent/` package into a **fresh local scratch directory** and overlay exactly two files:

- `overlay/baseline_agent/entity_filter.py` adds manifest-labelled admissibility; a document must list the target in `entity_ids` or be marked `shared`, and an incomplete manifest fails closed.
- `overlay/baseline_agent/cli.py` uses the task-declared `corpus_manifest` to restrict **both primary retrieval and citation fallback** to admissible documents. A missing qualifying citation is a failure, never an unrelated invented citation.

The exemplar declares a root `manifest.json`; ten practice units declare `corpus/manifest.json`. The original v20a prototype **failed on the exemplar** because it assumed a corpus-local manifest; that negative result is preserved, and this separately versioned v20a.1 variant respects both declared paths.

**Review issue:** mapping `manifest files[].path` to `doc_id` currently uses `Path(path).stem`. Hidden-units may not preserve that invariant; require independent source review before production adoption. A future change must be separately versioned and retested.

## Measured verification (SOURCE-ONLY; not a scored entry)

On the ten public practice units (77 entities), the unchanged minimal baseline produced **17 `claim_wrong_entity`** findings under the official deterministic claim rail; v20a.1 produced **0**. Date and citation offset checks reported no problems. Both original and candidate returned **10 `claim_tokens_unchecked`** notices because the judge tokenizer was absent. The ten practice-unit JSON answers passed the official toolkit analysis schema.

The worked exemplar output remains byte-identical to the frozen baseline: SHA-256 `e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2`. All **11** public answer JSON files passed the pinned schema. Detailed per-unit findings are in `evidence/practice_ten_units.json`, retained as source-only evidence, not an official result.

**Not established:** full NLI entailment/faithfulness threshold, judge token cap, hidden-set robustness, ranking or competitive forecasts, Docker integration, package/image security, inherited redistribution license clearance, CodaBench upload or scored run. The last retained v20 OCI audit found **55 High** package vulnerability matches and an unresolved licensing hold.

No further Docker/test execution, OCI build, public registry image, Team Key, proof, submission ZIP, CodaBench upload, PR merge or final license choice is authorized by this draft PR.

## Reproducing in a scratch checkout (no Docker)

```sh
TRACK=/path/to/checked-out-official-track4-at-5d3b726
REVIEW=/path/to/this/v20a1-directory
SCRATCH=$(mktemp -d)
cp -R "$TRACK/baselines/baseline_agent" "$SCRATCH/baseline_agent"
cp "$REVIEW/overlay/baseline_agent/cli.py" "$SCRATCH/baseline_agent/cli.py"
cp "$REVIEW/overlay/baseline_agent/entity_filter.py" "$SCRATCH/baseline_agent/entity_filter.py"
PYTHONPATH="$SCRATCH:$TRACK" python -m baseline_agent.cli \
  --task "$TRACK/units/t4-EXAMPLE-eps-beat/task.json" \
  --corpus "$TRACK/units/t4-EXAMPLE-eps-beat/corpus" \
  --out "$SCRATCH/answer.json"
```

Preserve the historical experiment logs and hashes instead of recalculating them as though they were official scores.
