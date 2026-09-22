# Silver banner alignment

Target text:

- UA: `Одне торкання → Instagram-профіль.`
- EN: `One tap → Instagram profile.`

Implementation uses layout only on `.instagram-product-content > .detail-signature`:

- `display: grid`
- `place-items: center`
- `text-align: center`
- symmetric block/inline padding
- bounded minimum block size

No `transform`, negative offset or magic alignment margin is used. Static tests inspect the scoped rule; the nine-width Chromium matrix inspects computed styles and banner height for both locales.
