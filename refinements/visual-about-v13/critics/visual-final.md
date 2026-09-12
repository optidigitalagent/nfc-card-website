# Independent final visual / UX acceptance — NFC CARD v13

**Verdict: ACCEPT for local v13 visual scope. Open critical: 0; high: 0; medium: 0.**

Public site revision: `4b0ccbc08aecda587aae9600e79352a1829c6de9758de87caffcdaf0821e5414`  
Sealed source revision: `446a54d0dddac08cb10e0d0bf27f698986861b5812defd8da381b126bb28fec5`

This conclusion follows native screenshot inspection, source review, independent defect reports and retest evidence. The implementation was not authored or changed by this critic. It preserves the accepted v11 design and behavior; it does not propose an unrelated redesign.

## Scope verdict

- **Design:** Approved graphite/silver skin and typographic family retained. Catalogue media occupies its frame without dead bands; direct illustration and caption are complete. Larger deliberate headings, compact quote and immediate footer resolve the specified visual issues.
- **Ux:** Both product pages expose marketplace rails and current-image controls. Lightbox controls, keyboard containment, zoomed touch pan and return behavior are evidenced. Messenger choice is compact, branded and uses native radio semantics; error recovery is coherent.
- **Responsive:** Eight requested widths have 80 focused contexts and 144 legacy route contexts. No horizontal document overflow, broken image or heading-count anomaly in focused matrix. Native mobile/tablet/desktop inspected, including complete UA home/About sequences and EN counterparts/samples.
- **Accessibility:** Visible focus and selected states inspected. Current interaction evidence covers keyboard rail Home/End/arrows, modal bidirectional Tab trap/Escape, return/scroll restoration and radio keyboard selection. Independent evidence audit also records seven actual 200% zoom routes and reduced-motion checks; this is scoped review, not a WCAG certification.
- **Anti-Template:** Existing product-specific imagery, physical review-card information, founder story, timeline and authorized photography give the pages a coherent NFC CARD identity. About uses the approved site visual system, rather than importing iADDS styling or generic testimonial filler.

## Defect closure

- **V13-VIS-MEDIA-RESERVATION (high) — CLOSED.** Intrinsic predecode media ratios reserve the same geometry as decoded assets. All four delayed-image home/catalogue UA/EN cases record zero rectangle change and session CLS 0. Evidence: `layout-shift-diagnosis.md`, `targeted-regression/delayed-media-en-home.json`, `targeted-regression/delayed-media-en-catalog.json`, `targeted-regression/delayed-media-uk-home.json`, `targeted-regression/delayed-media-uk-catalog.json`, `critics/visual-pixel-compatibility.json`.
- **V13-VIS-ABOUT-H1 (medium) — CLOSED.** Original wording preserved, responsive typography produces coherent three-line title at 320/390; hierarchy remains strong. Evidence: `legacy-regression/screenshots/verified/uk-about-320-top.png`, `legacy-regression/screenshots/verified/uk-about-390-section-01.png`.
- **V13-UX-ZOOM-PAN (medium) — CLOSED.** Zoomed image permits both-axis pan; carousel handling is suppressed while zoomed. Genuine touch regression observes scrollLeft 145, and modal keyboard/close/scroll restoration passes. Evidence: `targeted-regression/gallery-standard-320.json`, `targeted-regression/screenshots/en-standard-lightbox-zoom-touch-pan-320.png`.
- **V13-VIS-EN-CTA (medium) — CLOSED.** Locale-specific narrow typography keeps original headline in two cohesive lines; UA retains larger heading. Evidence: `screenshots/after/en-home-390-ending.png`, `screenshots/after/uk-home-390-ending.png`.
- **V13-UX-MSG-CLEAR (medium) — CLOSED.** Selecting a messenger clears its own error and aria-invalid while retaining unrelated invalid-field feedback. Focus and single selection remain visible. Evidence: `targeted-regression/controls-footer-390.json`, `critics/messenger-feedback-boundary.json`, `targeted-regression/screenshots/en-messenger-keyboard-selected-390.png`.
- **V13-QA-ABOUT-TAIL (evidence gap) — CLOSED.** Native sequence recomputes page extent and proves actual bottom. UA390 reaches 13773+900=14673; EN390 reaches 13562+900=14462. Mission, final CTA and complete footer inspected. Evidence: `final-test-evidence-audit.json`, `legacy-regression/screenshots/verified/uk-about-390-section-21.png`, `legacy-regression/screenshots/verified/en-about-390-section-20.png`.

## Current evidence

The completed `after-matrix.json` binds all 80 focused contexts to the public revision above: 320, 360, 390, 430, 768, 1024, 1280 and 1440px, with UA/EN home, both products, order and About. All return 200, have one H1, no horizontal document overflow and no broken images; page/HTTP error arrays are empty. 512 separate native focused PNGs are present. The independent test evidence audit also binds 144 legacy route-width contexts, 15 targeted reports and the complete 465-pass local suite to this candidate. Test totals support but do not substitute for visual inspection.

At 390×844, the home main action center is approximately 54.93% of viewport height (the requested approximate 55% lower edge), with a 325.56px footer immediately following the final CTA. UA/EN text is complete; the EN title has two cohesive lines. Desktop endings use a compact light footer below the graphite CTA, without an extra large section.

