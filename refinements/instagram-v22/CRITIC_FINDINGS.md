# Independent critic findings

| Critic | Highest finding | Resolution |
|---|---|---|
| Copy | Medium: stale unused pre-v22 information renderer could reintroduce rejected founder/mechanics copy. | Deleted the legacy renderer, renamed the v22 renderer and removed the unused import. |
| Visual | No medium+ findings. Low: a few locator-only catalog screenshots included fixed-header/focus artifacts. | Production UI unchanged; route/full-page evidence confirms no UI defect. |
| Media | A transient invalid manifest delimiter appeared during CRLF-preserving importer work. | Importer corrected; JSON valid, repeat SHA identical, `git diff --check` clean, 102 baseline + 40 managed records verified. |
| Accessibility | High: legacy `#faq-instagram-subscription` was absolutely positioned at page top. | Returned the alias to document flow; UA/EN browser tests at 320/1440 verify FAQ scroll geometry and one canonical entry. |
| SEO | High: Product schema media URLs initially omitted the GitHub Pages base path. | Images now use `publicURL(..., publication)`; UA/EN PUBLIC artifacts and tests verify all five `/nfc-card-website/assets/...` URLs. Low inherited slash canonical/Pages redirect mismatch recorded as backlog. |
| Regression | Medium: catalog render selection was hidden behind a CSS-class special case; prior media-manifest protection was too broad a skip. | Catalog explicitly requests `IG05`; special case removed. A frozen semantic digest now protects all 102 prior records. |
| Acceptance | No implementation critical/high/meaningful medium findings; release gates remained pending by design. | Closed local acceptance after home-at-393 and touch/swipe coverage; final suite recorded `745 passed`. |

All critical/high and meaningful medium findings are resolved before release. Seven independent specialist critics and the final independent acceptance critic completed their reviews.
