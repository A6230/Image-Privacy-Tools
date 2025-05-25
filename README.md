# Image Privacy Tools

This repository contains a single utility script for converting HEIC/HEIF
images (such as those airdropped from an iPhone) into JPEG files with **all
metadata removed**.  The resulting JPEGs are safe to upload without leaking
location or device information.

## Dependencies

- Python 3.8+
- [`pillow`](https://pypi.org/project/Pillow/) and
  [`pillow-heif`](https://pypi.org/project/pillow-heif/)

On macOS you may also need `libheif` which can be installed via Homebrew:

```bash
brew install libheif
pip install pillow pillow-heif
```

## Usage

```bash
python sanitize_heic_to_jpg.py DIRECTORY [options]
```

Options:

- `-r`, `--recursive` – process images in sub‑directories as well
- `-q`, `--quality` – JPEG quality between 1 and 100 (default `90`)
- `--delete` – delete the original HEIC files after successful conversion
- `--ext` – comma-separated list of extensions to match (default
  `heic,heif`)

Example converting images in `~/Airdrop` and removing the originals:

```bash
python sanitize_heic_to_jpg.py ~/Airdrop --delete
```

This will create JPEG versions of all `*.heic` or `*.heif` files in the given
directory, ensuring no metadata is copied over.
