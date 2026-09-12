# v13 bounded architecture and regression audit

Date: 2026-09-11. Role: independent read-only refinement architect. This is a source audit before implementation, not candidate acceptance. The existing application is `runs/nfc-card-manual-v1` in the current SiteAgent workspace. No application source, test, private data, database or running service was changed by this audit. No browser was started; root owns baseline capture to avoid memory contention.

## Scope and authority

The explicit v13 owner request supersedes v11 only for the eight listed visual/About areas. The current v12 accepted implementation remains the baseline for commerce, reviews, persistence and security. The pinned iADDS commit supplies founder/company content architecture and approved founder derivatives, not NFC product claims or visual styling. Existing `commerce-v12` evidence must remain immutable.

Read inputs: SiteAgent `AGENTS.md`; Project Brain index, vision, quality, feedback, director protocol and references; current workflow goal/next-action and this NFC run's checkpoint; the v13 start, execution, issue matrix and iADDS source-map files; current builder, commerce views/runtime/styles, public model, regression tests and browser harness. Root owns full v11 pack ingestion and source/media provenance acquisition. This audit does not attest to the remote iADDS source itself.

Applied local guidance: `.agents/skills/siteagent-project-director/SKILL.md`, `.agents/skills/siteagent-web-studio/SKILL.md`, `.agents/skills/responsive-review/SKILL.md`; `.codex/skills/frontend-implementer/SKILL.md`, `qa-tester/SKILL.md`, `acceptance-auditor/SKILL.md`, `siteagent-acceptance-audit/SKILL.md`, `accessibility-reviewer/SKILL.md`, `performance-reviewer/SKILL.md` in the repository instruction source. Application: preserve accepted architecture, scope edits, require evidence per criterion, separate implementation from criticism, verify interactions beyond layout, and retain no-publish boundaries. The new-concept workflow does not apply to this explicitly accepted-design refinement.

## Exact component ownership

| Area | Existing owner and integration | Smallest justified v13 change |
|---|---|---|
| Catalog and full-card link | `src/commerce-view.mjs:card()` invoked by `src/build.mjs:catalog()`; `commerce.css` media/copy/prices rules | Asset-aware ratio and responsive derivative markup. Keep the single genuine card link, stretched hit area, exact prices, delivery copy and separate canonical products. Never place interactive gallery controls inside the stretched card link. |
| Product gallery | `commerce-view.mjs:gallery()`, exported `galleries` order; `commerce.js` initial gallery block; `commerce.css` frame/controls/thumbnails/lightbox | Visible thumbnail rail at every width, small derivatives, clear active marker, adjacent preloading, lightbox rail/arrows/swipe/keyboard/focus and scroll restoration. Preserve standard order 05,03,01,02,04 and branded placeholder,current-hand,current-back. |
| Custom quote | `build.mjs:catalog()` has `.catalog-assist`; `commerce-view.mjs:product()` has `#business-orders`/`#branches` cross-link; shared `.catalog-assist`/`.product-cross-link` styles | One content-sized compact composition per actual placement; preserve 3+ => `more` custom quote, anchor IDs and business-order destination. |
| Direct review section | `build.mjs:destination()` and `style.css:.destination-section/.destination-image` | Independent media sizing from caption; safe full image at intrinsic ratio, explicit responsive dimensions; stronger H2. Preserve customer-choice and Google sign-in disclosure. |
| Heading hierarchy | Base h1/h2/h3 in `style.css`; several component overrides in `style.css` and `commerce.css` | Coherent tokens and component roles, one H1; inspect overrides at 768/359px and prose/product/About. Enlarging only base H2 is insufficient because specificity overrides it. |
| Messenger options | `commerce-view.mjs:form()` generates native required radios; `commerce.css:.messenger-*`; `commerce.js` form validation/draft/retry | Replace generic inline drawings with local audited official icons, brand colors and 44–56px horizontal controls. Retain input names, values, IDs, fieldset/legend and pending disabled-state semantics. |
| Final CTA, footer | `build.mjs:home()/formSection()/footer()/shell()`; `style.css:.request-section/.footer*` | Purposeful final homepage action followed immediately by compact footer; form-heavy PDP/order/contact retain form endpoint. No giant second CTA after a final form. Footer currently repeats a branded action and full contact/navigation stack. |
| Founder teaser and About | `build.mjs:founder()/story()/home()`; `model.mjs` existing approved short copy; new dedicated content/view module can be added inside `src` | Teaser links to `/about`; add bilingual narrative depth and authorized local responsive media, no homepage story duplication. Preserve founder background story behavior unless an explicitly documented v13 scope adjustment requires moving it. |
| Navigation and SEO | `build.mjs:navPaths/nav/footer/shell/schema/emit()` and sitemap output | Replace only the About nav destination `/#about` with `/about`; two new pages yield 26 total localized routes. Existing legacy `#about` may remain as teaser target for inbound links. Canonical, reciprocal hreflang, locale switch and sitemap must include both pages. |
| Media allowlist | `src/media-manifest.json`; `build.mjs:asset()/picture()` and strict checksum/copy loop | Append exact approved founder/product-thumbnail derivatives with provenance/claim role, hashes and dimensions. Continue safe local source and output containment checks. No reference-only screenshot, held QR creative or original founder source in public output. |
| Native browserless form | `server/preview.py:hydrate_native_form()` consumes selectors/field names in built markup | Preserve markup contracts; avoid backend edits. Existing native tests must pass with the new surrounding visual markup. |
| Preview/build/test orchestration | `package.json`, `Run-Checks.ps1`, `Start-Commerce-Preview.ps1`, tests | Only local current-evidence path redirection and scoped test additions justified. No new starter, stack or service architecture. |

