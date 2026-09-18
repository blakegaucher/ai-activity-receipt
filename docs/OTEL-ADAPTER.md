# OpenTelemetry GenAI Adapter — Candidate v0.1

> **Status:** Synthetic interoperability prototype. This adapter is not an OpenTelemetry conformance implementation and does not establish real-world audit benefit, authorization correctness, or production readiness.

The candidate adapter converts **one OTLP/JSON GenAI trace plus a separate authority/materiality sidecar** into the project's candidate Canonical Activity Record. The existing deterministic derivation utility can then produce an AI Activity Receipt.

Files:

- `adapters/otel_genai.py`
- `examples/otel-genai-traces.json`
- `examples/otel-adapter-context.json`
- `examples/otel-derived-record.json`
- `examples/otel-derived-receipt.json`

## Why the sidecar is separate

OpenTelemetry is evidence about observed execution. A successful telemetry span is **not proof that an action was authorized**.

The adapter therefore does not infer:

- principal identity;
- delegated authority scope;
- authority start/end times;
- materiality;
- consequentiality;
- approval merely from successful execution.

Those values come from the sidecar context or remain unknown.

This separation is deliberate: observability evidence and authorization evidence answer different questions.

## Current OpenTelemetry basis

The prototype follows the current public OTLP/JSON and GenAI semantic-convention direction.

References:

- OTLP specification: https://opentelemetry.io/docs/specs/otlp/
- OTLP file exporter / JSON serialization: https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/
- OpenTelemetry GenAI semantic conventions: https://github.com/open-telemetry/semantic-conventions-genai
- GenAI agent spans: https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
- GenAI spans / tool execution: https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md

At the time of this research snapshot, OTLP traces are stable while the GenAI semantic conventions remain under development. The adapter is therefore explicitly versioned and intentionally narrow.

## Supported OTLP/JSON structure

The adapter reads the standard OTLP JSON trace nesting:

```text
resourceSpans[]
  -> scopeSpans[]
    -> spans[]
```

It expects one logical GenAI trace per adapter invocation.

OTLP `traceId` becomes the canonical record `trace_id`.

The adapter now checks the OpenTelemetry identifier widths directly: trace IDs must be 32 hexadecimal characters (16 bytes), span IDs must be 16 hexadecimal characters (8 bytes), and all-zero identifiers are rejected. Hexadecimal identifiers are normalized to lowercase.

Each adapted GenAI span receives a canonical event ID derived from its OTLP span ID:

```text
otel-span:<spanId>
```

The current candidate record does not yet preserve every possible OpenTelemetry identifier or link.

## Supported GenAI attributes

The prototype currently uses:

| OpenTelemetry attribute | Candidate record use |
| --- | --- |
| `gen_ai.operation.name` | identifies GenAI spans and supplies the operation class |
| `gen_ai.agent.id` | candidate `system.agent_id` |
| `gen_ai.agent.version` | candidate `system.version` |
| `gen_ai.provider.name` | optional `system.provider` |
| `gen_ai.request.model` | optional `system.model` |
| `gen_ai.tool.name` | operation name for `execute_tool` spans |
| `gen_ai.data_source.id` | candidate source identifier |
| `error.type` | failure signal |
| resource `service.version` | fallback version evidence |

The adapter does **not** treat `gen_ai.agent.name` as authenticated identity.

## Tool content deliberately excluded

The current OpenTelemetry GenAI conventions allow opt-in capture of tool arguments and results, and explicitly warn that these values may contain sensitive information.

The adapter therefore ignores:

- `gen_ai.tool.call.arguments`;
- `gen_ai.tool.call.result`;
- prompt/system-instruction content;
- hidden/private reasoning.

The synthetic OTLP fixture deliberately contains a fake recipient address inside tool arguments. The self-test confirms that this value never appears in the canonical record.

## Timestamp fidelity

OTLP span timestamps are Unix nanoseconds. Candidate v0.1 preserves the full significant nanosecond fraction when converting `startTimeUnixNano` to RFC 3339 UTC text.

For example:

```text
1789711500123456789 -> 2026-09-18T06:05:00.123456789Z
```

This avoids silently truncating telemetry timestamps to Python's microsecond-resolution `datetime` representation.

The canonical record still does not claim that source clocks are synchronized or factually accurate; this is a fidelity rule for the captured timestamp value.

## Event status

Candidate mapping:

- OTLP span status `ERROR` or an `error.type` attribute -> `failed`;
- a span without an end timestamp -> `pending`;
- otherwise -> `completed`.

The sidecar may supply an explicit status override for cases where a separate policy/control plane has stronger evidence, such as an action known to have been blocked.

## Tool operation mapping

For an `execute_tool` span with `gen_ai.tool.name`, the canonical event operation is the tool name rather than the generic string `execute_tool`.

Example:

```text
gen_ai.operation.name = execute_tool
gen_ai.tool.name      = send_email

canonical operation   = send_email
```

