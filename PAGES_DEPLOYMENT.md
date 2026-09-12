# GitHub Pages publication and form boundary

The v17 deployment target is the existing NFC CARD website at
https://optidigitalagent.github.io/nfc-card-website/.
It replaces legacy Pages publication of repository-root README content with the
accepted site's generated `site/` output. The visual design and public media are
preserved. Deployment is verified only when this URL serves that output over HTTPS.

## Build

Use Node 24 and the existing lockfile:

```sh
npm ci
NFC_ENV=production NFC_DEPLOYMENT_TARGET=github-pages \
NFC_PUBLIC_ORIGIN=https://optidigitalagent.github.io \
NFC_PUBLIC_BASE_PATH=/nfc-card-website \
NFC_PUBLICATION_MODE=PUBLIC_PREVIEW NFC_TELEGRAM_ENABLED=false npm run build
```

Origin remains an origin; the project path has its own explicit variable.
GitHub Pages needs trailing-slash directory routes. The Pages artifact contains
only public output, with `.nojekyll`, and excludes unsupported server endpoints.
All navigation, assets, language switches, metadata and sitemap use the project path.

The existing validation workflow retains every full-stack test and adds Pages
regressions. Its Pages jobs depend on successful validation of the same commit.
They accept only main push/manual events and require the repository variable
`NFC_PAGES_DEPLOY_ENABLED=true`. The default switch is off while publication
acceptance is pending. Configure Pages to use GitHub Actions, not branch-root Jekyll.
The deployment job uses the `github-pages` environment and only contents-read,
pages-write and id-token-write permissions. Official action versions are pinned.
Never bypass validation or move the immutable accepted `v1.0.0` tag.

## Preview and unsupported server functions

The initial mode remains PUBLIC_PREVIEW. Every HTML page includes noindex/nofollow.
Project-path robots.txt is included but GitHub controls the origin-root robots.txt;
per-page meta noindex is the effective preview boundary. Pages cannot configure
WSGI security/cache headers and must not be described as the full-stack runtime.
No public review submission/admin navigation or fake-working server UI is shipped.
The accepted reviews, moderation, PostgreSQL and private S3 source stays in Git.
There is no published testimonial or synthetic customer proof.

## Lead integration is blocked on real infrastructure

Read-only Railway audit, 2026-09-12: the specified `antonov-lead-gateway` project
has one production service, `lead-gateway`, and no PostgreSQL, volume, bucket or
browser-facing bridge. It is built from the protected iADDS repository. Its current
handler sends Telegram synchronously and uses process-memory deduplication; it
has no transaction, durable lead store or notification outbox.

Do not describe that handler's HTTP 200 as durable acceptance. Do not configure a
source secret or create a bridge that can send real Telegram before the durable
backend and per-source disabled-notification boundary are implemented and verified.
Do not reuse a database from another project or create a new database without the
separate authorization required by section 9 of the v17 pack. The iADDS repository,
source secret, bot/chat configuration and existing behavior remain unchanged.

Until those prerequisites pass, `NFC_LEAD_ENDPOINT` stays unset. The Pages form
must visibly state that sending is unavailable, keep user-entered values, and
never emit a success receipt. Publishing this limited preview requires the owner's
explicit decision about the missing lead backend. No completed v17 integration
is claimed merely because the static site is reachable.

After a real bridge is independently verified, its public HTTPS endpoint may be
provided through the non-secret repository variable `NFC_LEAD_ENDPOINT`. The frontend
must send only the approved minimal fields and a stable idempotency key. It must
never include a gateway secret, source assignment, lead ID, timestamp or trusted
price from browser input. Only a server-created lead ID plus confirmed durable-save
response can unlock success. CORS is a browser boundary, not authentication.

The source secret must live only in Railway Variables and be added by the bridge
on the server-to-server request. `NFC_TELEGRAM_ENABLED=false` remains mandatory;
real notifications need a separate owner command after persistence acceptance.

## Recovery

The pre-v17 accepted release is immutable `v1.0.0`, commit
`2d4bf23be16e988ead0a815806a8e7c9d5b09788`. Keep the verified handoff and recovery
bundle while integration is incomplete. Do not delete SiteAgent, iADDS, other runs,
other Railway projects or any application data. Rollback of Pages uses a previously
verified Pages artifact/commit; the original v1.0.0 root-hosted build is not itself
a valid project-path Pages artifact. Never replace the accepted source with README
publication and call that a site rollback.
