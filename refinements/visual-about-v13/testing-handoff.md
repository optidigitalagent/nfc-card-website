# v13 test implementation and final verification

Final local run: **465 passed**, no failures or skipped tests. All stages ran sequentially without rebuilding or changing production source from 2026-09-11 12:40:45 to 12:53:54 UTC.

| Stage | Result | Evidence |
| --- | --- | --- |
| New v13 browser behavior | 15 passed, 157.22 s | `v13-browser-final.txt` |
| Existing browser width matrix | 8 passed; 18 bilingual routes per width | `legacy-browser-width-{320,360,390,430,768,1024,1280,1440}.txt` |
| Existing browser flows and diagnostics | 11 passed, 157.41 s | `legacy-browser-flows.txt` |
| Server, persistence, security, static and media tests | 431 passed, 174.96 s | `nonbrowser-final.txt` |

`final-test-sequence.json` records every stage, exit code, exact summary and timing. `final-test-start.json` and `final-test-end.json` contain file-level hashes. The source fingerprint includes a stated selection of source, server, test and runner files; its selection and ordering can differ from the root's broader candidate seal.

- Public SHA-256 before and after: `4b0ccbc08aecda587aae9600e79352a1829c6de9758de87caffcdaf0821e5414`.
- Test-inclusive source SHA-256 before and after: `e1fd7a116c99fa2030fc3b6cebe92aebbf3b69a6926c8f7b3621aaf08da10c8b`.

`final-test-evidence-audit.json` confirms current-revision consistency across all 144 route/width contexts and 26 targeted contexts, zero recorded problems in 36 console/network/name diagnostic contexts, seven routes at actual browser zoom factor 2, and 362 referenced native screenshots. About UA/EN at 390 and 1440 px include their actual final bottom viewport. The disabled messenger screenshot is captured during a real isolated pending retry flow. Targeted screenshot hashes were checked against their reports.

Test changes were limited to `tests/test_site.py`, `tests/test_v9.py`, `tests/test_v12_browser.py`, new `tests/test_v13.py`, new `tests/test_v13_browser.py` and `Run-Checks.ps1`. Intentional contract updates cover 26 localized routes, homepage final CTA replacing its inline form, one stable lightbox opener and responsive media allowlisting. Pricing, redirect, review, authentication and persistence assertions remain enforced.

New behavior checks cover all gallery thumbnails, original-size lightbox media, keyboard focus containment/restoration, actual touch swipe and zoomed image panning, native messenger selection/error clearing and pending disabling, compact quote/footer geometry, CTA analytics semantics, pinned About content/media, About navigation and responsive image selection, and About console/CSP errors. The exact seven approved founder photos and their 28 derivatives are verified against pinned source data; original product media bytes and protected backend bytes are checked against the recovery snapshot.

Four new delayed-media cases cover UA/EN home and catalog at 390 px. Each holds the actual local product-image request through first contentful paint, verifies an undecoded image has its full 435 px space reserved, releases the request and verifies identical final image/copy rectangles. All four final cases recorded session CLS 0 and maximum rectangle change 0. Native before-load screenshots deliberately document the delayed request state and are labeled accordingly. The current 144-context initial-load matrix's maximum observed eligible-shift sum is 0.0442106; EN home/catalog at 390 both record 0. These are bounded local observations, not a blanket field CLS claim.

Earlier failed attempts are retained in initial and pretypography logs. They document both corrected harness assumptions and production findings subsequently fixed by the root implementer: the About anchor collision, About inline-style CSP violation, CTA analytics semantics, selected messenger error feedback, and catalog media without intrinsic space reservation. The prior 461-test run and its c632-revision captures were archived under `history/pre-cls-c632`; they remain historical functional evidence. `layout-shift-diagnosis.md` and `layout-shift-diagnostic-390.json` attribute the earlier 0.271658 shift to a 435 px image insertion and prove the ratio fix without source changes. Final acceptance relies only on the current 465-test run above.

All browser and data checks used local ephemeral servers and isolated PostgreSQL test schemas. No deployment, Git push, production resource provisioning or real notification was performed. These checks do not constitute full WCAG certification or field performance measurements. Root remains responsible for final focused before/after capture, independent critic closure, acceptance report and rollback instructions.
