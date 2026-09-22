# Test report

Pre-change focused baseline: `162 passed, 6 skipped`.

Implementation checks completed:

- Exact P1–P4/media/schema tests: pass.
- Nine-width UA/EN Pages matrix: `9 passed`.
- Legacy FAQ anchor UA/EN × 320/1440: `4 passed`.
- Production GitHub Pages build using the existing configured gateway URL: pass, with no network POST.
- First full suite: `735 passed`, one allowlist failure caused by the new v22 source class; the allowlist was narrowed to exact v22 `requirements_source` + `managed_by`, and its retry passed.
- Actual 200% Chromium zoom, reduced motion, keyboard/focus, no-JS and protected product/browser regressions ran in the full suite.
- Post-critic targeted matrix: `11 passed`, including UA/EN home at 393 px, the corrected legacy anchor and Instagram gallery touch/swipe.
- Final default-build full suite against isolated PostgreSQL: `745 passed in 325.23s`, with zero failures and zero skips.

The final full suite was run after every critic-driven source change and before the source-manifest refresh.
