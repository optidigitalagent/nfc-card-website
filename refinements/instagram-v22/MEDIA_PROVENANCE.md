# Media provenance

The deterministic importer is `scripts/update_instagram_media.py`. It accepts only the five fixed filenames and SHA-256 values below, verifies dimensions, flattens transparency onto white without cropping, strips embedded metadata and writes responsive WebP/AVIF derivatives. Running it twice produces an identical manifest SHA.

| Source | SHA-256 | Class | Public role |
|---|---|---|---|
| `instagram-card-real-front-window.png` | `a022447d050fb9088c9747db645c89ebcad37fecaeb08678c18eba55c58b036b` | owner-supplied product photo | gallery primary / info |
| `instagram-card-real-front-desk.png` | `6250a2d021491d8c053f16ddb94031d7e81ac19b4847b0562ea9afcbeb90da8d` | owner-supplied product photo | gallery |
| `instagram-card-real-edge-profile.png` | `35ca22e129e7a8f8d70fe7300b2ff405b3d5409a48ce4a49d2f8ef1f707f323c` | owner-supplied product photo | gallery / info |
| `instagram-card-real-back-mounting.png` | `c470f4cf80cb11ec820d4ed806bb84851d5e9145c57ace0f5d7963920f54f5a0` | owner-supplied product photo | gallery |
| `instagram-card-clean-front-render.png` | `15204c4e924033062498cf85f52dc7ab0fc4a3f9c4b4147a9c4f00190ed31278` | owner-supplied promotional render | catalog / gallery secondary |

Output: 40 files (20 WebP, 20 AVIF), 40 managed manifest records, 102 pre-existing manifest records preserved. Tests verify bytes, hashes, dimensions, metadata absence, source confinement, real-before-render order and the exact public allowlist.

The four `instagram-card-promo-*-ua.png` assets are classified `REVIEW_REQUIRED_NOT_PUBLIC`; the importer never reads or copies them.
