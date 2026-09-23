# NFC CARD repository workflow

This repository is the source of truth for `optidigitalagent/nfc-card-website`.
Preserve the accepted graphite and metallic-silver design, the Review Card
flows, the bilingual URL structure, server-authoritative prices, and the
durable lead boundary.

For every complete owner-requested website fix:

1. start from the actual current `main` without rewriting history;
2. preserve unrelated work and take a recovery snapshot before material edits;
3. run applicable deterministic tests and browser QA;
4. obtain independent acceptance and resolve all critical/high findings;
5. rebuild generated output and refresh the source manifest with approved tools;
6. create one atomic commit and push it to the existing `main` without force;
7. wait for green CI and the existing GitHub Pages deployment;
8. verify the exact deployed commit on the public site;
9. report the commit, workflow run, and live URLs.

This default applies to one coherent, tested fix set, not to each save or an
unfinished intermediate state. When the fix also changes the NFC lead gateway,
release and verify that existing Railway service before the dependent Pages
site. Do not leave a completed NFC CARD fix only in a local checkout.

Public site: `https://optidigitalagent.github.io/nfc-card-website/`.

Do not ask again for an ordinary same-repository, same-URL GitHub Pages
deployment after an owner-requested fix. Stop instead when tests fail, a
critical/high finding remains, a secret or private record could be exposed, a
form could show false success, unrelated work would be overwritten, or the
change requires a new paid resource, billing change, domain change, secret
rotation, or destructive data operation. An explicit owner instruction such as
`local only`, `do not deploy`, or `не публиковать` for the current task overrides
the default release step. Report the exact safety blocker when release stops.

Never create a replacement repository, public URL, Railway project, bot, or
paid resource; never force-push; never send real customer or Telegram test
messages or submit production forms during QA without explicit authorization;
and never regress the existing Review Card or iADDS flows.
