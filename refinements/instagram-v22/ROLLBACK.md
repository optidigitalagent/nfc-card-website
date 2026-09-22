# Rollback

Baseline: `d00fe629ffbd0d4c103af6e65fdcc8886ae44887`.

Recovery checkpoint: local tag `recovery/instagram-v22-start-20260922`.

If a task-related live defect cannot be corrected immediately, create a new forward commit that restores the affected v22 files to the baseline behavior and push normally to `main`. Do not force-push, rewrite `main`, delete current Review Card data or change the gateway/Railway resources. Confirm green CI, GitHub Pages completion and the public SHA/content after the forward rollback.
