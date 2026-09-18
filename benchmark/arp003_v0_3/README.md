# AR-P003 v0.3 Benchmark Workspace

This directory contains **development infrastructure** for the next human-centered AR-P003 evaluation.

> Nothing here is a completed human experiment. The repository does not yet contain a frozen confirmatory corpus, human reviewer data, or evidence of a Receipt benefit.

## Files

- `protocol.json` — machine-readable candidate protocol scaffold.
- `score_responses.py` — deterministic component-level scorer with a built-in synthetic self-test.

The human-readable preregistration draft is in:

- `../../docs/AR-P003-V0.3-PROTOCOL.md`

## Data boundary

Do **not** commit identifiable human-participant data, access tokens, private chain-of-thought, passwords, or other secrets to this public repository.

Future confirmatory materials should distinguish:

- **development data** — may be inspected and changed while tooling is developed;
- **sealed confirmatory data** — fixed before scored human outcomes are inspected;
- **release data** — de-identified material that can responsibly be published after evaluation.

The synthetic records embedded in the scorer self-test are developer checks only. They are not AR-P003 evidence.

## Response record format

The current scorer expects one JSON object per line.

Example shape:

```json
{
  "reviewer_id": "pseudonymous-reviewer-id",
  "case_id": "case-id",
  "condition": "control",
  "stratum": "ordinary",
  "elapsed_seconds": 83.4,
  "gold": {
    "material_actions": ["action-1"],
    "authorization_violation": false,
    "material_sources": ["source-1"],
    "incidents": [],
    "verification_state": "confirmed",
    "missing_evidence": false
  },
  "answer": {
    "material_actions": ["action-1"],
    "authorization_violation": false,
    "material_sources": ["source-1"],
    "incidents": [],
    "verification_state": "confirmed",
    "missing_evidence": false,
    "confidence": 4
  }
}
```

In an actual study, gold labels must remain hidden from reviewers. The combined record above is an analysis/scoring representation, not a reviewer-facing file.

## Scoring

Run the development self-test:

```bash
python benchmark/arp003_v0_3/score_responses.py --self-test
```

Score JSONL records:

```bash
python benchmark/arp003_v0_3/score_responses.py responses.jsonl --output scored.json
```

The scorer intentionally reports endpoint components separately:

- set precision/recall/F1 for material actions, sources, and incidents;
- exact accuracy for authorization violation, verification state, and missing-evidence state;
- elapsed time;
- confidence as a descriptive measure.

It does **not** generate a post-hoc weighted primary composite.

## Before human execution

Do not describe AR-P003 v0.3 as frozen or confirmatory until the checklist in the preregistration draft is complete, including population definition, endpoint selection, sample-size/precision analysis, corpus freeze, reviewer instructions, assignment procedure, scorer/analysis freeze, applicable ethics determination, and SHA-256 freeze manifest.