This allows the operation to be compared directly with delegated authority scope.

Other GenAI spans preserve `gen_ai.operation.name` as their operation.

## Sidecar context

The sidecar supplies governance evidence and classification rules that telemetry does not prove.

Current fields include:

- `record_id`;
- `principal`;
- `authority.scope`;
- `authority.prohibited`;
- `authority.valid_from`;
- `authority.valid_until`;
- `material_operations`;
- `consequential_operations`;
- `material_source_ids`;
- `source_roles`;
- `source_refs_by_span_id`;
- `authorization_by_span_id`;
- optional `status_by_span_id`;
- `verification`;
- `generated_at`.

The sidecar may also explicitly override agent/provider/model metadata if telemetry is absent or contains conflicting values.

### Sidecar reference integrity

Candidate v0.1 now validates sidecar container shapes and cross-references before deriving a record. Span-keyed authorization, source-reference, and status maps are normalized to valid OpenTelemetry span IDs and must point to spans actually present in the adapted trace. Material-source and source-role entries must resolve to a telemetry-discovered or explicitly referenced source.

This prevents stale sidecar entries from being silently dropped. It does not authenticate the sidecar or prove that the referenced governance evidence is true.

## Authorization behavior

For a consequential operation:

- if sidecar authorization evidence exists, the recorded state is used;
- if it does not exist, authorization is `unknown`.

The adapter does **not** convert a successful span into `approved`.

The self-test intentionally removes authorization evidence and verifies that the derived Receipt then fails the existing consequential-action authorization invariant.

## Data sources

The adapter discovers `gen_ai.data_source.id` values and can also receive source references from the sidecar.

Materiality is supplied separately.

A source discovered in telemetry is not automatically material simply because it was present in a trace.

## Deterministic synthetic test

Run:

```bash
python adapters/otel_genai.py --self-test
```

The test confirms that:

1. the OTLP fixture maps exactly to the published expected canonical record;
2. the canonical record passes the record schema and semantic checks;
3. deterministic Receipt derivation exactly matches the published expected Receipt;
4. the derived Receipt passes the Receipt schema and executable invariants;
5. missing authorization evidence is preserved as `unknown` and causes the consequential-action Receipt check to fail;
6. sensitive tool arguments/results are not copied into the record;
7. OTLP nanosecond timestamp precision is preserved;
8. malformed, short, duplicate, or all-zero trace/span identifiers are rejected;
9. duplicate OTLP attribute keys are rejected instead of silently overwriting one another;
10. span end time may not precede span start time, and unsupported timestamp magnitudes fail as validation errors;
11. sidecar list/object fields reject malformed scalar shapes;
12. authorization/source/status sidecar maps may reference only observed span IDs;
13. material-source and source-role sidecar entries may reference only sources present in telemetry or explicit source references.

## Manual use

```bash
python adapters/otel_genai.py \
  traces.json \
  --context adapter-context.json \
  --output activity-record.json \
  --receipt-output activity-receipt.json
```

If the canonical record is internally valid but the resulting Receipt violates a Receipt invariant—for example, a completed consequential action has no approval evidence—the command fails rather than silently presenting the Receipt as valid.

## Known limitations

Candidate v0.1 intentionally does not yet:

- ingest more than one logical trace per invocation;
- preserve every span link, event, or trace-state field;
- preserve `gen_ai.tool.call.id` separately from OTLP span identity;
- map distributed authorization systems automatically;
- prove that sidecar authority evidence is authentic;
- ingest logs or metrics;
- provide streaming ingestion;
- sign the canonical record;
- implement OpenTelemetry conformance testing.

These gaps are useful design signals rather than hidden limitations.

## Design findings from the prototype

The prototype reinforces several architectural choices:

1. **Telemetry and authorization must stay separate.** Execution evidence alone cannot establish delegated authority.
2. **The canonical record is the right adapter target.** OpenTelemetry does not need to map directly into a human-facing Receipt.
3. **Materiality needs an explicit policy layer.** Telemetry volume is not the same thing as audit relevance.
4. **Stable trace/event IDs are valuable.** They let the compact Receipt remain tied to the underlying telemetry episode.
5. **Content minimization matters.** Most audit questions can be addressed without copying prompts, tool arguments, or tool results.
6. **A richer evidence-reference model may eventually be useful.** Candidate record v0.1 preserves trace/span identity through `trace_id` and event IDs, but a future version may need explicit evidence-substrate references for span links, authorization decisions, or external attestations.

## Evidence boundary

Passing the adapter self-test establishes only deterministic behavior on the published synthetic OTLP example.

It does not establish:

- OpenTelemetry certification/conformance;
- authorization correctness;
- completeness of telemetry capture;
- source clock accuracy;
- production security;
- human audit improvement;
- regulatory compliance;
- interoperability with every GenAI framework/provider.
