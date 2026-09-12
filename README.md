# NFC CARD by Antonov Digital

Source repository: https://github.com/optidigitalagent/nfc-card-website

Website: [NFC CARD](https://optidigitalagent.github.io/nfc-card-website/).

The static frontend is published by GitHub Pages. Public enquiries use the existing
Antonov lead gateway, its private PostgreSQL 17 and the separate `nfc_card` schema.
The gateway persists a lead and outbox together before attempting Telegram.
See [PUBLIC launch and rollback](PUBLIC_LAUNCH.md) for the active architecture;
older full-stack release documents describe the retained alternative runtime.
No additional Railway service, bucket or worker is needed.

Release documentation: [deployment/publication](DEPLOYMENT.md),
[operations and recovery](RUNBOOK.md), [security](SECURITY.md),
[release evidence](docs/release/v1.0.0/RELEASE_REPORT.md),
[source provenance](docs/release/v1.0.0/SOURCE_PROVENANCE.md).

Run `python scripts/verify_manifest.py` and `python scripts/release_guard.py`
before release. The original handoff manifest is retained under
`docs/release/v1.0.0/source-handoff-manifest.json`; the root manifest covers the
current release. Historical rollback reports reference omitted Windows/v12
archives; use the current RUNBOOK instead.

This contains the existing bilingual NFC CARD application, Python API, PostgreSQL migrations, private S3 adapter, order/review/admin implementation and approved public product/founder media. Public output and private admin templates are regenerated from source.

Historical v13 evidence records ACCEPT_LOCAL_CANDIDATE with 465 passing tests. It explicitly records userAccepted=false and publicationAuthorized=false. No owner or production acceptance is implied. Historical report paths are sanitized; historical hashes refer to the original run and omitted QA artifacts, not this handoff. SOURCE_MANIFEST.json is authoritative for this package.

## Install

Use Node 24, Python 3.14 and PostgreSQL 17. Create/activate a fresh Python virtual environment (`python -m venv .venv`; Windows: `.venv/Scripts/Activate.ps1`; POSIX: `. .venv/bin/activate`).

```sh
npm ci
python -m pip install --require-hashes -r requirements-test.lock
python -m playwright install chromium
```

For runtime-only installation use requirements.lock instead. Python lockfiles include transitive versions and artifact SHA-256 hashes. npm has no external dependencies; its lockfile was created for this handoff.

## Test and build

Provide NFC_TEST_DATABASE_URL through the environment for a disposable PostgreSQL database named nfc_v12_test. Tests create/drop randomized schemas and synthetic fixtures. Never point tests at production. Browser evidence is written locally; optionally set NFC_BROWSER_EVIDENCE and NFC_V13_BROWSER_EVIDENCE outside the source directory.

```sh
npm test
npm run build
```

The complete suite runs in separate processes to bound browser memory. Chromium is required. No test is deliberately omitted. The two SiteAgent orchestration utilities (repository inspector and acceptance sealer) are excluded; they are not pytest tests and require the internal agent installation.

## Configure and start

.env.example contains empty values only and is not loaded automatically. REQUIRED_ENVIRONMENT_VARIABLES.md lists runtime and test variable names only; configure applicable values externally. Production requires NFC_ENV, NFC_PUBLIC_ORIGIN (HTTPS), NFC_DATABASE_URL, NFC_ADMIN_SESSION_SECRET, NFC_ADMIN_PASSWORD_HASH and the NFC_S3_* settings. Storage must be private. For local mode enable NFC_LOCAL_STORAGE_ENABLED and provide NFC_LOCAL_STORAGE_PATH outside site/. No real messaging transport is enabled.

Apply migrations to your explicitly selected database:

```sh
python -c "import os; from server.review_repository import ReviewRepository; ReviewRepository(os.environ['NFC_DATABASE_URL']).migrate()"
python -m server.set_admin_password --help
npm start
```

npm start is a loopback WSGI development server. Production container configuration is supplied as Dockerfile; it builds the same frontend and starts Gunicorn. Alternatively on Linux: `gunicorn --bind 0.0.0.0:8000 server.wsgi:application`. These are the retained full-stack runtime instructions, not the active Pages gateway deployment. PUBLIC_PREVIEW preserves noindex. PUBLIC_INDEXABLE requires final legal content and explicit owner approval bound to its content hash; an environment flag alone cannot enable indexing.

## Packaging changes and exclusions

The accepted product, visual system, public assets and core commerce/review/auth/migration implementation are retained. Release changes add explicit publication/origin/cache boundaries, health reporting, portability guards, CI and focused regression tests. The original handoff manifest is retained separately; the root release manifest records the final authored tree. Generated server/templates and site are omitted. Test-only synthetic credentials and contacts are fixtures, not operational secrets or customer records. Public business contacts and authorized founder biography/media are intentional website content.

Excluded: real .env/secrets/credentials, database and storage connection values, production/customer submissions and unpublished reviews, private uploads, sessions/cookies, node_modules, generated build output/caches, local databases/logs/browser profiles, SiteAgent checkpoints/internal orchestration, recovery archives, original private founder uploads, and raw QA screenshots. RECOVERY_SNAPSHOT.json is retained solely as a hash fixture needed by unchanged regression tests; it contains no recovered payloads.

The release manifest covers every authored repository file except itself. Verification independently walks the filesystem and tolerates only the documented generated roots, so it also runs after install, tests and build. It does not trust .gitignore. The original ZIP digest authenticates the original manifest; the Git release commit seals the current manifest.
