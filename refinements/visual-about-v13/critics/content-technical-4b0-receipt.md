# Independent receipt for the image-reservation correction

**Source and focused delayed-media verification PASS; complete new-revision runtime acceptance remains pending.** This receipt does not promote the earlier c632 verdict to the current revision.

- Current public SHA-256: `4b0ccbc08aecda587aae9600e79352a1829c6de9758de87caffcdaf0821e5414`.
- Current full-source SHA-256: `446a54d0dddac08cb10e0d0bf27f698986861b5812defd8da381b126bb28fec5`.
- Independently recomputed both sealed digests and verified every source/public file against the seal.
- Relative to c632, exactly two authored files changed: `src/visual-v13.css` and the targeted `tests/test_v13_browser.py`. Exactly one public file changed: `assets/style.css`. All content, HTML, media bytes, JavaScript, pricing, persistence, reviews and security files retain their previous sealed hashes.

## CT-04 — High — Catalogue image space was not reserved before decoding

The independent visual critic and the node-attributed diagnostic identified a genuine first-paint regression. On the prior c632 revision, the standard card copy moved down 435 px when the image decoded. This was timing-sensitive and could pass ordinary screenshot-after-load checks. The earlier content/technical verdict did not establish universal layout-shift correctness.

The actual source correction changes the standard catalogue and direct-review images to `aspect-ratio: auto 4/5`, including the mobile catalogue override. The branded-specific selector reserves `auto 1160/940`; its higher specificity preserves that ratio at mobile widths. Existing `width:100%`, `height:auto` and `object-fit:contain` remain. No crop, stretch or media replacement was introduced.

Independent media checks confirm the standard responsive derivatives are exactly 160×200, 480×600 and 800×1000. The canonical image is 1122×1402, with a small rounding difference; `auto` retains the decoded image's true natural proportion rather than forcing a crop. The branded source remains its approved 1160×940 viewBox. All five files retain their previous hashes.

The new regression deliberately holds the lead image request through a real first contentful paint, checks that the image is still undecoded, measures the reserved image/copy geometry, then releases and decodes the image. This directly tests the demonstrated failure rather than mirroring a CSS class assertion.

Four inspected current-revision results — UA/EN home and catalogue at 390 px — each record an actual held request, release after first contentful paint, session-window CLS **0**, maximum image/copy geometry delta **0 px**, and no page/external-request errors. Their separate before-load/loaded screenshots match the JSON checksums. These are focused diagnostic results, not a replacement for the fresh complete 465-test sequence and after matrix.

[Machine receipt with exact hashes](content-technical-4b0-receipt.json) · [reproducible read-only checker](check_cls_revision.py).

## History and remaining gate

The complete prior test/capture evidence is preserved in `history/pre-cls-c632/`. The previous critic verdict and finding history are copied to `critics/history/c63289/`. Their findings remain tied to the c632 revision; CT-04 is an additional high issue whose source/focused closure is verified here.

CT-01/02/03 and messenger source fixes are unchanged. Their current-revision runtime closure and CT-04's final acceptance must be restamped only after the frozen 465-test sequence and required current after/diagnostic evidence complete. This reviewer launched no browser, changed no source and performed no deployment or external send.
