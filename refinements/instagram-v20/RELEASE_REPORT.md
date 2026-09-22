# NFC Instagram Card corrective release v20

## Release scope

The existing NFC CARD site gains complete UA/EN commercial and informational
Instagram Card pages, the ready-only 1/2-card order flow, server-authoritative
pricing and additive durable gateway support. Review Card, Branded Review Card,
iADDS frontend behavior and the accepted graphite/metallic-silver visual system
remain intact.

## Acceptance evidence

| Gate | Result |
|---|---|
| Source baseline | `de3d2533381d12cee9f42567bfb7a67290d716c0` |
| Handoff integrity | exact expected SHA-256; internal checksums passed |
| NFC CARD tests | 728 passed; no skipped groups |
| Widths | 320, 360, 390, 393, 430, 768, 1024, 1280, 1440 |
| Locales/routes | UA/EN catalog, commercial, information, order and Review regressions |
| Accessibility | keyboard, 200% zoom and reduced motion passed |
| Independent reviews | two final ACCEPT decisions; C0/H0/M0/L0 |
| Gateway | 137 passed on PostgreSQL 17; migration 003 and outbox verified |
| iADDS boundary | frontend source unchanged; build and 99 unit/integration tests passed |
| Publication | content-bound owner authorization; PUBLIC Pages build passed |
| Messaging | no real form or Telegram submission during QA |
| Infrastructure | existing GitHub Pages and Railway gateway only; no new resource |

The exact frontend release SHA, GitHub Actions URLs, Railway deployment ID and
anonymous live route checks are supplied in the final release response because
they exist only after this report is committed and deployed.

## Rollback

Follow [ROLLBACK.md](ROLLBACK.md). Revert ordinary commits without force and
preserve PostgreSQL records plus migration 003 columns.
