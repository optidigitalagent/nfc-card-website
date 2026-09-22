# Test report — local candidate, 2026-09-22

After two700-check passes, the final auditor requested additional claim guards. The final complete run passed **722 checks, zero failures/errors/skips**, including22 new editorial regression checks. This final run is sealed in [evidence/test-run-summary.json](evidence/test-run-summary.json). Counts are pytest checks, not a claim that every check is an independent user scenario.

|Group|Passed|
|---|---:|
|Unit/integration|667|
|Existing eight-width browser groups|8 (144 route-width observations)|
|Existing v12 interactive flows|11|
|Existing v13 visual/About flows|15|
|New Instagram browser groups|21 (including 108 route-width observations)|
|Total|722|

Runtime: Node 24, Python 3.14, PostgreSQL 17, Chromium. Use the existing QA virtualenv and an isolated local database matching the runner's `nfc_v12_test` name guard. Actual fixture schemas are random and removed at teardown. No production credentials or data are used.

```sh
# Set NFC_TEST_DATABASE_URL privately to the isolated local test database first.
NFC_TELEGRAM_ENABLED=false PYTHONDONTWRITEBYTECODE=1 npm test
NFC_ENV=production NFC_PUBLICATION_MODE=PUBLIC_PREVIEW NFC_PUBLIC_ORIGIN=https://optidigitalagent.github.io NFC_TELEGRAM_ENABLED=false npm run build
python -B scripts/verify_manifest.py
python -B scripts/release_guard.py --history
git -c core.whitespace=cr-at-eol diff --check
```

No separate lint or TypeScript configuration exists in this JavaScript/Python project. Node `--check` and Python `ast.parse` cover all 62 JS/Python authored files; this is syntax validation, not an invented typecheck. Existing lockfiles and dependencies remain unchanged.

New behavior checks cover exact ASCII HTTPS profile validation in Node/Python, deceptive hosts and reserved/non-profile paths, product/offer/SKU/quantity allowlists, 1500/2600 server prices, forged price rejection, payload identity, durable PostgreSQL transaction/outbox/retry/idempotency, native form parsing, Pages payload without client prices, publication approval remaining content-bound, four routes, FAQ/schema equality, eight honest media placeholders and protected Review assets/modules.

Browser tests use two boundaries: Pages POSTs are intercepted with a synthetic endpoint and receipt; full-stack forms write only to the isolated local PostgreSQL schema and deliver through MockNotifier. A `sent` fixture row proves the local state transition, not live Telegram delivery. Failed Pages submission retains all inputs and idempotency key; retry returns a durable-shaped mocked receipt; duplicate UI submission is suppressed. Real production gateway compatibility remains a future release prerequisite.

Fresh default/full-stack build emits 30 localized routes. Disposable Pages builds emit 28 routes with `/nfc-card-website`. PUBLIC tests derive an explicit synthetic approval only in disposable copies; the repository's publication approval is unchanged and will reject unapproved changed public content. The final Instagram-only desktop placeholder fill was present in the second run's fresh Pages fixtures; the root build was refreshed afterward.

Full console logs, JUnit files and raw captures stay in private task storage or ignored `work/`. GitHub CI, remote clone, deployment and live submission were deliberately not performed in this local-only task. [Portable source verification](evidence/portable-verification.json) passed manifest verification before/after `npm ci --ignore-scripts --no-audit --no-fund` and both production PUBLIC_PREVIEW builds (30 full-stack /28 Pages routes). It used the local manifest-selected candidate, not a GitHub clean clone. [Syntax evidence](evidence/syntax-verification.json) lists the62 checked files. The loopback-only static preview uses that Pages artifact with no backend endpoint and disabled submission; browser inspection confirmed the rendered product page.

Final-auditor follow-up: the product-only build-time content validator rejects seven prohibited promise categories in UA/EN. Fourteen adversarial inputs are tested across six source destinations (copy, informational lead, both descriptions and FAQ answers), alongside approved negations, adjacent false-claim isolation, rendered pages/metadata and actual failed-build tests. This bounds known editorial regressions; human source review remains necessary for new paraphrases.
