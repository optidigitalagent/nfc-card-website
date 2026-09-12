# v13 revision brief and execution log

The design and backend of the accepted v11/v12 application remain the baseline. This log records substantive v13 implementation and independent-review corrections; it does not claim acceptance before final tests/screenshots.

| Revision | Evidence / reason | Change and acceptance condition |
|---|---|---|
| R1 focused implementation | Four owner screenshots plus v13 scope | Product-specific media sizing, responsive derivatives, stable gallery opener and visible thumbnail rails, compact quote and messenger controls, full direct-review image, strong H2 tokens, canonical UA/EN About and shared final CTA/footer. Preserve protected backend bytes. |
| R2 footer | Initial 390 px screenshot measured about 420 px and pale legal links | Reset inherited contact flex direction; explicit graphite legal-link color; 12 px navigation labels and 44 px targets. Revised footer about 326 px at390 and225 px desktop. |
| R3 final composition | Initial mobile primary action was too high | Primary and secondary actions share a compact row, purposeful end alignment within54svh, stronger final heading. At390×844 primary center approximately55% of the final viewport; footer immediately adjacent. |
| R4 lightbox source | Test author source review | Zoom uses the canonical approved original image, not responsive `currentSrc`; adjacent preload remains bounded. |
| R5 mobile image evidence | Independent visual critic saw a blank lead image in early smoke | Fresh browser reproduction showed complete image filling its intended frame. Final screenshot helper waits for visible image decode and two paint frames; no source/media substitution. |
| R6 About title | Independent visual critic found a one-word line at390 | Preserve exact approved wording; narrowly tune About H1 responsive sizing. 320/390 screenshots now have three coherent lines. Critic visually rechecked both. |
| R7 zoom touch | Independent visual critic identified horizontal-panning risk | Zoomed scroll area allows horizontal/vertical pan; suppress carousel gestures while zoomed; reset scroll on zoom toggle. Genuine touch test must reach image edges without changing slide. |
| R8 analytics | Independent technical critic found About catalog navigation tagged as order start | Scope `order_start` to the order CTA and `telegram_click` to the actual Telegram action. About catalog/contact navigation should not fabricate an order-start event. Verification follows in final tests. |

Initial failed test logs are retained. Five static assertions initially confused image width with the longest image edge; they were corrected to verify the actual responsive-width contract while preserving aspect-ratio/provenance checks. The complete target static module then passed. A browser invocation with a nonexistent TEMP directory failed before launch; the isolated task TEMP was created and the suite rerun. Neither was an application defect.

## R9 — High runtime collision found by full matrix

The first full18-route bilingual320px matrix found two page errors on About. Its new `founder-story` ID collided with the accepted homepage story initializer, which expected a story toggle. The new About component now uses the distinct `about-founder-story` anchor/title IDs; existing `app.js` and homepage story behavior remain unchanged. New About navigation tests also assert zero page errors. All affected browser verification is repeated on the rebuilt candidate; the failed legacy320 log is retained.

## R10–R12 — Final review and CSP corrections

- EN final mobile CTA uses a locale-scoped title size (~36.7 px at390) so “reviewing simpler?” stays together; UA display size remains unchanged.
- A valid native messenger selection clears only that field's stale error/aria-invalid state. Other field errors, the pending guard, exact payload/validation, canonical pricing and persistence/retry code remain unchanged.
- The full console/security diagnostic found seven inline founder aspect-ratio declarations blocked by the existing strict CSP (High). The same source-bound ratios now live in external about.css selectors; the About view has no inline style attributes. CSP/server code is unchanged. The screenshot sweep also measures the document after lazy media resolves and explicitly captures the actual bottom, so full mobile About evidence includes its mission, CTA and footer.

All final checks and native captures are regenerated for this candidate. Earlier successful partial runs and failed diagnostic logs are retained as pre-final history.

## R13 — Decode-time catalog shift found by independent performance review

The complete c63289 candidate passed 461 behavioral tests, but the visual critic identified a real layout-shift gate outside those assertions. A node-attributed diagnostic reproduced one 0.271658 shift: the standard product photo inserted its 435 px height after first paint, moving card copy and the next product. The explicit `aspect-ratio:auto` declaration had removed predecode reservation. A browser-only response experiment proved causality: per-product `auto 4/5` and `auto 1160/940` fallbacks (and `auto 4/5` for direct-review media) produced zero session CLS in five scenarios while preserving identical decoded rectangles.

The production CSS now reserves those approved proportions at desktop and mobile widths; `auto` still adopts the decoded intrinsic image ratio. No image, product copy, backend or final layout was changed. A delayed-media browser regression checks space reservation before image release and stable geometry afterwards. The complete source-bound tests, after matrix and critiques are rerun for the rebuilt candidate. Superseded c63289 reports, logs and native screenshots are retained under `history/pre-cls-c632`; the original baseline is untouched. Raw cumulative measurements and diagnostic session-window CLS are distinguished in the final performance report.
