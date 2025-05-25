#!/usr/bin/env python3
"""
heic_strip_and_convert_to_jpg.py (v2.1 — 2025‑05‑25)
====================================================
**One‑step privacy wipe & convert — now deletes the original HEIC _by default_.**

Workflow
~~~~~~~~
1. **Remove every metadata tag** from each HEIC/HEIF (`exiftool -all=`).
2. Save a pristine **JPEG**.
3. **Delete the source HEIC automatically**, unless you pass `--keep`.

Usage
-----
    python heic_strip_and_convert_to_jpg.py DIR [--recursive] [--quality 90] [--keep]

Positional
~~~~~~~~~~
DIR                 Folder containing HEIC/HEIF files.

Flags
~~~~~
-r / --recursive    Recurse into sub‑folders.
-q / --quality      JPEG quality 1‑100 (default 90).
--keep              _Retain_ the original HEIC instead of deleting it.
--ext heic,heif     Extensions to scan (comma‑sep, case‑insensitive).

Dependencies
~~~~~~~~~~~~
  • **ExifTool** on PATH
  • **Pillow ≥10** + **pillow‑heif** (`pip install pillow pillow‑heif`)
    macOS users: `brew install libheif` before `pip install pillow‑heif`.

Example
~~~~~~~
    # Recurse, quality 92 % JPGs, keep originals
    python heic_strip_and_convert_to_jpg.py ~/Pictures/iPhone -r -q 92 --keep
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
from typing import Iterable, Set

from PIL import Image, ImageOps  # type: ignore

# ---------------------------------------------------------------------------
# Pillow‑HEIF registration (allows Pillow to read HEIC)
# ---------------------------------------------------------------------------
try:
    from pillow_heif import register_heif_opener  # type: ignore

    register_heif_opener()
except ImportError:
    sys.exit(
        "Error: pillow‑heif not installed. Run 'pip install pillow‑heif' "
        "(and 'brew install libheif' on macOS) then retry."
    )

# ---------------------------------------------------------------------------
# ExifTool helpers
# ---------------------------------------------------------------------------

def exiftool_available() -> bool:
    return shutil.which("exiftool") is not None


def strip_all_metadata(file: pathlib.Path) -> None:
    """Remove every metadata tag using ExifTool in‑place."""
    subprocess.run(
        ["exiftool", "-overwrite_original", "-all=", str(file)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def convert_to_jpg(src: pathlib.Path, quality: int, delete_original: bool) -> None:
    dst = src.with_suffix(".jpg")
    if dst.exists():
        print(f"[SKIP] {dst.name} already exists")
        if delete_original:
            src.unlink(missing_ok=True)
        return

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # honour orientation *before* we nuke EXIF
        im.convert("RGB").save(dst, "JPEG", quality=quality)
        print(f"[OK] {src.name} → {dst.name}")

    if delete_original:
        src.unlink()
        print(f"      Deleted original {src.name}")


# ---------------------------------------------------------------------------
# Traversal helpers
# ---------------------------------------------------------------------------

def discover(root: pathlib.Path, exts: Set[str], recursive: bool) -> Iterable[pathlib.Path]:
    iterator = root.rglob("*") if recursive else root.iterdir()
    for p in iterator:
        if p.is_file() and p.suffix.lower().lstrip(".") in exts:
            yield p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strip all metadata from HEIC/HEIF then convert to JPG, deleting originals by default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("directory", type=pathlib.Path, help="Source folder.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recurse into sub‑folders.")
    parser.add_argument("-q", "--quality", type=int, default=90, help="JPEG quality 1‑100.")
    parser.add_argument("--keep", action="store_true", help="Keep the original HEIC instead of deleting it.")
    parser.add_argument("--ext", default="heic,heif", help="Extensions to match, comma‑sep.")

    args = parser.parse_args()

    if not args.directory.exists():
        parser.error(f"{args.directory} does not exist.")
    if not (1 <= args.quality <= 100):
        parser.error("--quality must be between 1 and 100.")
    if not exiftool_available():
        sys.exit("Error: ExifTool not found (install via brew / apt / choco).")

    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}
    if not exts:
        parser.error("--ext yielded no valid extensions.")

    delete_originals = not args.keep

    total = 0
    for heic in discover(args.directory, exts, args.recursive):
        try:
            strip_all_metadata(heic)
            convert_to_jpg(heic, args.quality, delete_originals)
            total += 1
        except subprocess.CalledProcessError as exc:
            print(f"[ERROR] {heic.name}: ExifTool → {exc.stderr.decode().strip()}", file=sys.stderr)
        except Exception as exc:
            print(f"[ERROR] {heic.name}: {exc}", file=sys.stderr)

    if total == 0:
        print("No matching files processed — check [ERROR] messages above.")
    else:
        print(f"Done. Processed {total} file{'s' if total != 1 else ''}.")


if __name__ == "__main__":
    main()
