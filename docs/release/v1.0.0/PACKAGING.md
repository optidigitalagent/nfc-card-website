# Release source packaging

The accepted input is `NFC_CARD_ACCEPTED_SOURCE_HANDOFF.zip`, archive SHA-256
`9cf61bc26214321d296adeae4c63eb21a5b624bfa9f8849797bcb51c66ff5de0`.
The release coordinator verified the archive before making this working copy.
The original manifest is preserved byte for byte at
`docs/release/v1.0.0/source-handoff-manifest.json`: 35,204 bytes, 199 hashed
files plus the original manifest, SHA-256
`7d6db6f7b5c6d911cbdae2a8eed4a94568fc300ffd1f699bdf49b1b92427bf68`.
Do not replace that historical record when preparing a release.

## Source inventory and refresh

`scripts/verify_manifest.py` walks the filesystem without consulting Git ignore
rules. It checks exact path membership, SHA-256 and byte sizes; rejects missing,
changed or unexpected authored files, symlinks at authored/generated boundaries,
special files, unsafe paths, duplicate entries/JSON keys and case collisions.
It works after dependency installation, a local virtual environment, build and
tests. `src/`, docs, tests, migration SQL, static reports and accepted refinement
evidence remain covered. Root-level `site/` is generated; `src/site/` is not.
An ignored `.env`, log or other unexpected authored file still fails inventory.
The implementation uses explicit exceptions rather than Python `assert`, so
optimized Python does not disable the gate.

Only these exact directory roots are excluded:

```text
.git/
.pytest_cache/
.venv/
__pycache__/
node_modules/
scripts/__pycache__/
server/__pycache__/
server/templates/
site/
tests/__pycache__/
work/
```

There is no global `**/__pycache__`, extension, secret-file or Git-ignore
exemption in the manifest walker. Filesystem dependency/build/test output below
the listed roots is outside the source seal; the walker does not follow its
internal links (package-manager/virtualenv links are normal). A symlink used as
one of the excluded roots is rejected. The Git guard rejects any generated file
that enters the index or history. Keep credentials, production data and private
uploads outside the release repository, including these generated directories.

`.gitattributes` disables line-ending conversion for all paths. This preserves
accepted CRLF source and the original manifest across Git checkouts. Changing
this policy requires regenerating and revalidating hashes; a newline-only drift
must not be mistaken for an unchanged handoff.

Only the release coordinator refreshes the root `SOURCE_MANIFEST.json`, after
all concurrent source and documentation edits have stopped:

```sh
python -B scripts/release_guard.py
python -B scripts/update_manifest.py
python -B scripts/verify_manifest.py
```

The updater requires the untouched original manifest, runs the guard first,
sorts paths deterministically, records archive provenance and the exact exclusion
policy, hashes all release source/docs/tests, checks for concurrent changes, and
verifies its output. It never silently enrolls a detected secret/private file.
It does not make Git commits. The root manifest deliberately does not hash
itself; the eventual Git commit/release archive binds its bytes. A coordinated
edit to both a source file and its manifest requires Git/release review to detect.

## Secret and private-data guard

```sh
python -B scripts/release_guard.py
# Mandatory after the first commit and from every clean clone:
python -B scripts/release_guard.py --history
```

The default guard checks every authored filesystem file, including dotfiles and
ignored files, and the actual Git index blobs when a release repository exists.
It does not trust a clean `git status`. History mode requires a non-shallow
repository with a commit. It scans every reachable commit tree across refs and
HEAD, including subsequently deleted files, plus commit and annotated tag
messages. It rejects staged/historical symlinks, submodules, private files and
generated artifacts. An old staged blob is scanned even when its working copy
has already been cleaned. This is read-only: no Git initialization, staging,
committing, history rewriting, pushing or deployment occurs.

Credential checks cover provider tokens, AWS access IDs, private keys, Telegram
tokens, JWTs, authenticated URLs, literal credential assignments, private user
paths and selected private-record fields. Token scanning includes binary files
and UTF-16 text; a binary suffix is not an exemption. Path checks reject private
environment files, private stores, database dumps, logs, browser profiles,
cookies, screenshots, recovery archives and orchestration internals. The only
environment example allowed is the root `.env.example`, whose entries must have
unique names and strictly empty values. Empty quotes or trailing value/comments
are not accepted as empty values; standalone comment lines are allowed.

