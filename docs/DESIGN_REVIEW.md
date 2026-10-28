# NFC CARD visual review

This review belongs to `design/visual-refresh-2026-10-28` in
`zaffirax55/nfc-card-website`. It is a proposed update to the existing site.
The pull request stays in draft until the owner has inspected the result.

## Preview from a fresh checkout

```sh
npm ci
NFC_ENV=production NFC_PUBLIC_ORIGIN=https://nfc-card.example NFC_PUBLICATION_MODE=PUBLIC_PREVIEW npm run build
python -m http.server 8765 --directory site
```

Open `http://localhost:8765/`. The catalog is at `/solutions/`; the
English and Polish versions are at `/en/` and `/pl/`. The local static
preview does not submit real orders. Do not use customer details for QA.

## What to inspect

| View | Desktop | Phone |
| --- | --- | --- |
| Home | The phone demo, readable copy and catalog link share the first screen | The heading and catalog link lead into the visible phone without horizontal scrolling |
| Catalog | Nine cards show full product imagery, prices, 3D buttons and photo choices | The main photo fits inside its frame; thumbnails are not cropped; actions remain reachable |
| Product | Gallery and purchase details are aligned | Gallery sits above purchase details; all images fit and the lightbox closes by keyboard |
| About, delivery and order | Typography and spacing remain consistent | Content, links and form controls fit at 320–390 px |

The 3D renderer loads only after a visitor opens one card. Reduced-motion
visitors do not get automatic model rotation. The customer review section
shows an honest empty state until verified reviews are available.

GitHub Actions validates the full route and browser matrix. On this pull
request it also saves a short-lived `nfc-card-design-preview` artifact with
screenshots of public pages at 390 px and 1440 px. The current live Pages site,
production gateway and `main` are outside this visual review.
