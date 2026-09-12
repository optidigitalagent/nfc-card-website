# v17 preparation acceptance — not a live deployment

Prepared from accepted v1.0.0 commit `2d4bf23be16e988ead0a815806a8e7c9d5b09788`.

**Status: local Pages implementation verified; publication and gateway integration
remain blocked.** This is not a completed v17 release or a deployed-site receipt.

## Evidence from this preparation

- Full sequential Node 24 / Python 3.14 / PostgreSQL 17 / Chromium suite:
  **600 passed**, no failed or skipped groups. Includes 14 new Pages regressions.
- Separate local Pages browser matrix: **144 route/width checks**, covering 16
  UA/EN routes at 320, 360, 390, 393, 430, 768, 1024, 1280 and 1440 pixels.
  No observed horizontal overflow, broken assets, missing image alt text,
  unsupported route links, browser errors or root-path failures.
- Six locale/width interaction sets cover thumbnails, gallery keyboard/lightbox,
  menu/keyboard, unavailable form status and reduced motion. Eight actual
  `chrome.tabs.setZoom/getZoom` checks verified zoom factor 2 and reflow.
- Two additional browser flows with intercepted synthetic transport reject a
  false durable receipt, retain fields through reload, retry the same key/body,
  and show success only for a confirmed durable receipt. **No real backend was
  called. These are not persistence, outbox or CORS-server acceptance tests.**
- An independent reviewer found no critical/high issue in the Pages preparation;
  independently checked 1,327 generated URL references and sampled three
  hash-verified screenshots. Normal full-stack artifact bytes match the accepted
  baseline except the two client scripts with inactive-by-default Pages branches.
- Authored source, Git index and complete reachable history passed the release
  guard. Four individually hashed benign-code/test-fixture scan exemptions are
  documented in `PACKAGING.md`. No blanket exemption was added.
- Current existing gateway's 47 mock-delivery tests passed without real sends.
  iADDS changed concurrently in another workstream; this task made no writes to
  its repository or Railway service and does not claim ownership of those changes.

## Remaining issue before enabling an endpoint

One medium client issue is explicitly held for the real bridge contract: a
conclusive validation rejection currently keeps the pending form locked, just
like an ambiguous transport failure. The verified disabled-endpoint preview is
unaffected. Before endpoint activation, define a conclusively unpersisted rejection
response, allow correction while retaining fields, and preserve the old key for
ambiguous outcomes. Add the corresponding end-to-end bridge/client tests.

## External blockers

The read-only target inventory found only `lead-gateway` in the specified
`antonov-lead-gateway` production project. There is no PostgreSQL, volume, bucket
or browser bridge. The gateway sends Telegram before success and deduplicates
in memory. It does not read `NFC_TELEGRAM_ENABLED`, so that variable alone cannot
provide the required NFC dry-run boundary. No NFC source was activated.

Creating a PostgreSQL service/volume needs separate owner authorization under
v17 section 9. Gateway implementation also needs a narrow source-scope exception:
its code lives in the iADDS repository that v17 otherwise forbids changing.
An additive schema/outbox/migration proposal is retained privately for review.
A syntax/ledger check on local PostgreSQL 17 succeeded inside a fully rolled-back
transaction; no Railway migration was executed and no live persistence is claimed.

The owner was asked whether to publish the Pages preview with explicitly
unavailable submission while these backend blockers remain. No answer has been
received at this checkpoint; deployment stays disabled, endpoint unset.

The target URL is https://optidigitalagent.github.io/nfc-card-website/.
At baseline it returned HTTP 200 with a Jekyll-rendered repository README,
**not the accepted NFC CARD website**. Local screenshots and CI cannot replace a
live HTTPS site verification. Update this report only with actual deployment,
workflow, browser and backend evidence when the missing decisions are resolved.

No new Railway resources, secret changes, billing changes, source onboarding,
real Telegram messages or recovery deletion occurred in this preparation.
