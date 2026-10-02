# AI/SI Frontier Controls Evidence Crosswalk — 2026-09-29

> **Status:** Dated research snapshot; documentation-only; non-normative.  
> **Project boundary:** This document does not change the candidate schemas, validators, AR-P003 methodology, frozen/historical artifacts, or recruitment/execution state.

## Purpose

This snapshot records two September 2026 developments that may matter to AI Activity Receipt:

1. current U.S. executive-branch materials have begun using **Super Intelligence (SI)** terminology for technologies otherwise widely described as **Artificial Intelligence (AI)**; and
2. the **White House Accord on Super Intelligence — Joint Commitment on Frontier Responsibilities** describes four voluntary layers of controls and audits for companies training and deploying frontier models.

The useful question for this project is not whether AI Activity Receipt "complies" with that accord. The bounded question is:

> Which existing Activity Record / Receipt concepts could preserve evidence useful to organizations implementing or independently evaluating those control layers?

## Source and terminology status

### U.S. executive-branch terminology

Current White House public materials use **Super Intelligence (SI)** terminology:

- White House release on the September 22, 2026 United Nations address:  
  https://www.whitehouse.gov/releases/2026/09/president-trump-at-the-united-nations-while-others-have-talked-i-have-acted/
- White House September 25, 2026 U.S.-China state-visit fact sheet, which records an agreement to use "super intelligence" rather than "artificial intelligence" for the applicable technologies and establishes a U.S.-China SI Dialogue:  
  https://www.whitehouse.gov/fact-sheets/2026/09/fact-sheet-president-donald-j-trump-advances-a-fair-and-reciprocal-relationship-with-china-while-hosting-historic-state-visit/
- White House September 29, 2026 America.gov fact sheet, which describes America.gov as using **Super Intelligence (SI)**:  
  https://www.whitehouse.gov/fact-sheets/2026/09/fact-sheet-president-donald-j-trump-streamlines-access-to-government-services-through-america-gov/

Contemporaneous reporting says the September 29 terminology directive applies to U.S. executive-branch non-statutory materials. This snapshot does **not** treat that terminology choice as a technical redefinition of model capability.

### Established standards vocabulary remains AI

Important external frameworks continue to use **AI** terminology, including:

- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- ISO/IEC 42001:2023, Artificial intelligence — Management system: https://www.iso.org/standard/42001

Therefore the project keeps **AI Activity Receipt (AIAR)** as the canonical name and uses **AI/SI** only as a prose-level compatibility bridge where useful.

## White House Accord control layers

Contemporaneous publication of the accord describes four layers for frontier-model developers:

1. **Internal controls** to monitor model capabilities/alignment during training and deployment, including cyber, bio, chemical, and unintended technical-system access risks.
2. **Internal assurance team** empowered to verify that controls, monitoring, and detection operate as intended and that identified issues are remediated.
3. **Independent external auditor or evaluator** assessing whether controls, monitoring, and detection operate as intended.
4. **Independent board committee** receiving reports from control operators and internal/external assurance functions and overseeing remediation.

The accord is described as voluntary / "morally binding," with possible future codification left open. It should not be represented as a current statutory compliance regime.

Primary/near-primary publication trail for the snapshot:

- Reuters, September 29, 2026: https://www.reuters.com/world/us/trump-releases-ai-accord-with-tech-executives-2026-09-29/
- White House release stream / accord email captured by Factba.se: https://rollcall.com/factbase/topic/latest/
- Contemporaneous reproduction of the accord text: https://georgemagazine.com/read-in-full-trump-and-tech-leaders-white-house-accord-on-super-intelligence/

## Candidate AIAR evidence crosswalk

| Accord control layer | Existing AI Activity Receipt evidence concepts | What the Receipt can support | What it does **not** establish |
| --- | --- | --- | --- |
| Internal model / system controls | `authority`, `material_actions`, `authorization`, `verification`, `incidents`, timestamps, trace links | Preserve observable control decisions, blocked/failed actions, timing, verification state, and evidence references for consequential activity | That the developer's full internal-control program is adequate or that the model is safe |
| Internal assurance / remediation team | verification evidence, incident records, mitigation text, actor identity in the underlying canonical record, integrity links | Preserve evidence that checks occurred, issues were recorded, and remediation evidence was linked | Independence, competence, or organizational effectiveness of the assurance team |
| Independent external auditor / evaluator | stable trace/run IDs, material-source references, event IDs, verification evidence refs, hashes / derivation links | Provide a compact index into the evidence substrate an external evaluator can inspect and independently test | That an external audit occurred, was independent, or reached a favorable conclusion |
| Independent board oversight | provenance links to reports/evidence, incidents, verification state, integrity/derivation references | Help package inspectable evidence that can feed governance reporting | Board independence, fiduciary oversight, remediation closure, or legal compliance |

## Architectural implication

The strongest project framing is:

> **Activity Receipt is an evidence substrate and human-facing index for assurance; it is not the assurance conclusion itself.**

A receipt can help answer:

- which system or agent acted;
- under whose delegated authority;
- what consequential actions occurred;
- which sources materially supported those actions;
- which authorization decisions preceded execution;
- what verification state was recorded;
- what incidents, failures, or blocks were preserved;
- which hashes / trace identifiers bind the summary back to underlying evidence.

An independent evaluator must still inspect the underlying evidence and apply its own methods. Board or governance oversight must still make its own decisions.

## Gap analysis

The current candidate model intentionally does **not** claim to represent an organization's complete control environment. In particular, it does not currently require:

- board-committee identity, independence, membership, or minutes;
- auditor accreditation, contractual independence, or scope;
- enterprise-wide model-risk inventories;
- control-design effectiveness ratings;
- control operating-effectiveness conclusions;
- remediation ownership / due dates / closure approvals;
- statutory or regulatory compliance determinations.

Those concepts should **not** be forced into the current candidate schema merely because the accord names them.

If future evidence justifies expansion, they can be evaluated as separately versioned governance/assurance references rather than silently changing candidate-record-v0.1 or candidate-receipt semantics.

## Bounded repository decision

For the September 29 snapshot:

- **KEEP** the canonical project/repository name **AI Activity Receipt**.
- **ADD** **AI/SI** as a prose-level interoperability/terminology bridge.
- **PRESERVE** all existing AI schema identifiers, payload types, protocol versions, hashes, citations, and frozen/historical artifacts.
- **DO NOT** relabel external standards or laws; use their official names.
- **DO NOT** claim that SI terminology means current systems are technically superintelligent.
- **DO NOT** claim White House Accord compliance, certification, endorsement, or legal sufficiency.
- **DO NOT** change AR-P003 design choices, recruitment status, execution status, or evidence claims.
- **USE** this crosswalk as a research input for future assurance/interoperability work only.

## Suggested public descriptor

A forward-compatible descriptor that preserves project identity is:

> **AI Activity Receipt (AIAR) — provenance-aware activity records for consequential AI/SI-agent activity.**

Where precision matters, first use may be expanded as:

> **AI/SI (Artificial Intelligence / Super Intelligence, depending on source or jurisdiction terminology).**

This wording is descriptive only and does not assert a capability threshold.
