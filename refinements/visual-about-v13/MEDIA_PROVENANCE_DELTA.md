# Media and icon provenance delta

The existing 15 media records and their source bytes are retained. The exact 44 additions are recorded in [media-delta.json](media-delta.json), with SHA-256, local source/output path, dimensions, provenance and parent asset.

| Addition | Count | Treatment |
|---|---|---|
| Product photo derivatives | 15 | Five existing approved photos, widths 160/480/800 px; aspect-preserving downsample without crop, metadata stripped. The 160 px rail avoids loading original photos as thumbnails. Main gallery uses responsive images; lightbox uses the original approved resolution. |
| Branded catalog SVG | 1 | Tighter viewBox around the existing neutral branded placeholder. Card edges, label and shadow preserved; the original remains in the PDP gallery. Clearly labelled personalization example. |
| Founder photos | 28 | Seven roles × mobile/desktop × AVIF/WebP. Exact approved source derivatives, privacy crop/blur unchanged. No regeneration or source-photo substitution. |

Founder roles in order: portrait, hockey team, hockey puck, GoPro, jet ski, boat, urban. The supplied mobile boat crop and jet-ski registration blur remain intact; urban stays contained at no more than 300 px desktop / 240 px mobile. These are personal-history media, never a customer review or case. [Detailed source privacy provenance](about-source/MEDIA_PROVENANCE_DELTA.md).

Messenger icons: Telegram, WhatsApp and Viber SVG paths from Simple Icons, pinned commit `5d5d4d1d28cbb00b21770bb69d8112da52211a95`; local CC0 license copy and source hashes in [icon-source/manifest.json](icon-source/manifest.json). Only audited inline paths are included, with accessible text labels. Brand colors: #229ED9, #25D366, #7360F2; no CDN requests. CC0 covers the icon source implementation and does not assert ownership of trademarks.

The build's exact public allowlist and provenance assertions remain enforced. No diagnostic screenshot, held QR creative, original unredacted founder source, raw uploaded review or private storage object is copied into public assets.
