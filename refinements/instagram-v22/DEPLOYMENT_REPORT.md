# Deployment report

This release uses one immutable atomic commit. To avoid a second documentation-only
commit, the exact post-commit SHA, push result, CI URL, Pages deployment URL and
released SHA are recorded in the final task report after the release gates complete.

Verification protocol:

1. Push the single commit to the existing `origin/main` without force.
2. Require every job in the repository CI workflow to succeed for that exact SHA.
3. Require the GitHub Pages deployment to report success for the same SHA.
4. Confirm the public UA and EN routes, approved media assets and JSON-LD over
   cache-busted GET/HEAD requests only.
5. Confirm the public content is the content from the released commit before closing
   acceptance.
