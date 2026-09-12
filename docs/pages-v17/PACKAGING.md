# Pages v17 source changes

The accepted v1.0.0 tag and sealed handoff manifest remain unchanged. The v17
source adds an explicit Pages target and project base path while retaining the
root-hosted full-stack default, backend source, media and accepted visual system.
The generated Pages artifact omits server-only routes, scripts and API fallbacks.
A missing verified lead endpoint produces a localized unavailable state.

The release guard still scans all authored files, staged blobs and reachable
history. Four exact-line SHA-256 exemptions were reviewed for the v17 additions:

- `src/pages.mjs`: the Fetch API credentials field set to omit, which prevents
  browser credentials from being sent; it is not a credential value.
- `tests/test_pages_v17.py`: one synthetic sentinel used to assert that server
  secret environment variables are excluded from generated Pages output.
- The same test file: two lines with deliberately invalid credential-bearing
  endpoint URLs. One tests validation, one tests build rejection. No transport
  reaches those URLs.

These exemptions bind path, rule and whole stripped-line hash. Editing a line
invalidates its exemption. No blanket test-directory or credential exemption was
added. Environment examples remain blank; the public endpoint is a URL, never a
source secret. Live Railway variables and iADDS files are outside this release.

Fresh test/QA and independent acceptance evidence is recorded separately; these
source notes are not proof of live deployment or gateway persistence.
