# Rollback — Instagram corrective release v20

1. Identify the last green NFC CARD commit immediately before the v20 release.
2. Revert the v20 NFC CARD commit with an ordinary `git revert`; do not reset,
   rewrite history or force-push.
3. Push the revert to the existing `main`, wait for the existing validation and
   GitHub Pages workflow, then verify the public site.
4. If the additive lead-gateway release is involved, first disable only the
   Instagram entry point in the frontend or revert the gateway commit with an
   ordinary revert. Preserve PostgreSQL records, the `nfc_card` schema, outbox
   rows and all iADDS configuration.
5. Never drop migration 003 columns or restore an older production database
   over current data. Prefer a forward fix after preserving evidence.

The rollback must not create a new repository, Pages URL, Railway project,
database, volume, worker, bucket or bot.
