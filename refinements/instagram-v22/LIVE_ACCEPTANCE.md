# Live acceptance

Final acceptance is executed only after GitHub Pages succeeds for the immutable
release commit. Exact URLs, released SHA and results are recorded in the final task
report so the repository remains clean after its single atomic commit.

The acceptance protocol uses GET/HEAD-only checks against
`https://optidigitalagent.github.io/nfc-card-website/` and the UA/EN Instagram routes:

- verify successful route and approved AVIF/WebP asset responses;
- verify exact P1-P4 UA/EN copy and absence of review-only promo assets;
- verify Product/FAQ structured data and repository base-path image URLs;
- verify the silver banner's computed layout alignment at representative viewports;
- verify the deployed GitHub Pages SHA matches the release commit.

No production form submission, real Telegram notification, Gmail access or
`nfc_outbound` access is permitted during live acceptance.
