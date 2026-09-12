# Independent final acceptance — NFC CARD v13

**Decision: ACCEPT_LOCAL_CANDIDATE. Open critical: 0. Open high: 0. Open medium: 0.**

Public revision: `4b0ccbc08aecda587aae9600e79352a1829c6de9758de87caffcdaf0821e5414`. Full source/test revision: `446a54d0dddac08cb10e0d0bf27f698986861b5812defd8da381b126bb28fec5`.

This accepts the requested local v13 refinement and its evidence. It does **not** infer owner visual acceptance, production acceptance or permission to publish. `userAccepted` and `publicationAuthorized` remain false. The independent auditor did not implement the site, launch a browser/test, inspect private customer data or perform an external send.

[Authoritative machine receipt](acceptance-final.json) binds the evidence and decision. [Reproducible evidence-only checker](issue_acceptance.py) independently recomputes the file, log, matrix, screenshot and critic checks; its assertions passed before this decision.

## Evidence independently checked

- All 143 candidate source files and 101 public files match the sealed digests; the public file set contains no extra unsealed file. Frozen test-start/end source and public inventories match, with only recording timestamps differing.
- All 465 current pytest cases passed across the declared sequential groups. Every final log hash and pass summary matches the result manifest; every stage has exit code 0. Initial failures and superseded revisions remain historical evidence and are not counted as current passes.
- The baseline contains 64 contexts; the current focused matrix has 80 contexts across exactly 320, 360, 390, 430, 768, 1024, 1280 and 1440 px. All current focused rows return 200, have one H1, no document overflow, no broken images and the required hidden zero-review section/nav state. Page and HTTP error arrays are empty.
- Integration evidence covers 144 route/width contexts, plus 32 authenticated empty-admin contexts and seven actual 200% browser-zoom routes. Fifteen targeted reports bind gallery/radio/About behavior and four delayed-media cases to the same current public revision. The existing transaction, pending-review, privacy, moderation and retry evidence is included in the frozen 465-case suite.
- All **1,520** native screenshots are explicitly referenced and present: 592 before, 512 focused after, 356 integration/state and 60 targeted. No orphan or missing image was found in these accepted screenshot roots. The 16 previously unindexed auxiliary images now have exact test producers, current producer hashes, image hashes and synthetic-state labels.
- The recovery ZIP and all 142 archived entries independently match their hashes. All 33 protected source/data/server/template files remain byte-identical to recovery; all 56 historical v12 evidence files remain unchanged. Current rollback inventory matches every modified/addition byte. The helper is dry-run by default and restores/removes only bounded, exact, hash-verified files; no recursive delete, database rollback or private-upload operation is involved.
- Local preview evidence reports HTTP 200 for home, both About locales and current CSS, with response bytes matched to the sealed output and the preserved server hydration. This is a local preview check, not a deployment receipt.

## Owner requirements and independent criticism

The [requirement matrix](../REQUIREMENT_MATRIX.md), [four screenshot issue closures](../SCREENSHOT_ISSUE_MATRIX.md) and [before/after map](../BEFORE_AFTER.md) cover the controlled scope. The existing product routes/pricing/persistence/security remain protected; only the declared visual/gallery/messenger/ending/About surfaces changed.

The [independent visual verdict](visual-final.md) covers design, UX, responsive behavior, accessibility and anti-template review. The [independent content/technical verdict](content-technical-final.md) covers exact founder/company copy, pinned-source media, SEO, public/private boundaries and runtime non-regression. Both identify the same current source/public revision and report no open critical/high/medium finding. Independently verified all 100 image hashes in the visual receipt and all 31 evidence hashes in the technical receipt. The [consolidated finding history](../CRITIC_FINDINGS.md) retains concrete defects and their corrections rather than substituting self-scores for review.

This auditor additionally inspected current native catalogue media at 1440 px, homepage ending at 390 px, About introduction at 320 px and the English standard product gallery at 390 px. The media fills its catalogue column, gallery thumbnails are visible, the compact ending is complete and the approved About wording wraps coherently. Detailed native chapter, mobile/state and privacy-crop inspection is supplied by the separate critics, with exact inspected paths and hashes.

The material loading regression is closed: the earlier 435 px catalogue-image insertion was traced to missing predecode space. Four delayed-image cases now record identical before/after image/copy rectangles and session CLS 0. The complete current focused matrix has maximum initial session-window CLS **0.045981**, not a blanket zero claim. The separate 144-row legacy initial-load measurement has maximum eligible shift sum 0.04421. The report correctly distinguishes these laboratory observations from field performance.

The exact pinned About source remains `013bd2d904d5be143a0e203d0005c29f25db729f`, with 28 approved founder derivatives, eight timeline entries and nine ecosystem entries. The iADDS/NFC CARD dates remain distinct; original privacy-safe crops and source facts are preserved. No real first customer review, company testimonial, result, rating or client photograph was fabricated.

## Finalization and boundaries

The director may now record **CANDIDATE_READY** for this exact local candidate. After changing the task checkpoint, refresh its rollback inventory and verification-only dry run, update the readable report status, then create the source/screenshot/evidence seals. This is bookkeeping after the independent decision; any application-byte change requires renewed relevant verification. Finalization bytes receive a separate read-only closure check before delivery.

Only installed Chromium was exercised. Physical devices, other browser engines and a human screen-reader session were not certified. Production Railway/S3 resources, owner admin-credential setup and real Telegram/email delivery were not provisioned or tested. The retained runbook explains the owner-admin setup; no default password was introduced. The small 320 px footer-height deviation from the approximate 340 px guidance is explained by legitimate legal/link wrapping, with no clipping or substantive defect.

Deployment, Git push, domain changes, production provisioning, rollback apply and real Telegram/email/customer sends were not performed in this refinement. These actions remain outside this acceptance and outside the owner's current authorization.
