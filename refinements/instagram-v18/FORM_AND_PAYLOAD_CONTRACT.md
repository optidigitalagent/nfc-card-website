# Form and payload contract

> Historical v18 design note. The deployed additive PostgreSQL/outbox contract is
> documented in `refinements/instagram-v20/GATEWAY_CONTRACT.md`; its migration 003
> supersedes the v18 assumption that no gateway migration would be needed.

The HTML selection key `instagram` resolves through `commerce.selections` to product_id `nfc-instagram-card`, offer `ready`, SKU `NFC-IG-READY`. It is not added to `commerce.variants` (Review only). `productSchemaVersion:1` is additive to the existing lead `contractVersion:6`.

Local/native JSON includes the v6 name/phone/messenger/quantity/comment/consent/locale/source/attribution/requestToken plus productSchemaVersion, product_id, offer and instagramUrl for Instagram only. Server derives SKU and fixed1500/2600 quote. Old Review intents remain byte-equivalent after normalization; stale Instagram identity/destination on Review is rejected. No migrations are needed: additive fields reside in existing JSONB payload; lead/outbox remain one transaction.

Validation: exact HTTPS instagram.com or www.instagram.com single profile segment, ASCII letters/digits/underscore/dot,1–30characters. Reject auth, ports, queries/fragments, encoded characters, nested content paths, reserved routes, control/Unicode confusables, leading/trailing/double dots. Canonicalize hostname and username casing. Never fetch a supplied URL. No @handle auto-expansion.

Pages wire contract: existing language/customerName/contact/sourcePage/selection/UTM envelope, `product:'nfc-instagram-card'`, numeric quantity1/2, productSchemaVersion1, product_id, SKU, ready offer, canonical instagramUrl, optional bounded comment and consent=true. No client price is sent. Transport keeps fresh challenge + stable idempotency key/body + 202/ok/NFC_CARD/durableSaved/UUID receipt requirements. Retry retains values; no false success. In Pages mode browser storage contains only opaque attempt IDs/state, never Instagram URL or comment. Analytics receives only allowlisted product_id/selection/quantity/channel/route.

Generic form keeps common contact fields, clears/disables Instagram URL when leaving the product and restores Review quantity choices. Selection changes announced. Fullstack native UA/EN forms hydrate canonical prices and required identity/URL; native schema string is strictly converted. Generic no-JS form links to dedicated Instagram form.

## Historical v18 release prerequisite — completed by v20
The existing production bridge is in a separate repository. Before release, its server must accept exactly this versioned Instagram contract, price1500/2600 server-side, permit these source pages in challenge/CORS checks, store destination/comment/consent durably with outbox in a transaction and return the existing receipt. Local Python tests and mocked Pages transport do not prove that remote deployment. No gateway or Railway edits were authorized/performed in this task. Reuse existing infrastructure; no new resources. Also obtain content-bound owner release approval after real product media decision. Keep current PUBLIC approval unchanged until then.

## Inherited full-stack browser retention
The full-stack target retains its existing recovery behavior: sessionStorage stores contact drafts (name/phone/messenger/comment); IndexedDB stores pending payloads before a request, including Instagram URL for the new product. Confirmed receipt or field-validation rejection deletes the pending entry. Network uncertainty retains it for stable-key retry. There is no claimed automatic expiry. This code is removed from the Pages output; the Pages-only opaque-state guarantee must not be generalized to full-stack mode. Personal fields are excluded from analytics in both modes.
