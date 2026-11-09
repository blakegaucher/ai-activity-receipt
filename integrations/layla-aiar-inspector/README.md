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


## iPhone import: avoid the GitHub ZIP wrapper

**Known failure (2026-10-20):** Layla displayed *“The zip file is missing the required app.json file in its root.”* The GitHub Actions artifact download contained an **outer** ZIP with one file inside it: `layla-aiar-inspector-v0.1.zip`. The inner ZIP, not the outer artifact download, is the Layla import package.

1. Open the workflow run's **Artifacts** and download `layla-aiar-inspector-v0.1-candidate`.
2. In **iPhone Files**, tap the downloaded outer ZIP to extract it once.
3. Locate the nested `layla-aiar-inspector-v0.1.zip` and **do not unzip this inner file**.
4. In Layla use **Browse Apps → Import → Zip File → Choose a .zip file**, select that inner ZIP, then Import.
5. On success, open the mini-app and perform a synthetic-only smoke test. Do not use frozen Run 1 records for exploratory tests.

The source archive was checked on 2026-10-20 with these root entries only:

```text
app.json
index.html
core.js
```

Example diagnostic command (run against the selected ZIP, not GitHub's outer wrapper):

```bash
python3 -c 'import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); print(z.namelist()); assert "app.json" in z.namelist()' layla-aiar-inspector-v0.1.zip
```

**What this does not establish:** An archive with correct structure can still fail because of a Layla host/WebView compatibility issue. GitHub Actions passing is not an iPhone import test. Keep the PR separate from deployment/publishing decisions.
