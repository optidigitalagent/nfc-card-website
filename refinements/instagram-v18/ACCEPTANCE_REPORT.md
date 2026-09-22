# NFC Instagram Card v18 — local candidate acceptance

Implementation and repeated local verification are complete. **This is a reviewable local candidate, not a released Instagram product.** Existing production remains unchanged. Final independent auditor evidence is recorded in INDEPENDENT_ACCEPTANCE.md.

|Item|Verified result|
|---|---|
|Repository|optidigitalagent/nfc-card-website|
|Starting full HEAD|`de3d2533381d12cee9f42567bfb7a67290d716c0`, clean current main/origin main|
|Working branch|`refinement/instagram-v18`; candidate remains uncommitted for review|
|Handoff SHA-256|`82bd92c32db01fcdae1b632f3ca6d5aebd853a16f9b1f9d89669a7dd2e7017b0`|
|Handoff internal checksums|27/27 pass; v18 instruction checksums4/4 pass|
|Recovery|Verified private full-history Git bundle; source/input archives retained|
|Product|NFC Instagram Card, `nfc-instagram-card`, `NFC-IG-READY`, ready only|
|Prices/quantities|1 =1500UAH;2 =2600UAH; no3+, branded/custom or QR|
|New routes|`/solutions/instagram-card`, `/en/solutions/instagram-card`, `/instagram-card`, `/en/instagram-card`|
|Design|Shared graphite/metallic-silver components, additive third catalog card after Review/Branded|
|Form|Required exact Instagram profile URL,1/2 quantity, name/phone/messenger/consent; optional comment; canonical server quote|
|Persistence|Isolated local PostgreSQL transaction/outbox, same-key retry and mock notification verified; no real submissions|
|Media|8 labelled neutral placeholders, no generated product image. Founder video disabled: approved poster/text alternative unavailable; approved founder text present|
|Content|Product9FAQ,4 new globalFAQ, cross-links, truthful NFC/system-notification flow, no automatic-follower/sales guarantee|
|SEO|Local canonical/hreflang/sitemap/structured-data and Pages base path verified; no search visibility claim|
|Tests|Final722-check run after two700-check passes, no failures/errors/skips; Node24/Python3.14/PostgreSQL17/Chromium|
|Browser QA|9 requested widths,108 new Pages route observations +144 existing full-stack observations; keyboard,actual200% zoom,reduced motion and errors checked|
|Review regression|Passed; standard13 and branded3 gallery items; protected media/About/admin/review files match baseline hashes|
|Critic findings|All14 unique medium findings across critic/auditor rounds fixed/re-reviewed; unresolved critical0/high0/medium0; two low notes: placeholder enlargement and bounded claim-guard paraphrase coverage|
|Security|Secret/private-data scan including reachable history; Pages: no personal fields in browser storage/analytics, no secret in Pages wire/bundle. Inherited full-stack contact drafts/pending payload retention is documented below|
|Publication authorization|Existing content-bound approval unchanged; no silent reauthorization of new PUBLIC content|
|Deployment/push/Railway/media generation|Not performed|

Changes and commands: [FILES_CHANGED.md](FILES_CHANGED.md), [TEST_REPORT.md](TEST_REPORT.md). Evidence: [BROWSER_QA_MATRIX.md](BROWSER_QA_MATRIX.md), [BEFORE_AFTER.md](BEFORE_AFTER.md), [CRITIC_FINDINGS.md](CRITIC_FINDINGS.md), [ROLLBACK.md](ROLLBACK.md).

Remaining release prerequisites are explicit: real approved Instagram product photography (or separately approved placeholder release); separate owner release permission; and compatibility/rollout verification for the existing external production gateway's new Instagram product/URL/pricing contract. That gateway belongs to another repository and was not changed or live-tested under this request. No new database or infrastructure is required by this local implementation; existing JSONB can store the additive fields. Do not enable the product on the live site until the gateway accepts the additive contract and durable receipt/outbox behavior is verified under separate authority. Historical deployment blockers in older reports are not evidence about today's infrastructure.

No remote CI run, GitHub clean clone, live CORS, Telegram delivery, public indexing or production performance result is claimed for this task. Read local regression and private install/build evidence within their actual boundaries. Runtime raw QA is excluded from the source manifest; representative evidence is included. Repository HEAD remains the recorded starting SHA; all intended source/tests/docs are a local reviewable patch.

Storage scope: the browser-storage privacy assertion applies to the Pages target only. The retained full-stack target stores contact draft fields (name, phone, messenger, comment) in sessionStorage and an unconfirmed submission payload, including Instagram URL, in IndexedDB for cross-reload idempotent retry. The pending record is deleted after a durable receipt or field-validation rejection; a failed/uncertain request remains until resolved or browser storage is cleared. No automatic expiry is claimed. That inherited behavior was preserved for Review compatibility and is excluded from the Pages build. Neither target sends personal fields to analytics.
