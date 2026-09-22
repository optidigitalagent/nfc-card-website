# Browser QA matrix

All 9 required widths passed: **320, 360, 390, 393, 430, 768, 1024, 1280, 1440 px**. Chromium, desktop height900, UA/EN. [Machine-readable Pages observations](evidence/pages-route-matrix.json).

|Coverage|Result and evidence|
|---|---|
|Before baseline|72 captures, 8 existing routes ×9 widths, no horizontal overflow; immutable private baseline|
|Instagram/additive Pages matrix|108 observations: 6 routes ×2 locales ×9 widths, each direct load + reload returns200|
|New routes|`/solutions/instagram-card`, `/en/solutions/instagram-card`, `/instagram-card`, `/en/instagram-card`|
|Shared/old routes in Pages matrix|UA/EN catalog, order, Review Card, Branded Review Card|
|Existing full-stack regression|144 observations:9 routes ×2 locales ×8 original widths, including home, About, contact, public review and admin login|
|Gallery|6 visible labelled slots, thumbnail selection, Enter opens, arrow navigation, Escape closes and restores focus; existing standard13 and branded3 items preserved|
|Purchase|1/2 only, 1500/2600, product-specific required URL, visible total, header/mobile menu retains product and quantity, locale switch preserves preselection|
|Submission boundary|UA/EN Pages validation failure before request, forced network failure/input retention, same-key retry/mocked success and duplicate suppression|
|Local persistence|UA/EN actual isolated PostgreSQL submissions plus4 UA/EN×quantity native no-JS cases; mock delivery only|
|Accessibility|One H1, correct lang, image alt coverage, keyboard/gallery focus, error association/focus, native control operation, no horizontal overflow, reduced motion|
|200% zoom|Existing extension-based `tabs.setZoom/getZoom` test extended to all4 new pages:11 routes total; actual browser zoom2,720 CSS px at1440 physical px|
|Assets/base path|Rendered local links retain `/nfc-card-website`, visible images decode, reload succeeds; route/asset/404/SEO tests cover the full generated inventory|
|Console/network|No page/console errors or blocked external requests in the new normal-navigation matrix. All real remote transport denied; intentional failure simulation is confined to the retry test|
|Pages privacy|No personal inputs in localStorage/sessionStorage/analytics; product_id is allowlisted, no client pricing or gateway secret in Pages payload|

Raw captures: ignored `work/qa/instagram-v18`; existing regression `work/qa/v12` and `work/qa/v13`. Only10 representative screenshots are included here. Screenshot counts do not by themselves establish quality: automated assertions were supplemented by implementer visual inspection and independent visual/UX/accessibility criticism. No formal WCAG certification, Safari/device-lab coverage, production performance or search-visibility result is claimed.

The full-stack mode has inherited sessionStorage contact drafts and IndexedDB pending-request retention for reload/retry. It was preserved; the Pages privacy test does not assert otherwise. See FORM_AND_PAYLOAD_CONTRACT.md for deletion conditions and lack of automatic expiry.
