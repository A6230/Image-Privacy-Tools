#!/usr/bin/env python3
"""
strip_heic_metadata.py (v1.2 — 2025‑05‑25)
==========================================
Strip GPS/location and device‑identifying metadata from HEIC/HEIF files using
ExifTool.

Usage
-----
    python strip_heic_metadata.py DIR [--keep-datetimes] [--recursive]
                                     [--ext heic,heif]

Arguments
~~~~~~~~~
DIR                Folder containing images to process.
-r / --recursive   Recurse into sub‑folders.
-k / --keep-datetimes
                   After wiping everything, copy DateTimeOriginal/CreateDate/
                   ModifyDate back in (keeps capture time).
--ext EXT1,EXT2    Comma‑separated list of extensions (default: heic,heif).
                   Matching is case‑insensitive.

Dependencies
~~~~~~~~~~~~
  • Python 3.8+
  • ExifTool in PATH (`brew install exiftool` on macOS).

Revision history
~~~~~~~~~~~~~~~~
* **v1.0** – initial script.
* **v1.1** – case‑insensitive *.heic glob.
* **v1.2** – support .HEIF, custom --ext, better diagnostics.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
from typing import Iterable, List, Set


def exiftool_available() -> bool:
    """Return True if ExifTool is on PATH."""
    return shutil.which("exiftool") is not None


def strip_metadata(file: pathlib.Path, keep_datetimes: bool = False) -> None:
    """Strip metadata from *file*; optionally restore date/time tags."""
    if keep_datetimes:
        args: List[str] = [
            "exiftool",
            "-overwrite_original",
            "-all=",  # wipe everything
            "-tagsfromfile",
            "@",  # pull back from the in‑memory original
            "-datetimeoriginal",
            "-createdate",
            "-modifydate",
            str(file),
        ]
    else:
        args = ["exiftool", "-overwrite_original", "-all=", str(file)]

    subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def discover(
    root: pathlib.Path, exts: Set[str], recursive: bool = False
) -> Iterable[pathlib.Path]:
    """Yield files whose *suffix* (case‑folded) is in *exts*."""
    if recursive:
        iterator = root.rglob("*")
    else:
        iterator = root.iterdir()

    for p in iterator:
        if p.is_file() and p.suffix.lower().lstrip(".") in exts:
            yield p


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strip location & device metadata from HEIC/HEIF images.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "directory",
        type=pathlib.Path,
        help="Folder containing images to process.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process images in sub‑directories as well.",
    )
    parser.add_argument(
        "-k",
        "--keep-datetimes",
        action="store_true",
        help="Preserve DateTimeOriginal/CreateDate/ModifyDate tags.",
    )
    parser.add_argument(
        "--ext",
        default="heic,heif",
        help="Comma‑separated list of extensions to match (case‑insensitive).",
    )

    args = parser.parse_args()

    if not args.directory.exists():
        parser.error(f"Directory {args.directory} does not exist.")

    if not exiftool_available():
        sys.exit(
            "Error: ExifTool not found. Install it first (e.g. 'brew install exiftool')."
        )

    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}
    if not exts:
        parser.error("--ext yielded no valid extensions – give at least one.")

    files = list(discover(args.directory, exts, recursive=args.recursive))
    if not files:
        print(
            f"No files with extensions {', '.join(sorted(exts))} found in "
            f"{args.directory} (recursive={args.recursive})."
        )
        return

    count = 0
    for f in files:
        try:
            strip_metadata(f, keep_datetimes=args.keep_datetimes)
            count += 1
            rel = f.relative_to(args.directory)
            print(f"[OK] Stripped metadata from {rel}")
        except subprocess.CalledProcessError as exc:
            print(
                f"[ERROR] {f}: {exc.stderr.decode(errors='ignore').strip()}",
                file=sys.stderr,
            )

    print(f"Done. Processed {count} file{'s' if count != 1 else ''}.")


if __name__ == "__main__":
    main()
