#!/usr/bin/env python3
"""
heic_to_jpg.py (v1.3 — 2025-05-25)
===================================
Batch-convert HEIC/HEIF images to JPEG.

Changelog
---------
* **v1.3** – Handle images with **no EXIF at all** (NoneType error).
  We now pass the `exif=` parameter only when we actually have a non-empty
  byte-blob to supply.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Iterable, Set

from PIL import Image, ImageOps, ExifTags  # type: ignore

try:
    from pillow_heif import register_heif_opener  # type: ignore

    register_heif_opener()
except ImportError:
    sys.exit(
        "Error: pillow-heif not installed. Run 'pip install pillow-heif' "
        "(and 'brew install libheif' on macOS) then retry."
    )

TAG_MAP = {v: k for k, v in ExifTags.TAGS.items()}
KEEP_TAG_NAMES = {"DateTimeOriginal", "CreateDate", "DateTime"}


def discover(root: pathlib.Path, exts: Set[str], recursive: bool) -> Iterable[pathlib.Path]:
    iterator = root.rglob("*") if recursive else root.iterdir()
    for p in iterator:
        if p.is_file() and p.suffix.lower().lstrip(".") in exts:
            yield p


def build_exif_bytes(src_img: Image.Image) -> bytes | None:
    orig = src_img.getexif()
    if not orig:
        return None
    new = Image.Exif()
    for tag_id, value in orig.items():
        if TAG_MAP.get(tag_id) in KEEP_TAG_NAMES:
            new[tag_id] = value
    return new.tobytes() if new else None


def convert(src: pathlib.Path, quality: int, delete: bool) -> None:
    dst = src.with_suffix(".jpg")
    if dst.exists():
        print(f"[SKIP] {dst.name} already exists")
        return

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        exif_bytes = build_exif_bytes(im)
        save_kwargs = {"quality": quality}
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        im.convert("RGB").save(dst, "JPEG", **save_kwargs)
        print(f"[OK] {src.name} → {dst.name}")

    if delete:
        src.unlink()
        print(f"      Deleted original {src.name}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Convert HEIC/HEIF images to JPEG.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("directory", type=pathlib.Path, help="Source folder.")
    p.add_argument("-r", "--recursive", action="store_true", help="Recurse into sub-folders.")
    p.add_argument("-q", "--quality", type=int, default=90, help="JPEG quality 1-100.")
    p.add_argument("--ext", default="heic,heif", help="Comma-separated list of extensions.")
    p.add_argument("--delete", action="store_true", help="Delete original files.")

    args = p.parse_args()

    if not args.directory.exists():
        p.error(f"{args.directory} does not exist.")
    if not (1 <= args.quality <= 100):
        p.error("--quality must be between 1 and 100.")

    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}
    if not exts:
        p.error("--ext yielded no valid extensions.")

    total = 0
    for src in discover(args.directory, exts, args.recursive):
        try:
            convert(src, args.quality, args.delete)
            total += 1
        except Exception as exc:
            print(f"[ERROR] {src.name}: {exc}", file=sys.stderr)

    if total == 0:
        print("No matching files converted (review [ERROR] lines).")
    else:
        print(f"Done. Converted {total} file{'s' if total != 1 else ''}.")


if __name__ == "__main__":
    main()