## Evidence isolation hazards found before implementation

1. **Builder writes old evidence:** `src/build.mjs` declares `task=.../refinements/commerce-v12` and writes `routes.json` there. Route addition will overwrite v12 evidence unless redirected before the first v13 build. The media source itself is the main `src/media-manifest.json`; this audit found no build write to the v12 media report.
2. **Browser harness writes old evidence:** `tests/test_v12_browser.py` hard-codes `EVIDENCE=ROOT/'refinements/commerce-v12'`, creates its verified screenshots directory on import, and writes matrix/state/zoom files there. Add an explicit current-evidence path environment/config parameter with a v13 invocation, or intentionally migrate the current harness's output root. Keep the original v12 artifacts immutable. Do not run even a collection that creates v12 output directories while preserving historical snapshots without assessing it.
3. `Run-Checks.ps1` defaults its artifact root to the v12 directory. Point current test runs at v13 without copying old PASS files. Its existing separate process per width is appropriate for this host's known memory pressure.
4. Historical `tests/browser_qa.py` and `tests/seal_acceptance.py` use an older gallery API and `generation_reports/routes.json`. They are historical acceptance scripts, not current runnable v12 pytest tests. Do not claim that these old scripts validate v13 without actually adapting and running them; use current pytest integration harness.
5. Matrix reports bind the public output hash before and after a width run. Preserve this stale-evidence rejection: all accepted screenshots must match final application output, and root must not rebuild mid-capture. Native viewport sequences are valid for pages exceeding bitmap memory, with real scroll positions and complete coverage recorded; do not stitch or synthesize images.

## Backend immutable boundary

No v13 feature requires modifying the following: `server/pricing.py`, `commerce_repository.py`, review service/repository/storage/images/auth/http/runtime/config modules, migrations 001–003, retention/reconcile/outbox maintenance, WSGI production adapter or notification boundaries. `src/commerce.json`, display canonical quote helpers, review renderer/client/admin scripts and review form content are also protected non-visual contracts. The builder may rewrite generated admin templates with identical bytes; a non-identical template diff needs explanation.

The public pricing API and lead POST remain server authoritative: standard 1500/2600 UAH, branded 2000/3600, 3+ custom, 200 UAH deposit included. Messenger payload remains lowercase `telegram`, `whatsapp`, `viber`. Pending IndexedDB and idempotency partitioning by actual product/explicit order variant must remain intact. Reviews remain pending-only and hidden in public navigation until published; no synthetic testimonial insertion. Private storage access, two-photo publication gating, raw-review immutability, session/CSRF enforcement and durable-before-notification tests are required regressions, even if their source bytes do not change.

## Existing tests requiring intentional updates

| Test | Reason and safe update |
|---|---|
| `test_site.py:BASE_ROUTES`, `test_exact_twenty_four_localized_routes` | Add `/about`, rename count-specific test to 26/current route set, retain exact equality. All route integrity, href target, one-H1, locale and canonical checks then automatically cover new pages. |
| `test_site.py:test_sitemap_has_only_current_nontransactional_nondraft_routes` | Inherits expanded route set; continue exact equality and exclusion of drafts/transactional pages. |
| `test_v9.py:test_public_media_exact_allowlist_and_original_hashes` | Existing `len(expected)==15` becomes stale with approved derivatives. Replace fixed count with explicit accepted baseline subset plus v13 derivative/provenance manifest; continue exact public-vs-allowlist equality and byte-hash validation. Do not remove allowlist enforcement. |
| `test_v9.py:test_gallery_provenance_and_visible_faq_match_schema` | Preserve exact gallery count/order/provenance; if derivative filenames change, assert canonical source identities through manifest rather than delete the order check. Keep closed product disclosure and truthful schemas. |
| `test_site.py:test_new_primary_form_fields_and_conditional_contract` | If homepage final composition intentionally becomes link CTA rather than inline form, remove only `/` and `/en` from the form-route parametrization and add a test that their final CTA reaches the exact working order route. Product/order/contact native forms retain original contract. Keeping the home form needs no change. |
| Browser geometry `galleryDisplay == flex/grid` | This tests implementation choice, not behavior. If layout implementation changes intentionally, replace with measured main-gallery/purchase order and non-overlap assertions; retain width, overflow, content and interactions. |
| Browser story test | Keep the actual current story controls and reduced-motion/contrast assertions. If v13 intentionally relocates the story to About, test the destination route; do not remove motion coverage merely because a selector moved. |
| Existing browser route lists and evidence counts | Add About UA/EN to matrix and diagnostics; update counts from real result rows, not a hard-coded assumed total. Keep all commerce/reviews/admin checks. |

