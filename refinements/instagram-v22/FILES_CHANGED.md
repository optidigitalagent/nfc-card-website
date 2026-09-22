# Files changed

Implementation:

- `src/instagram.mjs` — exact P1–P4 source copy, approved media slots and provenance validation.
- `src/instagram-view.mjs` — information-page composition with no stale founder renderer.
- `src/commerce-view.mjs` — five-item gallery and explicit clean-render catalog selection.
- `src/build.mjs` — AVIF/WebP `<picture>`, base-path-safe Product schema images and legacy FAQ anchor.
- `src/instagram.css` — layout-only banner centering, responsive media and functional legacy anchor.
- `src/model.mjs` — canonical global destination/monthly FAQs and shared order step.
- `src/publication-approval.json` — content-bound v22 owner authorization.
- `src/media-manifest.json` — 40 script-managed Instagram media records; 102 prior records frozen.
- `src/media/instagram/` — 40 optimized WebP/AVIF files generated from five approved sources.
- `scripts/update_instagram_media.py` — deterministic, hash-gated v22 media importer.

Tests and documentation:

- `tests/test_instagram_v18.py`, `tests/test_instagram_v20.py`, `tests/test_instagram_browser.py`, `tests/test_v9.py` — updated release expectations and browser/regression gates.
- `tests/test_instagram_v22.py` — exact copy, FAQ/schema, media/provenance, banner and protected-baseline acceptance.
- `README.md` — current media/release state.
- `refinements/instagram-v22/` — baseline, evidence, QA, critic, release and rollback records.
- `SOURCE_MANIFEST.json` — refreshed only after all authored changes are final.

No migrations, gateway code, commerce prices, production infrastructure, Gmail, `nfc_outbound`, Railway resources or CI workflow were changed.
