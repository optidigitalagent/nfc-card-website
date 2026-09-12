# Operations, migration and recovery

## Database

Use a database dedicated to NFC CARD. Identify the environment and existing data
before migration. Back up existing data into an approved private destination;
never put backups or connection strings in Git.

With `NFC_DATABASE_URL` set externally to the intended database:

```sh
python -c "import os; from server.review_repository import ReviewRepository; ReviewRepository(os.environ['NFC_DATABASE_URL']).migrate()"
python -c "import os; from server.review_repository import ReviewRepository; assert ReviewRepository(os.environ['NFC_DATABASE_URL']).ready()"
```

Order: `001_reviews.sql`, `002_commerce.sql`, `003_retention.sql`. Readiness checks
their checksums. Reapplication is idempotent; do not silently accept changed
applied migrations. Never drop/truncate customer tables. Tests require a disposable
database URL containing `/nfc_v12_test`; randomized synthetic schemas are removed.

## Private storage

Production uses `PrivateS3Storage` with an HTTPS endpoint, dedicated private bucket,
region and credentials from the host secret store. Do not grant anonymous bucket
list/get access or expose raw/proof uploads through a static CDN. Public derivatives
are served only after application checks confirm their review is published.

Acceptance needs a synthetic authenticated put/get/delete, anonymous list/get
denial, and application public/private tests. Remove synthetic objects afterwards.
Local/in-memory adapters do not prove live S3 behavior. Retention is operated via
`python -m server.maintenance`; inspect help and select the correct environment.

## Admin

Login/moderation: `/admin/login`, `/admin/reviews`, with `/en/` equivalents.
Unauthenticated moderation redirects to login. Sessions, CSRF, password throttling
and publication eligibility must remain enforced.

The owner supplies a password of at least 14 characters. The optional helper prompts
without echo and writes an Argon2 hash to a new private file:

```sh
python -m server.set_admin_password --output "$PRIVATE_HASH_FILE"
```

`PRIVATE_HASH_FILE` must be outside the repository/public output. Transfer the hash
directly to `NFC_ADMIN_PASSWORD_HASH` in the host secret store, not chat or logs.
Use a separate high-entropy `NFC_ADMIN_SESSION_SECRET`; rotation invalidates
sessions. No default password or operational credential is shipped.

## Persistence verification

Keep real transports disabled. Use synthetic removable records in an isolated
environment. Verify server prices, persistence before response, lost-response
idempotency, pending-only public reviews, protected moderation and the absence of
public review sections before a real eligible review is published. Never show
synthetic records as customer proof.

## Restore and rollback

GitHub source, host secrets and private data backups are separate recovery inputs.
GitHub must not contain live DB/S3 data or credentials.

Clone the dedicated repository, checkout the verified release commit/tag, verify
manifest, install lockfiles, configure an isolated test DB, run `npm test` and
`npm run build`, then start WSGI. The original SiteAgent run must not be required.

Rollback means deploying a previously verified commit/image with matching build
origin/mode after verifying schema compatibility. Do not reverse migrations or
delete orders/reviews automatically. Data restoration requires a separately reviewed
private backup procedure.

This initial standalone release has no earlier verified standalone production
deployment. Keep the verified handoff while deployment is blocked. Historical v13
rollback instructions refer to omitted v12 archives/tools and are not operational.

Cleanup requires remote main/tag, green CI, clean-clone manifest/install/tests/build,
verified HTTPS, live PostgreSQL/private S3/admin/persistence and independent
acceptance. Until all pass, retain handoff and extraction. Later deletion must use
exact canonical task-created paths, never SiteAgent, its Git metadata, other runs,
iADDS or a parent directory.
