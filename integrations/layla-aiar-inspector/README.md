# Layla AIAR Receipt Inspector (v0.1)

An offline, read-only Layla mini-app for Taylor Moon and Julia AIAR research. **Not published or installed yet.** No automatic earning activities or email/MCP access.

## Official packaging
The Layla SDK mini-app overview: https://github.com/l3utterfly/layla-sdk/blob/main/.agents/layla-sdk/references/mini-apps-overview.md

Layla imports app.json plus index.html and relative assets at the ZIP root. This prototype makes no SDK calls; it is intentionally a zero-privilege WebView mini-app. No npm, API keys, network backend, hosted URL, SDK modifications or task.js needed.

From this directory, create the import ZIP:

    python3 -m zipfile -c layla-aiar-inspector-v0.1.zip app.json index.html core.js

Do not zip the containing folder. In Layla, import the generated ZIP and open the mini-app. Confirm UI, JSON inspection, and hashing on the actual device; no device test has been performed yet.

## Tests
From repository root:

    node --test integrations/layla-aiar-inspector/tests/inspector.test.cjs

## Scope and limitations
- JSON check is a **partial**, local advisory subset of activity-receipt.schema.json and its semantic rules, not full validation.
- SHA-256 digest comparison requires Web Crypto in the host. Matching bytes do **not** establish origin, chronology, intent, or absence of leakage.
- File reads are user-triggered; input is not persisted, uploaded, transmitted, or inserted into other chats. Do not load a sealed Designer file in a Navigator session.
- No HTML injection: results use textContent; JSON maximum 2 MiB, hash file maximum 20 MiB.
- The canonical validator is validate_receipts.py; do not claim schema compliance from the mini-app.
- Avoid publishing private receipts, keys, or other confidential records into the public repository.
- This mini-app is a potential research/demo asset, not a monetized product, production verifier, or evidence of AIAR human-performance benefit.

## Out of scope / future owner decisions
Optional host SDK connection to a chosen character, approved email drafting, Hugging Face or MCP access, scheduling, paid services, public publishing, and Run 1 verification remain disabled until separately approved.
