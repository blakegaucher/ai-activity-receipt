# Scientific-Model Tool Provenance Pilot — 2026-09-24

> **Status:** Development-only source-to-record fidelity research.  
> **Issue:** #99.  
> This does not change candidate-record-v0.1, AR-P003, or any frozen methodology state.

## Question

Can the current canonical Activity Record losslessly represent a versioned external
scientific-model invocation while keeping the acting agent distinct from the invoked
model/service?

The motivating public-safe example is a basic-pKa prediction call where useful
provenance includes an external service identity, exact model ID/version, structured
molecular input, numeric output, prediction status, and OOD/low-confidence flags.

## Result

**Not losslessly in candidate-record-v0.1.**

The current record can preserve that an agent invoked an external scientific service,
when it happened, under what authority, and which source/evidence references are
material. It cannot preserve the scientific result itself as typed canonical-record
fields without either:

1. overloading a closed object and becoming structurally invalid;
2. putting details into prose such as `notes`, which is machine-readably lossy; or
3. binding to an external evidence artifact that carries the richer result.

The pilot therefore supports the existing architectural preference for keeping rich
third-party evidence outside candidate-record-v0.1 while evaluating whether a future
version should add a small, generic tool-observation/result envelope.

## Executable pilot

Files:

- `research/scientific-model-provenance/reference-only-record.json`
- `research/scientific-model-provenance/invalid-overloaded-record.json`
- `research/scientific_model_provenance_pilot.py`

Run:

```bash
python research/scientific_model_provenance_pilot.py
```

The script checks that:

- the reference-only record passes the current canonical-record JSON Schema;
- the record passes current canonical semantic checks;
- deterministic Receipt derivation succeeds;
- the derived Receipt passes the current Receipt schema/invariants;
- exact model/result details are absent from the derived Receipt;
- adding `model_id`, `model_version`, and a typed `prediction` object directly
  to the closed event object is rejected by the schema.

This is intentionally a **negative capability test**: rejecting undeclared fields is
the correct behavior for the current version.

## Field-by-field mapping

| Scientific-tool fact | candidate-record-v0.1 | Receipt after derivation | Classification |
|---|---|---|---|
| Acting agent identity/version | `system` + `actors` | `system` | lossless |
| Human principal/delegate | `authority` + `actors` | `authority` | lossless |
| External service identity | service actor | not exposed in current Receipt view | record-only / view loss |
| Invocation operation/status/time | `events[]` | `material_actions[]` | lossless |
| Input/source locator | `sources[].uri` | `material_sources[].uri` | lossless when a locator exists |
| Result evidence identity | `sources[]` reference | `material_sources[]` reference | reference only |
| External model ID | no dedicated field | no dedicated field | dropped unless external/prose |
| External model version | no dedicated field | no dedicated field | dropped unless external/prose |
| Assay/property identity | no dedicated field | no dedicated field | dropped unless external/prose |
| Numeric prediction | no dedicated field | no dedicated field | dropped unless external/prose |
| Units | no dedicated field | no dedicated field | dropped unless external/prose |
| Uncertainty interval/class | no dedicated field | no dedicated field | dropped unless external/prose |
| OOD / low-confidence flags | no dedicated field | no dedicated field | dropped unless external/prose |
| Scientific correctness | must not be inferred | must not be inferred | separate verification question |

## Why `system.*` is not the answer

`system.agent_id` and `system.version` identify the **acting AI system**. Reusing
those fields for an invoked scientific model would collapse two different identities:
the agent making the call and the external model/service being called.

That would make provenance look more complete while actually making it less correct.

## External evidence index

The repository's existing external-evidence-reference prototype is directionally
compatible with this use case because it can bind a canonical record to an external
artifact by URI/digest and preserve validation state.

However, `external-evidence-ref-v0.1` is itself a locator/index profile, not a typed
scientific-result schema. It can point to the richer model-call artifact but does not
currently normalize prediction value, assay, uncertainty, or OOD metadata.

Therefore the pilot does **not** justify silently extending either existing schema.

## Current decision

Preserve all current public schemas unchanged.

For scientific-model calls today:

1. record the invocation, authority, actor/service, and material evidence references
   in the canonical record;
2. retain exact model/input/output/uncertainty metadata in a bound external evidence
   artifact;
3. do not promote a model prediction into experimental truth or verification;
4. evaluate a future versioned generic tool-observation/result envelope only after
   more than one external-tool family demonstrates the same mapping loss.

This avoids designing the core schema around one chemistry provider while preserving
the real interoperability gap as evidence.

## Evidence boundary

This pilot tests representation behavior only. It does not establish scientific model
accuracy, experimental validation, biological activity, safety, efficacy, standards
conformance, human audit benefit, or commercial value.
