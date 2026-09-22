"""Import the five approved NFC Instagram Card assets from release pack v22.

The script is deliberately narrow: source names and hashes are fixed, review-only
graphics are never read, output metadata is stripped, and only v22-managed media
manifest records are replaced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/media/instagram"
MANIFEST = ROOT / "src/media-manifest.json"
PUBLIC_PREFIX = "/assets/media/instagram"
MANAGED_BY = "scripts/update_instagram_media.py:v22"
WIDTHS = (320, 640, 960)

ASSETS = (
    {
        "stem": "instagram-card-real-front-window",
        "sha256": "a022447d050fb9088c9747db645c89ebcad37fecaeb08678c18eba55c58b036b",
        "width": 1086,
        "height": 1448,
        "classification": "owner_supplied_product_photo",
        "claim_role": "real_product_photo",
        "role": "Primary authentic product photo",
        "page_or_section": "Product gallery primary / information page",
        "alt_ua": "Передня сторона NFC Instagram Card у руці біля вікна.",
        "alt_en": "Front of the NFC Instagram Card held in a hand near a window.",
        "caption_ua": "Реальне фото NFC Instagram Card: передня сторона біля вікна.",
        "caption_en": "Real NFC Instagram Card photo: front view near a window.",
    },
    {
        "stem": "instagram-card-real-front-desk",
        "sha256": "6250a2d021491d8c053f16ddb94031d7e81ac19b4847b0562ea9afcbeb90da8d",
        "width": 1086,
        "height": 1448,
        "classification": "owner_supplied_product_photo",
        "claim_role": "real_product_photo",
        "role": "Secondary authentic product photo",
        "page_or_section": "Product gallery",
        "alt_ua": "Передня сторона NFC Instagram Card у руці над світлим робочим столом.",
        "alt_en": "Front of the NFC Instagram Card held above a light desk.",
        "caption_ua": "Реальне фото NFC Instagram Card над робочим столом.",
        "caption_en": "Real NFC Instagram Card photo above a desk.",
    },
    {
        "stem": "instagram-card-real-edge-profile",
        "sha256": "35ca22e129e7a8f8d70fe7300b2ff405b3d5409a48ce4a49d2f8ef1f707f323c",
        "width": 1086,
        "height": 1448,
        "classification": "owner_supplied_product_photo",
        "claim_role": "real_product_photo",
        "role": "Authentic edge and thickness context",
        "page_or_section": "Product gallery / information page",
        "alt_ua": "NFC Instagram Card під кутом у руці; видно край і товщину картки.",
        "alt_en": "NFC Instagram Card held at an angle, showing the edge and thickness.",
        "caption_ua": "Реальне фото NFC Instagram Card під кутом: видно край картки.",
        "caption_en": "Real NFC Instagram Card photo at an angle, showing its edge.",
    },
    {
        "stem": "instagram-card-real-back-mounting",
        "sha256": "c470f4cf80cb11ec820d4ed806bb84851d5e9145c57ace0f5d7963920f54f5a0",
        "width": 1086,
        "height": 1448,
        "classification": "owner_supplied_product_photo",
        "claim_role": "real_product_photo",
        "role": "Authentic reverse and mounting photo",
        "page_or_section": "Product gallery",
        "alt_ua": "Зворотний бік NFC Instagram Card із двома клейкими смугами для кріплення.",
        "alt_en": "Back of the NFC Instagram Card with two adhesive mounting strips.",
        "caption_ua": "Реальне фото зворотного боку NFC Instagram Card із клейкими смугами.",
        "caption_en": "Real photo of the NFC Instagram Card back with adhesive strips.",
    },
    {
        "stem": "instagram-card-clean-front-render",
        "sha256": "15204c4e924033062498cf85f52dc7ab0fc4a3f9c4b4147a9c4f00190ed31278",
        "width": 1254,
        "height": 1254,
        "classification": "owner_supplied_promotional_render",
        "claim_role": "promotional_product_render",
        "role": "Promotional front render",
        "page_or_section": "Catalogue primary / product gallery secondary",
        "alt_ua": "Промоілюстрація передньої сторони NFC Instagram Card на білому фоні.",
        "alt_en": "Promotional illustration of the front of the NFC Instagram Card on a white background.",
        "caption_ua": "Промоілюстрація готового дизайну NFC Instagram Card.",
        "caption_en": "Promotional illustration of the ready-made NFC Instagram Card design.",
    },
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        return background.convert("RGB")
    return image.convert("RGB")


def save(image: Image.Image, destination: Path, fmt: str) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    options = {"method": 6, "quality": 86} if fmt == "WEBP" else {"quality": 76, "speed": 6}
    image.save(destination, fmt, **options)
    return {
        "source": destination.relative_to(ROOT).as_posix(),
        "url": f"{PUBLIC_PREFIX}/{destination.name}",
        "bytes": destination.stat().st_size,
        "sha256": digest(destination),
        "width": image.width,
        "height": image.height,
    }


def manifest_record(asset: dict, file_data: dict, *, primary: bool, derivative_of: str | None = None) -> dict:
    record = {
        "path": f"media/product/instagram-card/2026-09/{Path(file_data['source']).name}",
        "status": "public",
        "role": asset["role"] if primary else f"Responsive derivative of {asset['role'].lower()}",
        "page_or_section": asset["page_or_section"],
        "alt_ua": asset["alt_ua"],
        "alt_en": asset["alt_en"],
        "caption_ua": asset["caption_ua"],
        "caption_en": asset["caption_en"],
        "notes": "Render, not documentary photography." if asset["claim_role"] == "promotional_product_render" else "Preserve the complete card and rounded corners.",
        **file_data,
        "duration_seconds": "",
        "provenance": "user_provided_business_asset",
        "claim_role": asset["claim_role"],
        "classification": asset["classification"],
        "product_id": "nfc-instagram-card",
        "requirements_source": "NFC_CARD_FRESH_CHAT_INSTAGRAM_UPDATE_PACK_v22",
        "original_sha256": asset["sha256"],
        "metadata_stripped": True,
        "managed_by": MANAGED_BY,
        "media_type": "image",
    }
    if derivative_of:
        record["derivative_of"] = derivative_of
    return record


def import_assets(source_dir: Path) -> int:
    original_bytes = MANIFEST.read_bytes()
    existing = json.loads(original_bytes)
    preserved = [entry for entry in existing if entry.get("managed_by") != MANAGED_BY]
    records: list[dict] = []

    for asset in ASSETS:
        source = source_dir / f"{asset['stem']}.png"
        if not source.is_file() or digest(source) != asset["sha256"]:
            raise SystemExit(f"Rejected source or checksum mismatch: {source.name}")
        with Image.open(source) as opened:
            image = flatten(opened)
        if image.size != (asset["width"], asset["height"]):
            raise SystemExit(f"Rejected dimensions for {source.name}: {image.size}")

        webp_full = save(image, OUTPUT / f"{asset['stem']}.webp", "WEBP")
        avif_full = save(image, OUTPUT / f"{asset['stem']}.avif", "AVIF")
        webp_variants, avif_variants = [], []
        for width in WIDTHS:
            resized = image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
            webp_variants.append(save(resized, OUTPUT / f"{asset['stem']}-{width}.webp", "WEBP"))
            avif_variants.append(save(resized, OUTPUT / f"{asset['stem']}-{width}.avif", "AVIF"))

        primary = manifest_record(asset, webp_full, primary=True)
        primary["thumbnail_url"] = webp_variants[0]["url"]
        primary["responsive"] = [{"url": item["url"], "width": item["width"]} for item in webp_variants]
        primary["avif"] = {
            "url": avif_full["url"],
            "width": avif_full["width"],
            "responsive": [{"url": item["url"], "width": item["width"]} for item in avif_variants],
        }
        records.append(primary)
        for item in [*webp_variants, avif_full, *avif_variants]:
            records.append(manifest_record(asset, item, primary=False, derivative_of=webp_full["url"]))

    expected = {record["source"] for record in records}
    for old in OUTPUT.glob("*"):
        if old.is_file() and old.relative_to(ROOT).as_posix() not in expected:
            old.unlink()
    marker = f'"managed_by": "{MANAGED_BY}"'.encode()
    if marker in original_bytes:
        marker_at = original_bytes.index(marker)
        start_crlf = original_bytes.rfind(b"\r\n  {", 0, marker_at)
        start_lf = original_bytes.rfind(b"\n  {", 0, marker_at)
        start = start_crlf if start_lf == start_crlf + 1 else start_lf
        if start < 0:
            raise SystemExit("Cannot locate the managed manifest section")
        preserved_bytes = original_bytes[:start]
        if preserved_bytes.endswith(b","):
            preserved_bytes = preserved_bytes[:-1]
    else:
        stripped = original_bytes.rstrip(b"\r\n")
        if not stripped.endswith(b"]"):
            raise SystemExit("Media manifest is not a JSON array")
        preserved_bytes = stripped[:-1].rstrip(b"\r\n")
    managed_json = json.dumps(records, ensure_ascii=False, indent=2)
    managed_body = managed_json.split("\n", 1)[1].rsplit("\n", 1)[0].encode("utf-8")
    MANIFEST.write_bytes(preserved_bytes + b",\n" + managed_body + b"\n]\n")
    print(f"Imported {len(ASSETS)} approved sources into {len(records)} optimized files; review-only graphics ignored")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    return import_assets(args.source_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
