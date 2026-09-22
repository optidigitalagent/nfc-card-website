# v22 baseline

- Repository: `optidigitalagent/nfc-card-website`
- Remote: `https://github.com/optidigitalagent/nfc-card-website.git`
- Branch: `main`
- Baseline local/origin SHA: `d00fe629ffbd0d4c103af6e65fdcc8886ae44887`
- Recovery checkpoint: local tag `recovery/instagram-v22-start-20260922`
- Starting status: clean before evidence capture
- Baseline build: pass
- Focused baseline tests: `162 passed, 6 skipped`
- The six skips were PostgreSQL-gated tests; the final suite uses an isolated PostgreSQL 17 cluster.

Read-only live baseline screenshots (no POST requests):

- `baseline-screenshots/ua-product-390.png`
- `baseline-screenshots/en-product-1440.png`
- `baseline-screenshots/ua-info-1440.png`
- `baseline-screenshots/en-info-390.png`

The baseline showed the six product-gallery placeholders and top-aligned text in the silver banner. No user work was deleted or overwritten.
