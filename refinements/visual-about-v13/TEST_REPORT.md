# Test results

465 unique current pytest cases PASS across sequential memory-safe groups. No test skip is counted as a pass. Test schemas are isolated in `nfc_v12_test`; external requests are blocked and notification adapters are in test/local mode.

| Group | PASS | Log |
|---|---:|---|
| v13-browser-final | 15 | [v13-browser-final.txt](v13-browser-final.txt) |
| legacy-browser-width-320 | 1 | [legacy-browser-width-320.txt](legacy-browser-width-320.txt) |
| legacy-browser-width-360 | 1 | [legacy-browser-width-360.txt](legacy-browser-width-360.txt) |
| legacy-browser-width-390 | 1 | [legacy-browser-width-390.txt](legacy-browser-width-390.txt) |
| legacy-browser-width-430 | 1 | [legacy-browser-width-430.txt](legacy-browser-width-430.txt) |
| legacy-browser-width-768 | 1 | [legacy-browser-width-768.txt](legacy-browser-width-768.txt) |
| legacy-browser-width-1024 | 1 | [legacy-browser-width-1024.txt](legacy-browser-width-1024.txt) |
| legacy-browser-width-1280 | 1 | [legacy-browser-width-1280.txt](legacy-browser-width-1280.txt) |
| legacy-browser-width-1440 | 1 | [legacy-browser-width-1440.txt](legacy-browser-width-1440.txt) |
| legacy-browser-flows | 11 | [legacy-browser-flows.txt](legacy-browser-flows.txt) |
| nonbrowser-final | 431 | [nonbrowser-final.txt](nonbrowser-final.txt) |

[Machine result manifest](test-results.json) binds logs and the candidate revision. Existing route-count/media assertions were updated only for the two authorized About routes, the removal of the homepage inline form and the appended exact media allowlist. Protected backend behavior assertions remain intact. Current source/tests are bound in `candidate-seal.json` and the final source seal.

Retained initial failures and fixes: five static image tests initially treated width labels as longest-edge labels; corrected contract checks passed. A missing task TEMP caused a pre-browser setup failure. Chromium serialized equivalent touch-action values differently from the first harness assertion. A strict navigation glob initially rejected accepted source/UTM query parameters. These harness issues were fixed without weakening behavioral checks. The full matrix then found the genuine About/home-story ID collision; the About ID was made unique, browser-bootstrap assertions added, and all affected verification repeated. The console diagnostic also found inline About aspect-ratio styles blocked by strict CSP; the ratios were moved into the external stylesheet without relaxing CSP, and the complete diagnostic suite was repeated. Initial logs remain available and are superseded by the passing logs above.

Historical `tests/browser_qa.py` and `tests/seal_acceptance.py` are prior-generation standalone acceptance scripts, not current pytest tests; no claim is made that they were run against v13. Current pytest files and new targeted cases were all collected and executed.

The independent performance review then found a genuine predecode product-image shift despite the prior 461 passing tests. Per-asset ratio reservation fixed it without changing decoded layout. Four added UA/EN home/catalog browser cases deliberately hold image responses until after first paint and verify reserved space, stable coordinates and session-window CLS. The entire expanded suite above was rerun on the corrected revision. The superseded passing run and its images are retained in `history/pre-cls-c632`; `layout-shift-diagnosis.md` preserves causality. An initial targeted harness attempt used a CSP-blocked string-evaluation helper; direct browser polling replaced it without changing CSP.
