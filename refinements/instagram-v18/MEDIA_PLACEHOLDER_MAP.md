# Instagram media slots
|Slot|Purpose|Current status|
|---|---|---|
|IG01|Catalog/product front|Text-only placeholder|
|IG02|Card in hand|Text-only placeholder|
|IG03|Smartphone tap|Text-only placeholder|
|IG04|Exact profile after tap|Text-only placeholder|
|IG05|Back/mounting|Text-only placeholder|
|IG06|Dimensions/thickness|Text-only placeholder|
|IG07|Informational reception scene|Text-only placeholder|
|IG08|Informational smartphone profile|Text-only placeholder|

All slots live in `src/instagram.mjs`. Gallery/copy/layout do not need rebuilding to insert approved media: set a slot's asset/status and add its hashed entry to the existing media manifest. Resolver requires public status, product_id=nfc-instagram-card, user_provided_business_asset provenance and real_product_photo claim role. Other product/private entries fall back to labelled placeholders. No new product art, stock product proof, synthetic brand or fake customer interface.
Founder video remains disabled. The supplied source MOV, internal contact sheet and web MP4 are not public assets; no approved poster and text alternative are available. Approved founder text is present. Current Review Card13-item gallery and branded3-item gallery are unchanged.
