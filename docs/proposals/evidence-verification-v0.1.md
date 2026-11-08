# Evidence verification profile proposal

Status: draft design for review. This is a proposed companion profile, not a change to a canonical schema, benchmark, verification state or normative trust policy. No image detector, forensic service or credential validator is implemented by this document.

## Purpose

Make the performed checks and remaining limits visible when a reviewer receives a link, screenshot, report, photograph or dataset. Grade the checking of a precise claim, not the presumed truth of a file format. Keep operational events, content origin, transformations and claim support separate.

This extends the existing [verification terminology](../TERMINOLOGY.md) and [external C2PA evidence-reference direction](../C2PA-EVIDENCE-REFERENCES.md). It does not replace them. A credential locator remains distinct from validation, and a file hash remains distinct from factual correctness.

## Approaches considered

| Approach | Trade-off | Design choice |
|---|---|---|
| One authenticity percentage | Easy to display; conflates source access, content coverage, manipulation and real-world truth. | Not proposed. No calibrated authenticity model or evaluation supports it. |
| Binary AI/fake detector | Appears simple; can misclassify genuine edits and cannot guarantee detection. | Not proposed as a decision rule. Any future detector output is a bounded supplementary observation. |
| Verification steps plus separate edit, provenance and claim-support fields | More explicit; requires a short statement of what was checked. | Proposed author choice for a small documentation-first evaluation. |

## Verification steps

| Level | Required performed check | What the level does not establish |
|---|---|---|
| V0 reference only | The item is only cited, linked, described or inaccessible. | Relevant content, authenticity or an event. |
| V1 inspected copy | Relevant supplied content and visible context were inspected. | Independent source authentication or an unedited lifetime history. |
| V2 source compared | Relevant content was compared with the accessible source/version or a separately obtained source. | Real-world truth, sufficient context for every claim or independently confirmed action. |
| V3 authoritatively confirmed | A trusted custodian/system record or non-circular corroborating record confirms the precise claim through a recorded route. | Approval, causation, legal admissibility, general correctness or universal authenticity. |

These are proposed labels for completed checks, not probabilities or evidence weights. They are not a requirement to perform every level for every item. Record the scope and reason for any additional check. The maximum performed level is displayed with its claim and limitations, never as a stand-alone “trusted” badge.

An illustrative AI image can have well-documented origin while supplying no evidence that its scene occurred. A crop can preserve a narrow claim or conceal the qualifier that defeats a broader claim. Two copies of the same source are not independent corroboration.

## Separate transformation assessment

Use one or more labels:

- `unassessed`: insufficient original or history to assess changes;
- `no_material_difference_observed_in_comparison`: a specified comparison found no material difference within its stated scope;
- `presentation_change`: crop, rotation, resize, compression or framing adjustment;
- `redaction_or_annotation`: masked information or added explanatory marks;
- `content_change`: text, amount, object, signature, feature or scene content changed;
- `generated_or_reconstructed`: synthesis, generative fill or a process that reconstructs details.

Every label has a basis: `declared`, `original_compared`, `validated_history`, `tool_report` or `unassessed`. Do not infer an AI method from a visual inconsistency alone. A declared crop is a declaration until compared or otherwise supported. A presentation change is acceptable only for a claim whose relevant context it preserves. Preserve the original, derivative relationship and affected regions.

Image enhancement is not automatically harmless. Reconstructed detail must not be treated as something present in the original. OCR is a derived reading aid; exact disputed wording should be checked on the source image.

## Provenance and integrity

Credential assessment is a separate field with states such as `not_checked`, `absent`, `valid`, `invalid`, `unsupported` or `uncertain`. A real validation record needs the validator identity/version, timestamp, asset binding, applicable trust profile and actual result. Merely detecting a metadata string or logo does not populate `valid`.

A cryptographic hash establishes equality to a specified byte baseline. It does not establish the truth of a scene or absence of edits before acquisition. Different hashes can result from metadata, encoding, compression or substantive changes; the difference alone does not distinguish them. A rendering comparison covers only the pages/regions/resolution and visible features actually examined, not hidden layers or all metadata.

Absent metadata or credentials is not evidence that content is fake. Valid provenance can accompany synthetic content. Unknown and unsupported results must remain available outcomes.

## Proposed companion record

Keep the record outside current canonical schemas while its semantics are reviewed. Suggested fields:

- profile version and item identifier;
- precise claim and intended use;
- source type, source/version reference, access and capture/retrieval dates;
- verification level and checks performed, each with scope, result, reviewer/time and evidence references;
- checks not performed;
- visible coverage and original/derivative relationship;
- transformation labels, basis, affected region and contextual impact;
- provenance-validation state and optional real validation result reference;
- hash/baseline scope where actually checked;
- corroboration group and independence explanation;
- claim support, limitations and next useful check.

For CSV, JSON and extracted tables, additionally record row lineage, units, schema, missingness, duplicate handling and reconciliation to the source. A parseable dataset is not a verified dataset.

Do not automatically map V0–V3 to `verification.state = confirmed`. Confirmation in the existing model must identify the result or event checked and resolve its evidence references. In particular, confirming that a screen displays a receipt message is different from confirming an issuer action, which is different from confirming approval.

## Research and business boundary

Possible use: an optional evidence-review worksheet within a fixed-scope document-review evaluation. The hypothesis is that explicit checks and limits reduce unsupported interpretations and reviewer effort. It has not been demonstrated by this proposal.

Candidate evaluation before implementation: compare current review instructions with the profile on new synthetic cases; predeclare measures of unsupported claim promotion, missing-context detection, correct abstention, transformation classification and review time. Record negative results, confusing cases and cost. Any human study, customer outreach or production use remains subject to existing project gates. Do not transfer results from another benchmark or call an authored example a validation result.

Commercial demand, willingness to pay, deployment cost and effectiveness require separate evidence. No price, sale, customer, financing approval, standards conformance or certification is claimed.

## Fictional examples and privacy

The companion [Atholia examples](atholia-verification-examples-v0.1.json) are newly invented design scenarios, not edited real records or a renamed private case. All people, organizations, case identifiers, event dates, amounts, addresses and cities in those examples are fictional. Reserved `.example` addresses are illustrative and were not contacted.

Do not publish real source images, medical or employment records, private links, actual source hashes, embedded metadata, real correspondence, hidden evaluation data or a private identity mapping. Filenames, OCR text, document properties, image backgrounds, QR codes, barcodes, location/time combinations and recognizable narratives can retain identifiers even after a name is replaced. Prefer wholly synthetic examples over sanitizing a real case.

This proposal contains no live credential validation or synthetic-image detection result. Example expected outcomes are design expectations under stated fictional assumptions, not performed tests.

## Primary references

- [C2PA explainer, version 2.2](https://spec.c2pa.org/specifications/specifications/2.2/explainer/Explainer.html): provenance does not establish content truth and may be incomplete or removed.
- [SWGDE Best Practices for Image Authentication](https://www.swgde.org/documents/published-complete-listing/18-i-001-best-practices-for-image-authentication/): preserve originals; distinguish baseline integrity from scene veracity; single-image analysis has limits.
- [NIST AI 100-4](https://doi.org/10.6028/NIST.AI.100-4): provenance, labelling and detection address different transparency problems.
- [Canadian Centre for Cyber Security provenance guidance](https://www.cyber.gc.ca/en/guidance/public-content-provenance-organizations-using-content-provenance-improve-audience-trust-organizations-information-online-itsp10005): examine source of trust, history coverage and verification methods.

Sources support the distinctions. They do not prescribe this proposed grading profile. Standards references retain their real attribution; the illustrative people and organizations are fictional.
