# AR-P003 runner reflow and automated browser supplement — 2026-10-26

A real local headless Chromium check reproduced horizontal overflow in the development runner at 390px viewport width with root text enlarged to 200%: document scroll width 504px. The incident fieldset's intrinsic minimum width and long identifiers contributed; an initial fieldset-only patch still left long heading/text overflow. Both failed observations are preserved.

The candidate changes four CSS declarations: allow wrapping in main and option labels, allow fieldsets to shrink, and bound grid minimum width to the container. Final document scroll width is 390px under the same authored fixture and viewport. JavaScript, answer content, schema, timing constants and methodology are unchanged.

The separate automated_runner_smoke.cjs binds the actual runner and authored-bundle SHA-256, uses three synthetic public example cases plus locally authored scrolling text, and emits its own AUTOMATED_AGENT_NOT_MANUAL_TESTER receipt. It must never produce the existing manual browser-smoke schema or a human acceptance claim.

Final source SHA-256: 44e5c5b3bdabfcb1c1105ffac56529b0ba369857c165d0f9b06326e83baecb15. Source base: 54b360554dee6879b2ee0bec62f86c009e9171d9. The receipt's runner_commit is null because it was an uncommitted candidate during testing; the exact bytes are bound by SHA-256. Environment: Linux x64, Node 24.22.1, Playwright 1.62.1, Chromium 152.0.7977.0 from pinned @sparticuz/chromium@152.0.0. Tested browser binary SHA-256 0144b4a0f456005a8185bb6a4629e909c8dd1f162b557364aaf5f1b12d4c1dc6. Browser/dependencies are not bundled.

Sixteen automated checks pass: invalid and oversized bundle rejection; valid load; keyboard activation; comprehension/practice failure and success gates; manual-pause clock separation; long scrolling; narrow layout with CSS text enlargement; three answer-control paths; two intermission boundaries; mid-session export; final export with three unique ordered cases. One real visibility transition is NOT_OBSERVED: headless page focus did not set document.hidden. No fake visibility event or document override was injected. Observed wall-clock change during a pause was approximately 0.253s with active change 0s. These are technical fixture measurements, not human performance.

Page errors and observed external page requests are zero in the exercised monitor. This is bounded observation, not proof against every background browser request. The browser uses a local fixture server; no live customer records, human reviewers, owner screenshots or hidden gold corpus are used. Synthetic answers are arbitrary test input, not measured human accuracy.

## Remaining acceptance gates

BLA-26 stays IN REVIEW. Native phone/Safari/Layla; real background/visibility timing; a complete keyboard-only session and human-visible focus; actual browser text zoom; and native reload/navigation warning need actual supported-host evidence. CSS enlargement is a layout proxy, not a native zoom pass. The existing development timing contract remains unresolved in the runner and is not silently frozen. No recruitment, human-study execution, quantitative threshold selection, publication claim or deployment approval follows from these tests.

## Reproduce

Use the current source checkout and trusted compatible Playwright/Chromium. Set AIAR_SOURCE_ROOT to the checkout, AIAR_SMOKE_OUTPUT to an empty test-output directory, JULIA_CHROMIUM_EXECUTABLE to the browser executable, and AIAR_EXPECTED_RUNNER_SHA256 to the exact candidate SHA above. Run node research/browser_smoke_2026_10_26/automated_runner_smoke.cjs. The default expected SHA targets the historical baseline so a changed candidate must be explicit. Exports remain local synthetic fixtures. Validate them with the existing validate_runner_data.py and runner-response schema.
