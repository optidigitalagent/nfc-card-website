# v1.0.0 release evidence

This is a standalone release of the accepted NFC CARD application, not a new
site. **Deployment is blocked; no live HTTPS URL is verified.** GitHub release
acceptance and production acceptance are separate gates.

This source-controlled report records pre-push preparation. Post-push commit/tag,
remote Actions URLs and clean-clone receipts are published in the
[v1.0.0 release notes and acceptance attachments](https://github.com/optidigitalagent/nfc-card-website/releases/tag/v1.0.0).
They must identify this exact commit; their existence or success is not inferred
from this link. This separation avoids changing the tested commit merely to
insert its own SHA or later CI result into a file it hashes.

## Source and release changes

- Original archive SHA-256:
  `9cf61bc26214321d296adeae4c63eb21a5b624bfa9f8849797bcb51c66ff5de0`.
- Initial exact inventory: 199 hashed files plus manifest, all passed.
- Original manifest retained separately; release manifest covers the final
  authored tree and release additions. See `SOURCE_PROVENANCE.md` and `PACKAGING.md`.
- Node-generated, bilingual 26-route frontend; Python/Gunicorn WSGI;
  PostgreSQL migrations 001–003; private S3 adapter; durable order/review storage;
  protected admin, explicit moderation and published-only review assets retained.
- Explicit default `PUBLIC_PREVIEW`, verified-origin requirement, content-bound
  `PUBLIC_INDEXABLE` authorization, private-route noindex, safe cache headers,
  generic initialization failure and DB-aware health response added.
- Railway's exact probe hostname is permitted only on read-only `/healthz`.
  Ordinary Host/Origin checks remain on forms, APIs and admin.
- A repeatable queued-dialog-close race found by fresh browser tests was fixed
  with synchronous/idempotent body-lock restoration. No gallery design changed.

## Fresh local validation

Declared environment: Node 24.20.0, Python 3.14.7, PostgreSQL 17.11,
Playwright 1.57.0 Chromium 143.0.7499.4. Dependencies installed into a fresh
virtual environment from hashed lockfiles; `npm ci` and build passed.
Only disposable loopback PostgreSQL databases and synthetic fixtures were used.

Final complete-run status: **PASS — 586 checks** (552 unit/integration and 34
browser cases). The compact `local-validation.json` receipt records every
sequential group with zero failures, errors and skipped tests before push. Historical 465-test reports
are preserved as provenance, not counted as a fresh pass.

Coverage includes all 465 original checks plus release/publication regressions:
server prices and idempotency; persistence-before-notification; migrations and
restart durability; private/public images and sanitation; upload failure and
compensation; pending-only submissions; admin authentication/CSRF/moderation;
publication metadata, origin rejection, runtime drift, noindex and caching;
manifest/source/index/history safeguards. Browser checks include the eight widths
320, 360, 390, 430, 768, 1024, 1280 and 1440, UA/EN routes, galleries, native and
enhanced forms, keyboard, real 200% browser zoom, reduced motion and touch.

The first run exposed the historical whole-file WSGI hash gate, incompatible
with the explicitly requested publication boundary. It now retains all 29 other
protected byte hashes and compares sealed original WSGI method AST hashes after
strictly constrained release-only normalization; behavioral tests cover every
changed boundary. No historical snapshot was rewritten. Gallery failures were
fixed in application code, without weakening or skipping the browser cases.

## Visual preservation

`selected-evidence/comparison.json` records separate before/after captures from
local WSGI, route/status/cache checks and hashes. Four selected desktop/mobile
pairs are pixel-identical. Twenty-four of 26 rendered body DOMs are identical;
only the bilingual privacy draft's inaccurate “this computer” storage wording
was corrected to private application-server storage. All 64 source media files
remain byte-identical; the 59 public-media manifest hashes passed independently.
An eight-cycle immediate close/reopen check verifies stale close events cannot
unlock an active gallery or leave a closed page locked.

Eight selected screenshots are retained. Raw matrices, private browser state,
logs, local databases and build outputs remain outside Git. Publicly supplied
founder/business media is intentional content; the initial incidental-vehicle
observation was independently withdrawn as a mandatory redaction requirement
after provenance/owner authorization was considered.

## Independent review and remaining gates

Independent implementer-separated reviewers inspect source, release packaging,
publication/security behavior and final acceptance. A probe-host compatibility
finding, trailing-dot origin bypass and overly broad preservation predicate were
fixed with new targeted tests. Final closure is recorded in the release receipt;
an earlier critic report must not be treated as reviewing later code automatically.

No production system was accessed for tests and no real messages were triggered.
Production PostgreSQL, S3 bucket policy/connectivity, deployed admin, live pending
reviews, live orders and HTTPS/browser acceptance remain **NOT VERIFIED**.
Local/fake storage tests do not prove a private production bucket. Docker was
not locally executed because no Docker runtime is installed.

Existing connected Railway infrastructure was inspected read-only; no intended
isolated NFC full-stack service/database/bucket was established. No unrelated
service was repurposed, paid resource created, billing/domain changed or Pages
deployment substituted. CI is configured; automatic CD awaits that target.
See root `DEPLOYMENT_BLOCKERS.md` for exact prerequisites and `RUNBOOK.md` for
migration, safe admin setup, persistence validation, restore and rollback.

Handoff, extraction, standalone source and clean clone must remain local while
any live gate is missing. SiteAgent, iADDS and other runs are outside cleanup.
