# Prospective Evaluator Pack

> **Status:** Pre-commercial customer discovery. This page describes a bounded evaluation concept that is being tested with prospective users/buyers. It does **not** claim validated demand, proven productivity, legal compliance, production security, or a commercially proven offering.

## What AI Activity Receipt is trying to solve

AI-assisted professional work can leave important context scattered across prompts, source documents, application logs, tool actions, approvals, and reviewer notes.

The practical question is:

> **Can a reviewer reconstruct what happened, under whose authority, using what evidence, with what human checks, without needing private chain-of-thought?**

AI Activity Receipt is exploring a model-neutral activity record plus a compact human-facing receipt that indexes the evidence needed to answer that question.

## Who this evaluation concept is for

Current customer discovery is focused on small professional teams that already use AI in document-heavy or evidence-heavy work, including:

- research and evaluation;
- finance, accounting, reconciliation, and reporting;
- legal or policy document review;
- professional-services reporting and synthesis.

The relevant workflow should involve meaningful human verification, approval, or accountability.

This is a hypothesis being tested, not a validated market segment.

## First conversation: what is needed

A first customer-discovery conversation should require **no client files or confidential records**.

A useful 20-minute discussion can start from one recent real workflow and cover:

1. **Workflow** — What task was being completed?
2. **AI use** — Which tool or AI capability was used, and at what step?
3. **Current evidence** — What records are kept today?
4. **Human review** — What must a person verify or approve before the result is relied on?
5. **Reconstruction pain** — When something is questioned later, what is hard to reconstruct?
6. **Current workaround** — How is that problem handled today?
7. **Cost of the current process** — Staff time, software, professional review, or rework.
8. **Budget path** — Who could approve a one-time external evaluation?
9. **Trial threshold** — What evidence would justify trying a new approach?
10. **Pricing evidence** — What comparable work already costs, or a credible price range / refusal to price.

A “no problem here” answer is useful evidence too.

## If a retrospective evaluation is later agreed

Only after workflow fit and authorization are confirmed, a bounded retrospective evaluation could use an **authorized, de-identified evidence bundle**.

### Minimum input package

The goal is to reduce ambiguity before analysis begins.

A useful package would identify:

- the workflow or document being reviewed;
- the AI system/tool(s) used;
- the final output or decision being checked;
- the source records that materially supported the work;
- known assumptions or facts that were not verified;
- material tool/actions taken during the workflow;
- human review or approval points;
- known failures, blocked actions, corrections, or conflicts;
- timing/version information where available;
- explicit exclusions and confidentiality restrictions.

Raw private chain-of-thought is **not** requested.

Sensitive or third-party confidential information should be removed unless there is explicit authorization and an appropriate handling agreement.

## What the evaluator would receive

A fixed-scope evaluation concept currently includes:

1. **Example AI Activity Receipt** — a compact human-facing view.
2. **Evidence-linked activity record** — normalized activity/evidence references.
3. **Checking guide** — how to follow the receipt back to source evidence.
4. **Gap/conflict register** — missing, stale, contradictory, or unverified information marked explicitly.
5. **Short findings report** — what could and could not be reconstructed from the supplied evidence.

The receipt is intended to summarize and index evidence, **not create facts that were not present**.

## What gets measured

A future trial should define success before the work begins.

Possible measures include:

- whether a reviewer can correctly reconstruct material actions;
- whether source/evidence links are complete enough to verify key claims;
- reviewer time required;
- number and type of missing-evidence questions;
- unresolved contradictions;
- reviewer confidence only as a secondary measure;
- delivery effort required to prepare the record and findings.

Current public research does **not** establish improvement on these measures.

## Privacy, confidentiality, and security boundary

The current concept is designed around data minimization:

- no private chain-of-thought requirement;
- no passwords, API keys, authentication secrets, or unnecessary prompt content;
- de-identification where practical;
- explicit source/evidence references rather than silent inference;
- failed, blocked, and contradictory evidence preserved rather than hidden.

Any real customer evaluation would require scope-specific authorization and data-handling terms before confidential material is accepted.

## Commercial boundary

The commercial form being tested is a **one-time, fixed-scope evaluation of one workflow**.

No price has been validated.

Customer discovery should first establish:

- the current alternative;
- actual review/rework cost;
- budget ownership;
- the evidence needed to justify a trial;
- an acceptable price range or explicit refusal to price.

A discovery conversation, expression of interest, technical demo, or standards discussion is **not** treated as a sale.

## What is already public

Technical and non-technical readers can inspect:

- [Human-readable illustrative receipt](../examples/sample-receipt-human-readable.md)
- [Machine-readable sample Activity Receipt](../examples/sample-receipt.json)
- [Canonical Activity Record design](CANONICAL-RECORD.md)
- [Candidate JSON Schema](../activity-receipt.schema.json)
- [Validation record](VALIDATION.md)
- [Reproducibility guide](REPRODUCIBILITY.md)
- [Interoperability research](INTEROPERABILITY.md)

The public repository primarily establishes engineering behavior on synthetic/test evidence. It does not establish customer demand or real-world effectiveness.

## What would make a prospect a useful discovery participant?

A particularly useful participant is someone who can describe a real AI-assisted professional workflow and answer at least some of these questions:

- What evidence must be checked before relying on the output?
- What is hardest to reconstruct later?
- What information is routinely missing?
- What currently consumes reviewer time?
- Who owns the risk and the budget?
- What would make a bounded evaluation worth paying for?

Positive, negative, and “not useful” feedback are all retained.

---

**Project:** AI Activity Receipt  
**Research identity:** Blake Gaucher / Ancient Immortal Art  
**Current stage:** pre-commercial research, customer discovery, and technical validation
