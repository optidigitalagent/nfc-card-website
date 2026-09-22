# Resolved conflicts
|Conflict|Resolution|
|---|---|
|Attached outbound engine vs named Instagram handoff|Found actual handoff with exact expected SHA; excluded outbound package.|
|Old two-variant model vs new product|Keep Review variants standard/branded; introduce productSchemaVersion1 products/selections and distinct ready offer. `instagram` is a selection key, not a Review variant.|
|Historical starter/SKUs/v1.0.0|Current main only; no Counter Stand/Team Kit/Multi-Location reintroduction.|
|Short handoff tap claim vs actual system notification|Retain approved short proposition; explicitly show tap→notification→user clicks→profile in product/info and step copy.|
|Partial English handoff|Translate UA-only blocks faithfully; no new claims.|
|Global4FAQ vs product9FAQ|Four added globally; nine product-specific questions and matching JSON-LD, no duplication.|
|Shared payment/delivery vs handoff|Current verified common terms retained; no new timeframe or warranty duration.|
|Optional video vs no poster/text alternative|Feature flag false, founder text fallback. No video/source/contact sheet in output.|
|Placeholders vs genuine product evidence|Neutral labelled HTML slots. Never use Review Card photography as Instagram evidence. Future asset mapping requires approved product-specific provenance.|
|Legacy PUBLIC content approval vs new local candidate|Do not update approval file. PUBLIC build remains blocked for this source until separate owner release approval. Disposable test copies use synthetic authorization for mocked PUBLIC QA only.|
|Local server extension vs separate production gateway|Local persistence/Pages wire contract implemented. Real gateway untouched and not proven compatible with Instagram yet; release prerequisite below.|
