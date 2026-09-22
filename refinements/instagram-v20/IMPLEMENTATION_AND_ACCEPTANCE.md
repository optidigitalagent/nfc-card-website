# NFC Instagram Card corrective release v20

## Scope

This release completes the additive Instagram product integration on the
accepted NFC CARD site. The existing Review Card and Branded Review Card
products, media, prices, forms, reviews, admin and visual system remain in
place.

The release adds and publishes these bilingual route pairs:

- `/solutions/instagram-card/` and `/en/solutions/instagram-card/`;
- `/instagram-card/` and `/en/instagram-card/`.

## Product truth

- NFC Instagram Card is available only with the ready-made design.
- It uses NFC and has no QR code or branded/custom variant.
- Quantity is limited to one or two cards.
- Server-authoritative totals are UAH 1,500 and UAH 2,600.
- Real product photography has not been supplied, so every product-media slot
  remains an explicitly labelled placeholder.
- The card opens the configured Instagram profile. It does not follow an
  account automatically and does not guarantee followers or sales.

## Corrective implementation

- The complete approved commercial copy is visible as page sections; it is no
  longer hidden in one master disclosure.
- Descriptive headings, paragraphs and lists use the primary ink token.
  Captions, hints, disabled controls and secondary labels retain muted tokens.
- The commercial page includes the six-slot placeholder gallery, fixed price
  selector, Instagram-specific form, complete product FAQ and Review Card
  cross-link.
- The informational page contains the approved problem, three-step mechanism,
  business value, use contexts, product truth, founder text fallback, product
  choice and final CTA.
- Catalog, product, information and order routes cross-link through the Pages
  base path.
- Product/Offer and visible FAQ structured data, canonical URLs, reciprocal
  UA/EN hreflang and sitemap routes are generated from the same model.
- `AGENTS.md` records the owner's same-repository, same-URL release rule.

## Evidence

The pre-change recovery bundle, patches, package checksum verification and
browser captures are stored outside the repository under the task-private v20
evidence directory. Raw screenshots are intentionally excluded from the source
release.

Required verification before release:

- complete local suite with PostgreSQL 17 and Chromium;
- browser matrix at 320, 360, 390, 393, 430, 768, 1024, 1280 and 1440 px;
- keyboard, 200% zoom and reduced-motion coverage;
- secret/private-data release guard and manifest verification;
- independent visual and technical acceptance with no critical/high issue;
- clean-clone install, tests and production build;
- green GitHub Actions for the exact release SHA;
- successful GitHub Pages deployment and anonymous live checks for all four
  routes, assets, reloads, metadata and form startup;
- existing Railway gateway deployment accepts the additive Instagram payload
  and preserves the iADDS and Review Card contracts.

## Completed local acceptance

- Package and handoff integrity: v20 package SHA-256
  `5075a0fa65d83dae9d1e3238d7b3c8135387bef92cd00ef6163de8870c194461`;
  source handoff SHA-256
  `82bd92c32db01fcdae1b632f3ca6d5aebd853a16f9b1f9d89669a7dd2e7017b0`;
  internal checksum sets 9/9 and 27/27.
- Complete NFC CARD suite: 728 checks, zero failures, errors or skipped groups
  on Node 24.20.0, Python 3.14.7, PostgreSQL 17.11 and Chromium 143.
- Browser coverage: 320, 360, 390, 393, 430, 768, 1024, 1280 and 1440 px,
  both locales, all Instagram routes plus protected Review routes; keyboard,
  actual 200% zoom and reduced motion are included in the sequential suite.
- Production Pages build: `PUBLIC`, 28 localized public routes, index/follow,
  base path, canonical, reciprocal hreflang, sitemap and robots verified.
- Independent visual/copy and technical critics: ACCEPT after corrections,
  with C0/H0/M0/L0 in both final reviews.
- Existing gateway release `1e42351e4250c2fe81e98a8ede265ada06bed524`
  adds migration 003 and the versioned Instagram contract. Its isolated suite
  passed 137/137 on Node 24 and PostgreSQL 17; the unchanged iADDS application
  build and 99 unit/integration tests also passed.
- No real form or Telegram submission was used. No new Railway or paid resource
  is part of the release.

Exact remote workflow IDs, the NFC CARD release SHA, Railway deployment ID and
anonymous live checks are reported with the completed release after verification.
