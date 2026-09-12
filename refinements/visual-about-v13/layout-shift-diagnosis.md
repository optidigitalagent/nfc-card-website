# v13 image reservation diagnosis

Confirmed production finding on public revision `c63289cb3d96e82035f98b2bd4f59b0b1de5891009fd6b79d1bfdacfabf45edb`. No source or public files changed during the investigation. The diagnostic browser exited after its run.

`layout-shift-diagnostic-390.json` records native layout-shift entries, source nodes and rectangles, resize observations, font events, resource timing, final media geometry, and a browser-response-only CSS experiment.

At 390×900 px, reduced motion, same browser context after navigating UA home, EN home produced **0.27165811965811965** in one shift at **126.8 ms**, with no recent input. The standard card's copy moved from y=309.4375 to y=744.4375: **435 px**, exactly the loaded image height. The next branded article left the visible viewport. EN catalog reproduced 0.271658; UA catalog produced 0.260163. Cold EN home and the first UA home did not shift in this particular run, demonstrating timing sensitivity rather than absence of a defect.

The v13 `.catalog-product-image` rules explicitly set `aspect-ratio:auto` in both base and mobile styles. Before the image is known, its height is not reserved; the branded image was also directly observed at height 0 before becoming 282 px. The existing mobile commerce rule contains `aspect-ratio:1`, so removing only the v13 declarations would reactivate the previous square ratio.

The reversible experiment fulfilled only the local stylesheet response with three appended rules:

```css
.commerce-card[data-variant=standard] .catalog-product-image { aspect-ratio: auto 4 / 5; }
.commerce-card[data-variant=branded] .catalog-product-image { aspect-ratio: auto 1160 / 940; }
.destination-image { aspect-ratio: auto 4 / 5; }
```

All five route observations in that experiment had a measured session CLS of 0. The final loaded media geometry matched the unmodified warm EN page exactly: standard 348×435 px, branded 348×282 px, and destination 350×437.5 px, with identical x/y positions. Thus explicit per-asset ratio fallback preserves the approved filled media layout while reserving its space before decode. Canonical standard media attributes are 1122×1402; its 480 px derivative is 480×600. A fallback derived from the canonical dimensions may differ slightly before decode because derivative rounding is unavoidable, but the `auto` keyword retains the loaded image's actual intrinsic ratio.

The matrix's recorded metric is sampled **before** screenshot capture or lazy-image sweeps (`tests/test_v12_browser.py`, performance sampling before `capture`). The focused after-capture tool samples later, after programmatic component scrolling and state capture. Both original tools sum eligible shifts for the entire observation rather than calculating session-window maximum. That distinction cannot explain this finding: it is a single attributed shift, and the diagnostic's session-window CLS equals the summed value.

The diagnostic uses the same external-network-blocking route mechanism as the QA harness. Routing disables the normal HTTP cache, so “warm” here means a previously used context and browser navigation scenario; it is not proof of a fully cached HTTP response. The exact scheduling difference between cold and subsequent navigation is not needed to establish the demonstrated image-reservation cause.

Recommendation: apply the bounded per-asset ratio reservation to the v13 catalog/destination rules, add a regression that delays product media until after first paint, rerun the attributed diagnostic on the real source change, then regenerate affected current-revision test/capture evidence. Preserve earlier c632 logs as valid historical checks, but do not use them to claim a blanket CLS pass or final performance closure after the source changes.

## Closure on the actual source fix

Root applied the scoped ratio reservation and built public revision `4b0ccbc08aecda587aae9600e79352a1829c6de9758de87caffcdaf0821e5414`. Four new native-browser tests delay the real local product image past first contentful paint on UA/EN home and catalog at 390 px. All four final cases reserve 435 px before decode, retain exactly the same image/copy rectangles after decode, and record session CLS 0. Their exact shift entries, request-release timings and native before/after load screenshots are in `targeted-regression/delayed-media-*.json`.

The full final sequence passed **465 tests** with identical source/public fingerprints before and after. The refreshed 144-context matrix records EN home/catalog at 390 with CLS 0; its largest initial-load eligible-shift sum across all routes/widths is 0.0442106. `final-test-evidence-audit.json` verifies current revision consistency. This closes the demonstrated photo-insertion regression within the tested local conditions; it is not a production or field Core Web Vitals certification.
