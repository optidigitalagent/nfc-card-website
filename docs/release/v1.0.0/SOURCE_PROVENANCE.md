# Accepted source provenance

Source: `NFC_CARD_ACCEPTED_SOURCE_HANDOFF.zip` inside the owner's v16 release pack.

| Check | Verified value |
|---|---|
| Source archive SHA-256 | `9cf61bc26214321d296adeae4c63eb21a5b624bfa9f8849797bcb51c66ff5de0` |
| Archive bytes | 16,934,796 |
| ZIP entries | 200 |
| Uncompressed bytes | 18,079,171 |
| Initial manifest | 199 hashed files plus manifest; every hash passed |
| Original manifest SHA-256 | `7d6db6f7b5c6d911cbdae2a8eed4a94568fc300ffd1f699bdf49b1b92427bf68` |
| v16 outer pack SHA-256 | `cb2f360d709220708f25fb5a3c2f292cc2397f84dbce8131fb35f92e2a50a673` |

Before extraction, duplicate names, traversal, absolute/backslash paths and
symlinks were rejected. The required frontend, WSGI backend, three PostgreSQL
migrations, private storage adapter, tests, lockfiles, public assets and historical
v13 evidence were present. This is the actual implementation, not instructions
reconstructed into a new site.

The original manifest is retained byte-for-byte in
`source-handoff-manifest.json`. Root `SOURCE_MANIFEST.json` records the release
tree, including deliberate release changes. These two manifests serve different
purposes. The original ZIP remains preserved outside the Git repository.

The accepted extraction was built only for baseline comparison, adding generated
`site/` and `server/templates/`; all original 199 authored hashes stayed intact.
Those generated extras are not original handoff files or staged source. They do
not invalidate the separately verified sealed ZIP.

## Public media

The handoff's `src/media-manifest.json` lists 59 permitted public derivatives
(57 public and two temporary public); all listed hashes were independently
verified. Product/founder provenance, About source mapping and the approved iADDS
commit `013bd2d904d5be143a0e203d0005c29f25db729f` are documented in the retained
v13 materials.
No iADDS code or repository was modified. Public media is intentionally supplied
business content, not private customer review uploads. Only the renderer's
allowlisted media reaches the website build; held comparison material is not
enabled merely by migrating the source repository.

## Release scope

The accepted visual/product experience and core commerce/review/authentication/
migration behavior remain the source of truth. Changes are limited to explicit
publication/origin/caching gates, health reporting, fresh regression coverage,
release guards, CI and release/operations documentation. Fresh browser tests also
exposed an accepted gallery close/reopen race; synchronous, idempotent body-lock
restoration corrects it without changing the visual system or weakening tests. The UA/EN privacy draft
now correctly describes private application-server storage rather than storage
on the reader's computer; it remains a draft without indexing approval. Historical acceptance
documents remain historical; they are not substituted for fresh release checks.

Neither the outer instructions ZIP nor SiteAgent orchestration, private stores,
operational credentials, generated outputs, raw screenshot matrix or unrelated
project history belongs in this repository.
