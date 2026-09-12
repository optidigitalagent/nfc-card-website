# Deployment blockers — v1.0.0

Status: **DEPLOYMENT_BLOCKED — no verified live NFC CARD URL**.
Checked 2026-09-12. GitHub migration and CI are independent release gates and
must still complete. Neither a local test server nor a synthetic build origin
is a deployed public preview.

## Existing infrastructure discovery

Read-only inspection of the connected Railway account enumerated 23 projects,
30 environments and 73 services with no listing failures. No intended NFC CARD
service was identified. Three plausible candidates were inspected: the existing
lead gateway belongs to iADDS; the agent and lead-discovery services are unrelated.
The SiteAgent control-plane service is also outside this release's scope.
No service, variables, billing, domain or production data was changed.

## Required to unblock public HTTPS preview

1. Identify an **already provisioned, isolated NFC CARD full-stack service** and
   its project/environment. It must deploy this repository's WSGI application,
   not only `site/`. No such target has been established. Creating paid resources
   is outside the current authorization.
2. Identify its PostgreSQL database, ownership and existing-data status. Configure
   `NFC_DATABASE_URL` securely, back up any existing NFC data, apply migrations
   001–003 and verify persistence across restart. The disposable local test DB
   does not establish this production gate.
3. Identify a private S3-compatible bucket and scoped credentials. Supply the
   `NFC_S3_*` variables externally; prove anonymous listing and raw object access
   fail. No bucket, policy, credential or connectivity proof is available for NFC.
4. Configure a strong admin session secret and Argon2id password hash externally,
   verify login, CSRF, session rotation and authorization on the actual host.
   No production admin account/default password is created in this repository.
5. Establish the service's actual HTTPS origin and use the same
   `NFC_PUBLIC_ORIGIN` at build and runtime, with `NFC_ENV=production` and
   `NFC_PUBLICATION_MODE=PUBLIC_PREVIEW`. Repository website metadata must remain
   unset until that URL is verified. The CI `.example` origin is not a live URL.
6. Deploy from a green, recorded GitHub commit; verify health, localized routes,
   galleries, keyboard/zoom/reduced motion, server pricing, durable synthetic
   orders and pending-only reviews on the actual service. Keep notifications
   disabled and remove synthetic records afterward.

## Separate indexing blockers

The owner has not confirmed final legal identity, registration/address,
privacy/terms, warranty/returns inputs or authorized indexing. These block
`PUBLIC_INDEXABLE`, not the technical implementation of an HTTPS noindex preview.
The current approval record remains false. See `DEPLOYMENT.md` for the
content-bound approval gate; changing one environment flag cannot bypass it.

## Acceptance and cleanup consequence

Live HTTPS, production PostgreSQL, private bucket, deployed admin and live
order/review persistence are **NOT VERIFIED**. Docker is supplied but was not
locally executed because a Docker runtime is unavailable; local and CI tests use
the declared runtimes directly. No deployment or CD target has been configured.

Retain the verified handoff ZIP, extraction, standalone source and clean clone.
Do not delete any of them while these gates remain open. No SiteAgent/iADDS/run
cleanup is authorized by this blocked state. Resume with `RUNBOOK.md` after the
existing target and secure configuration are available; do not request secrets
in chat or reuse another project's database/storage.
