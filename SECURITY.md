# Security boundaries

This repository contains source and approved public media, not customer data or
operational credentials. Report issues privately to the repository owner; do not
post credentials/customer information in public GitHub issues.

- Secrets are never auto-discovered from `.env` or sent to a browser. The env
  example has empty values only; production uses the host secret store.
- Production requires HTTPS, PostgreSQL, private S3, an Argon2 admin hash and a
  session secret. Missing configuration fails closed with 503.
- Public reviews are pending-only. Authentication, CSRF and publication-consent
  checks protect moderation and private media.
- Images are decoded/validated/sanitized. Client filenames are not storage keys.
  Raw/proof objects and unpublished media remain private.
- Orders/reviews commit with idempotency/outbox state before notification. Real
  transports remain disabled during this release.
- Hydrated HTML/forms, receipts, admin/API and private objects are never publicly
  cached. CSP, nosniff, same-origin referrer and noindex boundaries remain.
- Tests use explicitly isolated PostgreSQL schemas and synthetic credentials/data.
  Test constants are not operational credentials.

Run the release guard on the authored tree and committed history. Keep uploads,
databases, browser sessions, logs, raw screenshots and generated output out of Git.
Pattern scans cannot prove absence of every secret; review findings and provenance.

Historical acceptance and synthetic adapter tests do not establish live host/S3,
backup, scheduled retention or production-auth readiness. These remain deployment
acceptance gates.
