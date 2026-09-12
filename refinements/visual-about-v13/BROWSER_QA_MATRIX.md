# Native browser QA

Public output revision: `4b0ccbc08aecda587aae9600e79352a1829c6de9758de87caffcdaf0821e5414`. Separate roots preserve before evidence, focused after captures and regression/state captures. All matrices below use this exact public revision, with no candidate edits during their accepted runs.

| Width | Native before comparison | Native after comparison | Integration routes UA/EN | Maximum public footer height |
|---|---:|---:|---:|---:|
| 320 | 8 | 10 | 18 | 343.1 px |
| 360 | 8 | 10 | 18 | 343.1 px |
| 390 | 8 | 10 | 18 | 325.6 px |
| 430 | 8 | 10 | 18 | 325.6 px |
| 768 | 8 | 10 | 18 | 310.2 px |
| 1024 | 8 | 10 | 18 | 289.2 px |
| 1280 | 8 | 10 | 18 | 225.2 px |
| 1440 | 8 | 10 | 18 | 225.2 px |

Before: home, standard PDP, branded PDP and order, both locales. After: the same plus About. Integration matrix additionally exercises catalog, contact, public review form and admin login:144 rows. Authenticated empty admin queue/create contributes 32 route/width rows. Diagnostic route/control/network checks and actual browser zoom are separate state reports, not added to the144 route count.

All 80 focused after rows returned200, have one H1, no horizontal overflow, no broken image and no public review section/nav. Page errors and failed HTTP requests:0. Separate individual native screenshots are retained; long documents use overlapping viewport sequences with actual scroll offsets instead of synthesized stitched pages. Full390/1440 page sequences are referenced from the same-revision integration run (900px viewport height), avoiding duplicate captures; focused390px comparison/ending screenshots use844px height. Component clips use the native full-document capture API; visible images are decoded before capture.

- [Before comparison matrix](before-matrix.json) / [after comparison matrix](after-matrix.json).
- [144-row integration matrix](legacy-regression/browser-matrix-verified.json) / [32-row authenticated admin matrix](legacy-regression/admin-matrix-verified.json).
- [Actual200% browser zoom](legacy-regression/actual-browser-zoom.json): disposable extension/profile, `chrome.tabs.setZoom/getZoom`, DPR2 and720CSS-px reflow in1440 viewport. This is separate from the half-width reflow check.
- [Reduced motion and story controls](legacy-regression/motion-reflow.json); gallery/mobile-menu keyboard and real touch interactions in test logs.
- [Gallery, messenger and About state evidence](targeted-regression): all available thumbnails, first/last selection, keyboard, swipe, modal focus/scroll, original-resolution zoom, horizontal touch pan without changing slide, default/selected/error/focus states, and correct About routing/media variants.
- [Commerce retry/persistence](legacy-regression/commerce-browser-flow.json), including a lost response, immutable pending fields and exactly one durable record after retry. Disabled messenger screenshot is a labelled synthetic test state.
- [UA review/admin flow](legacy-regression/uk-review-admin-flow.json) / [EN](legacy-regression/en-review-admin-flow.json): pending-only submission, private assets, protected moderation, unsaved-change safeguards, logout and zero public reviews.

The final390×844 home primary CTA center is 54.9% of the viewport, and the footer follows immediately. All target links remain keyboard-accessible and touch controls meet the checked44 px boundary. Accessible roles/names, native radio state and dialog focus were verified; no physical screen-reader/device session is claimed.

Only Chromium is installed in the available Playwright runtime; Firefox/WebKit binaries were absent. [Engine inventory](browser-engines.json). Physical Safari/iOS/Android testing remains outside this local workstation evidence.

Performance observations: [raw local summary](performance-observations.json). LCP/CLS and sampled interaction durations are laboratory observations on a shared machine, not production/field certification. Product thumbnails use160px derivatives, nonadjacent original photos are deferred, founder AVIF/WebP sources are responsive and below-fold photos are lazy. No carousel dependency or runtime media hotlink was added.

[Explicit auxiliary state index](state-evidence-index.json) binds the 16 additional native regression captures to their exact passing test producer, final revision and image SHA-256, including disabled pending messenger, synthetic pending receipts, empty manual admin forms, reflow/menu and story-pause states.

A focused 768 px capture attempt stalled in an unbounded whole-body image-decode wait. The capture helper now scopes modal images to the active dialog, checks both viewport axes, and bounds waits with explicit failure diagnostics for incomplete visible images. The 768 px capture was repeated successfully; no site source changed. [Interruption record](capture-interruption.json).
