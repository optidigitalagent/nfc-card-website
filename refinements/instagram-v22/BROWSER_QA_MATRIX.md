# Browser QA matrix

Engine: Playwright Chromium. External traffic is denied. Static Pages builds use a synthetic mocked gateway only where form behavior is tested; no production POST or real notification is possible.

| Width | UA product/info | EN product/info | Overflow | Images | Banner layout |
|---:|---|---|---|---|---|
| 320 | pass | pass | none | pass | pass |
| 360 | pass | pass | none | pass | pass |
| 390 | pass | pass | none | pass | pass |
| 393 | pass | pass | none | pass | pass |
| 430 | pass | pass | none | pass | pass |
| 768 | pass | pass | none | pass | pass |
| 1024 | pass | pass | none | pass | pass |
| 1280 | pass | pass | none | pass | pass |
| 1440 | pass | pass | none | pass | pass |

The matrix also checks catalog/order/Review Card/Branded Review Card routes, reload stability, broken images, gallery keyboard navigation and lightbox focus return. The full suite covers actual Chromium 200% browser zoom on both UA/EN Instagram routes, 360 px equivalent reflow, reduced motion and keyboard-only controls.

Detailed local artifacts: `work/qa/instagram-v22/` and existing versioned QA suites under `work/qa/`.
