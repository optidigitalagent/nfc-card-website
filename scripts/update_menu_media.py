"""Import the ten owner-approved NFC Menu Card visualizations from pack v23.

Use only the packaged PNG masters. The outputs are aspect-preserving, metadata-free
WebP/AVIF derivatives; this script never generates or edits their printed content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/media/menu"
MANIFEST = ROOT / "src/media-manifest.json"
PUBLIC_PREFIX = "/assets/media/menu"
MANAGED_BY = "scripts/update_menu_media.py:v23"
REQUIREMENTS_SOURCE = "NFC_CARD_MENU_FRESH_CHAT_IMPLEMENTATION_PACK_v23"
WIDTHS = (320, 640, 960)

# Pinned source names and checksums from the owner-approved handoff.
SOURCES = {
    "menu-card-square-black-desk.png": "952d3488ecd213e9ae71d02447e3ded4e15bd98e957b8a808c2e306e528a3f59",
    "menu-card-square-black-hand.png": "5e150695d1985ba64e275b00e7d49002c58f7cfafb2f616ce98173836a7cc5ae",
    "menu-card-round-white-desk.png": "ff7bede9a3beb018582ddb49e3caab2b1fc2704d68e2e58cb7ad134e078d779b",
    "menu-card-round-white-hand.png": "123543ced19c42a854022b77fe84cd983b3590b87ce8bee15989100d8a1c3618",
    "menu-card-round-black-desk.png": "e4e52f978bef185dda86c1d6f490a058dc3bd2a200c50718561c5026fb100cde",
    "menu-card-round-black-hand.png": "0eca823b38686c6ca63d4fe51489af917abdba62edb86c9a89dd49b37467617d",
    "menu-card-square-white-desk.png": "5b686e9f06358e976c7c020d4589735d7e35d79213632f4e62846a6bfdea2d84",
    "menu-card-square-white-hand.png": "fd278fca02a07053498ca95a2aa0fdc50de8efbd570df0a97b7d2d3bd570d142",
    "menu-card-square-white-size-pair.png": "1311832be6b95365b9e004d44546523d6a11afd5bb1bf2f67b877e23a47a5df4",
    "menu-card-square-black-size-pair.png": "a68ce29dc0d00aa7fbf3805e675f5e8e68bc5bb4244c25a01c273fbb0ab66dc4",
}
GALLERY_ORDER = ["MENU01", "MENU02", "MENU07", "MENU08", "MENU05", "MENU06", "MENU03", "MENU04", "MENU10", "MENU09"]


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
    role = ", ".join(asset["recommended_roles"]).replace("_", " ")
    record = {
        "path": f"media/product/menu-card/2026-09/{Path(file_data['source']).name}",
        "status": "public",
        "role": role if primary else f"Responsive derivative of {role}",
        "page_or_section": "Catalogue / Menu product gallery / Menu information page",
        "alt_ua": asset["alt_uk"],
        "alt_en": asset["alt_en"],
        "caption_ua": asset["alt_uk"],
        "caption_en": asset["alt_en"],
        "notes": asset["notes"],
        **file_data,
        "duration_seconds": "",
        "provenance": "ai_generated_original",
        "claim_role": "generated_product_visualization",
        "classification": "OWNER_APPROVED_GENERATED_PRODUCT_VISUALIZATION",
        "product_id": "nfc-menu-card",
        "variant_coverage": asset["variant_coverage"],
        "requirements_source": REQUIREMENTS_SOURCE,
        "original_sha256": asset["sha256"],
        "metadata_stripped": True,
        "managed_by": MANAGED_BY,
        "media_type": "image",
    }
    if primary:
        record["gallery_order"] = GALLERY_ORDER.index(asset["id"]) + 1
        record["source_asset_id"] = asset["id"]
    if derivative_of:
        record["derivative_of"] = derivative_of
    return record


def import_assets(pack_dir: Path) -> int:
    spec = json.loads((pack_dir / "NFC_CARD_MENU_MEDIA_MANIFEST_v23.json").read_text("utf-8"))
    assets = spec["assets"]
    if spec.get("version") != "v23" or len(assets) != 10:
        raise SystemExit("Rejected incomplete or wrong-version media specification")
    policy = spec.get("policy", {})
    if not policy.get("all_assets_owner_approved_for_website") or policy.get("generate_new_images") is not False:
        raise SystemExit("Rejected media approval policy")
    if any(asset.get("classification") != "OWNER_APPROVED_GENERATED_PRODUCT_VISUALIZATION" or asset.get("public_status") != "PUBLIC_NOW" for asset in assets):
        raise SystemExit("Rejected non-public or differently classified asset")
    if {Path(a["packaged_file"]).name: a["sha256"] for a in assets} != SOURCES:
        raise SystemExit("Packaged source allowlist differs from pinned v23 assets")
    if {a["id"] for a in assets} != set(GALLERY_ORDER):
        raise SystemExit("Gallery IDs differ from pinned placement")
    old_bytes = MANIFEST.read_bytes()
    existing = json.loads(old_bytes)
    records = []
    for asset in assets:
        source = pack_dir / asset["packaged_file"]
        if not source.is_file() or digest(source) != asset["sha256"] or source.stat().st_size != asset["bytes"]:
            raise SystemExit(f"Rejected source or checksum mismatch: {source.name}")
        with Image.open(source) as opened:
            if (opened.width, opened.height, opened.mode, opened.format) != (asset["width"], asset["height"], "RGBA", "PNG"):
                raise SystemExit(f"Rejected image metadata: {source.name}")
            image = flatten(opened)
        stem = source.stem
        webp_full = save(image, OUTPUT / f"{stem}.webp", "WEBP")
        avif_full = save(image, OUTPUT / f"{stem}.avif", "AVIF")
        webp_variants, avif_variants = [], []
        for width in WIDTHS:
            resized = image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
            webp_variants.append(save(resized, OUTPUT / f"{stem}-{width}.webp", "WEBP"))
            avif_variants.append(save(resized, OUTPUT / f"{stem}-{width}.avif", "AVIF"))
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

    # Append or replace only this script's records, retaining every older record byte-for-byte.
    marker = f'"managed_by": "{MANAGED_BY}"'.encode()
    if marker in old_bytes:
        marker_at = old_bytes.index(marker)
        start_crlf = old_bytes.rfind(b"\r\n  {", 0, marker_at)
        start_lf = old_bytes.rfind(b"\n  {", 0, marker_at)
        start = start_crlf if start_lf == start_crlf + 1 else start_lf
        if start < 0 or any(item.get("managed_by") != MANAGED_BY for item in existing[existing.index(next(i for i in existing if i.get("managed_by") == MANAGED_BY)):]):
            raise SystemExit("Menu records must be a contiguous final manifest section")
        prefix = old_bytes[:start].rstrip(b",\r\n")
    else:
        stripped = old_bytes.rstrip(b"\r\n")
        if not stripped.endswith(b"]"):
            raise SystemExit("Media manifest is not a JSON array")
        prefix = stripped[:-1].rstrip(b"\r\n")
    managed_json = json.dumps(records, ensure_ascii=False, indent=2)
    managed_body = managed_json.split("\n", 1)[1].rsplit("\n", 1)[0].encode("utf-8")
    MANIFEST.write_bytes(prefix + b",\n" + managed_body + b"\n]\n")
    print(f"Imported {len(assets)} approved sources into {len(records)} optimized files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", type=Path, required=True)
    args = parser.parse_args()
    return import_assets(args.pack_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
