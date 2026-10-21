# Plugin evidence crosswalk: primary-source audit, 2026-10-21

This addendum reviews the existing PR #112 crosswalk at
`87808f6fa5648f26f037de712d1f0187d3b181a6`. Historical October 7 service IDs
remain historical reports. No external function, policy, endpoint, paid
service or reporting operation was activated in this audit.

| Material mapping | Classification | Primary source/version | Meaning and remaining gap |
| --- | --- | --- | --- |
| Existing evidence references | EXACT_EXISTING | `activity-record.schema.json`, `research/external-evidence-reference.schema.json` in current main `54b360554dee6879b2ee0bec62f86c009e9171d9` | Registered sources/events, verification references and separately bound evidence already exist. Do not create a duplicate core store or schema. |
| ArmorCodex plan to declared intent | PARTIAL | [Official repository](https://github.com/armoriq/armorCodex), [hosted documentation](https://docs.armoriq.ai/armorcodex), observed 2026-10-21 | Repository describes harness-specific Bash hook limits; broader hosted descriptions do not prove coverage in every harness/version. A registered plan is not a permit, enforcement result or observed effect. No immutable deployed-service revision obtained. |
| MicroFn output to execution report | PARTIAL | [Official docs](https://docs.microfn.dev/), [cron docs](https://docs.microfn.dev/triggers/cron/), observed 2026-10-21 | Manual and scheduled invocation differ. Reported output does not prove authorization or an independently observed downstream change. No pinned service revision or new execution receipt. |
| 3Min accepted/retrieved payload | PARTIAL | [Official FAQ](https://3minapi.com/docs/faq), observed 2026-10-21 | Sandbox and production retention differ; current documentation gives sandbox 30-day retention and production at least 60 days, with free endpoints deleted after seven days. Stored content is an attributed report, not certified truth or perpetual durability. |
| Sugra source/data-time mapping | PARTIAL | [Official docs](https://docs.sugra.ai/), [quickstart](https://docs.sugra.ai/doc-2263383), observed 2026-10-21 | `data_time` can fall back to response time when source time is unknown. Missing age is unknown, not zero; output timestamps alone cannot certify source freshness. |
| October 7 Sugra timestamp assumptions | OUTDATED_SOURCE | [Official changelog](https://docs.sugra.ai/doc-2263381), October 8 corrections | Several `data_time` fields changed after the original snapshot. Preserve the old observation; recheck exact endpoint/response bytes before using any freshness assertion. |
| Not Just You advisory channels | PARTIAL | [Publisher package `@notjustyou/antigravity-plugin` 0.2.5](https://www.npmjs.com/package/@notjustyou/antigravity-plugin), observed 2026-10-21 | Status queries and opt-in metadata reporting are separate. Tool availability does not authorize reporting; zero community reports does not establish absence of a service incident. Package metadata does not pin the current hosted ChatGPT surface. |
| October 7 external smoke IDs | UNVERIFIED | Existing crosswalk's preserved identifiers | Historical reports were not re-executed or independently recovered here. They cannot become current service/host acceptance. |
| Cross-service cryptographic binding | ABSENT | No authenticated correlation receipt supplied | Similar identifiers are not cryptographic evidence that records refer to the same action. |
| Provider schemas and cryptographic conformance | UNVERIFIED | Hosted docs lack immutable deployed revision receipts | Semantic correspondence is not exact schema compatibility or protocol conformance. |
| Automatic authority, synchronization or execution | INTENTIONALLY_EXCLUDED | Existing project boundaries | A connected tool does not grant permission. No adapter/store/background relay is justified by this audit. |

The ten existing adverse vectors remain useful synthetic requirements. They
overlap the current decision/effect prototype and external-evidence validator;
this documentation does not claim a new adapter suite ran. Generic green CI
checks repository consistency, not the provider claims above. Any later adapter
must bind provider revision, captured response bytes, scope and evidence class,
then demonstrate an actual uncovered behavior before altering core.
