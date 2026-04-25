#!/usr/bin/env python3
"""
Compress images in the uploads directory to under 500 KB.
Usage: python compress_uploads.py [uploads_dir]
"""

import io
import sys
from pathlib import Path

from PIL import Image

TARGET_BYTES = 500 * 1024
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def compress(path: Path) -> tuple[int, int]:
    original_size = path.stat().st_size
    if original_size <= TARGET_BYTES:
        return original_size, original_size

    img = Image.open(path)

    # Strip EXIF and convert palette/RGBA to RGB for JPEG output
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    suffix = path.suffix.lower()
    fmt = "JPEG" if suffix in (".jpg", ".jpeg") else suffix.lstrip(".").upper()

    # Try decreasing quality until we hit the target
    for quality in range(85, 39, -5):
        buf = io.BytesIO()
        save_kwargs = {"format": fmt, "optimize": True}
        if fmt in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
        img.save(buf, **save_kwargs)
        if buf.tell() <= TARGET_BYTES:
            path.write_bytes(buf.getvalue())
            return original_size, path.stat().st_size

    # Last resort: save at quality=40 regardless
    buf = io.BytesIO()
    save_kwargs = {"format": fmt, "optimize": True}
    if fmt in ("JPEG", "WEBP"):
        save_kwargs["quality"] = 40
    img.save(buf, **save_kwargs)
    path.write_bytes(buf.getvalue())
    return original_size, path.stat().st_size


def main():
    uploads_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("uploads")
    if not uploads_dir.is_dir():
        print(f"Directory not found: {uploads_dir}")
        sys.exit(1)

    images = [p for p in uploads_dir.iterdir() if p.suffix.lower() in EXTENSIONS]
    if not images:
        print("No images found.")
        return

    total_before = total_after = 0
    skipped = compressed = 0

    for path in sorted(images):
        before, after = compress(path)
        total_before += before
        total_after += after
        if before == after:
            print(f"  skip  {path.name}  ({before/1024:.0f} KB)")
            skipped += 1
        else:
            pct = (1 - after / before) * 100
            print(f"  {before/1024:.0f} KB → {after/1024:.0f} KB  -{pct:.0f}%  {path.name}")
            compressed += 1

    print()
    print(f"{compressed} compressed, {skipped} already under {TARGET_BYTES//1024} KB")
    if compressed:
        saved = total_before - total_after
        print(f"Total saved: {saved/1024/1024:.1f} MB  ({total_before/1024/1024:.1f} MB → {total_after/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