## Targeted behavioral test plan

1. About paths return 200; exact 26-page output; reciprocal canonicals/hreflang; header, menu, teaser and footer links open canonical About; cross-route navigation resets top while legacy hash navigation remains offset below sticky header.
2. Pin source commit/hash provenance, verify transferred exact founder/company paragraphs and approved translations, preserve distinct 15 August iADDS and 20 August NFC CARD timeline entries, verify expected sibling/service ecosystem and NFC-specific adaptation whitelist. No unresolved `{{product}}`, advertising-content promise or copied contact discrepancy.
3. Founder 7-image sequence includes all authorized roles locally; AVIF/WebP variants, responsive source selection, exact source privacy crops/alt text, no hotlinks or originals. Hold/reference-only hashes remain absent from every public output file.
4. Gallery every item reachable using visible mobile thumbnails and keyboard while focus is on rail (not only frame); current marker/counter/caption sync; last item selection; swipe changes once, not twice; main gallery and lightbox share current selection.
5. Lightbox close/Escape restores exact opener; Tab/Shift-Tab containment includes new controls; arrows/swipe and active rail work; scroll is locked while open and restored on close without viewport jump; safe close control at 320px and 200% zoom.
6. Network observations confirm thumbnails do not download full-resolution photos, non-adjacent images remain lazy and adjacent originals preload only when needed; dimensions reserve space. Local performance is laboratory evidence, never field Core Web Vitals certification.
7. Catalog media content bounds show no artificial neutral bands at 390/768/1440 while reviewers inspect safe edges/message/disclaimer. Full-card pointer and keyboard open correct products; no nested interactive element; canonical price/delivery still visible.
8. Direct-review image and caption fit their figure without crop/clipping at 320/390/768/1024/1440; one coherent heading scale across major public sections, no one-word line failure on narrow screens.
9. Compact 3+ callout measures content-sized height at 320/390/1024, no fixed/min-height dead zone; quantity 1/2/3+ changes display/native hidden fields/server amount consistently, with same locale and attribution behavior.
10. Messenger controls are native required radios, 44–56px high, three compact choices at 320; recognized local logos with recorded licenses, brand color plus non-color selection check; Tab/Arrow/Space selects one value; clear error/focus/disabled states; pending immutable order retry remains disabled and exact.
11. Homepage final action immediately precedes footer in the meaningful section sequence; actual 390x844 end composition places CTA around the requested band without invented empty spacers. Footer contains verified essential navigation/contact/legal content, no duplicate founder story, no tiny text or excessive stacking; all links remain reachable.
12. Full current pytest suite plus focused v13 tests in sequential memory-safe groups. Browser at eight widths UA/EN, Chromium plus installed secondary engine if available, keyboard, true 200% zoom and reduced motion; all console and failed-asset checks. Isolated synthetic schema only, external network blocked. No real Telegram/email/customer action.

## Review and acceptance risks

- Gallery rail doubles modal controls; a two-button-only focus trap becomes invalid after adding arrows/thumbnails. Filter focusable visible controls and prove behavior.
- Both pointer and touch listeners exist; changing swipe code can accidentally advance two slides per gesture. Retain one-gesture-one-slide proof.
- Existing native hydration parses known selectors and markup. Renaming form field/price markers can break no-JS selected quantity or canonical displayed values even when client JS appears correct.
- Global footer changes affect every route, including review submission/thank-you/legal pages. Verify those pages, not only home/PDP/About.
- Dark About sections and enlarged typography may inherit muted text or button colors with inadequate contrast. Review state-specific computed contrast and screenshots.
- Source founder media privacy crops are authoritative; superficially sharper uncropped originals are prohibited.
- Test PASS totals are not acceptance: require screenshot issue closure, independent reviewers and final revision binding. Prior v12 production caveats (real first review, owner password setup, untested production integrations) remain honestly stated.

## Audit verdict

Proceed with the bounded v13 implementation after root's baseline/recovery completes. Existing architecture supports all requested changes without a framework or backend rewrite. The main pre-build risk is overwriting historical v12 evidence; the main implementation risks are gallery modal lifecycle, exact About source transfer, media ratios and global footer/header changes. No independent candidate acceptance is claimed at this stage.
