# NFC Instagram Card gateway contract — v20

The existing `optidigitalagent/iadds-website` lead gateway remains the only
browser backend. The release adds product `nfc-instagram-card` to the existing
NFC endpoint without changing the iADDS source, formatter, frontend or secrets.

The browser sends schema version 1, product ID `nfc-instagram-card`, SKU
`NFC-IG-READY`, offer `ready`, quantity 1 or 2, the canonical Instagram profile
URL, optional comment, consent, contact, locale, source page, challenge and
idempotency key. It never sends a price. The server accepts only the four UA/EN
commercial and information routes, canonicalizes the profile URL and computes
UAH 1,500 or UAH 2,600.

Migration `003_instagram_card.sql` preserves migrations 001/002 and existing
rows. It expands the product constraint and adds nullable Instagram identity,
destination, comment and consent columns with a conditional database check.
The transaction writes the lead and outbox before returning a durable receipt.
Telegram reads the durable row after commit; a delivery failure keeps the lead
and schedules the existing bounded retry.

The implementation was released as gateway commit
`1e42351e4250c2fe81e98a8ede265ada06bed524`. Local evidence covers the populated
001/002 upgrade, checksum preservation, concurrent idempotency, rollback between
lead and outbox, restart/retry delivery, server pricing, CORS, PII-free logs and
legacy Review/iADDS behavior. Tests inject the sender and never call Telegram.

Rollback uses an ordinary revert of the gateway commit and a frontend revert or
forward fix. Migration 003 columns and stored records must remain in place; do
not drop them or restore an older database over current data.