Diagnostics contain only a rule name, source line number, revision and a
SHA-256-derived file identifier. Neither matching values, snippets, filenames
that could contain credentials, raw diffs nor Git error output are printed.
For local investigation, hash a suspected relative filename with SHA-256 and
compare the first 12 hexadecimal characters to `file-id`. Do not paste secrets
into reports. A failed filesystem/history audit exits nonzero; unavailable or
shallow history is a failure, not a clean scan.

The reviewed exemptions are exact `(path, rule, full stripped-line SHA-256)`
entries in `SAFE_FIXTURES`. They cover:

- Two existing URL-validation fixtures in `tests/test_leads.py` that reject
  authenticated URLs.
- Five existing lines in `tests/test_v12_reviews.py`: synthetic session/admin
  credentials, a rejected Instagram URL, a stubbed S3 client and a wrong-password
  rejection. Their credentials are used only by isolated fixtures.
- One `getpass` confirmation prompt in `server/set_admin_password.py` and the
  browser Fetch same-origin credentials option in `src/admin-reviews.js`.
  These are reviewed code false positives, not passwords.
- Two CI lines for the exact disposable PostgreSQL service and its loopback
  `nfc_v12_test` URL. CI has no production credentials.

There is no tests-directory or password-keyword bypass. Copying an exempt line
to another path or changing/appending to it invalidates the exemption. Regression
tests bind every exemption to its existing source line. Any new exemption needs
specific review and a documented reason. Pattern checks cannot prove the absence
of all possible secrets or personal data; independent privacy/provenance review
remains a release gate.

## Fresh validation and evidence

Use Node 24, Python 3.14, PostgreSQL 17 and Playwright Chromium. Create a fresh
virtual environment, preferably outside this repository. Set
`NFC_TEST_DATABASE_URL` to an explicitly disposable database whose path matches
`/nfc_v12_test(?:_[a-z0-9]+)?`, such as `nfc_v12_test` or `nfc_v12_test_clone`;
never production. The runner rejects other paths and query-string database/service
overrides. Synthetic test schemas are created
and removed by the existing tests; live notifications are disabled.

```sh
npm ci
python -m pip install --require-hashes -r requirements-test.lock
python -m pip check
python -m playwright install chromium
python -B scripts/verify_manifest.py
python -B scripts/release_guard.py
npm test
npm run build
python -B scripts/verify_manifest.py
python -B scripts/release_guard.py
```

`npm test` still runs the complete unit/integration discovery (including release
and publication tests), all eight browser widths, v12 browser flows and v13
browser tests sequentially. No group from the accepted 465-check suite is
omitted. The runner defaults fresh screenshots and reports to `work/qa/v12` and
`work/qa/v13`, preserving accepted refinement evidence. Explicit evidence-path
overrides remain available to the release coordinator. Each group writes a fresh
JUnit report under `work/test-run`; the compact `summary.json` records actual
counts, elapsed time and exit status. Missing/empty reports, test failures and
skipped checks fail the run; `complete` is set only after every group passes.

CI repeats the clean checkout/installed/post-test manifest gates, hashed Python
installation, Chromium installation with Linux dependencies, complete `npm test`,
an HTTPS public-preview build with the reserved synthetic origin
`https://nfc-card.example`, and current/index/history guards. It uses a disposable
PostgreSQL 17 service and read-only repository permissions. It neither deploys
nor enables indexing. Failure uploads contain one bounded JSON file with step
outcomes only. Raw screenshots, profiles, JUnit data and logs are not uploaded.

Action refs were resolved read-only from these upstream repositories using
`git ls-remote` on 2026-09-12; CI pins the resulting full commits:

| Action / verified ref | Pinned commit |
| --- | --- |
| [actions/checkout](https://github.com/actions/checkout), `refs/tags/v5` | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` |
| [actions/setup-node](https://github.com/actions/setup-node), `refs/tags/v6` | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| [actions/setup-python](https://github.com/actions/setup-python), `refs/tags/v6` | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| [actions/upload-artifact](https://github.com/actions/upload-artifact), `refs/tags/v6` | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` |

These are provenance records for the chosen revisions, not a claim that mutable
major tags will keep resolving to them. Refresh action pins only after verifying
new upstream refs and reviewing the change.

Remote CI, actual post-commit history, clean-clone recovery and deployment require
their own recorded evidence. Local test results do not imply those gates passed.
