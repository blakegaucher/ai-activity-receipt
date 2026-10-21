# AI/SI source and mapping audit, 2026-10-21

Existing PR #103 at `f6745783610aa0b54d1bc76dbd288b6cdbed98ec` is a
terminology/evidence-index candidate. It does not rename historical identifiers,
certify capability or implement a governance program.

| Material mapping | Classification | Exact source | Bounded interpretation |
| --- | --- | --- | --- |
| Executive-branch SI prose | EXACT_EXISTING | Three White House releases already linked in the September 29 crosswalk, rechecked 2026-10-21 | The cited pages use the term. That observation does not measure system intelligence. |
| September 29 terminology directive | OUTDATED_SOURCE | [Official Executive Order 14434, 2026-09-29](https://www.whitehouse.gov/presidential-actions/2026/09/inaugurating-the-era-of-super-intelligence/) | Replace reliance on contemporary reporting with the exact official order. Its non-statutory executive-branch terminology direction is not a universal standards rename. |
| Four Accord control layers | PARTIAL | [Archived original White House text, 2026-09-29](https://www.presidency.ucsb.edu/documents/white-house-accord-super-intelligence); [official participant remarks](https://mikejohnson.house.gov/news/documentsingle.aspx?DocumentID=2939) | The archived statement describes internal controls, assurance, external evaluation and board oversight. Its historical text is preserved separately from this engineering mapping. |
| Observable control decisions/events | EXACT_EXISTING | Current main `54b360554dee6879b2ee0bec62f86c009e9171d9`, `activity-record.schema.json`, `docs/INVARIANTS.md` | Existing sources/events/authority/verification/incidents can index relevant evidence. |
| Layer-to-Receipt evidence crosswalk | PARTIAL | Existing `AI-SI-FRONTIER-CONTROLS-CROSSWALK-2026-09-29.md` | Semantic evidence support only; no Accord-defined JSON schema or cryptographic protocol is supplied. |
| Auditor independence, accreditation and board governance | INTENTIONALLY_EXCLUDED | Existing crosswalk gap analysis | Records can reference an audit report; they do not establish qualifications, independence, oversight or compliance. |
| Successful external audit or model-safety conclusion | ABSENT | No qualifying external audit receipt | CI cannot supply these observations. |
| Mandatory universal compliance / authorization semantics | UNVERIFIED | No applicable compliance determination in this candidate | This source audit makes no such claim and changes no permissions. |

The existing canonical project name, AIAR identifiers, wall-clock methodology,
three study conditions, frozen artifacts and owner gates stay as recorded.
No numerical methodology is chosen here. The term SI must always carry source
and context when it could otherwise be read as a technical capability claim.