Current native tablet/desktop catalogue, direct section, quote and endings were inspected after capture. Full UA home390, UA About390/1440 and listed EN About sequences were inspected during the preceding frozen visual review. Their current pixels were independently matched byte-for-byte: all 129 current home/About390/1440 sequence files match the c632 images despite the predecode-ratio correction. This validates visual continuity while the new delayed-media tests validate the loading fix. Exact inspected paths, methods and SHA-256 values are in `visual-final.json`; the complete identity comparison is `visual-pixel-compatibility.json`.

Performance caveat: the final focused maximum initial session-window CLS is 0.045981, rather than a blanket zero claim. The four causally targeted delayed-media cases specifically record CLS 0 and no rectangle movement. These are unthrottled local Chromium observations, not field metrics.

## Exact native images inspected

- `legacy-regression/screenshots/verified/uk-home-390-section-01.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-02.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-03.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-04.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-05.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-06.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-07.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-08.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-09.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-10.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-11.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-12.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-13.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-14.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-15.png`
- `legacy-regression/screenshots/verified/uk-home-390-section-16.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-01.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-02.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-03.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-04.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-05.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-06.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-07.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-08.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-09.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-10.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-11.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-12.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-13.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-14.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-15.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-16.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-17.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-18.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-19.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-20.png`
- `legacy-regression/screenshots/verified/uk-about-390-section-21.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-01.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-02.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-03.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-04.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-05.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-06.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-07.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-08.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-09.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-10.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-11.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-12.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-13.png`
- `legacy-regression/screenshots/verified/uk-about-1440-section-14.png`
- `legacy-regression/screenshots/verified/en-about-390-section-01.png`
- `legacy-regression/screenshots/verified/en-about-390-section-02.png`
- `legacy-regression/screenshots/verified/en-about-390-section-14.png`
- `legacy-regression/screenshots/verified/en-about-390-section-17.png`
- `legacy-regression/screenshots/verified/en-about-390-section-18.png`
- `legacy-regression/screenshots/verified/en-about-390-section-19.png`
- `legacy-regression/screenshots/verified/en-about-390-section-20.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-01.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-03.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-04.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-06.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-08.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-10.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-12.png`
- `legacy-regression/screenshots/verified/en-about-1440-section-14.png`
- `screenshots/after/uk-home-390-ending.png`
- `screenshots/after/en-home-390-ending.png`
- `screenshots/after/uk-home-390-catalog.png`
- `screenshots/after/uk-home-390-direct.png`
- `screenshots/after/en-about-390-ending.png`
- `screenshots/after/uk-order-390-messenger-focus.png`
- `screenshots/after/uk-home-320-direct.png`
- `screenshots/after/uk-home-320-quote.png`
- `screenshots/after/uk-home-320-catalog.png`
- `screenshots/after/uk-about-320-ending.png`
- `screenshots/after/uk-home-768-catalog.png`
- `screenshots/after/uk-home-1024-direct.png`
- `screenshots/after/en-home-1280-ending.png`
- `screenshots/after/uk-home-1024-quote.png`
- `screenshots/after/uk-home-768-footer.png`
- `screenshots/after/uk-home-1440-ending.png`
- `screenshots/after/en-home-1440-catalog.png`
- `screenshots/after/en-about-1440-ending.png`
- `screenshots/after/uk-home-1440-direct.png`
- `legacy-regression/screenshots/verified/uk-about-320-top.png`
- `legacy-regression/screenshots/verified/en-about-360-top.png`
- `legacy-regression/screenshots/verified/uk-about-768-top.png`
- `legacy-regression/screenshots/verified/en-about-1024-top.png`
- `legacy-regression/screenshots/verified/uk-solutions-review-card-1280-top.png`
- `legacy-regression/screenshots/verified/en-solutions-branded-review-card-430-top.png`
- `targeted-regression/screenshots/en-final-cta-footer-390.png`
- `targeted-regression/screenshots/uk-final-cta-footer-390.png`
- `targeted-regression/screenshots/uk-messenger-keyboard-selected-320.png`
- `targeted-regression/screenshots/en-messenger-keyboard-selected-390.png`
- `targeted-regression/screenshots/uk-standard-thumb-selected-320.png`
- `targeted-regression/screenshots/en-branded-lightbox-1440.png`
- `targeted-regression/screenshots/en-standard-lightbox-zoom-touch-pan-320.png`
- `targeted-regression/screenshots/uk-standard-lightbox-390.png`
- `targeted-regression/screenshots/uk-standard-lightbox-zoom-touch-pan-320.png`

## Boundaries

- Independent critic used native screenshots, source inspection and recorded browser evidence; no browser was launched or app source modified by this critic.
- Acceptance is for the requested local v13 visual/UX/responsive/accessibility scope. It does not independently certify production infrastructure, third-party delivery, other browser engines or physical devices.
- Performance observations are unthrottled local Chromium on a shared workstation. Maximum focused initial session-window CLS is 0.045980556604229984; this is not a claim of blanket zero CLS or field Core Web Vitals. Four causal delayed-media cases are specifically zero.
- Not every generated PNG was individually viewed. Exact inspected native images are listed with SHA-256; 129 sequence-image identities additionally bind prior visual inspection to the corrected current candidate.
- At 320px the compact UA footer is about 343px due to legitimate legal/link wrapping, marginally above the approximate 340px guide; no clipping, unreadable controls or substantive visual defect was found.

Required local design/UX/responsive/accessibility/anti-template critic skills were applied along with the project director and web studio workflow. The scope, issue matrix and existing-site constraints governed the review. No deployment, Git push, domain/provisioning operation or real customer message was performed.
