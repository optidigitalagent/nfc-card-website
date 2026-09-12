# Route / API / data / media map

| Surface | Before | After |
|---|---|---|
| Public static routes | 24 localized routes | 26; only `/about` and `/en/about` added |
| About navigation | Homepage `#about` teaser | Canonical About in header, mobile menu, footer and teaser; existing `#about` retained |
| Commerce | Separate Review Card / Branded Review Card, order/contact flows | Same canonical routes, server pricing, quantities, native form hydration and redirects |
| Homepage endpoint | Large embedded request form | Compact final action to the existing localized order route, plus Telegram link |
| About endpoint | No standalone company/founder page | Full verified founder/company narrative; final CTA to localized solutions/contact |
| Public reviews | Zero-review section/nav absent, submission page available | Same; no first review fabricated |
| Private admin | Authenticated server-rendered moderation application | Same routes, authentication, CSRF, moderation and asset boundaries |

Full exact localized lists: [route-map.json](route-map.json). No existing route was removed. About canonical, reciprocal UA/EN hreflang, language switch and sitemap use the established builder. Metadata is localized and truthful; no invented Person/review/rating schema.

| API boundary | Owner / unchanged behavior |
|---|---|
| GET `/api/pricing`, POST `/api/leads` | `server/preview.py`, canonical pricing, durable lead persistence, idempotency and notification boundary |
| GET `/api/reviews`, `/api/reviews/options`; POST `/api/reviews/submit` | Pending-only public submissions; published-only public data |
| `/api/reviews/assets/{id}/{small|large}` | Published approved derivatives only |
| `/api/admin/session`, login/logout, reviews and review actions | Protected session/CSRF moderation, raw review retention, publication eligibility |
| `/api/admin/reviews/assets/{id}/{small|large}` | Authenticated private derivative access |

Data: existing PostgreSQL migrations 001–003, repositories, private S3-compatible adapter, image sanitization, outbox/durable-before-send, session and retention implementation are byte-identical. V13 adds no migration, schema, production resource or new data store. Tests use isolated synthetic schemas in `nfc_v12_test`; the preview's real records are not edited for QA.

Media: the existing 15 approved catalog/product/brand assets remain byte-identical; 16 bounded product derivatives and 28 exact approved founder AVIF/WebP derivatives are appended through the strict build allowlist. Messenger icon paths are locally bundled. Reference screenshots, held creatives, source portraits and private review uploads are excluded from public output. [Media delta](MEDIA_PROVENANCE_DELTA.md), [protected hashes](integrity-check.json).
